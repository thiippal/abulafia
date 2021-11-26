# -*- coding: utf-8 -*-

# Import libraries
from wasabi import msg, TracebackPrinter
from typing import Union
import json
import pandas as pd
import time
import toloka.client as toloka
import traceback


# Set up TracebackPrinter
tracep = TracebackPrinter()


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


def open_pool(client: toloka.TolokaClient, pool_id: Union[str, list]):
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
            conf_dict = json.loads(conf.read())

            # Print status message
            msg.good(f'Successfully loaded configuration from {configuration}')

    except FileNotFoundError:

        raise_error(f'Could not load the file {configuration}! Check the path '
                    f'to the file!')

    # Close the JSON file
    conf.close()

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

        # Retrieve analytics for completion percentage from the pool
        op = client.get_analytics(
            [toloka.analytics_request.UniqueSubmittersCountPoolAnalytics(subject_id=pool.id)])

        # Wait until the previous operation finishes
        op = client.wait_operation(op)

        # Retrieve the percentage value
        count = op.details['value'][0]['result']

        # Print status message
        msg.info(f'{count} workers submitted to pool with ID {pool.id}.')

        # Sleep until next message
        time.sleep(sleep)

        # Update pool information to check for completeness
        pool = client.get_pool(pool_id=pool_id)

    # Print status message when pool is completed
    msg.good(f'Successfully closed pool with ID {pool.id}')


# Map JSON entries to Toloka objects for input/output
data_spec = {
    'url': toloka.project.UrlSpec(),
    'json': toloka.project.JsonSpec(),
    'str': toloka.project.StringSpec(),
    'bool': toloka.project.BooleanSpec()
}
