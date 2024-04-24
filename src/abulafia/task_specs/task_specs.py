# -*- coding: utf-8 -*-

# Import libraries
from ..functions.core_functions import *
from wasabi import Printer
from .core_task import CrowdsourcingTask
from urllib3.util import Retry
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
        # Define expected input and output types for the task. For image classification, the expected
        # inputs include an image URL, whereas the output consists of Boolean values (true or false)
        # or strings (e.g. for different labels).
        expected_i, expected_o = {'url'}, {'bool', 'str'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)

        # Add a data specification for incoming assignment IDs, which are needed for accepting and
        # rejecting verified tasks.
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)

        # Create the task interface; start by setting up the image viewer with the input URL
        img_viewer = tb.ImageViewV1(url=tb.InputData(input_data['url']),
                                    rotatable=True,
                                    full_height=True)

        # Define the prompt text above the radio button group
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Check the labels defined for the radio button group
        try:
            labels = [tb.fields.GroupFieldOption(value=value, label=label) for
                      value, label in configuration["interface"]["labels"].items()]

        except KeyError:

            msg.fail(f"Please add the key 'labels' under the top-level key 'interface' to define "
                     f"the labels for the interface. The labels should be provided as key/value "
                     f"pairs, e.g. cat: Cat. The key is stored into the output data ('cat'), "
                     f"whereas the value defines that label shown on the interface ('Cat').",
                     exits=1)

        # Set up a radio button group
        radio_group = tb.ButtonRadioGroupFieldV1(

            # Set up the output data field; this can be either a string or a Boolean value
            data=tb.OutputData(output_data['bool'] if 'bool' in output_data else output_data['str']),

            # Create radio buttons
            options=labels,

            # Set up validation
            validation=tb.RequiredConditionV1(hint="You must choose one response.")
        )

        # Set task width limit
        task_width_plugin = tb.TolokaPluginV1(kind='scroll', task_width=500)

        # Check if numbered hotkeys should be configured. Hotkeys are only defined if there are less than
        # nine labels.
        if len(configuration["interface"]["labels"]) <= 9:

            # Create hotkeys for all possible responses
            hotkey_dict = {f'key_{i+1}': tb.SetActionV1(
                data=tb.OutputData(output_data['bool'] if 'bool' in output_data else output_data['str']),
                payload=list(configuration["interface"]["labels"].keys())[i])
                for i in range(len(configuration["interface"]["labels"]))}

            hotkey_plugin = tb.HotkeysPluginV1(**hotkey_dict)

        else:

            hotkey_plugin = None

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([img_viewer, prompt, radio_group]),
            plugins=[task_width_plugin, hotkey_plugin if hotkey_plugin is not None else hotkey_plugin]
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
        expected_i, expected_o = {'json', 'url', 'bool'}, {'json', 'bool'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)

        # Add a data specification for incoming assignment IDs, which are needed for accepting and
        # rejecting verified tasks.
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)

        # If labels for bounding boxes should be added to the interface, create a list of labels
        # to be added. The 'label' will be added to the UI, whereas 'value' contains the value
        # added to the JSON output.
        labels = [tb.ImageAnnotationFieldV1.Label(value=value, label=label) for
                  value, label in configuration['interface']['labels'].items()] \
            if 'labels' in configuration['interface'] else None

        # Check if particular tools have been defined for the interface
        if 'tools' in configuration['interface']:

            # Check that the tools have been provided as a list
            assert type(configuration['interface']['tools']) == list, "Please provide the list of " \
                                                                      "annotation tools as a YAML " \
                                                                      "list."

            # Check that the tools provided are valid components of the interface
            assert set(configuration['interface']['tools']).issubset(
                {'rectangle', 'polygon', 'point'}), "Found invalid values for annotation tools. " \
                                                    "Valid tools include 'rectangle', 'polygon' " \
                                                    "and 'point'."

            # Create tools (shapes)
            shapes = {s: True for s in configuration['interface']['tools']}

        else:

            shapes = {'rectangle': True, 'polygon': True, 'point': True}

        # Check if the input data contains existing bounding boxes in JSON
        if 'json' in input_data:

            # Set up the output data for image segmentation, but add the
            # incoming segmentation data as default values.
            data = tb.OutputData(path=output_data['json'],
                                 default=tb.InputData(input_data['json']))

        else:

            # Set up the output path without incoming bounding boxes
            data = tb.OutputData(path=output_data['json'])

        # Initialise a list of conditions for validating the output data
        conditions = [tb.RequiredConditionV1(data=tb.OutputData(path=output_data['json']))]

        # Check if a checkbox should be added to the interface
        if 'checkbox' in configuration['interface']:

            # Check that a boolean value is included in the output data
            assert 'bool' in output_data, "Please add an output with a Boolean value " \
                                          "under the top-level key 'data' to use the " \
                                          "checkbox."

            # Create the checkbox object; set the default value to false (unchecked) and add label
            checkbox = tb.CheckboxFieldV1(data=tb.OutputData(output_data['bool'], default=False),
                                          label=configuration['interface']['checkbox'])

            # If a checkbox is present, disable the requirements for output
            data_out[output_data['json']].required = False
            data_out[output_data['bool']].required = False

        # Create the task interface; start by setting up the image segmentation interface
        img_ui = tb.ImageAnnotationFieldV1(

            # Set up the output data field
            data=data,

            # Set up the input data field
            image=tb.InputData(input_data['url']),

            # Set up the allowed shapes: note that their order will define the order in the UI
            shapes=shapes,

            # Set this element to use all available vertical space on the page. This should ensure
            # that all UI elements are visible.
            full_height=True,

            # Set up labels
            labels=labels
        )

        # Define the text prompt below the segmentation UI
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Add hotkey plugin
        hotkey_plugin = tb.ImageAnnotationHotkeysPluginV1(cancel='s',
                                                          confirm='a',
                                                          polygon='e',
                                                          rectangle='w',
                                                          point='r',
                                                          select='q',)

        # Create a list of interface elements
        view = [img_ui, prompt]

        # Check for optional checkbox element
        if 'checkbox' in configuration['interface']:

            # Add the checkbox element to the interface
            view.append(checkbox)

            # Add validation criteria for the checkbox
            conditions.append(tb.EqualsConditionV1(data=tb.OutputData(path=output_data['bool']),
                                                   to=True))

        # Combine the validation criteria (at least one criterion must hold)
        validation = tb.AnyConditionV1(conditions=conditions, hint="Please draw at least one "
                                                                   "shape or check the box.")

        # Combine the components into a single user interface; add validation criteria
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1(items=view,
                               validation=validation),
            plugins=[hotkey_plugin]
        )

        # Create a task specification with the interface and input/output data
        task_spec = toloka.project.task_spec.TaskSpec(
            input_spec=data_in,
            output_spec=data_out,
            view_spec=interface
        )

        # Return the task specification
        return task_spec


class SegmentationClassification(CrowdsourcingTask):
    """
    This is a class for classifying bounding boxes and other forms of image segmentation.
    """
    def __init__(self, configuration, client, **kwargs):
        """
        This function initialises the SegmentationClassification class, which inherits attributes
        and methods from the superclass CrowdsourcingTask.

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
        expected_i, expected_o = {'url', 'json', 'bool', 'str'}, {'bool', 'str'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)

        # Add a data specification for incoming assignment IDs, which are needed for accepting and
        # rejecting verified tasks.
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)

        # Check if labels associated with the image annotation element have been defined
        if 'segmentation' in configuration['interface']:

            if 'labels' in configuration['interface']['segmentation']:

                # Create labels for the image annotation interface
                seg_labels = [tb.ImageAnnotationFieldV1.Label(value=v, label=l) for
                              v, l in configuration['interface']['segmentation']['labels'].items()]

        else:

            seg_labels = None

        # Check if a checkbox should be added to the interface
        if 'checkbox' in configuration['interface']:

            # Create a checkbox
            try:

                # Define data and default value
                path = input_data['bool'] if 'bool' in input_data else input_data['str']
                default = tb.InputData(path)

                # Create checkbox
                checkbox = tb.CheckboxFieldV1(
                    data=tb.InternalData(path=path, default=default),
                    label=configuration['interface']['checkbox'],
                    disabled=True)

            except KeyError:

                msg.fail(f"Please add the key 'checkbox' under the top-level key 'interface' to "
                         f"define a text that is displayed above the checkbox. Define the text as a "
                         f"string e.g. checkbox: There is nothing to outline.", exits=1)

        # Create the task interface; start by setting up the image segmentation interface
        img_ui = tb.ImageAnnotationFieldV1(

            # Set up the data to be displayed
            data=tb.InternalData(path=input_data['json'],
                                 default=tb.InputData(input_data['json'])),

            # Set up the input data field
            image=tb.InputData(path=input_data['url']),

            # Set labels
            labels=seg_labels,

            # Set this element to use all available vertical space on the page. This should ensure
            # that all UI elements are visible.
            full_height=True,

            # Disable the annotation interface
            disabled=True)

        # Define the text prompt above the radio button group
        radio_prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Check the labels defined for the radio button group
        try:
            radio_labels = [tb.fields.GroupFieldOption(value=value, label=label) for
                            value, label in configuration['interface']['labels'].items()]

        except KeyError:

            msg.fail(f"Please add the key 'labels' under the top-level key 'interface' to define "
                     f"the labels for the interface. The labels should be provided as key/value "
                     f"pairs, e.g. cat: Cat. The key is stored into the output data ('cat'), "
                     f"whereas the value defines that label shown on the interface ('Cat').",
                     exits=1)

        # Set up a radio group for labels
        radio_group = tb.ButtonRadioGroupFieldV1(

            # Set up the output data field; this can be either a string or a Boolean value
            data=tb.OutputData(output_data['bool'] if 'bool' in output_data else output_data['str']),

            # Create radio buttons
            options=radio_labels,

            # Set up validation
            validation=tb.RequiredConditionV1(hint="You must choose one response.")
        )

        # Check if numbered hotkeys should be configured. Hotkeys are only defined if there are less
        # than nine labels.
        if len(configuration["interface"]["labels"]) <= 9:

            # Create hotkeys for all possible responses
            hotkey_dict = {f'key_{i+1}': tb.SetActionV1(
                data=tb.OutputData(output_data['bool'] if 'bool' in output_data else output_data['str']),
                payload=list(configuration['interface']['labels'].keys())[i])
                for i in range(len(configuration['interface']['labels']))}

            hotkey_plugin = tb.HotkeysPluginV1(**hotkey_dict)

        else:

            hotkey_plugin = None

        # Create a list of interface elements
        view = [img_ui, radio_prompt, radio_group]

        # Check for possible checkbox element
        if 'checkbox' in configuration['interface']:

            view = [img_ui, checkbox, radio_prompt, radio_group]

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1(view),
            plugins=[hotkey_plugin if hotkey_plugin is not None else hotkey_plugin]
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

    def __init__(self, configuration, creds, **kwargs):
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

        # Initialize client
        client = toloka.TolokaClient(creds['token'], creds['mode'],
                                     retryer_factory=lambda: Retry(total=10,
                                                                   status_forcelist=toloka.STATUSES_TO_RETRY,
                                                                   allowed_methods=['HEAD', 'GET', 'PUT', 'DELETE',
                                                                                    'OPTIONS', 'TRACE', 'POST', 'PATCH'],
                                                                   backoff_factor=0.5)
                                     )

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
        expected_i, expected_o = {'str'}, {'str', 'bool'}

        # Configure Toloka data specifications and check the expected input against configuration
        data_in, data_out, input_data, output_data = check_io(configuration=configuration,
                                                              expected_input=expected_i,
                                                              expected_output=expected_o)

        # Add a data specification for incoming assignment IDs, which are needed for accepting and
        # rejecting verified tasks.
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)

        # Create the task interface; start by setting up the text classification interface
        text_ui = tb.TextViewV1(content=tb.InputData(path=input_data['str']))

        # Define the text prompt below the classification UI
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Check the labels defined for the radio button group
        try:
            labels = [tb.fields.GroupFieldOption(value=value, label=label) for
                       (value, label) in configuration['interface']['labels'].items()]

        except KeyError:

            # TODO Move these warnings into a separate file, since they're frequently reused
            msg.fail(f"Please add the key 'labels' under the top-level key 'interface' to define "
                     f"the labels for the interface. The labels should be provided as key/value "
                     f"pairs, e.g. cat: Cat. The key is stored into the output data ('cat'), "
                     f"whereas the value defines that label shown on the interface ('Cat').",
                     exits=1)

        # Set up a radio group for labels
        radio_group = tb.ButtonRadioGroupFieldV1(

            # Set up the output data field
            data=tb.OutputData(output_data['bool'] if 'bool' in output_data else output_data['str']),

            # Create radio buttons
            options=labels,

            # Set up validation
            validation=tb.RequiredConditionV1(hint="You must choose one response.")
        )

        # Set task width limit
        task_width_plugin = tb.TolokaPluginV1(kind='scroll', task_width=500)

        # Check if numbered hotkeys should be configured. Hotkeys are only defined if there are less than
        # nine labels.
        if len(configuration["interface"]["labels"]) <= 9:

            # Create hotkeys for all possible responses
            hotkey_dict = {f'key_{i+1}': tb.SetActionV1(
                data=tb.OutputData(output_data['bool'] if 'bool' in output_data else output_data['str']),
                payload=list(configuration["interface"]["labels"].keys())[i])
                for i in range(len(configuration["interface"]["labels"]))}

            hotkey_plugin = tb.HotkeysPluginV1(**hotkey_dict)

        else:

            hotkey_plugin = None

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([prompt, text_ui, radio_group]),
            plugins=[task_width_plugin, hotkey_plugin if hotkey_plugin is not None else hotkey_plugin]
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

    def __init__(self, configuration, client, **kwargs):
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

        # Add a data specification for incoming assignment IDs, which are needed for accepting and
        # rejecting verified tasks.
        data_in['assignment_id'] = toloka.project.StringSpec(required=False)

        # Define the text prompt above the annotation UI
        prompt = tb.TextViewV1(content=configuration['interface']['prompt'])

        # Check the labels defined for the radio button group
        try:
            labels = [tb.fields.GroupFieldOption(value=value, label=label) for
                      (value, label) in configuration['interface']['labels'].items()]

        except KeyError:

            # TODO Move these warnings into a separate file, since they're frequently reused
            msg.fail(f"Please add the key 'labels' under the top-level key 'interface' to define "
                     f"the labels for the interface. The labels should be provided as key/value "
                     f"pairs, e.g. cat: Cat. The key is stored into the output data ('cat'), "
                     f"whereas the value defines that label shown on the interface ('Cat').",
                     exits=1)

        # Set up annotation UI
        annotation_field = tb.TextAnnotationFieldV1(

            # Set up the output data field
            data=tb.OutputData(output_data['json']),
            content=tb.InputData(input_data['str']),
            labels=labels,

            # Set up validation
            validation=tb.RequiredConditionV1(hint="You must choose one response.")
        )

        # Set task width limit
        task_width_plugin = tb.TolokaPluginV1(kind='scroll', task_width=500)

        # Check if numbered hotkeys should be configured. Hotkeys are only defined if there are less than
        # nine labels.
        if len(configuration["interface"]["labels"]) <= 9:

            # Create hotkeys for all possible responses
            hotkey_dict = {f'key_{i + 1}': tb.SetActionV1(
                data=tb.OutputData(output_data['json']),
                payload=list(configuration['interface']['labels'].keys())[i])
                for i in range(len(configuration['interface']['labels']))}

            hotkey_plugin = tb.HotkeysPluginV1(**hotkey_dict)

        else:

            hotkey_plugin = None

        # Combine the task interface elements into a view
        interface = toloka.project.TemplateBuilderViewSpec(
            view=tb.ListViewV1([prompt, annotation_field]),
            plugins=[task_width_plugin, hotkey_plugin if hotkey_plugin is not None else hotkey_plugin]
        )

        # Create a task specification with interface and input/output data
        task_spec = toloka.project.task_spec.TaskSpec(
            input_spec=data_in,
            output_spec=data_out,
            view_spec=interface
        )

        # Return the task specification
        return task_spec
