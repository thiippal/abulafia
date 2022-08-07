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
import json


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

    assert set(input_values.keys()) == set(input_data.columns), raise_error(f"Input data column names "
                                                                            f"do not match input configuration "
                                                                            f"for the pool {input_obj.name}!")

    # Create a list of Toloka Task objects by looping over the input DataFrame. Use the
    # dictionary of input variable names 'input_values' to retrieve the correct columns
    # from the DataFrame.
    tasks = [toloka.Task(pool_id=input_obj.pool.id,
                         input_values={k: row[v] for k, v in input_values.items()},
                         unavailable_for=input_obj.blocklist)
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
    exam_data = load_data(input_obj.conf['data']['file'], input_obj.conf['data']['input'])

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
                         infinite_overlap=True,
                         unavailable_for=input_obj.blocklist)
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


def check_io(configuration: dict, expected_input: set, expected_output: set):

    # Read input and output data and create data specifications
    data_in = {k: data_spec[v] for k, v in configuration['data']['input'].items()}
    data_out = {k: data_spec[v] for k, v in configuration['data']['output'].items()}

    # Create a dictionary mapping input data types to variable names.
    input_data = {v: k for k, v in configuration['data']['input'].items()}

    # Raise error if the expected input data types have been provided
    if not set(input_data.keys()) == expected_input:

        raise_error(f'Could not find the expected input types ({", ".join(expected_input)}) for '
                    f'{configuration["name"]}. Please check the configuration under the '
                    f'key data/input.')

    # Create a dictionary mapping output data types to variable names.
    output_data = {v: k for k, v in configuration['data']['output'].items()}

    # Raise error if the expected input data types have been provided
    if not set(output_data.keys()) == expected_output:

        raise_error(f'Could not find the expected input types ({", ".join(expected_output)}) for '
                    f'{configuration["name"]}. Please check the configuration under the '
                    f'key data/input.')

    return data_in, data_out, input_data, output_data


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


def load_data(data: str, inputs: dict):
    """
    This function loads data from a TSV file and returns a pandas DataFrame.

    Parameters:
        data: A string that defines a path to a TSV file with data.

    Returns:
        A pandas DataFrame with input data.
    """

    # Print status
    msg.info(f'Loading data from {data}')

    # Make sure that a TSV-file is used, otherwise raise error
    assert data[-4:] == ".tsv", raise_error("Please use a TSV-file for the tasks!")

    # Load data from the TSV file into a pandas DataFrame
    try:

        # Read the TSV file – assume that header is provided on the first row
        df = pd.read_csv(data, sep='\t', header=0)

        # Convert JSON inputs from string to JSON
        json_inputs = [k for k, v in inputs.items() if v == "json"]

        for i in json_inputs:

            df[i] = df[i].apply(lambda x: json.loads(x))
            
        # Print message
        msg.good(f'Successfully loaded {len(df)} rows of data from {data}')

    except FileNotFoundError:

        # Print message
        raise_error(f'Could not load the file {data}!')

    # Return the DataFrame
    return df


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
    This function reads the Task configuration from a YAML file.

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


def create_metrics(task_sequence) -> MetricCollector:
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
        if hasattr(task, 'pool') and not task.exam:

            # Create metric for percentage
            p_metric = metrics.pool_metrics.PoolCompletedPercentage(pool_id=task.pool.id,
                                                                    percents_name=f'{task.name}-pct',
                                                                    toloka_client=task_sequence.client)

            # Append to the placeholder list
            p_metrics.append(p_metric)

        else:

            continue

    # Create a MetricCollector object that holds the metrics. The second argument defines the
    # function to be called on the metrics collected.
    if p_metrics:

        p_metrics = MetricCollector(p_metrics, process_metrics)

    if not p_metrics:

        p_metrics = None

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


def create_pool_table(task_sequence: list) -> None:
    """
    This function creates a table with essential information on pools in a task sequence.
    A pool table. :-)

    Parameters:
        task_sequence: a list of CrowdsourcingTask objects and/or actions.

    Returns:
         Prints a table with information on all pools/actions to standard output.
    """

    # Set up headers and a placeholder for data
    header = ('Name', 'Input', 'Output', 'Pool ID', 'Project ID', 'Pool type')
    data = []

    # Loop over the tasks
    for task in task_sequence:

        # Check if training has been defined
        try:

            if task.training:

                # Collect input and output data from the configuration
                inputs = [f'{k} ({v})' for k, v in task.conf['training']['data']['input'].items()]
                outputs = [f'{k} ({v})' for k, v in task.conf['training']['data']['output'].items()]

                # Append data as a tuple to the list
                data.append((task.name, ', '.join(inputs), ', '.join(outputs), task.training.id,
                             task.training.project_id, 'Training'))

        except AttributeError:

            pass

        try:

            if task.pool:

                obj_type = 'Pool' if not task.exam else 'Exam'

                # Collect input and output data from the configuration
                inputs = [f'{k} ({v})' for k, v in task.conf['data']['input'].items()]
                outputs = [f'{k} ({v})' for k, v in task.conf['data']['output'].items()]

                # Append data as a tuple to the list
                data.append((task.name, ', '.join(inputs), ', '.join(outputs), task.pool.id,
                             task.project.id, obj_type))

        except AttributeError:

            # If task.pool raises an attribute error, the object is an action
            obj_type = 'Action'

            # Append data as a tuple to the list
            data.append((task.name, '--', '--', '--', '--', obj_type))

    # Print a table with inputs and outputs
    msg.table(data=data, header=header, divider=True)


def verify_connections(task_sequence: list) -> None:
    """
    This function verifies any connections between pools that have been configured.

    Parameters:
        task_sequence: A list of CrowdsourcingTask objects and/or actions.

    Returns:
        Raises an error if a pool has been referred to but cannot be found.
    """
    for task in task_sequence:

        # Check if actions have been defined in the configuration
        if 'actions' in task.conf.keys() and task.conf['actions'] is not None:

            # Check if the next task has been defined in the configuration
            try:

                # Fetch a list of tasks defined in the actions
                tasks = list(task.conf['actions'].values())

                # Check that the task exists in the task sequence
                for next_task in tasks:

                    # Check if multiple next tasks are configured and validate each individually
                    if type(next_task) == dict:

                        for n_task in next_task.values():

                            if type(n_task) == list:

                                for t in n_task:

                                    if t not in [task.name for task in task_sequence] and t not in ['accept', 'reject']:

                                        raise_error(f'Cannot find a task named {t} in the task sequence. '
                                                    f'Please check the name of the task under the key '
                                                    f'"actions" in the configuration file.')

                            else:

                                if n_task not in [task.name for task in task_sequence]:

                                    raise_error(f'Cannot find a task named {n_task} in the task sequence. '
                                                f'Please check the name of the task under the key '
                                                f'"actions" in the configuration file.')

                    elif next_task not in [task.name for task in task_sequence]:

                        raise_error(f'Cannot find a task named {next_task} in the task sequence. '
                                    f'Please check the name of the task under the key '
                                    f'"actions/next" in the configuration file.')

            except KeyError:

                pass
        
        # Check if source pool is configured to current action
        if 'source' in task.conf.keys() and task.conf['source'] is not None:

            if task.conf['source'] not in [task.name for task in task_sequence]:

                raise_error(f'Cannot find a task named {task.conf["source"]} in the task sequence. '
                            f'Please check the name of the task under the key '
                            f'"source" in the configuration file.')


def check_reward(time_per_suite: int, reward: Union[int, float], name: str) -> None:
    """
    Calculates a fair reward per task suite and checks if the configured reward reaches that.

    Parameters:
        time_per_suite: estimated time it takes a worker to complete one task suite
        reward: reward per assignment that has been set in the configuration file
        name: name of the current CrowdsourcingTask

    Returns:
        Raises a warning if the configured reward is too low and prompts the user to verify if they
        wish to proceed with the current configuration. If not, the pipeline is cancelled.
    """
    
    suites_per_hour = 60*60 / time_per_suite
    suggested_reward = 12 / suites_per_hour

    if reward < suggested_reward:

        msg.warn(f"The reward you have set per assignment for {name} does not result in a fair wage for the workers. "
                 f"In order for the workers to receive a salary of $12 per hour, set reward_per_assignment to at least ${suggested_reward}.\n"
                 f"Do you wish to proceed with the current configuration anyway (y/n)?")
        choice = input("")

        if choice == "n":

            msg.info("Cancelling pipeline", exits=1)


# Map JSON entries to Toloka objects for input/output
data_spec = {
    'url': toloka.project.UrlSpec(),
    'json': toloka.project.JsonSpec(),
    'str': toloka.project.StringSpec(),
    'bool': toloka.project.BooleanSpec()
}
