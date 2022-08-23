# -*- coding: utf-8 -*-

# Import libraries
from ..functions.core_functions import *
from wasabi import Printer
from toloka.streaming.event import AssignmentEvent
import datetime
import uuid
import toloka.client as toloka
from toloka.client.pool.speed_quality_balance_config import BestConcurrentUsersByQuality, TopPercentageByQuality

# Set up Printer
msg = Printer(pretty=True, timestamp=True, hide_animation=True)


# Define the base class for Toloka tasks
class CrowdsourcingTask:
    """
    This is the base class for defining crowdsourcing tasks on Toloka. The class loads
    the task configuration from the JSON file, validates input data, and opens and closes
    pools on Toloka.
    """

    def __init__(self, configuration, client, task_spec, **kwargs):
        """
        This function initialises the CrowdsourcingTask class.

        Parameters:
            configuration: A dictionary that contains the configuration loaded from the YAML file.
            client: A TolokaClient object with valid credentials.
            task_spec: A Toloka TaskSpec object with task interface and input/output data.
        """
        # Create unique identifier for the Task and shorten
        self.task_id = str(uuid.uuid4())[:8].upper()

        # Assign configuration and client to attributes
        self.client = client
        self.conf = configuration

        # Unpack the configuration from YAML into attributes
        self.data_conf = self.conf['data']
        self.project_conf = self.conf['project']
        self.action_conf = self.conf['actions'] if 'actions' in self.conf.keys() else None
        self.pool_conf = self.conf['pool']
        self.train_conf = self.conf['training'] if 'training' in self.conf.keys() else None
        self.qual_conf = self.conf['quality_control'] if 'quality_control' in self.conf.keys() else None

        # Assign flags and default values
        self.name = self.conf['name']  # Unique name of the task
        self.project = None  # Placeholder for Toloka Project object
        self.training = None  # Placeholder for Toloka Training object
        self.pool = None  # Placeholder for Toloka Pool object
        self.prev_task = None  # Previous Task object in the task sequence
        self.input_data = None  # Placeholder for input data
        self.output_data = None  # Placeholder for output data
        self.train_data = None  # Placeholder for training data
        self.train_tasks = None  # Placeholder for training tasks
        self.tasks = None  # Placeholder for main tasks
        self.results = None  # Placeholder for results
        self.is_complete = False  # Is the Task complete or not?
        self.skill = False  # Does the Task provide or require a skill?
        self.exam = False  # Is this Task an exam?
        self.test = True if kwargs and kwargs['test'] else False  # Are we running a test?

        # See if users should be banned from the pool and check that blocklist is configured correctly
        try:

            self.blocklist = list(pd.read_csv(self.pool_conf['blocklist'], sep="\t")["user_id"]) \
                if 'blocklist' in self.pool_conf.keys() else []

        except KeyError:

            msg.warn(f"Could not find the column 'user_id' from blocklist.", exits=1)

        # Print status message
        msg.info(f'The unique ID for this object ({self.name}) is {self.task_id}')

        # Get requester information unless we're running a test
        if not self.test:

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

        # Create exam tasks if necessary
        if self.exam and 'file' in self.data_conf:

            # Create exam tasks and add them to the pool
            self.tasks = create_exam_tasks(self)

            if not self.test:

                add_tasks(self, tasks=self.tasks)

        # Create main tasks if they have been defined
        if not self.exam and 'file' in self.data_conf:

            # Load data
            data = load_data(self.data_conf['file'], self.data_conf['input'])

            # Create tasks and add them to the pool
            self.tasks = create_tasks(self, data)

            if not self.test:

                add_tasks(self, self.tasks)

    def __call__(self, in_obj, **options):

        # Check that the input object is a list of AssignmentEvent objects
        if type(in_obj) == list and all(isinstance(item, AssignmentEvent) for item in in_obj):

            # Check the status of AssignmentEvent objects. These AssignmentEvent objects correspond
            # to task suites on Toloka. Their status may be accepted, rejected, submitted, etc.
            for event in in_obj:

                # If the event type is accepted or submitted, create new tasks in current pool
                if event.event_type.value in ['ACCEPTED', 'SUBMITTED']:

                    # Create new Task objects
                    new_tasks = [Task(pool_id=self.pool.id,
                                      overlap=self.pool_conf['defaults']['default_overlap_for_new_tasks'],
                                      input_values={k: v for k, v in task.input_values.items()},
                                      unavailable_for=self.blocklist
                                      )
                                 for task, solution
                                 in zip(event.assignment.tasks,
                                        event.assignment.solutions)]

                    # If the assignments are for a verification pool, add the output values to the input of
                    # the new task and make the verification task unavailable for the performer
                    if options and 'verify' in options:

                        new_tasks = [Task(pool_id=self.pool.id,
                                          overlap=self.pool_conf['defaults']['default_overlap_for_new_tasks'],
                                          input_values={**task.input_values,
                                                        **solution.output_values,
                                                        'assignment_id': event.assignment.id},
                                          unavailable_for=[*self.blocklist, event.assignment.user_id])
                                     for task, solution in zip(event.assignment.tasks, event.assignment.solutions)]

                    # Add Tasks and open the pool
                    self.client.create_tasks(tasks=new_tasks, open_pool=True)

                    # Print status messages
                    msg.good(f'Received {len(new_tasks)} {event.event_type.value.lower()} tasks '
                             f'from pool {event.assignment.pool_id}')
                    msg.good(f'Creating {len(new_tasks)} new tasks in pool {self.pool.id}')

    def load_project(self, client, task_spec):
        """
        This function loads an existing project from Toloka or creates a new project according to
        the configuration in the YAML file under the key "project".

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

            # Create a new Toloka Project object
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

            # Create new project on the platform if we're not testing
            if not self.test:

                self.project = client.create_project(self.project)

                # Print status message
                msg.good(f'Successfully created a new project with ID {self.project.id} on Toloka')

    def load_training(self, client):
        """
        This function loads a Training pool from Toloka or creates a new Training according to
        the configuration in the YAML file under the key "training".

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

                # Create the training pool if not testing
                if not self.test:

                    self.training = client.create_training(self.training)

                    # Print status messages
                    msg.good(f'Successfully created a new training pool')

                # Load training data
                self.train_data = load_data(self.conf['training']['data']['file'],
                                            self.conf['training']['data']['input'])

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
                                                infinite_overlap=True,
                                                unavailable_for=self.blocklist)
                                    for _, row in self.train_data.iterrows()]

                # Add training tasks to the training pool
                if not self.test:

                    add_tasks_to_pool(client=self.client, tasks=self.train_tasks, pool=self.training,
                                      kind='train')

    def load_pool(self, client):
        """
        This function loads a main pool from Toloka or creates a new pool according to the
        configuration defined in the YAML file under the key "pool".

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
                                    will_expire=datetime.datetime.now() + datetime.timedelta(
                                        days=365),
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

            if 'estimated_time_per_suite' not in self.pool_conf.keys():
                msg.warn(f"Parameter estimated_time_per_suite is not configured in pool settings for {self.name}. "
                         f"Consider adding it to verify that the reward_per_assignment you have set results in a fair "
                         f"hourly wage of at least $12. Do you wish to proceed with the current configuration anyway "
                         f"(y/n)?")

                choice = input("")

                if choice == "n":

                    msg.info("Cancelling pipeline")
                    exit()

            else:

                check_reward(self.pool_conf['estimated_time_per_suite'], 
                             self.pool_conf['setup']['reward_per_assignment'],
                             self.name)

            # Check if filters have been defined
            if 'filter' in self.pool_conf.keys() and self.pool_conf['filter'] is not None:

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
                        skill_id = str(list(self.pool_conf['filter']['skill'][0].keys())[0])
                        skill_value = int(list(self.pool_conf['filter']['skill'][0].values())[0])

                        # Define filter
                        skill = (toloka.filter.Skill(skill_id) >= skill_value)

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=skill)

                    # Check if more than one skill has been defined
                    if len(self.pool_conf['filter']['skill']) > 1:

                        # Get the skill ID and values from the dictionary key and cast to integers
                        skills = [(toloka.filter.Skill(str(list(skill_dict.keys())[0])) >=
                                   int(list(skill_dict.values())[0]))
                                  for skill_dict in self.pool_conf['filter']['skill']]

                        # Add skills one by one
                        for skill in skills:
                            # Check for existing filters and set
                            self.pool.filter = set_filter(filters=self.pool.filter,
                                                          new_filters=skill)

                # Check if workers should be filtered based on gender
                if 'gender' in self.pool_conf['filter'].keys():

                    choice = self.pool_conf['filter']['gender'].upper()
                    gender = (toloka.filter.Gender == choice)

                    self.pool.filter = set_filter(filters=self.pool.filter,
                                                  new_filters=gender)

                # Check if workers should be filtered based on whether they allow
                # adult content or not
                if 'adult_allowed' in self.pool_conf['filter'].keys():

                    choice = bool(self.pool_conf['filter']['adult_allowed'])

                    adult_allowed = (toloka.filter.AdultAllowed == choice)

                    self.pool.filter = set_filter(filters=self.pool.filter,
                                                  new_filters=adult_allowed)

                # Check if workers should be filtered based on country
                if 'country' in self.pool_conf['filter'].keys():

                    # Check if only one country has been defined
                    if len(self.pool_conf['filter']['country']) == 1:

                        # Create filter
                        country = (toloka.filter.Country ==
                                   self.pool_conf['filter']['country'][0].upper())

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=country)

                    # Check if more than one country has been defined
                    if len(self.pool_conf['filter']['country']) > 1:

                        # Create filters
                        levels = [(toloka.filter.Country == c.upper()) for c in
                                  self.pool_conf['filter']['country']]

                        # Combine filters
                        levels = toloka.filter.FilterOr(levels)

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=levels)

                # Check if workers should be filtered based on city
                if 'city' in self.pool_conf['filter'].keys():

                    # Check if only one city has been defined
                    if len(self.pool_conf['filter']['city']) == 1:

                        # Create filter
                        city = (toloka.filter.City ==
                                   int(self.pool_conf['filter']['city'][0]))

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=city)

                    # Check if more than one city has been defined
                    if len(self.pool_conf['filter']['city']) > 1:

                        # Create filters
                        levels = [(toloka.filter.City == int(c)) for c in
                                  self.pool_conf['filter']['city']]

                        # Combine filters
                        levels = toloka.filter.FilterOr(levels)

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=levels)

                # Filter performers by date of birth (before or after a certain date or both)
                # Note that date of birth needs to be expressed as a UNIX timestamp

                # TODO converter from datetime to UNIX timestamp, so date can be configured as 
                # a date in the configuration file
                if 'date_of_birth' in self.pool_conf['filter'].keys():

                    if len(self.pool_conf['filter']['date_of_birth']) == 1:
                        
                        if 'before' in self.pool_conf['filter']['date_of_birth'].keys():
                            
                            before = self.pool_conf['filter']['date_of_birth']['before']
                            b_filter = (toloka.filter.DateOfBirth <= before)
                            self.pool.filter = set_filter(filters=self.pool.filter,
                                                          new_filters=b_filter)

                        if 'after' in self.pool_conf['filter']['date_of_birth'].keys():
                            
                            after = self.pool_conf['filter']['date_of_birth']['after']
                            a_filter = (toloka.filter.DateOfBirth >= after)
                            self.pool.filter = set_filter(filters=self.pool.filter,
                                                          new_filters=a_filter)

                    if len(self.pool_conf['filter']['date_of_birth']) > 1:

                        before = self.pool_conf['filter']['date_of_birth']['before']
                        after = self.pool_conf['filter']['date_of_birth']['after']

                        ba_filters = [(toloka.filter.DateOfBirth <= before), (toloka.filter.DateOfBirth >= after)]
                        levels = toloka.filter.FilterAnd(ba_filters)

                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=levels)

                # Check if workers should be filtered based on UserAgentType
                if 'user_agent_type' in self.pool_conf['filter'].keys():

                    # Check if only one agent type has been defined
                    if len(self.pool_conf['filter']['user_agent_type']) == 1:

                        # Create filter
                        agent = (toloka.filter.UserAgentType ==
                                   self.pool_conf['filter']['user_agent_type'][0].upper())

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=agent)

                    # Check if more than one user agent has been defined
                    if len(self.pool_conf['filter']['user_agent_type']) > 1:

                        # Create filters
                        levels = [(toloka.filter.UserAgentType == agent.upper()) for agent in
                                  self.pool_conf['filter']['user_agent_type']]

                        # Combine filters
                        levels = toloka.filter.FilterOr(levels)

                        # Check for existing filters and set
                        self.pool.filter = set_filter(filters=self.pool.filter,
                                                      new_filters=levels)

                # TODO missing filters

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
                                                     public_requester_description={
                                                         self.pool_conf['skill']['language']:
                                                             self.pool_conf['skill'][
                                                                 'description']})
                    # Print status message
                    msg.good(f'Successfully created skill with ID {self.skill.id}')

            # If general quality control rules exist, add them to the pool
            if self.qual_conf is not None:

                # Print status message
                msg.info(f'Setting up quality control rules')

                # Check if speed/quality balance settings have been configured
                if 'speed_quality_balance' in self.qual_conf and self.qual_conf['speed_quality_balance'] is not None:

                    if "top_percentage_by_quality" in self.qual_conf['speed_quality_balance']:
    
                        # Get percentage for top workers from configuration
                        user_percentage = self.qual_conf["speed_quality_balance"]["top_percentage_by_quality"]

                        speed_quality = TopPercentageByQuality(percent=user_percentage)
                        
                        msg.info(f"Speed/quality setting: only top {user_percentage}% of users will have access to pool {self.name}")

                    elif "best_concurrent_users_by_quality" in self.qual_conf['speed_quality_balance']:
                        
                        # Get number of top workers from configuration
                        user_count = self.qual_conf['speed_quality_balance']["best_concurrent_users_by_quality"]
                        
                        speed_quality = BestConcurrentUsersByQuality(count=user_count)

                        msg.info(f"Speed/quality setting: only top {user_count} users will have access to pool {self.name}")
                    
                    # Set speed/quality setting
                    self.pool.set_speed_quality_balance(speed_quality)

                # Set up quality control rule for fast responses
                if 'fast_responses' in self.qual_conf:

                    # Unpack rules into variables
                    history_size = self.qual_conf['fast_responses']['history_size']
                    count = self.qual_conf['fast_responses']['count']
                    threshold = self.qual_conf['fast_responses']['threshold']
                    duration = self.qual_conf['fast_responses']['ban_duration']
                    units = self.qual_conf['fast_responses']['ban_units'].upper()

                    # Add quality control rule to the pool
                    self.pool.quality_control.add_action(
                        collector=toloka.collectors.AssignmentSubmitTime(history_size=history_size,
                                                                         fast_submit_threshold_seconds=threshold),
                        conditions=[toloka.conditions.FastSubmittedCount > count],
                        action=toloka.actions.RestrictionV2(
                            scope=toloka.user_restriction.UserRestriction.PROJECT,
                            duration=duration,
                            duration_unit=units,
                            private_comment='Fast responses'
                        )
                    )

                    # Print status message
                    msg.good(f'Added quality control rule: ban for {duration} {units.lower()} if '
                             f'response time is less than {threshold} seconds for {count} out '
                             f'of {history_size} tasks')

                # Set up quality control rule for skipped assignments
                if 'skipped_assignments' in self.qual_conf:

                    # Unpack rules into variables
                    count = self.qual_conf['skipped_assignments']['count']
                    duration = self.qual_conf['skipped_assignments']['ban_duration']
                    units = self.qual_conf['skipped_assignments']['ban_units'].upper()

                    # Add quality control rule to the pool
                    self.pool.quality_control.add_action(
                        collector=toloka.collectors.SkippedInRowAssignments(),
                        conditions=[toloka.conditions.SkippedInRowCount > count],
                        action=toloka.actions.RestrictionV2(
                            scope=toloka.user_restriction.UserRestriction.PROJECT,
                            duration=duration,
                            duration_unit=units,
                            private_comment='Skipped assignments'
                        )
                    )

                    # Print status message
                    msg.good(f'Added quality control rule: ban for {duration} {units.lower()} if '
                             f'user skipped {count} assignments in a row.')

                # Set up quality control rule for re-assigning work from banned users
                if 'redo_banned' in self.qual_conf:

                    if self.qual_conf['redo_banned']:

                        # Add quality control rule to the pool
                        self.pool.quality_control.add_action(
                            collector=toloka.collectors.UsersAssessment(),
                            conditions=[toloka.conditions.PoolAccessRevokedReason
                                        == toloka.conditions.PoolAccessRevokedReason.RESTRICTION],
                            action=toloka.actions.ChangeOverlap(delta=1, open_pool=True)
                        )

                # Set up captcha quality control
                if 'captcha' in self.qual_conf:

                    # Unpack rules into variables 
                    freq = self.qual_conf['captcha']['frequency'].upper()
                    success_rate = self.qual_conf['captcha']['success_rate']
                    duration = self.qual_conf['captcha']['ban_duration']
                    units = self.qual_conf['captcha']['ban_units'].upper()

                    # Set captcha frequency according to configuration
                    self.pool.set_captcha_frequency(freq)

                    # Add quality control rule to the pool
                    self.pool.quality_control.add_action(
                        collector=toloka.collectors.Captcha(),
                        conditions=[toloka.conditions.SuccessRate < success_rate],
                        action=toloka.actions.RestrictionV2(
                            scope=toloka.user_restriction.UserRestriction.PROJECT,
                            duration=duration,
                            duration_unit=units,
                            private_comment="Too many Captcha mistakes"
                        )
                    )

                    # Print status message
                    msg.good(f"Added quality control rule: ban for {duration} {units.lower()} if "
                             f"user's CAPTCHA success rate is less than {success_rate}%. "
                             f"CAPTCHA frequency is set to {freq}.")

                # Set up GoldenSet quality control (performance on control tasks)
                if 'golden_set' in self.qual_conf:

                    # How many previous answers to control tasks to consider
                    history_size = self.qual_conf['golden_set']['history_size']

                    # Ban user if they fail control tasks with a rate higher than the threshold
                    if 'ban_rules' in self.qual_conf['golden_set']:

                        # Unpack rules into variables
                        incorrect_threshold = self.qual_conf['golden_set']['ban_rules']['incorrect_threshold']
                        ban_duration = self.qual_conf['golden_set']['ban_rules']['ban_duration']
                        ban_units = self.qual_conf['golden_set']['ban_rules']['ban_units']

                        self.pool.quality_control.add_action(
                            collector=toloka.collectors.GoldenSet(history_size=history_size),
                            conditions=[toloka.conditions.GoldenSetIncorrectAnswersRate > incorrect_threshold],
                            action=toloka.actions.RestrictionV2(
                                scope=toloka.user_restriction.UserRestriction.PROJECT,
                                duration=ban_duration,
                                duration_unit=ban_units,
                                private_comment="Fails control tasks too often"
                            )
                        )

                        # Print status message
                        msg.good(f"Added quality control rule: ban for {ban_duration} {ban_units.lower()} if "
                                 f"user fails over {incorrect_threshold}% of control tasks.")
                    
                    # Automatically reject assignments from user if they often fail control tasks
                    if 'reject_rules' in self.qual_conf['golden_set']:

                        incorrect_threshold = self.qual_conf['golden_set']['reject_rules']['incorrect_threshold']

                        self.pool.quality_control.add_action(
                            collector=toloka.collectors.GoldenSet(history_size=history_size),
                            conditions=[toloka.conditions.GoldenSetIncorrectAnswersRate > incorrect_threshold],
                            action=toloka.actions.RejectAllAssignments(
                                public_comment="Failed too many control tasks"
                            )
                        )

                        # Print status message
                        msg.good(f"Added quality control rule: Reject all user's assignments if "
                                 f"user fails over {incorrect_threshold}% of control tasks.")

                    # Automatically approve assignments from user if they are successful in control tasks
                    if 'approve_rules' in self.qual_conf['golden_set']:

                        correct_threshold = self.qual_conf['golden_set']['approve_rules']['correct_threshold']

                        self.pool.quality_control.add_action(
                            collector=toloka.collectors.GoldenSet(history_size=history_size),
                            conditions=[toloka.conditions.GoldenSetCorrectAnswersRate > correct_threshold],
                            action=toloka.actions.ApproveAllAssignments()
                        )

                        # Print status message
                        msg.good(f"Added quality control rule: Approve all user's assignments if "
                                 f"user successfully completes over {correct_threshold}% of control tasks.")

                    # Set a skill for user if they are successful in control tasks
                    if 'skill_rules' in self.qual_conf['golden_set']:
                        
                        # Unpack rules into variables
                        correct_threshold = self.qual_conf['golden_set']['skill_rules']['correct_threshold']
                        skill_id = self.qual_conf['golden_set']['skill_rules']['skill_id']
                        skill_value = self.qual_conf['golden_set']['skill_rules']['skill_value']

                        self.pool.quality_control.add_action(
                            collector=toloka.collectors.GoldenSet(history_size=history_size),
                            conditions=[toloka.conditions.GoldenSetCorrectAnswersRate > correct_threshold],
                            action=toloka.actions.SetSkill(skill_id=skill_id, skill_value=skill_value)
                        )

                        # Print status message
                        msg.good(f"Added quality control rule: Grant user a skill value {skill_value} for skill "
                                 f"{skill_id} if user successfully completes over {correct_threshold}% of control tasks.")

            # Check if the pool is an exam pool
            if 'exam' in self.pool_conf.keys():

                # Set exam flag to True
                self.exam = True

                # First, check that a skill has been defined in the configuration file
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
                    collector=toloka.collectors.GoldenSet(
                        history_size=self.pool_conf['exam']['history_size']),
                    conditions=[toloka.conditions.TotalAnswersCount >= self.pool_conf['exam'][
                        'min_answers']],
                    action=toloka.actions.SetSkillFromOutputField(skill_id=self.skill.id,
                                                                  from_field='correct_answers_rate'))

                # Print status message
                msg.good(f'Successfully configured exam pool using skill {self.skill.id}')

            # Create pool on Toloka
            if not self.test:

                self.pool = self.client.create_pool(self.pool)

                # Print status message
                msg.good(f'Successfully created a new pool with ID {self.pool.id} on Toloka')