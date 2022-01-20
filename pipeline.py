# -*- coding: utf-8 -*-

import asyncio
import datetime
from core_functions import *
from toloka.util.async_utils import AsyncMultithreadWrapper
from toloka.streaming import AssignmentsObserver, Pipeline, PoolStatusObserver
from wasabi import Printer

# Set up Printer
msg = Printer(pretty=True, timestamp=True, hide_animation=True)


class TaskSequence:
    """
    This class allows defining a sequence of crowdsourcing tasks on Toloka.

    """
    def __init__(self, sequence, client):
        """
        This function initialises the TaskSequence class.

        Parameters:
            sequence: A list of objects that inherit from the CrowdsourcingTask class.
            client: A TolokaClient object with valid credentials.
        """
        # Set up attributes
        self.complete = False       # Tracks if all tasks have been completed
        self.sequence = sequence    # A list of CrowdsourcingTask objects
        self.client = client        # A Toloka Client object
        self.pipeline = None        # Placeholder for a Toloka Pipeline object

        msg.info(f'Creating a task sequence')

        # Verify that connections between tasks have been specified in the configuration
        verify_connections(self.sequence)

        msg.info(f'Printing tasks, inputs and outputs')
        create_pool_table(self.sequence)

        # Create the pipeline
        self.create_pipeline()

    def start(self):

        try:

            msg.info(f'Starting the task sequence')

            # Open all pools in the sequence that contain tasks. Note that pools without tasks cannot
            # be opened: they will be opened when tasks are added to them by these initial tasks.
            for task in self.sequence:

                if hasattr(task, 'tasks') and task.tasks is not None:

                    # Open main pool
                    self.client.open_pool(pool_id=task.pool.id)

                if hasattr(task, 'training') and task.training is not None:

                    # Open training pool
                    self.client.open_pool(pool_id=task.training.id)

            # Set up a Toloka MetricCollectors for all pools
            proc_collector = create_process_collector(task_sequence=self)

            # Define an asynchronous function to run the MetricCollector and
            # the Pipeline objects at the same time
            async def main():

                # The 'ensure_future' method allows running the MetricCollector
                # in a fire-and-forget manner
                asyncio.ensure_future(proc_collector.run())

                # The Pipeline object needs to be awaited
                await asyncio.gather(self.pipeline.run())

            # Call the asynchronous function to start the collectors and pipeline
            asyncio.run(main())

        finally:

            # Collect pool statuses here
            status = []

            # Close all training and exam pools that may remain open after the pipeline finishes
            while not self.complete:

                for task in self.sequence:

                    if hasattr(task, 'training') and task.training is not None:

                        # Close main pool first, then the training
                        self.client.close_pool(pool_id=task.pool.id)

                        # Append current status to the collector
                        status.append(self.client.get_pool(pool_id=task.pool.id).is_open())

                        msg.info(f'Closed pool with ID {task.pool.id}')

                        if self.client.get_pool(pool_id=task.training.id).is_open():

                            # Close training pool
                            self.client.close_pool(pool_id=task.training.id)

                            # Append current training status to the collector
                            status.append(self.client.get_pool(pool_id=task.training.id).is_open())

                            msg.info(f'Closed pool with ID {task.training.id}')

                    if hasattr(task, 'pool') and task.pool.is_open():

                        # Close main pool
                        self.client.close_pool(pool_id=task.pool.id)

                        # Append current status to the collector
                        status.append(self.client.get_pool(pool_id=task.pool.id).is_open())

                        msg.info(f'Closed pool with ID {task.pool.id}')

                if not any(status):

                    self.complete = True

            msg.good(f'Successfully completed the task sequence')

            # Check the outputs
            if self.complete:

                # Check if tasks are supposed to output the results
                for task in self.sequence:

                    if hasattr(task, 'pool'):

                        # Get the output DataFrame for each task; assign under 'output_data'
                        task.output_data = self.client.get_assignments_df(pool_id=task.pool.id)

                        # Check if the output should be written to disk
                        try:

                            if 'output' in task.conf['actions']:

                                # Write the DataFrame to disk
                                task.output_data.to_csv(f'{task.name}_{task.pool.id}.csv')

                                msg.good(f'Wrote data for task {task.name} ({task.pool.id}) to disk.')

                        except KeyError:

                            pass

    def create_pipeline(self):

        # Create an asyncronous client
        async_client = AsyncMultithreadWrapper(self.client)

        # Loop over the tasks and create an AssignmentsObserver object for each task. Exam tasks
        # do not require observers, and they do not create further tasks.
        a_observers = {task.name: AssignmentsObserver(async_client, task.pool.id)
                       for task in self.sequence if hasattr(task, 'pool')
                       and not task.exam if hasattr(task, 'pool')}

        # Set up pool observers for monitoring all pool states
        p_observers = {task.name: PoolStatusObserver(async_client, task.pool.id)
                       for task in self.sequence if hasattr(task, 'pool')
                       and not task.exam if hasattr(task, 'pool')}

        # Create a Toloka Pipeline object and register observers; call observers every 15 seconds
        self.pipeline = Pipeline(period=datetime.timedelta(seconds=15))

        # Create a dictionary of CrowdsourcingTasks in the pipeline keyed by their names
        tasks = {task.name: task for task in self.sequence}

        # Register each assignment observer with the Pipeline object
        for name, a_observer in a_observers.items():

            self.pipeline.register(observer=a_observer)

            msg.info(f'Registered an assignments observer for task {name} ({tasks[name].pool.id})')

        # Register each pool observer and actions
        for name, p_observer in p_observers.items():

            p_observer.on_closed(lambda pool: msg.info(f'Closed pool with ID {pool.id}'))
            p_observer.on_open(lambda pool: msg.info(f'Opened pool with ID {pool.id}'))

            self.pipeline.register(observer=p_observer)

            msg.info(f'Registered a pool observer for task {name} ({tasks[name].pool.id})')

        # Loop over the observers and get the actions configuration to determine task flow
        for name, observer in a_observers.items():

            # Get the CrowdsourcingTask object from the TaskSequence by matching its name
            current_task = tasks[name]

            # Check if actions have been configured
            if current_task.action_conf is not None:

                if 'on_accepted' in current_task.action_conf:

                    # Attempt to register the action with the AssignmentObserver. If a task is
                    # accepted, it will be sent to the CrowdsourcingTask object defined in the
                    # configuration.
                    try:

                        observer.on_accepted(tasks[current_task.action_conf['on_accepted']])

                        msg.info(f'Setting up a connection from {name} '
                                 f'to {tasks[current_task.action_conf["on_accepted"]].name} '
                                 f'on acceptance ...')

                    except KeyError:

                        raise_error(f'Could not find a CrowdsourcingTask object named '
                                    f'{current_task.action_conf["on_accepted"]} in the '
                                    f'TaskSequence. Please check the configuration '
                                    f'under the key "actions"!')

                if 'on_submitted' in current_task.action_conf:

                    try:

                        # Register the action with the AssignmentObserver. If a task is submitted,
                        # it will be sent to the CrowdsourcingTask object defined in the configuration.
                        observer.on_submitted(tasks[current_task.action_conf['on_submitted']])

                        msg.info(f'Setting up a connection from {name} '
                                 f'to {tasks[current_task.action_conf["on_submitted"]].name} '
                                 f'on submission ...')

                    except KeyError:

                        raise_error(f'Could not find a CrowdsourcingTask object named '
                                    f'{current_task.action_conf["on_submitted"]} in the '
                                    f'TaskSequence. Please check the configuration '
                                    f'under the key "actions"!')

                if 'on_rejected' in current_task.action_conf:

                    try:

                        # Register the action with the AssignmentObserver. If a task is rejected,
                        # it will be sent to the CrowdsourcingTask object defined in the configuration.
                        observer.on_rejected(tasks[current_task.action_conf['on_rejected']])

                        msg.info(f'Setting up a connection from {name}'
                                 f'to {tasks[current_task.action_conf["on_rejected"]].name} '
                                 f'on rejected ...')

                    except KeyError:

                        raise_error(f'Could not find a CrowdsourcingTask object named '
                                    f'{current_task.action_conf["on_rejected"]} in the '
                                    f'TaskSequence. Please check the configuration '
                                    f'under the key "actions"!')
