# -*- coding: utf-8 -*-

# Import libraries
from core import *
from wasabi import msg
import datetime
import json
import uuid
import toloka.client as toloka
import toloka.client.project.template_builder as tb


# Define the base class for Toloka tasks
class Task:
    """
    This is the base class for all Toloka tasks. The class is responsible for
    loading the configuration from JSON.
    """

    def __init__(self, configuration, client, task_spec):
        """
        This function initialises the Task class.

        Parameters:

            configuration: A dictionary that contains the configuration loaded from the JSON file.
            client: A toloka.TolokaClient object with valid credentials.
            task_spec: A Toloka TaskSpec object with task interface and input/output data.
        """

        # Create unique identifier for the Task and shorten
        self.task_id = str(uuid.uuid4())[:8].upper()

        # Print status message
        msg.info(f'The unique ID of this Task object is {self.task_id}')

        # Assign configuration to attribute
        self.conf = configuration

        # Unpack the configuration from JSON into attributes
        self.data_conf = self.conf['data']
        self.project_conf = self.conf['project']
        self.pool_conf = self.conf['pool']
        self.train_conf = self.conf['training']
        self.qual_conf = self.conf['quality_control']

        # Assign flags and default values
        self.add_train_data = False     # Do not add training tasks by default
        self.training = None            # No training
        self.is_complete = False        # Is the Task complete or not?

        # Get requester information
        requester = client.get_requester()

        # Print status messages on requester ID and balance
        msg.info(f'Using Toloka with requester with ID {requester.id}')
        msg.info(f'Current balance on this account is ${requester.balance}')

        # If the configuration file contains a key named 'id' for 'project', assume
        # that an existing project should be used.
        if 'id' in self.project_conf.keys():

            # Attempt to load the project configuration from Toloka
            try:

                # Use the get_project() method to retrieve the project
                self.project = client.get_project(project_id=self.project_conf['id'])

                # Print status message
                msg.good(f'Successfully loaded project {self.project.id} from Toloka')

            # Catch the error
            except toloka.exceptions.DoesNotExistApiError as error:

                # Raise error
                raise_error(f'Failed to load project with ID {self.project_conf["id"]} from '
                            f'Toloka. Check the project ID!')

        # Otherwise create new project
        else:

            # Print status message
            msg.info(f'Creating a new Toloka project ...')

            # Create a new toloka-kit Project object
            self.project = toloka.Project(**self.project_conf['setup'])
            try:

                # Load public instructions from a HTML file
                with open(self.project_conf['instructions'], mode='r', encoding='utf-8') as inst:

                    # Read the instructions and assign to the project
                    self.project.public_instructions = inst.read()

            except FileNotFoundError:

                # Raise error
                raise_error(f'Could not load task instructions '
                            f'from {self.project_conf["instructions"]}')

            # Assign a private comment to the project with the Task object identifier
            self.project.private_comment = f'Created by Task object with ID {self.task_id}'

            # Create the task interface
            self.project.task_spec = task_spec

            # Create new project on the platform
            self.project = client.create_project(self.project)

            # Print status message
            msg.good(f'Successfully created a new project with ID {self.project.id} on Toloka')

        # Load input data from the CSV file into a pandas DataFrame
        self.input_data = load_data(self.data_conf['file'])

        # If a training configuration has been provided, create a training pool
        if self.train_conf is not None:

            # Check if an existing training pool should be used
            if 'id' in self.train_conf.keys():

                # Attempt to retrieve the pool from Toloka
                try:

                    # Retrieve the existing training pool from Toloka
                    self.training = client.get_pool(pool_id=self.train_conf['id'])

                    # Print status message
                    msg.good(f'Successfully loaded training pool with ID {self.training.id} '
                             f'from Toloka')

                # Catch the error
                except toloka.exceptions.DoesNotExistApiError:

                    # Raise error
                    raise_error(f'Failed to load training pool with ID {self.train_conf["id"]} '
                                f'from Toloka')

            # Otherwise create a new training pool
            else:

                # Create a new training
                self.training = toloka.Training(project_id=self.project.id,
                                                may_contain_adult_content=False,
                                                **self.train_conf['setup']
                                                )

                # Print status message
                msg.good(f'Successfully configured a new training pool')

                # Create the training pool
                self.training = client.create_training(self.training)

                # Print status message
                msg.good(f'Successfully created a new training pool')

                # Assign flag to indicate that training tasks must be added
                self.add_train_data = True

        # If the configuration file contains a key named 'id' for 'pool', assume
        # that an existing pool should be used.
        if 'id' in self.pool_conf.keys():

            # Attempt to retrieve the pool from Toloka
            try:

                # Retrieve the existing pool from Toloka
                self.pool = client.get_pool(pool_id=self.pool_conf['id'])

                # Print status message
                msg.good(f'Successfully loaded main pool with ID {self.pool.id} from Toloka')

            # Catch the error
            except toloka.exceptions.DoesNotExistApiError:

                # Raise error
                raise_error(f'Failed to load pool with ID {self.pool_conf["id"]} from Toloka')

        # Otherwise proceed to create a new main pool
        else:

            # Set up the main pool
            self.pool = toloka.Pool(project_id=self.project.id,
                                    private_comment=f'Created by Task object with ID {self.task_id}',
                                    may_contain_adult_content=False,
                                    will_expire=datetime.datetime.now() + datetime.timedelta(days=365),
                                    **self.pool_conf['setup']
                                    )

            # Set default settings that are applied to any tasks uploaded to the pool
            self.pool.defaults = toloka.pool.Pool.Defaults(**self.pool_conf['defaults'])

            # Set the number of real, control and training tasks per suite
            self.pool.set_mixer_config(**self.pool_conf['mixer'])

            # If training has been defined, set up training and required quality
            if self.train_conf is not None:

                # Link training pool and retrieve minimum performance value
                self.pool.set_training_requirement(training_pool_id=self.training.id,
                                                   **self.pool_conf['training'])

            # Print status message
            msg.good(f'Successfully configured a new main pool')

            # Check if filters have been defined
            if 'filter' in self.pool_conf.keys():

                # Print status message
                msg.info(f'Setting up filters')

                # Check if workers should be filtered based on language skills
                if 'languages' in self.pool_conf['filter'].keys():

                    # If only one language has been defined, proceed to set the filter
                    if len(self.pool_conf['filter']['languages']) == 1:

                        # Create filter
                        language = toloka.filter.Languages.in_(
                            self.pool_conf['filter']['languages'][0].upper())

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=language)

                    # If more than one languages have been defined, combine and set filters
                    if len(self.pool_conf['filter']['languages']) > 1:

                        # Create filters
                        languages = [(toloka.filter.Languages.in_(lang.upper()))
                                     for lang in self.pool_conf['filter']['languages']]

                        # Combine filters
                        languages = toloka.filter.FilterOr(languages)

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=languages)

                # Check if workers should be filtered based on client type
                if 'client_type' in self.pool_conf['filter'].keys():

                    # Check if only one client type has been defined
                    if len(self.pool_conf['filter']['client_type']) == 1:

                        # Create filter
                        client = (toloka.filter.ClientType ==
                                  self.pool_conf['filter']['client_type'][0].upper())

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=client)

                    # Check if more than one client type has been defined
                    if len(self.pool_conf['filter']['client_type']) > 1:

                        # Create filters
                        clients = [(toloka.filter.ClientType == client.upper())
                                   for client in self.pool_conf['filter']['client_type']]

                        # Combine filters
                        clients = toloka.filter.FilterOr(clients)

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=clients)

                # Check if workers should be filtered based on rating
                if 'rating' in self.pool_conf['filter'].keys():

                    # Create filter
                    rating = (toloka.filter.Rating >= self.pool_conf['filter']['rating'])

                    # Check for existing filters and set
                    self.pool.filter = set_filter(filters=self.pool.filter,
                                                  new_filters=rating)

                # Check if workers should be filtered based on education
                if 'education' in self.pool_conf['filter'].keys():

                    # Check if only one education level has been defined
                    if len(self.pool_conf['filter']['education']) == 1:

                        # Create filter
                        education = (toloka.filter.Education ==
                                     self.pool_conf['filter']['education'][0].upper())

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=education)

                    # Check if more than one education level has been defined
                    if len(self.pool_conf['filter']['education']) > 1:

                        # Create filters
                        levels = [(toloka.filter.Education == edu.upper()) for edu in
                                  self.pool_conf['filter']['education']]

                        # Combine filters
                        levels = toloka.filter.FilterOr(levels)

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=levels)

                # Print status message
                msg.good(f'Finished adding filters to the pool')

            # If quality control rules exist, add them to the pool
            if self.qual_conf is not None:

                # Print status message
                msg.info(f'Setting up quality control rules')

                # Set up quality control rule for fast responses
                if "fast_responses" in self.qual_conf:

                    # Unpack rules into variables
                    history_size = self.qual_conf['fast_responses'][0]
                    count = self.qual_conf['fast_responses'][1]
                    threshold = self.qual_conf['fast_responses'][2]
                    duration = self.qual_conf['fast_responses'][3]
                    units = self.qual_conf['fast_responses'][4].upper()

                    # Add quality control rule to the pool
                    self.pool.quality_control.add_action(
                        collector=toloka.collectors.AssignmentSubmitTime(history_size=history_size,
                                                                         fast_submit_threshold_seconds=threshold),
                        conditions=[toloka.conditions.FastSubmittedCount > count],
                        action=toloka.actions.RestrictionV2(
                            scope=toloka.user_restriction.UserRestriction.ALL_PROJECTS,
                            duration=duration,
                            duration_unit=units,
                            private_comment='Fast responses'
                        )
                    )

                    # Print status message
                    msg.good(f'Added quality control rule: ban for {duration} {units.lower()} if '
                             f'response time is less than {threshold} seconds for {count} out '
                             f'of {history_size} tasks')

                # TODO Add other quality control rules

            # Create pool on Toloka
            self.pool = client.create_pool(self.pool)

            # Print status message
            msg.good(f'Successfully created a new pool with ID {self.pool.id} on Toloka')


class ImageClassificationTask(Task):
    """
    This is a class for classification tasks.
    """

    def __init__(self, configuration, client):
        """
        This function initialises the ClassificationTask class, which inherits attributes
        and methods from the Task class.
        """

        # Read the configuration from the JSON file
        configuration = read_configuration(configuration=configuration)

        # Read input and output data and create data specifications
        data_in = {k: data_spec[v] for k, v in configuration['data']['input'].items()}
        data_out = {k: data_spec[v] for k, v in configuration['data']['output'].items()}

        # Get the names of input and output variables for setting up the interface
        in_var = list(configuration['data']['input'].keys())[0]
        out_var = list(configuration['data']['output'].keys())[0]

        # Create the task interface; start by setting up the image viewer
        img_viewer = tb.ImageViewV1(url=tb.InputData(in_var),
                                    rotatable=True,
                                    ratio=[1, 1])

        # Define the prompt text above the button group
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Set up a radio group for labels
        radio_group = tb.ButtonRadioGroupFieldV1(

            # Set up the output data field
            data=tb.OutputData(out_var),

            # Create radio buttons
            options=[
                tb.fields.GroupFieldOption(value=True, label='Yes'),
                tb.fields.GroupFieldOption(value=False, label='No')
            ],

            # Set up validation
            validation=tb.RequiredConditionV1(hint="You must choose one response.")
        )

        # Set task width limit
        task_width_plugin = tb.TolokaPluginV1(kind='scroll', task_width=500)

        # Add hotkey plugin
        hotkey_plugin = tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData(out_var),
                                                                payload=True),
                                           key_2=tb.SetActionV1(data=tb.OutputData(out_var),
                                                                payload=False))

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([img_viewer, prompt, radio_group]),
            plugins=[task_width_plugin, hotkey_plugin]
        )

        # Create a task specification with interface and input/output data
        task_spec = toloka.project.task_spec.TaskSpec(
            input_spec=data_in,
            output_spec=data_out,
            view_spec=interface
        )

        # Use the super() function to access the superclass Task and its methods and attributes.
        # This will set up the project, pool and training as specified in the configuration JSON.
        super().__init__(configuration, client, task_spec)

        # Check if training tasks should be added
        if self.add_train_data:

            # Load training data
            self.train_data = load_data(configuration['training']['data']['file'])

            # Get the input and output variable names
            in_var_t = list(configuration['training']['data']['input'].keys())[0]
            out_var_t = list(configuration['training']['data']['output'].keys())[0]

            # Create training task objects
            self.train_tasks = [toloka.Task(pool_id=self.training.id,
                                            input_values={in_var_t: row[in_var_t]},
                                            known_solutions=[toloka.task.BaseTask.KnownSolution(output_values={out_var_t: str(row[out_var_t])})],
                                            message_on_unknown_solution=row['hint'],
                                            overlap=1)
                                for _, row in self.train_data.iterrows()]

            # Add training tasks to the training pool
            add_tasks_to_pool(client=client, tasks=self.train_tasks, pool=self.training,
                              kind='train')

        # Print status message
        msg.info(f'Creating and adding main tasks to pool with ID {self.pool.id}')

        # Create a list of Toloka Task objects by looping over the input DataFrame stored under
        # self.input_data. Use the name of the input column ('in_var') to get the correct column
        # from the DataFrame.
        self.tasks = [toloka.Task(input_values={in_var: row}, pool_id=self.pool.id)
                      for row in self.input_data[in_var]]

        # Add tasks to the main pool
        add_tasks_to_pool(client=client, tasks=self.tasks, pool=self.pool, kind='main')

        # Open main and training pools for workers
        open_pool(client=client, pool_id=self.pool.id if self.training is None
                  else [self.pool.id, self.training.id])

        # Track pool progress to print status messages
        track_pool_progress(client=client, pool_id=self.pool.id, interval=0.5)

        # If the main pool is closed and a training pool exists
        if not self.pool.is_open() and self.training is not None:

            # Close training pool
            client.close_training(self.training.id)

            # Print status
            msg.good(f'Successfully closed pool with ID {self.training.id}')

        # TODO Get and process results


# Read the credentials
with open('creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

t = ImageClassificationTask(configuration='conf.json', client=tclient)
