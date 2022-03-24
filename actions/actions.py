# -*- coding: utf-8 -*-

# Import libraries
from functions.core_functions import *
from wasabi import Printer
import toloka.client as toloka
from toloka.streaming.event import AssignmentEvent
from toloka.client.exceptions import IncorrectActionsApiError
from typing import List
import collections

# Set up Printer
msg = Printer(pretty=True, timestamp=True, hide_animation=True)


class Verify:
    """
    This class defines an action for manually verifying crowdsourcing descriptions using other crowdsourced workers.

    To add this action to a TaskSequence, register this object with AssignmentObserver using the 'on_accepted' method.
    """
    def __init__(self, configuration, task):
        """
        This function initialises the manual verification mechanism.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            task: An object that inherits from the CrowdsourcingTask class.

        Returns:
            None
        """
        self.conf = read_configuration(configuration)
        self.name = self.conf['name']
        self.task = task
        self.client = self.task.client
        self.queue = collections.defaultdict(list)
        self.aggregator = None

    def __call__(self, events: List[AssignmentEvent]) -> None:

        # TODO Make the processing of results fairer by rejecting task suites only when a given percentage of tasks
        # TODO are rejected. One possible solution would be to fetch rejected Task objects and send them back to the
        # TODO origin pool for re-completion.

        # Loop over the list of incoming AssignmentEvent objects
        for event in events:

            # Zip and iterate over tasks and solutions in each event
            for task, solution in zip(event.assignment.tasks, event.assignment.solutions):

                # Retrieve the answer
                answer = solution.output_values[self.conf['data']['output']]

                # Add the answer to the queue under assignment id
                self.queue[task.input_values['assignment_id']].append(answer)

        # Set up a placeholder for processed task suites
        processed = []

        # Loop over the assignments in the queue
        for assignment_id, results in self.queue.items():

            try:

                # Accept the task suite if all assignments in the suite have been verified as correct
                if all(results) is True:

                    self.client.accept_assignment(assignment_id=assignment_id,
                                                  public_comment=self.conf['messages']['accepted'])

                    msg.good(f'Accepted assignment {assignment_id}')

                # Reject the task suite if all assignments in the suite have not been verified as correct
                if all(results) is not True:

                    self.client.reject_assignment(assignment_id=assignment_id,
                                                  public_comment=self.conf['messages']['rejected'])

                    msg.warn(f'Rejected assignment {assignment_id}')

            # Catch the error that might be raised by manually accepting/rejecting tasks in
            # the web interface
            except IncorrectActionsApiError:

                msg.warn(f'Could not {"accept" if all(results) == True else "reject"} assignment {assignment_id}')

            # Append the task suite to the list of processed suites
            processed.append(assignment_id)

        # Delete the assignment from the list of processed task suites
        for assignment_id in processed:

            processed.remove(assignment_id)


class Aggregate:
    """
    This class can be used to aggregate crowdsourced answers.
    """
    def __init__(self, configuration, task):

        self.conf = read_configuration(configuration)

    def __call__(self):

        raise NotImplementedError


class Forward:
    """
    This class defines an action for forwarding completed tasks to specific pools based on values.

    For example, if a task receives the value True, it can be forwarded to Pool 1, whereas tasks with value False
    will be forwarded to Pool 2.

    Parameters:
        configuration: A dict that includes the configuration for a CrowdsourcingTask object.
        task: An object that inherits from the CrowdsourcingTask class.

    Returns:
        None
    """

    def __init__(self, configuration, client, targets):

        self.conf = read_configuration(configuration)
        self.name = self.conf['name']
        self.client = client

        # Possible outputs for the task (e.g. true and false) and their forward pools
        self.outputs = self.conf['actions']['on_result']

        # Check if some outputs shoulf be accepted or rejected (these are not forwarded like other tasks,
        # but accepted or rejected based on the output) and remove these from outputs
        self.reject = [k for k, v in self.outputs.items() if v == 'reject']
        [self.outputs.pop(k) for k in self.reject]

        self.accept = [k for k, v in self.outputs.items() if v == 'accept']
        [self.outputs.pop(k) for k in self.accept]

        # If no forward pools are configured for some outputs, they will not be forwarded
        self.dont_forward = [k for k, v in self.outputs.items() if v == None]
        [self.outputs.pop(k) for k in self.dont_forward]

        # Create mapping for output and the configured CrowdsourcingTask object of the forward pool
        self.name_mapping = {pool.name: pool for pool in targets}
        self.forward_pools = {output: self.name_mapping[name] for (output, name) in self.outputs.items()}

        # Initialize dictionary of key-list pairs. Keys are possible outputs for the task
        # and the lists are tasks to be forwarded.
        self.tasks_to_forward = collections.defaultdict(list)
        

    def __call__(self, events: List[AssignmentEvent]) -> None:

        # Loop over the list of incoming AssignmentEvent objects
        for event in events:

                for i in range(len(event.assignment.tasks)):

                    solution = event.assignment.solutions[i].output_values[self.conf['data']['output']]

                    # If performer verified the task as incorrect, reject the original assignment
                    # and, if configured in source pool under "on_reject", re-add the task to the pool
                    if solution in self.reject:

                        self.client.reject_assignment(assignment_id=event.assignment.tasks[i].input_values['assignment_id'],
                                                      public_comment="Assignment was verified incorrect by another user.")
                        msg.warn(f'Rejected assignment {event.assignment.tasks[i].input_values["assignment_id"]}')

                    # If performer verified the task as correct, accept original assignment and don't forward task
                    elif solution in self.accept:

                        self.client.accept_assignment(assignment_id=event.assignment.tasks[i].input_values['assignment_id'],
                                                      public_comment="Assignment was verified correct by another user.")
                        msg.good(f'Accepted assignment {event.assignment.tasks[i].input_values["assignment_id"]}')

                    # If no forward pool was configured, submit task without forwarding/accepting/rejecting
                    elif solution in self.dont_forward:

                        msg.good(f'Received a submitted assignment with output "{solution}"')

                    # Else, forward task according to configuration
                    else:

                        try:
                            task = toloka.Task(
                                pool_id = self.forward_pools[solution].pool.id,
                                input_values=event.assignment.tasks[i].input_values
                            )
                            self.tasks_to_forward[solution].append(task)

                        # Catch errors
                        except toloka.exceptions.ValidationApiError:

                            # Raise error
                            raise_error(f'Failed to forward assignment {event.assignment.tasks[i].input_values["assignment_id"]}')
              
        tasks_list = [task for l in self.tasks_to_forward.values() for task in l]

        if tasks_list:
            
            # Add tasks to defined pools
            self.client.create_tasks(tasks_list, allow_defaults=True, open_pool=True)

            # Print status if any tasks were forwarded on this call
            msg.good(f"Successfully forwarded {len(tasks_list)} {'tasks' if len(tasks_list) > 1 else 'task'}")

        # Tasks currently in lists have been forwarded, so reset lists
        self.tasks_to_forward = collections.defaultdict(list)
        tasks_list = []

