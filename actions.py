# -*- coding: utf-8 -*-

# Import libraries
from core_functions import *
from wasabi import Printer
from toloka.streaming.event import AssignmentEvent
import collections

# Set up Printer
msg = Printer(pretty=True, timestamp=True, hide_animation=True)


class HumanVerification:
    """
    This class allows defining a human verification mechanism for a CrowdsourcingTask object within
    a TaskSequence object.

    To add this mechanism to a TaskSequence, register this object with an assignments observer
    using 'on_accepted'.
    """
    def __init__(self, task, configuration):
        """
        This function initialises the human verification mechanism.

        Parameters:
            task: An object that inherits from the CrowdsourcingTask class.
            configuration: A string object that defines a path to a YAML file with configuration.

        Returns:
            None.
        """
        self.conf = read_configuration(configuration)
        self.name = self.conf['name']
        self.task = task
        self.client = self.task.client
        self.queue = collections.defaultdict(list)

    def __call__(self, events: List[AssignmentEvent]) -> None:

        for event in events:

            for task, solution in zip(event.assignment.tasks, event.assignment.solutions):

                # Retrieve the answer
                answer = (solution.output_values[self.conf['data']['output']],
                          event.assignment.user_id)

                # Add the answer to the queue
                self.queue[task.input_values['assignment_id']].append(answer)








