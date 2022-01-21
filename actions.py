# -*- coding: utf-8 -*-

# Import libraries
from core_functions import *
from wasabi import Printer
from toloka.streaming.event import AssignmentEvent
from typing import List
import collections

# Set up Printer
msg = Printer(pretty=True, timestamp=True, hide_animation=True)


class Verify:
    """
    This class defines an action for manually verifying crowdsourcing descriptions using other crowdsourced workers.

    To add this action to a TaskSequence, register this object with AssignmentObserver using the 'on_accepted' method.
    """
    def __init__(self, task, configuration):
        """
        This function initialises the manual verification mechanism.

        Parameters:
            task: An object that inherits from the CrowdsourcingTask class.
            configuration: A string object that defines a path to a YAML file with configuration.

        Returns:
            None
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

                print(task)
                print(task.assignment.id)
                exit()

                # Add the answer to the queue
                self.queue[task.input_values['assignment_id']].append(answer)

                print(self.queue)








