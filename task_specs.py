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
