# -*- coding: utf-8 -*-

# Import libraries
from ..functions.core_functions import *
from wasabi import Printer
import contextlib
import io
import toloka.client as toloka
from toloka.streaming.event import AssignmentEvent
from toloka.client.exceptions import IncorrectActionsApiError
from typing import List, Union
import collections
import pandas as pd
import json

# Set up Printer
msg = Printer(pretty=True, timestamp=True, hide_animation=True)

f = io.StringIO()
with contextlib.redirect_stderr(f):
    from crowdkit.aggregation.classification.dawid_skene import DawidSkene
    from crowdkit.aggregation.classification.majority_vote import MajorityVote
    from crowdkit.aggregation.classification.gold_majority_vote import GoldMajorityVote
    from crowdkit.aggregation.classification.m_msr import MMSR
    from crowdkit.aggregation.classification.wawa import Wawa
    from crowdkit.aggregation.classification.zero_based_skill import ZeroBasedSkill
    from crowdkit.aggregation.classification.glad import GLAD
warn = f.getvalue()

if warn.startswith("None of PyTorch"):
    msg.warn(f"Could not find a working installation of PyTorch or TensorFlow, one of which is "
             f"needed for the crowd-kit aggregators to function. Cancelling pipeline.", exits=1)


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

    Parameters:
        configuration: A string object that defines a path to a YAML file with configuration.
        task: Crowdsourcing Task of which results will be aggregated.
        forward: Forward object with which the aggregated tasks will be forwarded to the next pool or accepted/rejected.

    Returns:
        None
    
    """
    def __init__(self, configuration, task, forward=None):

        self.task = task
        self.conf = read_configuration(configuration)
        self.name = self.conf['name']

        self.forward = forward

        self.majority_vote = True if self.conf['method'] == 'majority_vote' else False
        self.dawid_skene = True if self.conf['method'] == 'dawid_skene' else False
        self.gold_majority_vote = True if self.conf['method'] == 'gold_majority_vote' else False
        self.mmsr = True if self.conf['method'] == 'mmsr' else False
        self.wawa = True if self.conf['method'] == 'wawa' else False
        self.zero_based_skill = True if self.conf['method'] == 'zero_based_skill' else False
        self.glad = True if self.conf['method'] == "glad" else False

        self.result = None
        self.prev_assignments = set()

        self.complete = False

    def __call__(self, pool: toloka.Pool) -> None:

        assignments = list(self.task.client.get_assignments(pool_id=pool.id, status=[toloka.Assignment.SUBMITTED, toloka.Assignment.ACCEPTED]))

        if assignments:
            a_dict = {"task": [], "inputs": [], "label": [], "worker": [], "id": []}

            input_data = list(self.task.data_conf['input'].keys())[0]
            output_data = list(self.task.data_conf['output'].keys())[0]

            for a in assignments:
                if a.id not in self.prev_assignments:
                    for i in range(len(a.tasks)):
                        a_dict['task'].append(a.tasks[i].input_values[input_data])
                        a_dict['inputs'].append(a.tasks[i].input_values)
                        a_dict['label'].append(a.solutions[i].output_values[output_data])
                        a_dict['worker'].append(a.user_id)
                        a_dict['id'].append(a.id)
                    self.prev_assignments.add(a.id)

            df = pd.DataFrame(data=a_dict)

            if self.majority_vote:

                self.result = MajorityVote().fit_predict(df)

            elif self.dawid_skene:

                self.result = DawidSkene().fit_predict(df)

            elif self.gold_majority_vote:

                raise NotImplementedError

            elif self.mmsr:

                self.result = MMSR().fit_predict(df)

            elif self.wawa:

                self.result = Wawa().fit_predict(df)

            elif self.zero_based_skill:

                self.result = ZeroBasedSkill().fit_predict(df)

            elif self.glad:

                self.result = GLAD().fit_predict(df)

            assert self.result is not None, raise_error("Aggregation did not produce a result!")

            forward_data = [{"id": df.loc[df["task"] == task, "id"].iloc[0], 
                             "input_data": df.loc[df["task"] == task, "inputs"].iloc[0], 
                             "label": self.result[task]} 
                            for task in self.result.index]

            msg.good(f"Finished aggregating {len(forward_data)} submitted tasks from {self.task.name}")
            self.complete = True

            if self.forward:
                self.forward(forward_data)


class Forward:
    """
    This class defines an action for forwarding completed tasks to specific pools based on values.

    For example, if a task receives the value True, it can be forwarded to Pool 1, whereas tasks with value False
    will be forwarded to Pool 2.

    Parameters:
        configuration: A string object that defines a path to a YAML file with configuration.
        client: Toloka client object.
        targets: Pools where tasks will be forwarded.

    Returns:
        None
    """
    def __init__(self, configuration, client, targets=None):

        self.conf = read_configuration(configuration)
        self.name = self.conf['name']
        self.client = client
        self.reject = []
        self.accept = []
        self.dont_forward = []

        # Possible outputs for the task (e.g. true and false) and their forward pools
        self.outputs = self.conf['actions']['on_result']

        # Check if some outputs should be accepted or rejected (these are not forwarded like other tasks,
        # but accepted or rejected based on the output) and remove these from outputs
        self.reject.extend([k for k, v in self.outputs.items() if v == 'reject'])
        [self.outputs.pop(k) for k in self.reject]

        self.accept.extend([k for k, v in self.outputs.items() if v == 'accept'])
        [self.outputs.pop(k) for k in self.accept]

        # If no forward pools are configured for some outputs, they will not be forwarded
        self.dont_forward.extend([k for k, v in self.outputs.items() if v == None])
        [self.outputs.pop(k) for k in self.dont_forward]

        # Deal with outputs that have several actions (both accepting/rejecting and forwarding)
        multi_action = {k: v for (k, v) in self.outputs.items() if type(v) == list}
        self.reject.extend([k for k, v in multi_action.items() if 'reject' in v])
        self.accept.extend([k for k, v in multi_action.items() if 'accept' in v])
        multi_action = {k: [i for i in v if i not in ["accept", "reject"]][0] for (k, v) in multi_action.items()}

        self.outputs = {**self.outputs, **multi_action}

        # Create mapping for output and the configured CrowdsourcingTask object of the forward pool
        self.name_mapping = {pool.name: pool for pool in targets}
        self.forward_pools = {output: self.name_mapping[name] for (output, name) in self.outputs.items()}

        # Initialize dictionary of key-list pairs. Keys are possible outputs for the task
        # and the lists are tasks to be forwarded.
        self.tasks_to_forward = collections.defaultdict(list)

    def __call__(self, events: Union[List[AssignmentEvent], List[dict]]) -> None:

        # Process tasks that come from an observer call
        if all(isinstance(x, AssignmentEvent) for x in events):

            # Loop over the list of incoming AssignmentEvent objects
            for event in events:

                for i in range(len(event.assignment.tasks)):

                    solution = event.assignment.solutions[i].output_values[self.conf['data']['output']]

                    # If performer verified the task as incorrect, reject the original assignment
                    # and, if configured in source pool under "on_reject", re-add the task to the pool
                    if solution in self.reject:

                        self.client.reject_assignment(assignment_id=event.assignment.tasks[i].input_values['assignment_id'],
                                                      public_comment="Assignment was verified as incorrect by another user.")
                        msg.warn(f'Rejected assignment {event.assignment.tasks[i].input_values["assignment_id"]}')

                    # If performer verified the task as correct, accept original assignment and don't forward task
                    if solution in self.accept:

                        self.client.accept_assignment(assignment_id=event.assignment.tasks[i].input_values['assignment_id'],
                                                    public_comment="Assignment was verified correct by another user.")
                        msg.good(f'Accepted assignment {event.assignment.tasks[i].input_values["assignment_id"]}')

                    # If no forward pool was configured, submit task without forwarding/accepting/rejecting
                    if solution in self.dont_forward:

                        msg.good(f'Received a submitted assignment with output "{solution}"')

                    # Else, forward task according to configuration
                    if solution in self.forward_pools:

                        try:
                            task = toloka.Task(
                                pool_id = self.forward_pools[solution].pool.id,
                                input_values=event.assignment.tasks[i].input_values,
                                unavailable_for=self.forward_pools[solution].blocklist
                            )
                            self.tasks_to_forward[solution].append(task)

                        # Catch errors
                        except toloka.exceptions.ValidationApiError:

                            # Raise error
                            raise_error(f'Failed to forward assignment {event.assignment.tasks[i].input_values["assignment_id"]}')

                        # If object has no attribute 'pool', it is an action, and should be called to activate
                        except AttributeError:

                            action = self.forward_pools[solution]
                            action(event)

            tasks_list = [task for l in self.tasks_to_forward.values() for task in l]

            if tasks_list:
                
                # Add tasks to defined pools
                self.client.create_tasks(tasks_list, allow_defaults=True, open_pool=True)

                # Print status if any tasks were forwarded on this call
                msg.good(f"Successfully forwarded {len(tasks_list)} {'tasks' if len(tasks_list) > 1 else 'task'}")

            # Tasks currently in lists have been forwarded, so reset lists
            self.tasks_to_forward = collections.defaultdict(list)
            tasks_list = []

        # Process tasks that come from aggregation
        if all(isinstance(x, dict) for x in events):

            # Loop over the list of incoming AssignmentEvent objects
            for event in events:

                solution = event['label']

                # If performer verified the task as incorrect, reject the original assignment
                # and, if configured in source pool under "on_reject", re-add the task to the pool
                if solution in self.reject:

                    self.client.reject_assignment(assignment_id=event["input_data"]["assignment_id"],
                                                  public_comment="Assignment was verified incorrect by another user.")
                    msg.warn(f'Rejected assignment {event["input_data"]["assignment_id"]}')

                # If performer verified the task as correct, accept original assignment and don't forward task
                if solution in self.accept:

                    self.client.accept_assignment(assignment_id=event["input_data"]["assignment_id"],
                                                  public_comment="Assignment was verified correct by another user.")
                    msg.good(f'Accepted assignment {event["input_data"]["assignment_id"]}')

                # If no forward pool was configured, submit task without forwarding/accepting/rejecting
                if solution in self.dont_forward:

                    msg.good(f'Received a submitted assignment with output "{solution}"')

                # Else, forward task according to configuration
                if solution in self.forward_pools:

                    try:
                        task = toloka.Task(
                            pool_id = self.forward_pools[solution].pool.id,
                            input_values=event['input_data'],
                            unavailable_for=self.forward_pools[solution].blocklist
                        )
                        self.tasks_to_forward[solution].append(task)

                    # Catch errors
                    except toloka.exceptions.ValidationApiError:

                        # Raise error
                        raise_error(f'Failed to forward aggregated task')

                    # If object has no attribute 'pool', it is an action, and should be called to activate
                    except AttributeError:

                        action = self.forward_pools[solution]
                        action(event)
                
            tasks_list = [task for l in self.tasks_to_forward.values() for task in l]

            if tasks_list:
                
                # Add tasks to defined pools
                self.client.create_tasks(tasks_list, allow_defaults=True, open_pool=True)

                # Print status if any tasks were forwarded on this call
                msg.good(f"Successfully forwarded {len(tasks_list)} {'tasks' if len(tasks_list) > 1 else 'task'}")

            # Tasks currently in lists have been forwarded, so reset lists
            self.tasks_to_forward = collections.defaultdict(list)
            tasks_list = []


class SeparateBBoxes:
    """
    This class defines an action for separating an image with several bounding boxes to several tasks with one
    bounding box per image.

    Parameters:
        target: CrowdsourcingTask to which the new tasks will be created
        configuration: A string object that defines a path to a YAML file with configuration.
        add_label: A string object of a label that will be given to the created bounding boxes. Optional parameter.

    Returns:
        None
    """

    def __init__(self, target, configuration, add_label=False):
        self.target = target
        self.client = self.target.client
        self.conf = read_configuration(configuration)
        self.name = self.conf["name"]
        self.add_label = add_label

        if "input_file" in self.conf["data"]:
            self.input_file = self.conf["data"]["input_file"]

    def __call__(self, event: Union[AssignmentEvent, dict, List[AssignmentEvent]]=None) -> None:

        # If the object is registered with an observer, use data from AssignmentEvents or the incoming dict to create new tasks
        if event:

            if type(event) == AssignmentEvent:

                msg.info(f"Creating new tasks in pool {self.target.name} with action {self.name}")

                if self.add_label:

                    for i in range(len(event.assignment.tasks)):

                        new_tasks = [toloka.Task(pool_id=self.target.pool.id,
                                                input_values={"image": event.assignment.tasks[i].input_values["image"], "outlines": [bbox]},
                                                unavailable_for=self.target.blocklist) 
                                        for bbox in [dict(x, **{'label': self.add_label}) for x in event.assignment.solutions[i].output_values["outlines"]] ]

                        self.client.create_tasks(new_tasks, allow_defaults=True, open_pool=True)

                else:

                    for i in range(len(event.assignment.tasks)):

                        new_tasks = [toloka.Task(pool_id=self.target.pool.id,
                                                input_values={"image": event.assignment.tasks[i].input_values["image"], "outlines": [bbox]},
                                                unavailable_for=self.target.blocklist) 
                                        for bbox in event.assignment.solutions[i].output_values["outlines"] ]

                        self.client.create_tasks(new_tasks, allow_defaults=True, open_pool=True)

            elif type(event) == List[AssignmentEvent]:

                msg.info(f"Creating new tasks in pool {self.target.name} with action {self.name}")

                if self.add_label:

                    for e in event:

                        for i in range(len(e.assignment.tasks)):

                            new_tasks = [toloka.Task(pool_id=self.target.pool.id,
                                                    input_values={"image": e.assignment.tasks[i].input_values["image"], "outlines": [bbox]},
                                                    unavailable_for=self.target.blocklist) 
                                            for bbox in [dict(x, **{'label': self.add_label}) for x in e.assignment.solutions[i].output_values["outlines"]] ]

                            self.client.create_tasks(new_tasks, allow_defaults=True, open_pool=True)

                else:

                    for e in event:

                        for i in range(len(e.assignment.tasks)):

                            new_tasks = [toloka.Task(pool_id=self.target.pool.id,
                                                    input_values={"image": e.assignment.tasks[i].input_values["image"], "outlines": [bbox]},
                                                    unavailable_for=self.target.blocklist) 
                                            for bbox in e.assignment.solutions[i].output_values["outlines"] ]

                            self.client.create_tasks(new_tasks, allow_defaults=True, open_pool=True)

            # If input comes from a forward action, it is in the form of a dictionary:
            elif type(event) == dict:

                msg.info(f"Creating new tasks in pool {self.target.name} with action {self.name}")

                if self.add_label:

                    new_tasks = [toloka.Task(pool_id=self.target.pool.id,
                                            input_values={"image": event["input_data"]["image"], "outlines": [bbox]},
                                            unavailable_for=self.target.blocklist) 
                                        for bbox in [dict(x, **{'label': self.add_label}) for x in event['input_data']['outlines']] ]

                    self.client.create_tasks(new_tasks, allow_defaults=True, open_pool=True)

                else:

                    new_tasks = [toloka.Task(pool_id=self.target.pool.id,
                                            input_values={"image": event["input_data"]["image"], "outlines": [bbox]},
                                            unavailable_for=self.target.blocklist) 
                                        for bbox in event['input_data']['outlines'] ]

                    self.client.create_tasks(new_tasks, allow_defaults=True, open_pool=True)

        # If the object is called without AssignmentEvents, the action starts the pipeline and
        # input data should be read from a file 
        else:
        
            input_df = pd.read_csv(self.input_file, sep="\t", index_col=False)

            msg.info(f"Creating new tasks in pool {self.target.name} with action {self.name}")

            if self.add_label:

                input_df["outlines"] = input_df["outlines"].apply(lambda x: json.loads(x))
                input_df["outlines"] = input_df["outlines"].apply(lambda x: [dict(y, **{'label': self.add_label}) for y in x])

            for i, task in input_df.iterrows():

                new_tasks = [toloka.Task(pool_id=self.target.pool.id,
                                        input_values={"image": task["image"], "outlines": [bbox]},
                                        unavailable_for=self.target.blocklist)
                            for bbox in task["outlines"]
                ]
                
                self.client.create_tasks(new_tasks, allow_defaults=True, open_pool=True)
