# -*- coding: utf-8 -*-

# Import libraries
from wasabi import Printer, TracebackPrinter
from toloka.client.task import Task
from toloka.client.pool import Pool
from toloka.metrics import MetricCollector
from typing import Union, List
import yaml
import pandas as pd
import time
import toloka.client as toloka
import toloka.metrics as metrics
import traceback


# Set up Printer and TracebackPrinter
msg = Printer(pretty=True, timestamp=True, hide_animation=True)
tracep = TracebackPrinter()


def create_tasks(input_obj,
                 input_data: pd.DataFrame) -> list:
    """
    This function creates Toloka Task objects from input data based on the JSON configuration.

    Parameters:
        input_obj: A subclass of CrowdsourcingTask.
        input_data: a pandas DataFrame that contains the input data. The DataFrame should contain
                    headers that match those defined in the configuration.

    Returns:
         A list of Toloka Task objects.
    """

    # Print status message
    msg.info(f'Creating and adding tasks to pool with ID {input_obj.pool.id}')

    # Fetch input variable names from the configuration. Create a dictionary with matching
    # key and value pairs, which is updated when creating the toloka.Task objects below.
    input_values = {n: n for n in list(input_obj.conf['data']['input'].keys())}

    # Create a list of Toloka Task objects by looping over the input DataFrame. Use the
    # dictionary of input variable names 'input_values' to retrieve the correct columns
    # from the DataFrame.
    tasks = [toloka.Task(pool_id=input_obj.pool.id,
                         input_values={k: row[v] for k, v in input_values.items()})
             for _, row in input_data.iterrows()]

    return tasks


def create_exam_tasks(input_obj) -> list:
    """
    This function creates Toloka Task objects with known solutions from input data based on the
    JSON configuration.

    Parameters:
        input_obj: A subclass of CrowdsourcingTask.

    Returns:
         A list of Toloka Task objects with known solutions.
    """

    # Print status message
    msg.info(f'Creating and adding exam tasks to pool with ID {input_obj.pool.id}')

    # Load exam tasks from the path defined in the JSON configuration
    exam_data = load_data(input_obj.conf['data']['file'])

    # Fetch input variable names from the configuration. Create a dictionary with matching
    # key and value pairs, which is updated when creating the toloka.Task objects below.
    input_values = {n: n for n in list(input_obj.conf['data']['input'].keys())}
    output_values = {n: n for n in list(input_obj.conf['data']['output'].keys())}

    # Populate the pool with exam tasks that have known answers
    tasks = [toloka.Task(pool_id=input_obj.pool.id,
                         input_values={k: row[v] for k, v in input_values.items()},
                         known_solutions=[toloka.task.BaseTask.KnownSolution(
                             output_values={k: str(row[v]) for k, v in
                                            output_values.items()})],
                         infinite_overlap=True)
             for _, row in exam_data.iterrows()]

    return tasks


def add_tasks(input_obj,
              tasks: List[Task]) -> None:
    """
    This function adds Toloka Task objects to a pool on Toloka. The function first verifies that
    these have not been added to the pool already.

    Parameters:
        input_obj: A subclass of CrowdsourcingTask.
        tasks: A list of Toloka Task objects.

    Returns:
         The Task objects are added to the pool.
    """

    # Get Task objects currently in the pool from Toloka
    old_tasks = [task for task in input_obj.client.get_tasks(pool_id=input_obj.pool.id)]

    # If the request returns Tasks from Toloka
    if len(old_tasks) > 0:

        # Compare the existing tasks to those created above under self.tasks
        tasks_exist = compare_tasks(old_tasks=old_tasks,
                                    new_tasks=tasks)

        if tasks_exist:

            # Print status message
            msg.warn(f'The tasks to be added already exist in the pool. Not adding '
                     f'duplicates.')

    else:

        # If no tasks exist, set the flag to False
        tasks_exist = False

    # If tasks do not exist in the pool
    if not tasks_exist:

        # Add tasks to the main pool
        add_tasks_to_pool(client=input_obj.client,
                          tasks=tasks,
                          pool=input_obj.pool,
                          kind='main')


def add_tasks_to_pool(client: toloka.TolokaClient,
                      tasks: list,
                      pool: Union[toloka.Pool, toloka.Training],
                      kind: str):
    """
    This function loads Toloka Task objects to a pool on Toloka.

    Parameters:
        client: A toloka.TolokaClient object with valid credentials.
        tasks: A Python list with Toloka Task objects.
        pool: A Toloka Pool object.
        kind: A string that indicates task type: 'main' or 'train'.

    Returns:
         Prints a status message to standard output.
    """
    # Attempt to create the tasks on Toloka
    try:

        if kind == 'main':

            # Create tasks on Toloka; use the default settings
            client.create_tasks(tasks, allow_defaults=True)

        if kind == 'train':

            # Create tasks on Toloka without default settings
            client.create_tasks(tasks, allow_defaults=False)

        # Print status message
        msg.good(f'Successfully added {len(tasks)} tasks to pool with ID {pool.id}')

    # Catch validation error
    except toloka.exceptions.ValidationApiError:

        # Print status message
        raise_error(f'Failed to create tasks on Toloka due to validation error. Check '
                    f'the configuration file!')


def compare_tasks(old_tasks: list,
                  new_tasks: list) -> bool:
    """
    This function checks newly-defined Tasks against those that already exist in a given Pool.

    Parameters:
        old_tasks: A list of Toloka Task objects.
        new_tasks: A list of Toloka Task objects.

    Returns:
         True if the new and existing Tasks match, otherwise False
    """
    # Get the keys of existing tasks, flatten the list and cast into a set
    existing_keys = [list(task.input_values.keys()) for task in old_tasks]
    existing_keys = set([item for sublist in existing_keys for item in sublist])

    # Get the values of existing tasks, flatten the list and cast into a set
    existing_values = [list(task.input_values.values()) for task in old_tasks]
    existing_values = set([item for sublist in existing_values for item in sublist])

    # Do the same for the keys of new tasks ...
    new_keys = [list(task.input_values.keys()) for task in new_tasks]
    new_keys = set([item for sublist in new_keys for item in sublist])

    # ... and for values as well.
    new_values = [list(task.input_values.values()) for task in new_tasks]
    new_values = set([item for sublist in new_values for item in sublist])

    # Compare the sets of keys and values
    if new_keys == existing_keys and new_values == existing_values:

        # If match, return True
        return True

    else:

        return False


def get_results(client: toloka.TolokaClient,
                pool_id: str) -> pd.DataFrame:
    """
    This function retrieves task suites from a pool on Toloka, extracts the
    individual tasks and returns them in a pandas DataFrame.

    Parameters:
        client: A toloka.TolokaClient object with valid credentials.
        pool_id: A string that contains a valid pool identifier.

    Returns:
        A pandas DataFrame with assignments from the pool.
    """

    # Use the get_assignments() method to retrieve task suites from the current pool
    suites = [suite for suite in client.get_assignments(pool_id=pool_id)]

    # Define a placeholder for assignments retrieved from the task suites
    assignments = {}

    # Loop over each task suite
    for suite in suites:

        # Loop over tasks and solutions (answers) in each task suite
        for task, solution in zip(suite.tasks, suite.solutions):

            # Extract information from tasks and solutions
            assignments[len(assignments)] = {**task.input_values,
                                             **solution.output_values,
                                             'task_id': task.id,
                                             'suite_id': suite.id,
                                             'status': str(suite.status)}

    # Return results as a pandas DataFrame
    return pd.DataFrame.from_dict(assignments, orient='index')


def load_data(data: str):
    """
    This function loads data from a TSV file and returns a pandas DataFrame.

    Parameters:
        data: A string that defines a path to a TSV file with data.

    Returns:
        A pandas DataFrame with input data.
    """

    # Print status
    msg.info(f'Loading data from {data}')

    # Load data from the CSV file into a pandas DataFrame
    try:

        # Read the CSV file – assume that header is provide on the first row
        df = pd.read_csv(data, sep='\t', header=0)

        # Print message
        msg.good(f'Successfully loaded {len(df)} rows of data from {data}')

    except FileNotFoundError:

        # Print message
        raise_error(f'Could not load the file {data}!')

    # Return the DataFrame
    return df


def open_pool(client: toloka.TolokaClient,
              pool_id: Union[str, list]):
    """
    This function opens pools for workers.

    Parameters:
        client: A toloka.TolokaClient object with valid credentials.
        pool_id: A string that contains a valid pool identifier, or a list of pool identifiers.

    Returns:
        Opens the pools for workers on Toloka.
    """
    # Check if a single pool should be opened
    if type(pool_id) == str:

        # Open the pool for workers
        client.open_pool(pool_id=pool_id)

        # Print status message
        msg.good(f'Successfully opened pool with ID {pool_id} for workers')

    # If the 'pool_id' variable contains a list, open each pool in turn
    elif type(pool_id) == list:

        # Loop over the pool identifiers
        for pid in pool_id:

            # Open the pool for workers
            client.open_pool(pool_id=pid)

            # Print status message
            msg.good(f'Successfully opened pool with ID {pid} for workers')


def raise_error(message: str):
    """
    This function is used to raise error messages.

    Parameters:
        message: A string object that contains the error message.

    Returns:
        Raises an error.
    """
    # Create error message using TracebackPrinter
    error = tracep(title=message, tb=traceback.extract_stack())

    # Raise error
    raise ValueError(error)


def read_configuration(configuration: str):
    """
    This function reads the Task configuration from a JSON file.

    Parameters:
            configuration: A string object that defines the path to the configuration file.

    Returns:
         A Python dictionary that contains the configuration.
    """

    # Attempt to open the JSON file for reading
    try:

        with open(configuration) as conf:

            # Read the file contents and load JSON into a dictionary
            conf_dict = yaml.safe_load(conf)

            # Print status message
            msg.good(f'Successfully loaded configuration from {configuration}')

    except FileNotFoundError:

        raise_error(f'Could not load the file {configuration}! Check the path '
                    f'to the file!')

    # Return the dictionary
    return conf_dict


def set_filter(filters, new_filters):
    """
    This function checks the pool for existing filters and appends new ones to them.

    Parameters:
        filters: A Toloka filter object (e.g. Rating or FilterAnd) or None.
        new_filters: A Toloka filter object (e.g. Rating or FilterAnd).

    Returns:
        Updated Toloka filter objects for the pool.
    """
    # Check if the pool already contains filters
    if filters is not None:

        # Update the filters by adding new filters to the existing ones
        filters = (filters & new_filters)

    # Othewise set the new filters as filters
    else:

        # Update filters
        filters = new_filters

    # Return filters
    return filters


def status_change(pool: Pool) -> None:
    """
    This function monitors status changes in pools and print outs messages.

    Parameters:
        pool: A Toloka Pool object.

    Returns:
        Prints a status message to standard output.
    """
    if pool.is_closed:

        msg.info(f'Closed pool with ID {pool.id}')

    if pool.is_open:

        msg.info(f'Opened pool with ID {pool.id}')


def create_process_collector(task_sequence) -> MetricCollector:
    """
    This function creates Toloka MetricCollector objects for tracking the progress of pools in a
    task sequence.

    Parameters:
        task_sequence: A TaskSequence object.

    Returns:
         A Toloka MetricCollector object.
    """
    # Set up a placeholder
    p_metrics = []

    # Create metrics for pools in the sequence
    for task in task_sequence.sequence:

        # Skip exam pools, because they run infinitely
        if not task.exam:

            # Create metric for percentage
            p_metric = metrics.pool_metrics.PoolCompletedPercentage(pool_id=task.pool.id,
                                                                    percents_name=f'{task.name}-pct',
                                                                    toloka_client=task_sequence.client)

            # Append to the placeholder list
            p_metrics.append(p_metric)

    # Create a MetricCollector object that holds the metrics. The second argument defines the
    # function to be called on the metrics collected.
    p_metrics = MetricCollector(p_metrics, process_metrics)

    return p_metrics


def process_metrics(metric_dict: dict) -> None:
    """
    This function prints status messages about pool metrics.

    Parameters:
        metric_dict: A dictionary containing metrics for one or more pools.

    Returns:
         Prints out a status message.
    """

    for name, pct in metric_dict.items():

        msg.info(f'Pool {name.split("-")[0]} is now {pct[0][1]}% complete ...')

    time.sleep(15)


def track_pool_progress(client: toloka.TolokaClient,
                        pool_id: str,
                        interval: Union[int, float],
                        exam: bool,
                        **kwargs):
    """
    This function tracks the progress of a pool.

    Parameters:
        client: A toloka.TolokaClient object with valid credentials.
        pool_id: A valid identifier for a pool on Toloka.
        interval: An integer or float that defines how often a status message
                  should be printed. The value corresponds to minutes.
        exam: Whether the pool is an exam pool or not – progress cannot be measured on exam
              pools with infinite overlap.
        kwargs: Keywords and arguments.

    Returns:
        Prints a status message to standard output.
    """
    # Define the time that should pass between status messages
    sleep = 60 * interval

    # Retrieve the pool from Toloka
    pool = client.get_pool(pool_id=pool_id)

    # For main pools, run the following block while pool remains open
    while not exam and not pool.is_closed():

        # Retrieve analytics for completion percentage from the pool
        op = client.get_analytics(
            [toloka.analytics_request.CompletionPercentagePoolAnalytics(subject_id=pool.id)])

        # Wait until the previous operation finishes
        op = client.wait_operation(op)

        # Retrieve the percentage value
        percentage = op.details['value'][0]['result']['value']

        # Print status message
        msg.info(f'Pool with ID {pool.id} is {percentage}% complete.')

        # Sleep until next message
        time.sleep(sleep)

        # Update pool information to check for completeness
        pool = client.get_pool(pool_id=pool_id)

    # For exam pools, run the following block while pool remains open
    while exam and not pool.is_closed():

        # Check if a limit has been set for the number of submitting users
        if kwargs and 'limit' in kwargs:

            # Set limit
            limit = kwargs['limit']

        else:

            # Print status message
            msg.fail(f'No limit has been set to the number of workers submitting to the exam pool. '
                     f'This pool will run indefinitely.', exits=0)

        # Retrieve analytics for completion percentage from the pool
        op = client.get_analytics(
            [toloka.analytics_request.UniqueSubmittersCountPoolAnalytics(subject_id=pool.id)])

        # Wait until the previous operation finishes
        op = client.wait_operation(op)

        # Retrieve the percentage value
        count = op.details['value'][0]['result']

        # Print status message
        msg.info(f'{count} workers submitted to pool with ID {pool.id}.')

        # If the maximum number of performers has been reached
        if count >= limit:

            # Print status message
            msg.info(f'Maximum number of submitting workers reached. Closing pool ...')

            # Close the pool
            client.close_pool(pool_id=pool_id)

        # Sleep until next message
        time.sleep(sleep)

        # Update pool information to check for completeness
        pool = client.get_pool(pool_id=pool_id)

    # Print status message when pool is completed
    msg.good(f'Successfully closed pool with ID {pool.id}')


def create_pool_table(task_sequence: list) -> None:
    """
    This function creates a table with essential information on pools in a task sequence.

    Parameters:
        task_sequence: a list of CrowdsourcingTask objects.

    Returns:
         Prints a table with information on all pools to standard output.
    """

    # Set up headers and a placeholder for data
    header = ('Name', 'Input', 'Output', 'Pool ID', 'Project ID', 'Pool type')
    data = []

    # Loop over the tasks
    for task in task_sequence:

        # Check if training has been defined
        if task.training:

            # Collect input and output data from the configuration
            inputs = [f'{k} ({v})' for k, v in task.conf['training']['data']['input'].items()]
            outputs = [f'{k} ({v})' for k, v in task.conf['training']['data']['output'].items()]

            # Append data as a tuple to the list
            data.append((task.name, ', '.join(inputs), ', '.join(outputs), task.training.id,
                         task.training.project_id, 'Training'))

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


def verify_connections(task_sequence: list) -> None:
    """
    This function verifies any connections between pools that have been configured.

    Parameters:
        task_sequence: A list of CrowdsourcingTask objects.

    Returns:
        Raises an error if a pool has been referred to but cannot be found.
    """

    for task in task_sequence:

        # Check if actions have been defined in the configuration
        if task.action_conf:

            # Check if the next task has been defined in the configuration
            try:

                # Fetch the name of the next task from the configuration
                next_task = task.action_conf['next']

                # Check that the next task exists in the task sequence
                if next_task not in [task.name for task in task_sequence]:

                    raise_error(f'Cannot find a task named {next_task} in the task sequence. '
                                f'Please check the name of the task under the key '
                                f'"actions/next" in the configuration file.')

            except KeyError:

                pass


# Map JSON entries to Toloka objects for input/output
data_spec = {
    'url': toloka.project.UrlSpec(),
    'json': toloka.project.JsonSpec(),
    'str': toloka.project.StringSpec(),
    'bool': toloka.project.BooleanSpec()
}
