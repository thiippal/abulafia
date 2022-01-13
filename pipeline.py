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

    """
    def __init__(self, sequence, client):
        """

        """
        # Set up attributes
        self.complete = False       # Tracks if all tasks have been completed
        self.sequence = sequence    # A list of CrowdsourcingTask objects
        self.client = client        # A Toloka Client object
        self.pipeline = None        # Placeholder for a Toloka Pipeline object

        msg.info(f'Creating a task sequence')

        # Loop over the tasks to verify that they are connected properly
        for task in sequence:

            # Check if actions have been defined in the configuration
            if task.action_conf:

                # Check if the next task has been defined in the configuration
                if task.action_conf['next']:

                    # Fetch the name of the next task from the configuration
                    next_task = task.action_conf['next']

                    # Check that the next task exists in the task sequence
                    if next_task not in [task.name for task in sequence]:

                        raise_error(f'Cannot find a task named {next_task} in the task sequence. '
                                    f'Please check the name of the task under the key '
                                    f'"actions/next" in the configuration file.')

        msg.info(f'Printing tasks, inputs and outputs')

        # Set up headers and a placeholder for data
        header = ('Name', 'Input', 'Output', 'Pool ID', 'Project ID', 'Pool type')
        data = []

        # Loop over the tasks
        for task in sequence:

            # Check if training has been defined
            if task.training:

                # Collect input and output data from the configuration
                inputs = [f'{k} ({v})' for k, v in task.conf['training']['data']['input'].items()]
                outputs = [f'{k} ({v})' for k, v in task.conf['training']['data']['output'].items()]

                # Append data as a tuple to the list
                data.append((task.name, ', '.join(inputs), ', '.join(outputs), task.pool.id,
                             task.training.id, 'Training'))

            # Continue to process exam and ordinary pools
            pool_type = 'Pool' if not task.exam else 'Exam'

            # Collect input and output data from the configuration
            inputs = [f'{k} ({v})' for k, v in task.conf['data']['input'].items()]
            outputs = [f'{k} ({v})' for k, v in task.conf['data']['output'].items()]

            # Append data as a tuple to the list
            data.append((task.name, ', '.join(inputs), ', '.join(outputs), task.pool.id,
                         task.project.id, pool_type))

        # Print a table with inputs and outputs
        msg.table(data=data, header=header, divider=True)

        # Create the pipeline
        self.create_pipeline()

    def start(self):

        try:

            msg.info(f'Starting the task sequence')

            # Open all pools in the sequence that contain tasks. Note that pools without tasks cannot
            # be opened: they will be opened when tasks are added to them by these initial tasks.
            for task in self.sequence:

                if task.tasks is not None:

                    # Open main pool
                    self.client.open_pool(pool_id=task.pool.id)

                if task.training is not None:

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

                    if task.training is not None:

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

                    if task.pool.is_open():

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

                    # Get the output DataFrame for each task; assign under attribute 'output_data'
                    task.output_data = self.client.get_assignments_df(pool_id=task.pool.id)

                    # Check if the output should be written to disk
                    if task.action_conf['output']:

                        # Write the DataFrame to disk
                        task.output_data.to_csv(f'{task.name}_{task.pool.id}.csv')

                        msg.good(f'Wrote data for task {task.name} ({task.pool.id}) to disk.')

    def create_pipeline(self):

        # Create an asyncronous client
        async_client = AsyncMultithreadWrapper(self.client)

        # Loop over the tasks and create an AssignmentsObserver object for each task. Exam tasks
        # do not require observers, and they do not create further tasks.
        a_observers = {task.name: AssignmentsObserver(async_client, task.pool.id)
                       for task in self.sequence if not task.exam}

        # Set up pool observers for monitoring all pool states
        p_observers = {task.name: PoolStatusObserver(async_client, task.pool.id)
                       for task in self.sequence if not task.exam}

        # Create a Toloka Pipeline object and register observers; call observers every 15 seconds
        self.pipeline = Pipeline(period=datetime.timedelta(seconds=12))

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

                if type(current_task.action_conf['on_accepted']) == str:

                    # Attempt to register the action with the AssignmentObserver. If a task is
                    # accepted, it will be sent to the CrowdsourcingTask object defined in the
                    # configuration.
                    try:

                        observer.on_accepted(tasks[current_task.action_conf['on_accepted']])

                        msg.info(f'Setting up a connection from {name} ({current_task.pool.id})'
                                 f' to {tasks[current_task.action_conf["on_accepted"]].name} '
                                 f' ({tasks[current_task.action_conf["on_accepted"]].pool.id}) '
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

                        msg.info(f'Setting up a connection from {name} ({current_task.pool.id})'
                                 f' to {tasks[current_task.action_conf["on_submitted"]].name} '
                                 f' ({tasks[current_task.action_conf["on_submitted"]].pool.id}) '
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

                        msg.info(f'Setting up a connection from {name} ({current_task.pool.id})'
                                 f' to {tasks[current_task.action_conf["on_rejected"]].name} '
                                 f' ({tasks[current_task.action_conf["on_rejected"]].pool.id}) '
                                 f'on rejected ...')

                    except KeyError:

                        raise_error(f'Could not find a CrowdsourcingTask object named '
                                    f'{current_task.action_conf["on_rejected"]} in the '
                                    f'TaskSequence. Please check the configuration '
                                    f'under the key "actions"!')
