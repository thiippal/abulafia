# -*- coding: utf-8 -*-

# Import libraries
from wasabi import Printer
from toloka.streaming.observer import BaseObserver
from toloka.client.analytics_request import UniqueWorkersCountPoolAnalytics, ActiveWorkersByFilterCountPoolAnalytics, \
    SubmittedAssignmentsCountPoolAnalytics
from toloka.client.operations import Operation
from toloka.client.exceptions import DoesNotExistApiError


# Set up Printer
msg = Printer(pretty=True, timestamp=True, hide_animation=True)


class AnalyticsObserver(BaseObserver):

    def __init__(self, client, pool, **options) -> None:
        super().__init__()
        self.name = pool.id
        self.client = client
        self.operation = None
        self.pool = pool
        self.limit = options['max_performers'] if options and 'max_performers' in options else None
        self.limit_reached = False
        self.prev_result = None

    async def __call__(self):

        pass

    async def should_resume(self) -> bool:

        if self.operation is not None:

            # Fetch operation from Toloka
            operation = await self.client.get_operation(self.operation.id)

            # Check status
            if operation.status == Operation.Status.SUCCESS:

                for response in operation.details['value']:

                    # Check if pool should be closed after certain number of workers have
                    # submitted to the pool (this is used to limit the number of workers
                    # for exam pools with infinite overlap)
                    if self.limit and not self.limit_reached:

                        if response['request']['name'] == 'unique_workers_count' \
                                and response['result'] >= self.limit:

                            msg.warn(f'Maximum number of performers ({self.limit}) reached for '
                                     f'pool {self.pool.id}; closing pool ...')

                            self.limit_reached = True

                            await self.client.close_pool_async(pool_id=self.pool.id)

                            msg.good(f'Successfully closed pool {self.pool.id}')

                            # Manually close training pool(s) when exam pool is closed
                            try:

                                for training in await self.client.get_trainings(project_id=self.pool.project_id):
                                    await self.client.close_training_async(training_id=training.id)
                                    msg.good(f"Successfully closed training pool {training.id}")

                            except StopIteration:
                                
                                # If no training is found, continue as normal
                                pass

                            except DoesNotExistApiError:

                                # If a training is found, but it cannot be closed, raise warning
                                msg.warn(f"Attempted to close a training for pool {self.pool.id} that does not exist")

                    if response['request']['name'] == 'unique_workers_count' and not self.limit_reached:

                        # Check if number of submissions has changed: only print update 
                        # if there has been a change.
                        if response['result'] != self.prev_result:
                            
                            msg.info(f'{response["result"]} workers submitted to pool {self.pool.id}')
                            self.prev_result = response["result"]

            # If the operation is completed, reset the operation
            if operation.status.value in ['SUCCESS', 'FAIL']:

                self.operation = None

        if self.operation is None:

            # Create a new operation for analytics request
            self.operation = await self.create_operation()

        # Return False to prevent running forever
        return False

    async def create_operation(self):
        """
        This function creates an operation for requesting pool analytics from Toloka.

        Returns:
            An Operation object.
        """
        # Define analytics to be requested
        stat_requests = [
            UniqueWorkersCountPoolAnalytics(subject_id=self.pool.id),
            ActiveWorkersByFilterCountPoolAnalytics(subject_id=self.pool.id, interval_hours=1),
            SubmittedAssignmentsCountPoolAnalytics(subject_id=self.pool.id)
        ]

        # Get the analytics and return
        operation = await self.client.get_analytics(stat_requests)

        return operation
