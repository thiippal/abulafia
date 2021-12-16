# -*- coding: utf-8 -*-

import asyncio
from core_functions import *
from toloka.util.async_utils import AsyncMultithreadWrapper
from toloka.streaming import AssignmentsObserver, Pipeline, PoolStatusObserver
from wasabi import Printer

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
        header = ('Name', 'Input', 'Output', 'Pool ID')
        data = []

        # Loop over the tasks
        for task in sequence:

            # Collect input and output data from the configuration
            inputs = [f'{k} ({v})' for k, v in task.conf['data']['input'].items()]
            outputs = [f'{k} ({v})' for k, v in task.conf['data']['output'].items()]

            # Append data as a tuple to the list
            data.append((task.name, ', '.join(inputs), ', '.join(outputs), task.pool.id))

        # Print a table with inputs and outputs
        msg.table(data=data, header=header, divider=True)

        # Create the pipeline
        self.create_pipeline()

    def start(self):

        # Create an event loop
        loop = asyncio.get_event_loop()

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

            # Call the Toloka pipeline() method within the event loop
            loop.run_until_complete(self.pipeline.run())

        finally:

            # Finish the event loop
            loop.close()

            msg.good(f'Successfully completed the task sequence')

    def create_pipeline(self):

        # Create an asyncronous client
        async_client = AsyncMultithreadWrapper(self.client)

        # Loop over the tasks and create an AssignmentsObserver object for each task. Exam tasks
        # are excluded, because they do not require observers, as they do not generate further
        # tasks.
        a_observers = {task.name: AssignmentsObserver(async_client, task.pool.id)
                       for task in self.sequence if not task.exam}

        # Set up pool observers for monitoring all pool states
        p_observers = {task.name: PoolStatusObserver(async_client, task.pool.id)
                       for task in self.sequence}

        # Create a Toloka Pipeline object and register observers
        self.pipeline = Pipeline()

        # Register each assignment observer with the Pipeline object
        for name, a_observer in a_observers.items():

            self.pipeline.register(observer=a_observer)

            msg.info(f'Registered an assignments observer for task {name}')

        # Register each pool observer and actions
        for name, p_observer in p_observers.items():

            p_observer.on_closed(lambda pool: msg.info(f'Closed pool with ID {pool.id}'))
            p_observer.on_open(lambda pool: msg.info(f'Opened pool with ID {pool.id}'))

            self.pipeline.register(observer=p_observer)

            msg.info(f'Registered a pool observer for task {name}')

        # Create a dictionary of CrowdsourcingTasks keyed by their names
        task_objs = {task.name: task for task in self.sequence}

        # Loop over the observers and get the actions configuration to determine task flow
        for name, observer in a_observers.items():

            # Get the CrowdsourcingTask object from the TaskSequence by matching its name
            current_task = task_objs[name]

            # Check if actions have been configured
            if current_task.action_conf is not None:

                if 'on_accepted' in current_task.action_conf:

                    if type(current_task.action_conf['on_accepted']) == str:

                        # Attempt to register the action with the AssignmentObserver. If a task is
                        # accepted, it will be sent to the CrowdsourcingTask object defined in the
                        # configuration.
                        try:

                            observer.on_accepted(task_objs[current_task.action_conf['on_accepted']])

                            msg.info(f'Setting up a connection from {name} to '
                                     f'{task_objs[current_task.action_conf["on_accepted"]].name} '
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
                        observer.on_submitted(task_objs[current_task.action_conf['on_submitted']])

                        msg.info(f'Setting up a connection from {name} to '
                                 f'{task_objs[current_task.action_conf["on_submitted"]].name} '
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
                        observer.on_rejected(task_objs[current_task.action_conf['on_rejected']])

                        msg.info(f'Setting up a connection from {name} to '
                                 f'{task_objs[current_task.action_conf["on_rejected"]].name} '
                                 f'on rejection ...')

                    except KeyError:

                        raise_error(f'Could not find a CrowdsourcingTask object named '
                                    f'{current_task.action_conf["on_rejected"]} in the '
                                    f'TaskSequence. Please check the configuration '
                                    f'under the key "actions"!')
