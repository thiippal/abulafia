# -*- coding: utf-8 -*-

# Import libraries
from core_functions import *
from wasabi import Printer
from core_task import CrowdsourcingTask
import toloka.client as toloka
import toloka.client.project.template_builder as tb


# Set up Printer
msg = Printer(pretty=True, timestamp=True, hide_animation=True)


class ImageClassificationTask(CrowdsourcingTask):
    """
    This is a class for image classification tasks.
    """
    def __init__(self, configuration, client):
        """
        This function initialises the ImageClassificationTask class, which inherits attributes
        and methods from the superclass Task.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            An ImageClassificationTask object.
        """
        # Read the configuration from the YAML file
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
            configuration: A dictionary containing the configuration defined in the YAML file.

        Returns:
             A Toloka TaskSpec object.
        """
        # Define expected input and output types for the task
        expected_i, expected_o = {'url'}, {'bool'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)

        # Create the task interface; start by setting up the image viewer
        img_viewer = tb.ImageViewV1(url=tb.InputData(input_data['url']),
                                    rotatable=True,
                                    ratio=[1, 1])

        # Define the prompt text above the button group
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Set up a radio group for labels
        radio_group = tb.ButtonRadioGroupFieldV1(

            # Set up the output data field
            data=tb.OutputData(output_data['bool']),

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
        hotkey_plugin = tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData(output_data['bool']),
                                                                payload=True),
                                           key_2=tb.SetActionV1(data=tb.OutputData(output_data['bool']),
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


class ImageSegmentationTask(CrowdsourcingTask):
    """
    This is a class for image segmentation tasks.
    """
    def __init__(self, configuration, client):
        """
        This function initialises the ImageSegmentationTask class, which inherits attributes
        and methods from the superclass Task.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            An ImageSegmentationTask object.
        """
        # Read the configuration from the YAML file
        configuration = read_configuration(configuration=configuration)

        # Specify task and task interface
        task_spec = self.specify_task(configuration=configuration)

        # Use the super() function to access the superclass Task and its methods and attributes.
        # This will set up the project, pool and training as specified in the configuration file.
        super().__init__(configuration, client, task_spec)

    def __call__(self, input_obj, **kwargs):

        # If the class is called, use the __call__() method from the superclass
        super().__call__(input_obj, **kwargs)

        # When called, return the ImageSegmentationTask object
        return self

    @staticmethod
    def specify_task(configuration):
        """
        This function specifies the task interface on Toloka.

        Parameters:
            configuration: A dictionary containing the configuration defined in the YAML file.

        Returns:
             A Toloka TaskSpec object.
        """
        # Define expected input and output types for the task
        expected_i, expected_o = {'url'}, {'json'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)

        # Create the task interface; start by setting up the image segmentation interface
        img_ui = tb.ImageAnnotationFieldV1(

            # Set up the output data field
            data=tb.OutputData(output_data['json']),

            # Set up the input data field
            image=tb.InputData(input_data['url']),

            # Set up the allowed shapes: note that their order will define the order in the UI
            shapes={'rectangle': True, 'polygon': True},

            # Set minimum width in pixels
            min_width=500,

            # Set up validation
            validation=tb.RequiredConditionV1(hint="Please select at least one area!"))

        # Define the text prompt below the segmentation UI
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Add hotkey plugin
        hotkey_plugin = tb.ImageAnnotationHotkeysPluginV1(cancel='s',
                                                          confirm='a',
                                                          polygon='e',
                                                          rectangle='w',
                                                          select='q')

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([img_ui, prompt]),
            plugins=[hotkey_plugin]
        )

        # Create a task specification with interface and input/output data
        task_spec = toloka.project.task_spec.TaskSpec(
            input_spec=data_in,
            output_spec=data_out,
            view_spec=interface
        )

        # Return the task specification
        return task_spec


class SegmentationVerificationTask(CrowdsourcingTask):
    """
    This is a class for binary verification tasks.
    """
    def __init__(self, configuration, client):
        """
        This function initialises the SegmentationVerificationTask class, which inherits attributes
        and methods from the superclass Task.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            A SegmentationVerificationTask object.
        """
        # Read the configuration from the YAML file
        configuration = read_configuration(configuration=configuration)

        # Specify task and task interface
        task_spec = self.specify_task(configuration=configuration)

        # Use the super() function to access the superclass Task and its methods and attributes.
        # This will set up the project, pool and training as specified in the configuration file.
        super().__init__(configuration, client, task_spec)

    def __call__(self, input_obj, **kwargs):

        # If the class is called, use the __call__() method from the superclass
        super().__call__(input_obj, **kwargs)

        # When called, return the SegmentationVerificationTask object
        return self

    @staticmethod
    def specify_task(configuration):
        """
        This function specifies the task interface on Toloka.

        Parameters:
            configuration: A dictionary containing the configuration defined in the YAML file.

        Returns:
             A Toloka TaskSpec object.
        """
        # Define expected input and output types for the task
        expected_i, expected_o = {'url', 'json'}, {'bool'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)

        # Create the task interface; start by setting up the image segmentation interface
        img_ui = tb.ImageAnnotationFieldV1(

            # Set up the output data field
            data=tb.InternalData(path=input_data['json'],
                                 default=tb.InputData(input_data['json'])),

            # Set up the input data field
            image=tb.InputData(path=input_data['url']),

            # Set minimum width in pixels
            min_width=500,

            # Disable annotation interface
            disabled=True)

        # Define the text prompt below the segmentation UI
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Set up a radio group for labels
        radio_group = tb.ButtonRadioGroupFieldV1(

            # Set up the output data field
            data=tb.OutputData(output_data['bool']),

            # Create radio buttons
            options=[
                tb.fields.GroupFieldOption(value=True, label='Yes'),
                tb.fields.GroupFieldOption(value=False, label='No')
            ],

            # Set up validation
            validation=tb.RequiredConditionV1(hint="You must choose one response.")
        )

        # Add hotkey plugin
        hotkey_plugin = tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData(output_data['bool']),
                                                                payload=True),
                                           key_2=tb.SetActionV1(data=tb.OutputData(output_data['bool']),
                                                                payload=False))

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([img_ui, prompt, radio_group]),
            plugins=[hotkey_plugin]
        )

        # Create a task specification with interface and input/output data
        task_spec = toloka.project.task_spec.TaskSpec(
            input_spec=data_in,
            output_spec=data_out,
            view_spec=interface
        )

        # Return the task specification
        return task_spec
