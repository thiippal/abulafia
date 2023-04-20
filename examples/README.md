# Examples and tutorials

- [Creating a task for classifying images](#creating-a-task-for-classifying-images)
- [Defining input and output data](#defining-input-and-output-data)
- [Setting up projects](#setting-up-projects)
- [Configuring pools](#configuring-pools)
- Limiting access to tasks using filters

## Creating a task for classifying images

In this example, we create a YAML configuration file for the `ImageClassification` class.

This example breaks down how 𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊 uses YAML files to create and configure crowdsourcing tasks on Toloka. The complete configuration file referred to in this example may be found [here](config/classify_image.yaml).

First we define a unique name for the crowdsourcing task under the key `name`. In this case, we call the task *classify_images*.

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

This finishes the configuration. We can now use this configuration to create an `ImageClassification` object, as illustrated in [here](classify_images.py).

As shown on [line 35](classify_images.py#L35), we must provide a path to the configuration file using the parameter `configuration`.

```python
classify_image = ImageClassification(configuration="config/classify_image.yaml",
                                     client=tclient)
```

This object may be then added to a crowdsourcing pipeline, as shown on [line 39](classify_images.py#L39).

```python
pipe = TaskSequence(sequence=[classify_image], client=tclient)
```

## Defining input and output data

### Specifying data types

Each crowdsourcing task requires a data specification, which determines the types of input and output data associated with the task.

In the YAML configuration, the inputs and outputs are defined under the top-level key `data` using the keys `input` and `output`.

To define input and output data, provide key/value pairs that define the name of the data and its type, e.g. `outlines` and `json`.

```yaml
data:
  input:
    outlines: json
  output:
    correct: bool
```

### Loading data from a file

You can place the key `file` under `data` to provide input data to the task. The value of this key should point towards a TSV file that contains the input data. The TSV file must contain columns with headers that match those defined under the key `input`.

```yaml
data:
  file: images.tsv
  input:
    image: url
  output:
    result: bool
```

### Setting up human verification 

If the task is used for verifying work submitted by other crowdsourced workers, you must add the key `verify` under `data` and set its value to `true`. This adds the output data from the incoming tasks to the input of the current task, while also making the verification task unavailable to the worker who completed the original task.

```yaml
data:
  verify: true
  input:
    outlines: json
  output:
    result: bool
```

## Setting up projects

Projects are the most abstract entity on Toloka. A project may include multiple pools, which contain assignments for the workers. 

In the YAML configuration file, project settings are configured using the top-level key `projects`.

### Creating projects

To create a new project, use the key `setup` to define a public name and a description for the project, which are displayed on the Toloka platform for prospective workers. 

Use the keys `public_name` and `public_description` to provide the name and description as strings.

The key `instructions` should point to an HTML file that provides instructions for completing the task.

```yaml
project:
  setup:
    public_name: "Project name"
    public_description: "A brief description of the project."
  instructions: my_instructions.html
```

### Loading projects from Toloka

To load an existing project from Toloka, add the key `id` under the top-level key `project`. Then provide the project ID as the value.

```yaml
project:
  id: 12345
```

## Configuring pools

A pool contains **assignments** for the workers to complete. Multiple assignments may be grouped into a **task suite**. 

Pool settings are configured under the top-level key `pool` in the YAML configuration file.

### Creating pools

To begin with, the key `estimated_time_per_suite`, which must be placed under the key `pool`, is used to calculate a fair reward for the workers (an average hourly wage of $USD 12). 

Provide the estimated time required to complete a task suite in seconds.

The following example sets the value to 60 seconds.

```yaml
pool:
  estimated_time_per_suite: 60
```

The key properties of a pool are defined under the key `setup`. The following key/value paris can be defined under the key `pool`.

| Key                               | Value   | Description                                                    |
|:----------------------------------|:--------|:---------------------------------------------------------------|
| `private_name`                    | string  | A private name for the pool; not shown on the platform         |
| `reward_per_assignment`           | float   | The reward paid for completing a single task suite in USD      |
| `assignment_max_duration_seconds` | integer | The maximum time allowed for competing a task suite in seconds |
| `auto_accept_solutions`           | boolean | Whether submitted work is accepted and paid for immediately    |

If the value of `auto_accept_solutions` is set to `false`, the task suites must be accepted or rejected manually. This may be achieved using the Toloka web interface or by directing the tasks to another pool for [verification by other workers](#setting-up-human-verification).

The following example illustrates the use of the variables discussed above.

```yaml
pool:
  setup:
    private_name: "Dataset 1"
    reward_per_assignment: 0.15
    assignment_max_duration_seconds: 600
    auto_accept_solutions: false
```

The next key under the key `pool` is `defaults`, which is used to define default settings for assignments and task suites. The following key/value paris can be defined under the key `mixer`.

| Key                      | Value   | Description |
|:-------------------------|:--------|:------------|
| `default_overlap_for_new_tasks` | integer | How many workers should complete each assignment |
| `default_overlap_for_new_suites` | integer | How many workers should complete each task suite |

The following example sets both values to 3.

```yaml
pool:
  defaults:
    default_overlap_for_new_tasks: 3
    default_overlap_for_new_task_suites: 3
```

Next, use the key `mixer` to define the mix of different assignment types in each task suite. The following key/value pairs can be provided under the key `mixer`.

| Key                      | Value   | Description |
|:-------------------------|:--------|:------------|
| `real_tasks_count`       | integer | The number of actual assignments in each task suite |
| `golden_tasks_count`     | integer | The number of assignments with known answers in each task suite |
| `training_tasks_count`   | integer | The number of training assignments in each task suite |

The actual assignments are drawn from the [input data](#specifying-data-types), whereas the golden assignments can be used to evaluate the quality of work submitted to the pool.

The following example sets the number of real assignments to 5 and the number of golden assignments to 1, while leaving the number of training assignments to 0. This means that each task suite in the pool contains 6 assignments.

```yaml
pool:
  mixer:
    real_tasks_count: 5
    golden_tasks_count: 1
    training_tasks_count: 0
```

Finally, the key `filter` is used to limit access to the pool for workers with certain characteristics.



### Loading pools

To load an existing pool from Toloka, add the key `id` under the top-level key `pool`. Then provide the pool ID as the value.

```yaml
pool:
  id: 6789
```
