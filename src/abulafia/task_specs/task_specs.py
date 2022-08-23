# -*- coding: utf-8 -*-

# Import libraries
from ..functions.core_functions import *
from wasabi import Printer
from .core_task import CrowdsourcingTask
import toloka.client as toloka
import toloka.client.project.template_builder as tb
from collections import OrderedDict


# Set up Printer
msg = Printer(pretty=True, timestamp=True, hide_animation=True)


class ImageClassification(CrowdsourcingTask):
    """
    This is a class for image classification tasks.
    """
    def __init__(self, configuration, client, **kwargs):
        """
        This function initialises the ImageClassification class, which inherits attributes
        and methods from the superclass CrowdsourcingTask.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            An ImageClassification object.
        """
        # Read the configuration from the YAML file
        configuration = read_configuration(configuration=configuration)

        # Specify task and task interface
        task_spec = self.specify_task(configuration=configuration)

        # Use the super() function to access the superclass Task and its methods and attributes.
        # This will set up the project, pool and training as specified in the configuration JSON.
        super().__init__(configuration, client, task_spec, **kwargs)

    def __call__(self, input_obj, **kwargs):

        # If the class is called, use the __call__() method from the superclass
        super().__call__(input_obj, **kwargs)

        # When called, return the ImageClassification object
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


class ImageSegmentation(CrowdsourcingTask):
    """
    This is a class for image segmentation tasks.
    """
    def __init__(self, configuration, client):
        """
        This function initialises the ImageSegmentation class, which inherits attributes
        and methods from the superclass CrowdsourcingTask.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            An ImageSegmentation object.
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

        # When called, return the ImageSegmentation object
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


class AddOutlines(CrowdsourcingTask):
    """
    This is a class for tasks that add more bounding boxes to images with pre-existing labelled bounding boxes.
    """
    def __init__(self, configuration, client):
        """
        This function initialises the AddOutlines class, which inherits attributes
        and methods from the superclass CrowdsourcingTask.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            An AddOutlines object.
        """

        # Read the configuration from the YAML file
        configuration = read_configuration(configuration=configuration)

        # Specify task and task interface
        task_spec = self.specify_task(configuration=configuration)

        super().__init__(configuration, client, task_spec)


    def __call__(self, input_obj, **kwargs):

        # If the class is called, use the __call__() method from the superclass
        super().__call__(input_obj, **kwargs)

        # When called, return the AddOutlines object
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
        expected_i, expected_o = {'url', 'json'}, {'json', 'bool'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)
        
        # Add assignment ID to the input data
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)

        try:
            labels = [tb.ImageAnnotationFieldV1.Label(value=value, label=label) for 
                      value, label in configuration["interface"]["labels"].items()]
        except KeyError:
            msg.warn(f"Key 'labels' needs to be configured in the configuration of pool {configuration['name']} under key 'interface'",
                     exits=1)

        # Create the task interface; start by setting up the image segmentation interface
        img_ui = tb.ImageAnnotationFieldV1(

            # Set up the output data field
            data=tb.OutputData(path=output_data['json'],
                               default=tb.InputData(input_data['json'])),

            # Set up the input data field
            image=tb.InputData(input_data['url']),

            # Set up the allowed shapes: note that their order will define the order in the UI
            shapes={'polygon': True, 'rectangle': True},

            # Set minimum width in pixels
            min_width=500,

            # Set up labels for the outlines
            labels=labels,

            disabled=False
        )

        # Create a button for cases where a target does not exist
        checkbox = tb.CheckboxFieldV1(
            data=tb.OutputData(output_data['bool'], default=False),
            label="Target does not exist"
        )

        # Define the text prompt below the segmentation UI
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([img_ui, prompt, checkbox], 
            validation=tb.AnyConditionV1(conditions=[tb.SchemaConditionV1(data=tb.OutputData(output_data['json']),
                                                                          schema={'type': 'array', 'minItems': 2}),
                                                     tb.EqualsConditionV1(data=tb.OutputData(output_data['bool']), to=True)],
                                                     hint="Outline at least one target of specify if target does not exist."),
            )
        )

        # Create a task specification with interface and input/output data
        task_spec = toloka.project.task_spec.TaskSpec(
            input_spec=data_in,
            output_spec=data_out,
            view_spec=interface
        )

        # Return the task specification
        return task_spec


class SegmentationClassification(CrowdsourcingTask):
    """
    This is a class for binary segmentation classification tasks.
    """
    def __init__(self, configuration, client):
        """
        This function initialises the SegmentationClassification class, which inherits attributes
        and methods from the superclass Task.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            A SegmentationClassification object.
        """
        # Read the configuration from the YAML file
        configuration = read_configuration(configuration=configuration)

        # Specify task and task interface
        task_spec = self.specify_task(configuration=configuration)

        # Use the super() function to access the superclass Task and its methods and attributes.
        # This will set up the project, pool and training as specified in the configuration file.
        super().__init__(configuration, client, task_spec)

    def __call__(self, input_obj):

        # If the class is called, use the __call__() method from the superclass
        super().__call__(input_obj)

        # When called, return the SegmentationClassification object
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

        # Add assignment ID to the input data
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)

        labels = [tb.ImageAnnotationFieldV1.Label(value=value, label=label) for 
                    value, label in configuration["interface"]["labels"].items()] if "labels" in configuration["interface"] else None

        # Create the task interface; start by setting up the image segmentation interface
        img_ui = tb.ImageAnnotationFieldV1(

            # Set up the output data field
            data=tb.InternalData(path=input_data['json'],
                                 default=tb.InputData(input_data['json'])),

            # Set up the input data field
            image=tb.InputData(path=input_data['url']),

            labels=labels,

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

        # Set task width limit
        task_width_plugin = tb.TolokaPluginV1(kind='scroll', task_width=500)

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([img_ui, prompt, radio_group]),
            plugins=[hotkey_plugin, task_width_plugin]
        )

        # Create a task specification with interface and input/output data
        task_spec = toloka.project.task_spec.TaskSpec(
            input_spec=data_in,
            output_spec=data_out,
            view_spec=interface
        )

        # Return the task specification
        return task_spec


class LabelledSegmentationVerification(CrowdsourcingTask):
    """
    This is a class for binary segmentation verification tasks with labelled bounding boxes.
    """
    def __init__(self, configuration, client):
        """
        This function initialises the LabelledSegmentationVerification class, which inherits attributes
        and methods from the superclass Task.
        
        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            A LabelledSegmentationVerification object.
        """
        # Read the configuration from the YAML file
        configuration = read_configuration(configuration=configuration)

        # Specify task and task interface
        task_spec = self.specify_task(configuration=configuration)

        # Use the super() function to access the superclass Task and its methods and attributes.
        # This will set up the project, pool and training as specified in the configuration file.
        super().__init__(configuration, client, task_spec)

    def __call__(self, input_obj):

        # If the class is called, use the __call__() method from the superclass
        super().__call__(input_obj, verify=True)

        # When called, return the LabelledSegmentationVerification object
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
        expected_i, expected_o = {'url', 'json', 'bool'}, {'bool'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)

        # Add assignment ID to the input data
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)
        data_out['no_target'] = toloka.project.BooleanSpec()

        try:
            labels = [tb.ImageAnnotationFieldV1.Label(value=value, label=label) for 
                      value, label in configuration["interface"]["labels"].items()]
        except KeyError:
            msg.warn(f"Key 'labels' needs to be configured in the configuration of pool {configuration['name']} under key 'interface'",
                     exits=1)

        # Create the task interface; start by setting up the image segmentation interface
        img_ui = tb.ImageAnnotationFieldV1(

            # Set up the output data field
            data=tb.InternalData(path=input_data['json'],
                                 default=tb.InputData(input_data['json'])),

            # Set up the input data field
            image=tb.InputData(path=input_data['url']),

            # Set minimum width in pixels
            min_width=500,

            labels=labels,

            # Disable annotation interface
            disabled=True)

        # Define the text prompt below the segmentation UI
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Create a button for cases where a target does not exist
        checkbox = tb.CheckboxFieldV1(
            data=tb.OutputData('no_target', default=tb.InputData(input_data['bool'])),
            label="Target does not exist",
            disabled=True
        )

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

        # Set task width limit
        task_width_plugin = tb.TolokaPluginV1(kind='scroll', task_width=500)

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([img_ui, prompt, checkbox, radio_group]),
            plugins=[hotkey_plugin, task_width_plugin]
        )

        # Create a task specification with interface and input/output data
        task_spec = toloka.project.task_spec.TaskSpec(
            input_spec=data_in,
            output_spec=data_out,
            view_spec=interface
        )

        # Return the task specification
        return task_spec
        

class FixImageSegmentation(CrowdsourcingTask):
    """
    This is a class for fixing partially correct image segmentation tasks: modifying
    existing outlines and/or creating new ones.
    """
    def __init__(self, configuration, client):
        """
        This function initialises the FixImageSegmentation class, which inherits attributes
        and methods from the superclass Task.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            A FixImageSegmentation object.
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

        # When called, return the FixImageSegmentation object
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
        expected_i, expected_o = {'url', 'json'}, {'json'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)
        
        # Add assignment ID to the input data
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)
        
        # Create the task interface; start by setting up the image segmentation interface
        img_ui = tb.ImageAnnotationFieldV1(

            # Set up the output data field
            data=tb.OutputData(path=output_data['json'],
                               default=tb.InputData(input_data['json'])),

            # Set up the input data field
            image=tb.InputData(input_data['url']),

            # Set up the allowed shapes: note that their order will define the order in the UI
            shapes={'rectangle': True, 'polygon': True},

            # Set minimum width in pixels
            min_width=500,

            # Set up validation
            validation=tb.RequiredConditionV1(hint="Please select at least one area!"),

            disabled=False
        )

        # Define the text prompt below the segmentation UI
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([img_ui, prompt])
        )

        # Create a task specification with interface and input/output data
        task_spec = toloka.project.task_spec.TaskSpec(
            input_spec=data_in,
            output_spec=data_out,
            view_spec=interface
        )

        # Return the task specification
        return task_spec


class SegmentationVerification(CrowdsourcingTask):
    """
    This is a class for binary image segmentation verification tasks.
    """
    def __init__(self, configuration, client):
        """
        This function initialises the SegmentationVerification class, which inherits attributes
        and methods from the superclass Task.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            A SegmentationVerification object.
        """
        # Read the configuration from the YAML file
        configuration = read_configuration(configuration=configuration)

        # Specify task and task interface
        task_spec = self.specify_task(configuration=configuration)

        # Use the super() function to access the superclass Task and its methods and attributes.
        # This will set up the project, pool and training as specified in the configuration file.
        super().__init__(configuration, client, task_spec)

    def __call__(self, input_obj):

        # If the class is called, use the __call__() method from the superclass
        super().__call__(input_obj, verify=True)

        # When called, return the SegmentationVerification object
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

        # Add assignment ID to the input data
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)

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

        # Set task width limit
        task_width_plugin = tb.TolokaPluginV1(kind='scroll', task_width=500)

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([img_ui, prompt, radio_group]),
            plugins=[hotkey_plugin, task_width_plugin]
        )

        # Create a task specification with interface and input/output data
        task_spec = toloka.project.task_spec.TaskSpec(
            input_spec=data_in,
            output_spec=data_out,
            view_spec=interface
        )

        # Return the task specification
        return task_spec


class MulticlassVerification(CrowdsourcingTask):
    """
    This is a class for multiclass image segmentation verification tasks.
    """
    def __init__(self, configuration, client):
        """
        This function initialises the MulticlassVerification class, which inherits attributes
        and methods from the superclass Task.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            A MulticlassVerification object.
        """
        # Read the configuration from the YAML file
        configuration = OrderedDict(read_configuration(configuration=configuration))

        # Specify task and task interface
        task_spec = self.specify_task(configuration=configuration)

        # Use the super() function to access the superclass Task and its methods and attributes.
        # This will set up the project, pool and training as specified in the configuration file.
        super().__init__(configuration, client, task_spec)

    def __call__(self, input_obj):

        # If the class is called, use the __call__() method from the superclass
        super().__call__(input_obj, verify=True)

        # When called, return the MulticlassVerification object
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
        expected_i, expected_o = {'url', 'json'}, {'str'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)

        # Add assignment ID to the input data
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)

        # Create the task interface; start by setting up the image interface
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

        # Define the text prompt below the image UI
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        options = [tb.fields.GroupFieldOption(value=value, label=label) for (value, label) 
                   in configuration['options'].items()]

        # Set up a radio group for labels
        radio_group = tb.ButtonRadioGroupFieldV1(

            # Set up the output data field
            data=tb.OutputData(output_data['str']),

            # Create radio buttons
            options=options,

            # Set up validation
            validation=tb.RequiredConditionV1(hint="You must choose one response.")
        )

        # Set task width limit
        task_width_plugin = tb.TolokaPluginV1(kind='scroll', task_width=500)

        # Create hotkeys for each possible response
        hotkey_dict = {f'key_{i+1}': tb.SetActionV1(data=tb.OutputData(output_data['str']),
                                                    payload=list(configuration['options'].keys())[i]) 
                                                    for i in range(len(configuration['options']))}

        hotkey_plugin = tb.HotkeysPluginV1(**hotkey_dict)

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([img_ui, prompt, radio_group]),
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


class TextClassification(CrowdsourcingTask):
    """
    This is a class for text classification tasks.
    """

    def __init__(self, configuration, client):
        """
        This function initialises the TextClassification class, which inherits attributes
        and methods from the superclass CrowdsourcingTask.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            A TextClassification object.
        """
        # Read the configuration from the YAML file
        configuration = OrderedDict(read_configuration(configuration=configuration))

        # Specify task and task interface
        task_spec = self.specify_task(configuration=configuration)

        # Use the super() function to access the superclass Task and its methods and attributes.
        # This will set up the project, pool and training as specified in the configuration file.
        super().__init__(configuration, client, task_spec)

    def __call__(self, input_obj):

        # If the class is called, use the __call__() method from the superclass
        super().__call__(input_obj)

        # When called, return the TextClassification object
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
        expected_i, expected_o = {'str'}, {'str'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)

        # Add assignment ID to the input data
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)

        # Create the task interface; start by setting up the text classification interface
        text_ui = tb.TextViewV1(content=tb.InputData(path=input_data['str']))

        # Define the text prompt below the classification UI
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        options = [tb.fields.GroupFieldOption(value=value, label=label) for (value, label) 
                   in configuration['options'].items()]

        # Set up a radio group for labels
        radio_group = tb.ButtonRadioGroupFieldV1(

            # Set up the output data field
            data=tb.OutputData(output_data['str']),

            # Create radio buttons
            options=options,

            # Set up validation
            validation=tb.RequiredConditionV1(hint="You must choose one response.")
        )

        # Set task width limit
        task_width_plugin = tb.TolokaPluginV1(kind='scroll', task_width=500)

        # Create hotkeys for all possible responses
        hotkey_dict = {f'key_{i+1}': tb.SetActionV1(data=tb.OutputData(output_data['str']),
                                                    payload=list(configuration['options'].keys())[i]) 
                                                    for i in range(len(configuration['options']))}

        hotkey_plugin = tb.HotkeysPluginV1(**hotkey_dict)

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([prompt, text_ui, radio_group]),
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


class TextAnnotation(CrowdsourcingTask):
    """
    This is a class for text annotation tasks.
    """

    def __init__(self, configuration, client):
        """
        This function initialises the TextAnnotation class, which inherits attributes
        and methods from the superclass CrowdsourcingTask.

        Parameters:
            configuration: A string object that defines a path to a YAML file with configuration.
            client: A TolokaClient object with valid credentials.

        Returns:
            A TextAnnotation object.
        """
        # Read the configuration from the YAML file
        configuration = OrderedDict(read_configuration(configuration=configuration))

        # Specify task and task interface
        task_spec = self.specify_task(configuration=configuration)

        # Use the super() function to access the superclass Task and its methods and attributes.
        # This will set up the project, pool and training as specified in the configuration file.
        super().__init__(configuration, client, task_spec)

    def __call__(self, input_obj):

        # If the class is called, use the __call__() method from the superclass
        super().__call__(input_obj)

        # When called, return the TextAnnotation object
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
        expected_i, expected_o = {'str'}, {'json'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)

        # Add assignment ID to the input data
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)

        # Define the text prompt above the annotation UI
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Set up annotation options
        options = [tb.fields.GroupFieldOption(value=value, label=label) for (value, label) 
                   in configuration['options'].items()]

        # Set up annotation UI
        annotation_field = tb.TextAnnotationFieldV1(

            # Set up the output data field
            data=tb.OutputData(output_data['json']),

            content=tb.InputData(input_data['str']),

            labels=options,

            # Set up validation
            validation=tb.RequiredConditionV1(hint="You must choose one response.")
        )

        # Set task width limit
        task_width_plugin = tb.TolokaPluginV1(kind='scroll', task_width=500)

        # Create hotkeys for all possible responses
        hotkey_dict = {f'key_{i+1}': tb.SetActionV1(data=tb.OutputData(output_data['json']),
                                                    payload=list(configuration['options'].keys())[i]) 
                                                    for i in range(len(configuration['options']))}

        hotkey_plugin = tb.HotkeysPluginV1(**hotkey_dict)

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([prompt, annotation_field]),
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
