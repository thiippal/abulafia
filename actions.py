# -*- coding: utf-8 -*-

# Import libraries
from core_functions import *
from wasabi import Printer
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

    def __call__(self, events: List[AssignmentEvent], **options) -> None:

        # Loop over the list of incoming AssignmentEvent objects
        for event in events:

            # Zip and iterate over tasks and solutions in each event
            for task, solution in zip(event.assignment.tasks, event.assignment.solutions):

                # Retrieve the answer
                answer = (solution.output_values[self.conf['data']['output']],
                          event.assignment.user_id)

                # Add the answer to the queue
                self.queue[task.input_values['assignment_id']].append(answer)

        if options and 'aggregate' in options:

            pass

            # TODO For some algorithms, one needs to get all annotations – monitor pool status?

        # If no aggregation is to be performed, accept/reject incoming assignments
        else:

            # TODO This does not work as expected;

            for assignment_id, results in self.queue.items():

                for result in results:

                    try:

                        if result == True:

                            self.client.accept_assignment(assignment_id=assignment_id,
                                                          public_comment=self.conf['messages']['accept'])

                            msg.good(f'Accepted assignment {assignment_id}')

                        if result == False:

                            self.client.reject_assignment(assignment_id=assignment_id,
                                                          public_comment=self.conf['messages']['reject'])

                            msg.warn(f'Rejected assignment {assignment_id}')

                    # Catch the error that might be raised by manually accepting/rejecting tasks in
                    # the web interface
                    except IncorrectActionsApiError:

                        msg.warn(f'Could not {"accept" if result else "reject"} assignment {assignment_id}')

            # Delete the assignment from the queue
            del self.queue[assignment_id]


class Aggregate:
    """
    This class can be used to aggregate crowdsourced answers.
    """
    def __init__(self, configuration):

        self.conf = read_configuration(configuration)

    def __call__(self):

        raise NotImplementedError


class Forward:
    """
    This class defines an action for forwarding completed tasks to specific pools based on values.

    For example, if a task receives the value True, it can be forwarded to Pool 1, whereas tasks with value False
    will be forwarded to Pool 2.
    """

    def __init__(self, configuration):

        self.conf = read_configuration(configuration)

    def __call__(self):

        raise NotImplementedError
