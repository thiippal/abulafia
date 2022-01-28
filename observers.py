# -*- coding: utf-8 -*-

# Import libraries
from wasabi import Printer
from toloka.streaming.observer import BaseObserver
from toloka.client.analytics_request import UniqueWorkersCountPoolAnalytics, ActiveWorkersByFilterCountPoolAnalytics
from toloka.client.operations import Operation


# Set up Printer
msg = Printer(pretty=True, timestamp=True, hide_animation=True)


class AnalyticsObserver(BaseObserver):

    def __init__(self, client, pool, **options) -> None:
        super().__init__()
        self.name = 'Analytics'
        self.client = client
        self.operation = None
        self.pool = pool
        self.limit = options['max_performers'] if options and 'max_performers' in options else None

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
                    if self.limit:

                        if response['request']['name'] == 'unique_workers_count' and response['result'] >= 0:

                            msg.warn(f'Maximum number of performers ({self.limit}) reached for '
                                     f'pool {self.pool.id}; closing pool ...')

                            await self.client.close_pool_async(pool_id=self.pool.id)

                            msg.good(f'Successfully closed pool {self.pool.id}')

                    # print(response)
                    # print("\n")
                    # print(response['request']['name'], response['result'])
                    # exit()

            # If the operation is completed, reset the operation
            if operation.status in ['SUCCESS', 'FAIL']:

                self.operation = None

        if self.operation is None:

            # Create a new operation for analytics request
            self.operation = await self.create_operation()

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
        ]

        # Get the analytics and return
        operation = await self.client.get_analytics(stat_requests)

        return operation
