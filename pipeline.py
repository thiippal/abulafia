# -*- coding: utf-8 -*-

from core import *
from tasks import InputData, CrowdsourcingTask
from toloka.streaming import AssignmentsObserver, Pipeline
from wasabi import Printer

msg = Printer(pretty=True, timestamp=True, hide_animation=True)


class TaskSequence:
    """
    This class allows chaining together multiple InputData and CrowdsourcingTask objects into a
    crowdsourcing pipeline.
    """
    def __init__(self, first, last):
        """
        This function initialises the class by looping through the Tasks in the Pipeline.

        Parameters:

            first: The first Task or InputData in the Pipeline.
            last: The last Task in the Pipeline.

        Returns:

            A TaskSequence object.
        """
        # Set up attributes
        self.complete = False       # Tracks if all tasks have been completed
        self.input_data = None      # The input data to a Pipeline is assumed to be in the first layer
        self.output_data = None     # A placeholder for the output data
        self.tasks = None           # A placeholder for tasks

        # Print status message
        msg.info(f'Creating a Pipeline ...')

        # Set parse to True to begin looping through the Tasks
        parse = True

        # Create a list for tasks
        tasks = []

        # Start from the end of the list by setting the last Task as current task
        current = last

        # Enter a while loop for resolving the relations between Tasks
        while parse:

            # Start by appending the current Task into the list
            tasks.append(current)

            # Print status message
            msg.info(f'Added a task named {current.name} to the Pipeline')

            # Attempt to update the 'current' variable by retrieving the previous task from the
            # Task that was last added to the list
            try:

                current = tasks[-1].prev_task

            # If this raises an AttributeError, run the following block
            except AttributeError:

                # Check if the item last added to the 'tasks' list is the first one in the Pipeline
                if tasks[-1] == first:

                    # Quit parsing the relationships
                    parse = False

        # Reverse the order of the tasks in the list, since we began from the end
        tasks.reverse()

        # Assign tasks to attribute
        self.tasks = tasks

        # Get the input data for the first task and assign this to the pipeline
        self.input_data = tasks[0].input_data

        # Set up
        msg.info(f'Printing tasks, inputs and outputs ...')

        # Set up headers and a placeholder for data
        header = ('Name', 'Input values', 'Output values', 'Notes')
        data = []

        # Loop over the tasks
        for task in tasks:

            # Handle actual tasks first
            if type(task) != InputData:

                # Collect input and output data from the configuration
                inputs = [f'{k} ({v})' for k, v in task.conf['data']['input'].items()]
                outputs = [f'{k} ({v})' for k, v in task.conf['data']['output'].items()]

                # Append data as a tuple to the list
                data.append((task.name, ', '.join(inputs), ', '.join(outputs), 'exam' if task.exam else ''))

            # Process InputData tasks
            else:

                data.append((task.name, 'n/a', 'n/a', 'input'))

        # Print a table with inputs and outputs
        msg.table(data=data, header=header, divider=True)

    def start(self):

        # Loop over the tasks and create an AssignmentsObserver object for each task
        observers = {task.name: AssignmentsObserver(task.client, task.pool.id)
                     for task in self.tasks
                     if type(task) != InputData}

        # Create a Toloka Pipeline object and register observers
        pipeline = Pipeline()

        # Register each observer from the list of observers with the Pipeline object
        for observer in observers.values():

            pipeline.register(observer)

        # Create a dictionary of CrowdsourcingTasks keyed by their names
        task_objs = {task.name: task for task in self.tasks}

        # Loop over the observers and get the actions configuration to determine task flow
        for name, observer in observers.items():

            # Get the CrowdsourcingTask object from the TaskSequence by matching its name
            current_task = task_objs[name]

            # Check if actions have been configured
            if current_task.action_conf is not None:

                if 'on_accepted' in current_task.action_conf:

                    try:

                        # Register the action with the AssignmentObserver. If a task is accepted,
                        # it will be sent to the CrowdsourcingTask object defined in the configuration.
                        observer.on_accepted(task_objs[current_task.action_conf['on_accepted']])

                    except KeyError:

                        raise_error(f'Could not find a CrowdsourcingTask object named '
                                    f'{current_task.action_conf["on_accepted"]} in the '
                                    f'TaskSequence. Please check the configuration '
                                    f'under the key "actions"!')

                if 'on_submitted' in current_task.action_conf:

                    pass

                if 'on_rejected' in current_task.action_conf:

                    pass

                if 'on_created' in current_task.action_conf:

                    # TODO Could this be used for monitoring?
                    pass

        exit()

        # TODO Use the configuration and AssignmentsObserver to handle task flow between pools as instructed here:
        # https://github.com/Toloka/toloka-kit/blob/main/examples/6.streaming_pipelines/streaming_pipelines.ipynb

        # TODO Start by creating a Toloka Pipeline object and register AssignmentObserver objects for each pool.
        # TODO Create the AssignmentsObserver objects first and assign them into a dict

        # TODO Next, use the AssignmentObserver on_submitted() and on_accepted() methods to handle task flow.

        # TODO Then create a Pipeline and add the AssignmentsObservers to the Pipeline

        # TODO This probably requires adding configuration parameters to JSON for task flow. Refer to the tasks
        # by their name, e.g. "on_reject": "main_pool", "on_accept": "aggregation".

        pass