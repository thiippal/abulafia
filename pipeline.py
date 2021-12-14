# -*- coding: utf-8 -*-

from core_functions import *
from toloka.streaming import AssignmentsObserver, Pipeline
from wasabi import Printer

msg = Printer(pretty=True, timestamp=True, hide_animation=True)


class TaskSequence:
    """

    """
    def __init__(self, sequence):
        """

        """
        # Set up attributes
        self.complete = False       # Tracks if all tasks have been completed
        self.sequence = sequence    # A list of CrowdsourcingTask objects

        # Print status message
        msg.info(f'Creating a task sequence ...')

        # Loop over the tasks to verify that they are connected properly
        for task in sequence:

            # Set current task name
            current = task.name

            # Check if the next task has been defined
            if task.action_conf and task.action_conf['next']:

                next = task.action_conf['next']

                if next not in [task.name for task in sequence]:

                    raise_error(f'Cannot find a task named {next} in the task sequence. '
                                f'Please check the name of the task under the key "actions/next" '
                                f'in the configuration file.')

        # Set up
        msg.info(f'Printing tasks, inputs and outputs ...')

        # Set up headers and a placeholder for data
        header = ('Name', 'Input', 'Output')
        data = []

        # Loop over the tasks
        for task in sequence:

            # Collect input and output data from the configuration
            inputs = [f'{k} ({v})' for k, v in task.conf['data']['input'].items()]
            outputs = [f'{k} ({v})' for k, v in task.conf['data']['output'].items()]

            # Append data as a tuple to the list
            data.append((task.name, ', '.join(inputs), ', '.join(outputs)))

        # Print a table with inputs and outputs
        msg.table(data=data, header=header, divider=True)

    def start(self):

        # Loop over the tasks and create an AssignmentsObserver object for each task.
        # Exam tasks are excluded, because they do not require observers.
        observers = {task.name: AssignmentsObserver(task.client, task.pool.id)
                     for task in self.sequence if not task.exam}

        # Create a Toloka Pipeline object and register observers
        pipeline = Pipeline()

        # Register each observer from the list of observers with the Pipeline object
        for observer in observers.values():

            pipeline.register(observer)

        # Create a dictionary of CrowdsourcingTasks keyed by their names; exclude exams
        task_objs = {task.name: task for task in self.sequence if not task.exam}

        # Loop over the observers and get the actions configuration to determine task flow
        for name, observer in observers.items():

            # Get the CrowdsourcingTask object from the TaskSequence by matching its name
            current_task = task_objs[name]

            # Check if actions have been configured
            if current_task.action_conf is not None:

                if 'on_accepted' in current_task.action_conf:

                    if type(current_task.action_conf['on_accepted']) == str:

                        try:

                            # Register the action with the AssignmentObserver. If a task is accepted,
                            # it will be sent to the CrowdsourcingTask object defined in the
                            # configuration.
                            observer.on_accepted(task_objs[current_task.action_conf['on_accepted']])

                            msg.info(f'Setting up a connection from {name} to '
                                     f'{task_objs[current_task.action_conf["on_accepted"]].name} '
                                     f'on acceptance ...')

                        except KeyError:

                            raise_error(f'Could not find a CrowdsourcingTask object named '
                                        f'{current_task.action_conf["on_accepted"]} in the '
                                        f'TaskSequence. Please check the configuration '
                                        f'under the key "actions"!')

                    # TODO This needs to be completed.
                    if type(current_task.action_conf['on_accepted']) == dict:

                        for key, value in current_task.action_conf['on_accepted'].items():

                            try:

                                pass

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

        # TODO When the connections between tasks have been set, open all pools that contain tasks
