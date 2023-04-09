# Examples and tutorials

## Creating a YAML configuration for classifying images

In this example, we create a configuration file to be used with the `ImageClassification` class defined in 𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊.

The following example breaks down how 𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊 uses YAML configuration files to create crowdsourcing tasks on Toloka. The complete configuration file referred to in this example may be found [here](config/classify_image.yaml).

First we define a unique name for the crowdsourcing task under the key `name`. In this case, we call this task *classify_images*.

Next, we must provide information about the data and its structure under the key `data`. For this purpose, we define three additional keys: `file`, `input` and `output`. 

The value under the key `file` must point towards a TSV file containing the data to be loaded on the Toloka platform. The keys `input` and `output` contain key/value pairs that define the names of the input and output variables and their type. 

To exemplify, the input data consists of a URL, which can be found under the key `image`, as shown in the [TSV file](data/verify_image_data.tsv). The output data, in turn, consists of Boolean values stored under the variable *result*.

```yaml
name: classify_images
data:
  file: data/verify_image_data.tsv
  input:
    image: url                    
  output:
    result: bool
```

Next, we proceed to set up the user interface under the key `interface`. The key `prompt` defines the text that is positioned above the buttons for various labels. 

These labels are defined under the key `labels`. Each key under `labels` defines the value that will be stored when the user selects the label, whereas the label defines what shown in the user interface. Here we set up two labels in the user interface, *Yes* and *No*, which store the values *true* and *false*, respectively.

```yaml
interface:
  prompt: "Does the image contain text, letters or numbers?"
  labels:
    true: "Yes"
    false: "No" 
```

After configuring the user interface, we proceed to set up a project on Toloka. In Toloka, user interfaces are associated with projects, which may contain multiple different pools with different tasks.

To create a project, we provide the following information under the key `project`. The key `setup` contains two key/value pairs, `public_name` and `public_description`, which define basic information shown to workers on the platform. The key `instructions`, in turn, points towards an HTML file that contains instructions for completing the task. 

```yaml
project:
  setup:
    public_name: "Check if an image contains text, letters or numbers"
    public_description: "Look at diagrams from science textbooks and state if they
      contain text, letters or numbers."
  instructions: instructions/detect_text_instructions.html
```

Next, we configure a pool within the project to which the tasks will be uploaded. This configuration is provided under the key `pool`.

To begin with, we use the `estimated_time_per_suite` to estimate the time spent for completing each task suite (a group of one or more tasks) in seconds. This will allow 𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊 to estimate whether the payment for the task is fair.

Next, under the key `setup`, we provide a `private_name` for the pool, together with essential information. The key/value pairs `reward_per_assignment`, `assignment_max_duration_seconds` and `auto_accept_solutions` define the amount of money paid for each task suite, the maximum amount of time allowed for completing a task suite in seconds and whether the task suites submitted by workers should be accepted automatically.

```yaml
pool:
  estimated_time_per_suite: 10
  setup:
    private_name: "Classify images"
    reward_per_assignment: 0.034
    assignment_max_duration_seconds: 600
    auto_accept_solutions: true
  defaults:
    default_overlap_for_new_tasks: 1
    default_overlap_for_new_task_suites: 1
  mixer:
    real_tasks_count: 1
    golden_tasks_count: 0
    training_tasks_count: 0
  filter:
    client_type:
      - TOLOKA_APP
      - BROWSER
```
