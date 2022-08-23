# -*- coding: utf-8 -*-

import asyncio
import datetime
from ..observers import AnalyticsObserver
from ..functions.core_functions import *
from toloka.client.actions import ChangeOverlap
from toloka.client.collectors import AssignmentsAssessment
from toloka.client.conditions import AssessmentEvent
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

        msg.info(f'Starting the task sequence')

        # Open all pools in the sequence that contain tasks. Note that pools without tasks cannot
        # be opened: they will be opened when tasks are added to them by these tasks.
        for task in self.sequence:

            if hasattr(task, 'tasks') and task.tasks is not None:

                self.client.open_pool(pool_id=task.pool.id)

            if hasattr(task, 'training') and task.training is not None:

                self.client.open_pool(pool_id=task.training.id)

        # Set up MetricCollectors for all pools
        metrics_collector = create_metrics(task_sequence=self)

        # Define an asynchronous function to run the MetricCollector and
        # the Pipeline objects at the same time
        async def run_sequence(metrics):

            # The 'ensure_future' method allows running the MetricCollector
            # in a fire-and-forget manner
            if metrics is not None:

                asyncio.ensure_future(metrics.run())

            # The Pipeline object needs to be awaited
            await asyncio.gather(self.pipeline.run())

        # Call the asynchronous function to start the collectors and pipeline
        asyncio.run(run_sequence(metrics=metrics_collector))

        # Collect pool statuses here
        status = []

        # Close all training and exam pools that may remain open after the pipeline finishes
        while not self.complete:

            # Loop over tasks in the sequence and filter out actions by checking for pools
            for task in (t for t in self.sequence if hasattr(t, 'pool')):

                # Get the last reason for closing a pool: should be 'MANUAL' or 'COMPLETED',
                # can also be None.
                pool_status = self.client.get_pool(pool_id=task.pool.id).last_close_reason

                if pool_status is not None and pool_status.value in ['COMPLETED', 'MANUAL']:

                    if self.client.get_pool(pool_id=task.pool.id).is_closed():

                        status.append(True)

                    else:

                        self.client.close_pool(pool_id=task.pool.id)

                        msg.info(f'Closed pool with ID {task.pool.id}')

                # Check if there is a training pool that should be closed
                if hasattr(task, 'training') and task.training is not None:

                    if self.client.get_pool(pool_id=task.training.id).is_closed():

                        status.append(True)

                    else:

                        self.client.close_pool(pool_id=task.training.id)

                        msg.info(f'Closed pool with ID {task.training.id}')

            for action in (a for a in self.sequence if hasattr(a, 'aggregator')):

                if action.complete == True:
                    
                    status.append(True)

            if all(status):

                # Wait for a minute to ensure that no new tasks are added to pools in the pipeline
                # before ending the task sequence
                time.sleep(60)

                if all(status):

                    self.complete = True

                    msg.good(f'Successfully completed the task sequence')

        # Check the outputs
        if self.complete:

            exit()

            # Check if tasks are supposed to output the results
            for task in self.sequence:

                if hasattr(task, 'pool'):

                    # Get the output DataFrame for each task; assign under 'output_data'
                    task.output_data = self.client.get_assignments_df(pool_id=task.pool.id)

                    # Check if the output should be written to disk
                    try:

                        if task.conf['actions'] is not None and 'output' in task.conf['actions']:

                            # Write the DataFrame to disk
                            task.output_data.to_csv(f'{task.name}_{task.pool.id}.csv')

                            msg.good(f'Wrote data for task {task.name} ({task.pool.id}) to disk.')

                    except KeyError:

                        pass

    def create_pipeline(self):

        # Create an asyncronous client
        async_client = AsyncMultithreadWrapper(self.client)

        # Loop over the tasks and create an AssignmentsObserver object for each task. Exam tasks
        # do not require AssignmentsObservers, because they do not create further tasks to be
        # forwarded.
        a_observers = {task.name: AssignmentsObserver(async_client, task.pool.id)
                       for task in self.sequence if hasattr(task, 'pool')
                       and not task.exam if hasattr(task, 'pool')}

        # Set up pool observers for monitoring all pool states, including exams. These observers
        # are needed for the Pipeline to run correctly: a Pipeline cannot run without observers.
        p_observers = {task.name: PoolStatusObserver(async_client, task.pool.id)
                       for task in self.sequence if hasattr(task, 'pool')}

        # Set up pool analytics observers for monitoring exam pools
        pa_observers = {task.name: AnalyticsObserver(async_client, task.pool,
                                                     max_performers=task.pool_conf['exam']['max_performers'])
                        for task in self.sequence if hasattr(task, 'pool')
                        and task.exam if hasattr(task, 'pool')}

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

            current_task = tasks[name]

            if current_task.action_conf is not None:

                # If pool's input data comes from a source action (such as SeparateBBoxes), intialize tasks
                if 'data_source' in current_task.action_conf:

                    source = tasks[current_task.action_conf['data_source']]
                    source()

                # Register possible Aggregate-actions to activate when pool is closed
                if 'on_closed' in current_task.action_conf:

                    p_observer.on_closed(tasks[current_task.action_conf['on_closed']])

                    msg.info(f'Results from {name} will be aggregated with {tasks[current_task.action_conf["on_closed"]].name}')

            self.pipeline.register(observer=p_observer)

            msg.info(f'Registered a pool status observer for task {name} ({tasks[name].pool.id})')

        # Register each pool analytics observer
        for name, pa_observer in pa_observers.items():

            self.pipeline.register(observer=pa_observer)

            msg.info(f'Registered a pool analytics observer for task {name} ({tasks[name].pool.id})')

        # Loop over the assignment observers and get the actions configuration to determine task flow
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
                                 f'on acceptance')

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
                                 f'on submission')

                    except KeyError:

                        raise_error(f'Could not find a CrowdsourcingTask object named '
                                    f'{current_task.action_conf["on_submitted"]} in the '
                                    f'TaskSequence. Please check the configuration '
                                    f'under the key "actions"!')

                if 'on_rejected' in current_task.action_conf:

                    # Check if rejected assignments tasks should be routed to the same pool
                    if current_task.action_conf['on_rejected'] == name:

                        # Add a ChangeOverlap action to the pool, which returns this assignment into annotation queue.
                        current_task.pool.quality_control.add_action(
                            collector=AssignmentsAssessment(),
                            conditions=[AssessmentEvent == AssessmentEvent.REJECT],
                            action=(ChangeOverlap(delta=1, open_pool=True)))

                        # Update the pool configuration for the action to take place.
                        self.client.update_pool(current_task.pool.id, current_task.pool)

                        msg.info(f'Rejected tasks from pool {name} will be re-added to the pool')

                    else:

                        try:

                            # Register the action with the AssignmentObserver. If a task is rejected,
                            # it will be sent to the CrowdsourcingTask object defined in the configuration.
                            observer.on_rejected(tasks[current_task.action_conf['on_rejected']])

                            msg.info(f'Setting up a connection from {name}'
                                     f'to {tasks[current_task.action_conf["on_rejected"]].name} '
                                     f'on rejected')

                        except KeyError:

                            raise_error(f'Could not find a CrowdsourcingTask object named '
                                        f'{current_task.action_conf["on_rejected"]} in the '
                                        f'TaskSequence. Please check the configuration '
                                        f'under the key "actions"!')

                if ('on_result' in current_task.action_conf) and ('on_closed' not in current_task.action_conf):

                    # If current pool is not an action, use setup from current pool
                    if hasattr(current_task, 'pool'):

                        setup = current_task.conf['pool']['setup']

                    # If current pool is an action, use setup from source pool 
                    else:

                        setup = tasks[current_task.source].pool.setup

                    try:

                        # If tasks are not automatically accepted, forward using 'on_submitted'
                        if setup['auto_accept_solutions'] == False:

                            # Check if multiple forward pools are configured
                            if type(tasks[current_task.action_conf['on_result']]) == dict:

                                for pool in tasks[current_task.action_conf['on_result']].values():
                                    observer.on_submitted(pool)
                            
                            else:
                                observer.on_submitted(tasks[current_task.action_conf['on_result']])

                        # If tasks are automatically accepted, forward using 'on_accepted'
                        if setup['auto_accept_solutions'] == True:

                            # Check if multiple forward pools are configured
                            if type(tasks[current_task.action_conf['on_result']]) == dict:

                                for pool in tasks[current_task.action_conf['on_result']].values():
                                    observer.on_accepted(pool)

                            else:
                                
                                observer.on_accepted(tasks[current_task.action_conf['on_result']])

                        msg.info(f'Tasks from {name} will be forwarded with {tasks[current_task.action_conf["on_result"]].name} '
                                 f'on result according to configuration')

                    except KeyError:

                        raise_error(f'Could not find a CrowdsourcingTask object named '
                                    f'{current_task.action_conf["on_result"]} in the '
                                    f'TaskSequence. Please check the configuration '
                                    f'under the key "actions"!')