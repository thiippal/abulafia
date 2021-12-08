# -*- coding: utf-8 -*-

# Import libraries
from core import *
from wasabi import Printer
from toloka.streaming.event import AssignmentEvent
import datetime
import uuid
import toloka.client as toloka
import toloka.client.project.template_builder as tb

# Set up Printer
msg = Printer(pretty=True, timestamp=True, hide_animation=True)


# Define the base class for Toloka tasks
class CrowdsourcingTask:
    """
    This is the base class for all tasks defined on Toloka. The class is responsible for
    loading the Task configuration from the JSON file and for handling basic tasks, such
    as validating input data and opening and closing pools on Toloka.
    """

    def __init__(self, configuration, client, task_spec):
        """
        This function initialises the CrowdsourcingTask class.

        Parameters:

            configuration: A dictionary that contains the configuration loaded from the JSON file.
            client: A toloka.TolokaClient object with valid credentials.
            task_spec: A Toloka TaskSpec object with task interface and input/output data.
        """
        # Create unique identifier for the Task and shorten
        self.task_id = str(uuid.uuid4())[:8].upper()

        # Assign configuration and client to attributes
        self.client = client
        self.conf = configuration

        # Unpack the configuration from JSON into attributes
        self.data_conf = self.conf['data']
        self.project_conf = self.conf['project']
        self.action_conf = self.conf['actions']
        self.pool_conf = self.conf['pool']
        self.train_conf = self.conf['training']
        self.qual_conf = self.conf['quality_control']

        # Assign flags and default values
        self.name = self.conf['name']   # Unique name of the task
        self.project = None             # Placeholder for Toloka Project object
        self.training = None            # Placeholder for Toloka Training object
        self.pool = None                # Placeholder for Toloka Pool object
        self.prev_task = None           # Previous Task object in the crowdsourcing pipeline
        self.input_data = None          # Placeholder for input data
        self.output_data = None         # Placeholder for output data
        self.train_data = None          # Placeholder for training data
        self.train_tasks = None         # Placeholder for training tasks
        self.tasks = None               # Placeholder for main tasks
        self.results = None             # Placeholder for results
        self.is_complete = False        # Is the Task complete or not?
        self.skill = False              # Does the Task provide or require a skill?
        self.exam = False               # Is this Task an exam?

        # Print status message
        msg.info(f'The unique ID for this object ({self.name}) is {self.task_id}')

        # Get requester information
        requester = client.get_requester()

        # Print status messages on requester ID and balance
        msg.info(f'Using Toloka with requester with ID {requester.id}')
        msg.info(f'Current balance on this account is ${requester.balance}')

        # Load project configuration
        self.load_project(client=client, task_spec=task_spec)

        # Load training configuration
        self.load_training(client=client)

        # Load pool configuration
        self.load_pool(client=client)

        # If the pool is an exam pool, create exam tasks
        if self.exam:

            exam_tasks = self.create_exam_tasks()

            self.add_tasks(exam_tasks)

    def __call__(self, in_obj):

        # If the object on which this CrowdSourcingTask object is called
        # is an InputData object, proceed to create Toloka Task objects.
        if type(in_obj) == InputData:

            # Assign the InputData object as previous task
            self.prev_task = in_obj

            # If the current pool is not an exam pool, create tasks from
            # the InputData and add them to the pool
            if not self.exam:

                tasks = self.create_tasks(in_obj)

                self.add_tasks(tasks=tasks)

        # If the object on which the CrowdSourcing task is called is a
        # subclass of CrowdsourcingTask, set this object as the previous
        # task under the self.prev_task attribute. This information will
        # be used for creating a TaskSequence.
        if issubclass(type(in_obj), CrowdsourcingTask):

            # Assign the InputData object as previous task
            self.prev_task = in_obj

        # If the input is a list of AssignmentEvent objects, check if the
        # incoming tasks were originally created by this CrowdsourcingTask.
        if type(in_obj) == list and all(isinstance(item, AssignmentEvent) for item in in_obj):

            # TODO Adjust overlap for rejected items
            # TODO Create new tasks if necessary
            pass

    def load_project(self, client, task_spec):
        """
        This function loads an existing project from Toloka or creates a new project according to
        the configuration in the JSON file under the key "project".

        Parameters:

            client: A toloka.TolokaClient object with valid credentials.
            task_spec: A toloka.project.task_spec.TaskSpec object that defines an user interface.

        Returns:

             Assigns a Toloka Project object under self.project.
        """

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
            except toloka.exceptions.DoesNotExistApiError:

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

    def load_training(self, client):
        """
        This function loads a Training pool from Toloka or creates a new Training according to
        the configuration in the JSON file under the key "training".

        Parameters:

            client: A toloka.TolokaClient object with valid credentials.

        Returns:

            Assigns a Toloka Training object under self.training. If a new Training object is
            created, it is populated with Tasks as defined in the configuration.
        """

        # If a training configuration has been provided, create a training pool
        if self.train_conf is not None:

            # Check if an existing training pool should be used
            if 'id' in self.train_conf.keys():

                # Attempt to retrieve the pool from Toloka
                try:

                    # Retrieve the existing training pool from Toloka
                    self.training = client.get_training(training_id=self.train_conf['id'])

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

                # Print status messages
                msg.good(f'Successfully created a new training pool')

                # Load training data
                self.train_data = load_data(self.conf['training']['data']['file'])

                # Get the input and output variable names
                input_values = {n: n for n in list(self.conf['training']['data']['input'].keys())}
                output_values = {n: n for n in list(self.conf['training']['data']['output'].keys())}

                # Create Task objects for training
                self.train_tasks = [toloka.Task(pool_id=self.training.id,
                                                input_values={k: row[v] for k, v in
                                                              input_values.items()},
                                                known_solutions=[toloka.task.BaseTask.KnownSolution(
                                                    output_values={k: str(row[v]) for k, v in
                                                                   output_values.items()})],
                                                message_on_unknown_solution=row['hint'],
                                                overlap=1)
                                    for _, row in self.train_data.iterrows()]

                # Add training tasks to the training pool
                add_tasks_to_pool(client=self.client, tasks=self.train_tasks, pool=self.training,
                                  kind='train')

    def load_pool(self, client):
        """
        This function loads a main pool from Toloka or creates a new pool according to the
        configuration defined in the JSON file under the key "pool".

        Parameters:

            client: A toloka.TolokaClient object with valid credentials.

        Returns:

             Assigns a Toloka Pool object under self.pool.
        """

        # If the configuration file contains a key named 'id' under 'pool', assume
        # that an existing pool should be used for this task.
        if 'id' in self.pool_conf.keys():

            # Attempt to retrieve the main pool from Toloka
            try:

                # Retrieve the existing main pool from Toloka
                self.pool = client.get_pool(pool_id=self.pool_conf['id'])

                # Print status message
                msg.good(f'Successfully loaded main pool with ID {self.pool.id} from Toloka')

                # Check if the pool is an exam pool
                if 'exam' in self.pool_conf.keys():

                    # Set flag to True
                    self.exam = True

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

                # Check if workers should be filtered based on skill
                if 'skill' in self.pool_conf['filter'].keys():

                    # Check if only one skill has been defined
                    if len(self.pool_conf['filter']['skill']) == 1:

                        # Get the skill ID and values from the dictionary key and cast to integers
                        skill_id = list(self.pool_conf['filter']['skill'][0].keys())[0]
                        skill_value = int(list(self.pool_conf['filter']['skill'][0].values())[0])

                        # Define filter
                        skill = (toloka.filter.Skill(skill_id) >= skill_value)

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=skill)

                    # Check if more than one skill has been defined
                    if len(self.pool_conf['filter']['skill']) > 1:

                        # Get the skill ID and values from the dictionary key and cast to integers
                        skills = [(toloka.filter.Skill(list(skill_dict.keys())[0]) >=
                                   int(list(skill_dict.values())[0]))
                                  for skill_dict in self.pool_conf['filter']['skill']]

                        # Add skills one by one
                        for skill in skills:

                            # Check for existing filters and set
                            self.pool.filter = set_filter(filters=self.pool.filter,
                                                          new_filters=skill)

                # Print status message
                msg.good(f'Finished adding filters to the pool')

            # Check if skills have been defined
            if 'skill' in self.pool_conf.keys():

                # Print status message
                msg.info(f'Setting up skill')

                # Check if an existing skill has been requested
                if 'id' in self.pool_conf['skill'].keys():

                    # Attempt to retrieve the skill from Toloka
                    try:

                        # Retrieve the skill
                        self.skill = client.get_skill(skill_id=self.pool_conf['skill']['id'])

                        # Print status message
                        msg.good(f'Successfully loaded skill with ID {self.skill.id} from Toloka')

                    # Catch the error
                    except toloka.exceptions.DoesNotExistApiError:

                        # Raise error
                        raise_error(f'Failed to load skill with ID {self.pool_conf["skill"]["id"]} '
                                    f'from Toloka')

                # Otherwise create a new skill
                else:

                    # Create new skill and set public description
                    self.skill = client.create_skill(name=self.pool_conf['skill']['name'],
                                                     public_requester_description={self.pool_conf['skill']['language']:
                                                                                   self.pool_conf['skill']['description']})
                    # Print status message
                    msg.good(f'Successfully created skill with ID {self.skill.id}')

            # If general quality control rules exist, add them to the pool
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

            # Check if the pool is an exam pool
            if 'exam' in self.pool_conf.keys():

                # Set exam flag to True
                self.exam = True

                # First, check that a skill has been defined in the JSON configuration file
                if not self.skill:

                    # Print status message and exit
                    msg.fail(f'The pool configuration contains the key "exam", but no skill has '
                             f'been defined in the pool configuration.', exits=0)

                # Next, check that a maximum number of exam performers has been set
                if 'max_performers' not in self.pool_conf['exam']:

                    # Print status message and exit
                    msg.fail(f'The pool configuration contains the key "exam", but the number of '
                             f'maximum performers for the exam has not been set. With infinite '
                             f'overlap, the pool will never close. Set the number of maximum '
                             f'performers using the key "max_performers" under the "exam" entry.',
                             exits=0)

                # Next, check the mixer configuration – exam pools must contain tasks with known
                # answers only
                if not self.pool_conf['mixer']['real_tasks_count'] == 0 \
                        and self.pool_conf['mixer']['training_tasks_count'] == 0:

                    # Print status message and exit
                    msg.fail(f'The configuration file defines an exam pool, but the count for both '
                             f'real and training tasks is greater than 0. Exam pools must contain '
                             f'tasks with known (golden) answers only.', exits=0)

                # Finally, check that an input file for exam tasks has been provided
                if 'file' not in self.data_conf:

                    # Print status message and exit
                    msg.fail(f'The data configuration does not contain an entry for "file", which '
                             f'should define a path to a TSV with exam tasks.', exits=0)

                # Otherwise, set up the quality control rule for assigning skills
                self.pool.quality_control.add_action(
                    collector=toloka.collectors.GoldenSet(history_size=self.pool_conf['exam']['history_size']),
                    conditions=[toloka.conditions.TotalAnswersCount >= self.pool_conf['exam']['min_answers']],
                    action=toloka.actions.SetSkillFromOutputField(skill_id=self.skill.id,
                                                                  from_field='correct_answers_rate'))

                # Print status message
                msg.good(f'Successfully configured exam pool using skill {self.skill.id}')

            # Create pool on Toloka
            self.pool = client.create_pool(self.pool)

            # Print status message
            msg.good(f'Successfully created a new pool with ID {self.pool.id} on Toloka')

    def check_input(self, input_obj):
        """
        This function checks the type of the input object and validates the input.

        Parameters:

            input_obj: an InputData object or a subclass of CrowdsourcingTask.

        Returns:

            Assigns the input data under self.input_data or self.output_data, if
            the task defines an exam pool.
        """
        # If the current task is an exam, set the input data directly as output data. The exam input is defined
        # separately in the configuration file under "data". Essentially, this skips over the exam pool.
        if self.exam:

            try:

                # Set the input data as the output data
                self.output_data = input_obj.input_data
                self.prev_task = input_obj

                # Print status message
                msg.info(f'Task "{self.name}" defines an exam pool. Forwarding input data to output data.')

            except AttributeError:

                raise_error(f'Could not load input data from the previous task, although the '
                            f'"forward" flag has been set to True. Check the output from the '
                            f'previous Task!')

        if not self.exam:

            # Process InputData and CrowdsourcingTask objects
            if type(input_obj) == InputData or issubclass(type(input_obj), CrowdsourcingTask):

                # Set the input data for current task
                self.input_data = input_obj.output_data
                self.prev_task = input_obj

    def create_tasks(self, input_data):

        # Print status message
        msg.info(f'Creating and adding tasks to pool with ID {self.pool.id}')

        # Fetch input variable names from the configuration. Create a dictionary with matching
        # key and value pairs, which is updated when creating the toloka.Task objects below.
        input_values = {n: n for n in list(self.conf['data']['input'].keys())}

        # Create a list of Toloka Task objects by looping over the input DataFrame stored under
        # self.input_data. Use the dictionary of input variable names 'input_values' to retrieve
        # the correct columns from the DataFrame.
        tasks = [toloka.Task(pool_id=self.pool.id,
                             input_values={k: row[v] for k, v in input_values.items()},
                             origin_task_id=self.task_id)
                 for _, row in input_data.input_data.iterrows()]

        return tasks

    def create_exam_tasks(self):

        # Print status message
        msg.info(f'Creating and adding exam tasks to pool with ID {self.pool.id}')

        # Load exam tasks from the path defined in the JSON configuration
        exam_data = load_data(self.conf['data']['file'])

        # Fetch input variable names from the configuration. Create a dictionary with matching
        # key and value pairs, which is updated when creating the toloka.Task objects below.
        input_values = {n: n for n in list(self.conf['data']['input'].keys())}
        output_values = {n: n for n in list(self.conf['data']['output'].keys())}

        # Populate the pool with exam tasks that have known answers
        tasks = [toloka.Task(pool_id=self.pool.id,
                             input_values={k: row[v] for k, v in input_values.items()},
                             known_solutions=[toloka.task.BaseTask.KnownSolution(
                                 output_values={k: str(row[v]) for k, v in
                                                output_values.items()})],
                             infinite_overlap=True)
                 for _, row in exam_data.iterrows()]

        return tasks

    def add_tasks(self, tasks):

        # Get Task objects currently in the pool from Toloka
        old_tasks = [task for task in self.client.get_tasks(pool_id=self.pool.id)]

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
            add_tasks_to_pool(client=self.client,
                              tasks=tasks,
                              pool=self.pool,
                              kind='main')

    def run(self):

        # Open the main pool. If training exists, open training pool as well.
        open_pool(client=self.client,
                  pool_id=self.pool.id
                  if self.training is None
                  else [self.pool.id, self.training.id])

        # Track pool progress to print status messages
        track_pool_progress(client=self.client,
                            pool_id=self.pool.id,
                            interval=0.5,
                            exam=self.exam,
                            limit=None if not self.exam
                            else self.pool_conf['exam']['max_performers'])

        # If the main pool is closed and a training pool exists
        if not self.pool.is_open() and self.training is not None:
            
            # Close training pool
            self.client.close_training(self.training.id)

            # Print status
            msg.good(f'Successfully closed pool with ID {self.training.id}')

        # Get results and assign under the attribute 'results'
        self.results = get_results(client=self.client, pool_id=self.pool.id)


class ImageClassificationTask(CrowdsourcingTask):
    """
    This is a class for image classification tasks.
    """

    def __init__(self, configuration, client):
        """
        This function initialises the ImageClassificationTask class, which inherits attributes
        and methods from the superclass Task.
        """

        # Read the configuration from the JSON file
        configuration = read_configuration(configuration=configuration)

        # Specify task and task interface
        task_spec = self.specify_task(configuration=configuration)

        # Use the super() function to access the superclass Task and its methods and attributes.
        # This will set up the project, pool and training as specified in the configuration JSON.
        super().__init__(configuration, client, task_spec)

    def __call__(self, input_obj, **kwargs):

        # If the class is called, use the __call__() method from the superclass
        super().__call__(input_obj, **kwargs)

        # When called, return the ImageClassificationTask object
        return self

    @staticmethod
    def specify_task(configuration):
        """
        This function specifies the task interface on Toloka.

        Parameters:

            configuration: A dictionary containing the configuration defined in the JSON file.

        Returns:

             A Toloka TaskSpec object.
        """

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

        # Return the task specification
        return task_spec


class InputData:
    """
    This is a class for input data.
    """
    def __init__(self, tsv, name):
        """
        This function loads

        Parameters:

            tsv: A string object that defines a path to a TSV file with input data.

        Returns:

             Creates an InputData object.
        """
        # Assign unique name to the InputData object
        self.name = name

        # Load the data from the TSV and assign under attribute 'input_data' as a pandas DataFrame
        self.input_data = load_data(tsv)
