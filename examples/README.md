# Examples and tutorials

- [Creating Task objects](#creating-task-objects)
  - [ImageClassification](#imageclassification)
  - [ImageSegmentation](#imagesegmentation)
  - [SegmentationVerification](#segmentationverification)
  - [TextClassification](#textclassification)
  - [TextAnnotation](#textannotation)
- [Configuring Tasks](#configuring-tasks)
  - [Naming a Task](#naming-a-task)  
  - [Defining input and output data](#defining-input-and-output-data)
  - [Setting up projects](#setting-up-projects)
  - [Creating pools](#creating-pools)
  - [Configuring training](#configuring-training)
  - [Configuring quality control](#configuring-quality-control)
- [Combining Tasks into Task Sequences](#combining-tasks-into-task-sequences)
- [Processing Task outputs using Actions](#processing-task-outputs-using-actions)
  - [Forward](#forward)
  - [Aggregate](#aggregate)
  - [VerifyPolygon](#verifypolygon)
  - [SeparateBBoxes](#separatebboxes)
- [Tutorials](#tutorials)
  - [Creating a Task for classifying images](#creating-a-task-for-classifying-images)

## Creating Task objects

In 𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊, user interfaces are associated with Python classes that define the allowed input and output data types.

To create a Task object, create a YAML configuration file for a Task and pass this configuration to the appropriate class.

The following example creates a Task object using the `TextClassification` class, whose configuration is contained in a YAML configuration file named `classify_text`. A Toloka client stored under the variable `client` is used to interact with the Toloka platform.

```python
task = TextClassification(configuration='classify_text.yaml', client=client)
```

Use the top-level key `interface` in the YAML file to configure the user interface for a given Task as exemplified in connection with each pre-defined interface below.

You can create additional interfaces by inheriting the [`CrowdsourcingTask`](src/abulafia/task_specs/core_task.py) class, which defines the basic functionalities of a Task.

The currently implemented interfaces can be found in [`task_specs.py`](src/abulafia/task_specs/task_specs.py). These interfaces are documented below.

### ImageClassification

A class for image classification tasks. The following input and output formats are supported.

| Input         | Output                         |
|---------------|--------------------------------|
| `url` (image) | `boolean` (true/false)         |
|               | `string` (for multiple labels) |

Configure the interface by adding the following keys under the top-level key `interface`.

| Key      | Description                                                                                      |
|----------|--------------------------------------------------------------------------------------------------|
| `prompt` | A string that defines a text that is shown above the buttons on the interface.                   |
| `labels` | Key/value pairs that define the labels shown on the interface and the values stored in the data. |

The following example adds a prompt with two labels. The interface will show two options, *Yes* and *No*, which store the values `true` and `false`, respectively.

```yaml
interface:
  prompt: "Does the image contain text, letters or numbers?"
  labels:
    true: "Yes"
    false: "No" 
```

### ImageSegmentation

A class for image segmentation tasks. The following input and output formats are supported. 

| input                   | output                        |
|-------------------------|-------------------------------|
| `url` (image)           | `json` (bounding boxes)       |
| `json` (bounding boxes) | `boolean` (optional checkbox) |

Configure the interface by adding the following keys under the top-level key `interface`.

| Key                   | Description                                                                                      |
|-----------------------|--------------------------------------------------------------------------------------------------|
| `prompt`              | A string that defines a text that is shown below the image annotation interface.                 |
| `tools`               | A list of values that defines the annotation tools available for the interface.                  |
| `labels` (optional)   | Key/value pairs that define the labels shown on the interface and the values stored in the data. |
| `checkbox` (optional) | A string that defines a text that is shown above the checkbox in the interface.                  |

The following example defines a prompt, an image segmentation interface with three labels, two annotation tools and a checkbox.

```yaml
interface:
  prompt: "Outline all elements with text, letters or numbers."
  tools:
    - rectangle
    - polygon
  labels:
    text: "Text"
    letter: "Letter"
    number: "Number"
  checkbox: "Check this box if there is nothing to outline."
```

For the annotation tools, valid values include `rectangle`, `polygon` and `point`. Their order defines the order in which they appear in the user interface. If no tools are defined, all tools are made available by default.

If a `checkbox` is added to the user inteface, you must add an input data variable with the type `boolean` to the output. The checkbox can be used to mark images that do not contain any objects to be segmented. If selected, the checkbox stores the value `true`, and `false` if the checkpoint is not selected.

If you want to show pre-existing annotations, you must add an input data variable with the type `json`.

### SegmentationVerification

A class for verifying bounding boxes and other forms of image segmentation. The following input and output formats are supported.

| Input                   | Output                         |
|-------------------------|--------------------------------|
| `url` (image)           | `boolean` (true/false)         |
| `json` (bounding boxes) | `string` (for multiple labels) |
| `boolean` (checkbox)    |                                |
| `string` (checkbox)     |                                |

Configure the interface by adding the following keys under the top-level key `interface`.

| Key                              | Description                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------------|
| `prompt`                         | A string that defines a text that is shown above the radio buttons on the interface.            |
| `labels`                         | Key/value pairs that define the labels for the radio buttons and the values stored in the data. |
| `segmentation/labels` (optional) | Key/value pairs that define the labels for bounding boxes and the values stored in the data.    |
| `checkbox` (optional)            | A string that defines a text that is shown above the checkbox in the interface.                 |

The following example defines a prompt, an image segmentation interface with two labels for bounding boxes and two labels for the radio buttons.

```yaml
interface:
  prompt: "Is the image annotated correctly?"
  checkbox: "There is nothing to annotate in this image."
  segmentation:
    labels:
      source: "Source"
      target: "Target"
  labels:
    true: "Yes"
    false: "No"
```

### TextClassification

A class for text classification tasks. The following input and output formats are supported. 

| Input    | Output                         |
|----------|--------------------------------|
| `string` | `boolean` (true/false)         |
|          | `string` (for multiple labels) |

Configure the interface by adding the following keys under the top-level key `interface`.

| Key      | Description                                                                                      |
|----------|--------------------------------------------------------------------------------------------------|
| `prompt` | A string that defines a text that is shown above the buttons on the interface.                   |
| `labels` | Key/value pairs that define the labels shown on the interface and the values stored in the data. |

The following example defines an interface with a prompt and three labels. The interface will show three options, *Positive*, *Negative* and *Neutral*, which store the values `positive`, `negative` and `neutral`, respectively.

```yaml
interface:
  prompt: Read the text and classify its sentiment.
  labels:
    positive: Positive
    negative: Negative
    neutral: Neutral
```

### TextAnnotation

A class for text annotation tasks. The following input and output formats are supported.

| input    | output |
|----------|--------|
| `string` | `json` |

Configure the interface by adding the following keys under the top-level key `interface`.

| Key      | Description                                                                                      |
|----------|--------------------------------------------------------------------------------------------------|
| `prompt` | A string that defines a text that is shown above the buttons on the interface.                   |
| `labels` | Key/value pairs that define the labels shown on the interface and the values stored in the data. |

The following example defines an interface with a prompt and three labels. The interface will show three options, *Verb*, *Noun* and *Adjective*, which store the values `verb`, `noun` and `adj`, respectively.

```yaml
interface:
  prompt: Annotate verbs, nouns and adjectives in the text below.
  labels:
    verb: Verb
    noun: Noun
    adj: Adjective
```

## Configuring Tasks

In 𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊, a Task refers to a crowdsourcing task that is defined using its own YAML configuration file.

The following sections describe how to configure a Task.

### Naming a Task

Use the top-level key `name` in the YAML configuration to name the Task. Task names are used to identify and set up connections between Tasks in a pipeline.

The following example gives the Task the name `my_task`.

```yaml
name: my_task
```

### Defining input and output data

#### Specifying data types

Each Task requires a data specification, which determines the types of input and output data associated with the Task.

In the YAML configuration, the inputs and outputs are defined under the top-level key `data` using the keys `input` and `output`.

To define input and output data, provide key/value pairs that define the name of the data and its type, e.g. `outlines` and `json`.

```yaml
data:
  input:
    outlines: json
  output:
    correct: bool
```

#### Loading data from a file

You can place the key `file` under `data` to provide input data to the Task. The value of this key should point towards a TSV file that contains the input data. The TSV file must contain columns with headers that match those defined under the key `input`.

```yaml
data:
  file: images.tsv
  input:
    image: url
  output:
    result: bool
```

#### Setting up human verification 

If a Task is used for verifying work submitted by other crowdsourced workers, you must add the key `verify` under `data` and set its value to `true`. This adds the output data from the incoming Tasks to the input of the current Task, while also making the verification assignment unavailable to the worker who completed the original assignment.

```yaml
data:
  verify: true
  input:
    outlines: json
  output:
    result: bool
```

### Setting up projects

Projects are the most abstract entity on Toloka. A project may include multiple pools, which contain assignments for the workers. User interfaces are also defined at the level of a project.

In the YAML configuration file, project settings are configured using the top-level key `projects`.

#### Loading an existing project from Toloka

To load an existing project from Toloka, add the key `id` under the top-level key `project`. Then provide the project ID as the value.

```yaml
project:
  id: 12345
```

#### Creating new projects

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

### Creating pools

A pool contains **assignments** for the workers to complete. Each assignment is contained in a **task suite**. 

Pool settings are configured under the top-level key `pool` in the YAML configuration file.

#### Loading existing pools

To load an existing pool from Toloka, add the key `id` under the top-level key `pool`. Then provide the pool ID as the value.

```yaml
pool:
  id: 6789
```

#### Creating new pools

To begin with, the key `estimated_time_per_suite`, which must be placed under the key `pool`, is used to calculate a fair reward for the workers (an average hourly wage of 12 USD). 

Provide the estimated time required to complete a task suite in seconds. To calculate a fair reward per task suite, you can use the interactive script [`utils/calculate_fair_rewards.py`](../utils/calculate_fair_rewards.py).

The following example sets the estimated time needed for completing a single task suite to 60 seconds.

```yaml
pool:
  estimated_time_per_suite: 60
```

The following sections describe how to set the main properties of pools.

##### `setup`

The basic properties of a pool are defined under the mandatory key `setup`. The following key/value pairs can be defined under the key `pool`.

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

#### `defaults`

The mandatory key `defaults` is used to define default settings for assignments and task suites. The following key/value paris can be defined under the key `mixer`.

| Key                              | Value   | Description                                      |
|:---------------------------------|:--------|:-------------------------------------------------|
| `default_overlap_for_new_tasks`  | integer | How many workers should complete each assignment |
| `default_overlap_for_new_suites` | integer | How many workers should complete each task suite |

The following example sets the value of both settings to 3.

```yaml
pool:
  defaults:
    default_overlap_for_new_tasks: 3
    default_overlap_for_new_task_suites: 3
```

#### `mixer`

The mandatory key `mixer` is used to define the mix of different assignment types in each task suite. The following key/value pairs can be provided under the key `mixer`.

| Key                      | Value   | Description                                                     |
|:-------------------------|:--------|:----------------------------------------------------------------|
| `real_tasks_count`       | integer | The number of actual assignments in each task suite             |
| `golden_tasks_count`     | integer | The number of assignments with known answers in each task suite |
| `training_tasks_count`   | integer | The number of training assignments in each task suite           |

The actual assignments are drawn from the [input data](#specifying-data-types), whereas the golden assignments can be used to evaluate the quality of work submitted to the pool.

The following example sets the number of real assignments to 5 and the number of golden assignments to 1, while leaving the number of training assignments to 0. This means that each task suite in the pool contains 6 assignments.

```yaml
pool:
  mixer:
    real_tasks_count: 5
    golden_tasks_count: 1
    training_tasks_count: 0
```

#### `filter`

The optional key `filter` is used to allow only workers with certain characteristics to access the pool. Note that filters are used to *limit* access: without any filters, all workers on Toloka can access the pool. 

The following key/value pairs can be provided under the key `filter`.

| Key               | Value                | Description                                                              |
|:------------------|:---------------------|:-------------------------------------------------------------------------|
| `skill`           | list of dictionaries | Limit workers to these skills and skill levels                           |
| `languages`       | list of strings      | Limit workers to these languages (two-letter ISO 639-1 code)             |
| `client_type`     | list of strings      | Limit workers to these clients (BROWSER or TOLOKA_APP)                   |      
| `education`       | list of strings      | Limit workers to these education levels (BASIC, MIDDLE, HIGH)            |
| `gender`          | string               | Limit workers to this gender (MALE or FEMALE)                            |
| `adult_allowed`   | boolean              | Limit workers to those who have agreed to work with adult content        | 
| `country`         | list of strings      | Limit workers to these countries (two-letter ISO3166-1 codes)            |
| `date_of_birth`   | dictionary           | Limit workers to those born before or after this date (unix timestamp)   | 
| `user_agent_type` | list of strings      | Limit workers to these user agent types (BROWSER, MOBILE_BROWSER, OTHER) |

The following example demonstrates the use of all currently implemented filters:

```yaml
pool:
  filter:
    skill:
      - 12345: 80
    languages:
      - EN
      - FI
    client_type:
      - BROWSER
      - TOLOKA_APP
    education:
      - HIGH
      - MIDDLE
    gender: FEMALE
    adult_allowed: false
    country:
      - GB
      - US
      - FI
    date_of_birth:
      before: 631144800
    user_agent_type:
      - BROWSER
      - MOBILE_BROWSER
      - OTHER
```

#### `blocklist`

Use the optional key `blocklist` to block certain users from accessing the pool and the associated training. Provide a path to a TSV file with user identiers to be blocked as the value for this key.

The blocklist column that contains the user identifiers must have the header `user_id`. See an example of a blocklist file [here](data/blocklist.tsv).

The following example illustrates the use of a blocklist file.

```yaml
pool:
  blocklist: data/blocklist.tsv
```

#### `exam`

The optional key `exam` can be used to configure an examination pool, which contains assignments with known solutions. These assignments can be used to evaluate the performance of workers and to grant them skills.

The following key/value pairs can be provided under the key `exam`.

| Key              | Value   | Description                                                                     |
|:-----------------|:--------|:--------------------------------------------------------------------------------|
| `history_size`   | integer | The number of assignments taken into account when evaluating examination score  |
| `min_answers`    | integer | The minimum number of assignments that the worker must complete to be evaluated |
| `max_performers` | integer | How many workers are allowed to take the exam before the pool closes            |

The following example sets the number of assignments to be evaluated to 20, defines that the worker must complete all 20 assignments to be evaluated, and closes the pool when 50 performers have taken the exam.

```yaml
pool:
  exam:
    history_size: 20
    min_answers: 20
    max_performers: 20
```

#### `skill`

The optional key `skill` is used to define the skill assigned to a worker upon completing the examination.

The following key/value pairs can be provided under the key `exam`.

| Key              | Value   | Description                                                      |
|:-----------------|:--------|:-----------------------------------------------------------------|
| `id`             | integer | A valid identifier for a pre-existing skill on Toloka            |
| `name`           | string  | The name for the new skill to be created                         |
| `language`       | string  | The language associated with the new skill as an ISO 639-1 code  |
| `description`    | string  | A description of the new skill in the language defined above     |

The following example shows how to grant an existing skill to workers who complete the examination:

```yaml
pool:
  skill: 
    id: 12345
```

The following example shows how to create a new skill that is granted to workers who complete the examination:

```yaml
pool:
  skill:
    name: "My new skill"
    language: EN
    description: "This is my new skill."
```

#### `training`

Use the optional key `training` to set the skill level that the workers must achieve in [training](#configuring-training).

Use the key `training_passing_skill_value` to determine the percentage of correct answers needed for accessing the actual task suites.

The following example sets the training performance threshold to 70% for accessing the pool.

```yaml
pool:
  training:
    training_passing_skill_value: 70
```

### Configuring training

To train the workers in performing a task, use the top-level key `training` to define a training pool that must be completed before accessing the pool that contains the actual assignments.

Use the key `setup` to configure the training pool. The following key/value pairs can be defined under the key `setup`.

| Key                                | Value   | Description                                                                 |
|:-----------------------------------|:--------|:----------------------------------------------------------------------------|
| private_name                       | string  | A private name for the training pool; not shown on the platform             |
| shuffle_tasks_in_training_suite    | boolean | Defines whether the assignments are shuffled in the training pool           |
| assignment_max_duration_seconds    | integer | The maximum time allowed for competing a task suite in seconds              |
| training_tasks_in_task_suite_count | integer | The number of assignments in each training pool                             |
| retry_training_after_days          | integer | Defines when the worker can try the training again after failing            |
| inherited_instructions             | boolean | Defines whether the training pool uses the same instructions as the project |

Use the key `data` to configure input and output variables and the source of data, as instructed [above](#defining-input-and-output-data). 

The following example illustrates the configuration of training tasks.

```yaml
training:
  setup:
    private_name: Training for an examination
    shuffle_tasks_in_task_suite: false
    assignment_max_duration_seconds: 600
    training_tasks_in_task_suite_count: 5
    retry_training_after_days: 1
    inherited_instructions: true
  data:
    file: training.tsv
    input:
      image: url
      outlines: json
      no_target: bool
    output:
      result: bool
```

### Configuring quality control

Use the optional top-level key `quality_control` to define settings for automatic quality control. The following keys can be used to configure the quality control mechanisms.

#### `speed_quality_balance`

Use the key `speed_quality_balance` to limit access to the Task according to worker reputation. The following key/value pairs must be defined under the key `speed_quality_balance`.

| Key                                | Value   | Description                                                                    |
|:-----------------------------------|:--------|:-------------------------------------------------------------------------------|
| `top_percentage_by_quality`        | integer | The percentage of workers with the highest reputation who can access the Task. |
| `best_concurrent_users_by_quality` | integer | The number of workers with the highest reputation who can access the Task.     |

The following example allows only the highest-ranked 10% of workers to access the Task. 

```yaml
quality_control:
  speed_quality_balance:
    top_percentage_by_quality: 10
```

The example below allows only the 20 workers with the highest reputation currently active on the platform to access the Task.

```yaml
quality_control:
  speed_quality_balance:
    best_concurrent_users_by_quality: 20
```

#### `fast_responses`

Use the key `fast_responses` to ban workers if they complete assignments too quickly, which may be indicative of spamming. The following key/value pairs must be defined under the key `fast_responses`.

| Key            | Value   | Description                                                                   |
|:---------------|:--------|:------------------------------------------------------------------------------|
| `history_size` | integer | The number of previous assignments considered when evaluating response times. | 
| `count`        | integer | The maximum number of fast responses allowed within the `history_period`.     |
| `threshold`    | integer | The threshold for defining a response as fast in seconds.                     |
| `ban_duration` | integer | How long the worker will be banned from accessing the Task.                   |
| `ban_units`    | string  | Temporal unit that defines ban duration: MINUTES, HOURS, DAYS or PERMANENT.   |

The following example bans users who complete 3 out of the 5 most recent assignments in less than 10 seconds for 2 days.

```yaml
quality_control:
  fast_responses:
    history_size: 5
    count: 3
    threshold: 10
    ban_duration: 2
    ban_units: DAYS
```

#### `skipped_assignments`

Use the key `skipped_assignments` to ban workers who skip too many assignments in a row. The following key/value pairs must be defined under the key `skipped_assignments`. 

| Key            | Value   | Description                                                                         |
|:---------------|:--------|:------------------------------------------------------------------------------------|
| `count`        | integer | The maximum number of assignments that the user may skip without getting banned.    |
| `ban_duration` | integer | How long the worker will be banned from accessing the Task.                         |
| `ban_units`    | string  | Temporal unit that defines ban duration: `MINUTES`, `HOURS`, `DAYS` or `PERMANENT`. |

The following example bans workers who skip more than 10 tasks in a row for 30 minutes.

```yaml
quality_control:
  skipped_assignments:
    count: 10
    ban_duration: 30
    ban_units: MINUTES
```

#### `redo_banned`

Use the key `redo_banned` to re-do all assignments completed by a banned user. The following key/value pair must be defined under the key `redo_banned`.

| Key           | Value   | Description                                                      |
|:--------------|:--------|:-----------------------------------------------------------------|
| `redo_banned` | boolean | Whether assignments from banned users should be completed again. |

This following example re-does assignments completed by banned users. 

```yaml
quality_control:
  redo_banned: true
```

#### `golden_set`

Use the key `golden_set` to evaluate worker performance using 'golden' assignments with known answers. The following key/value pair must be defined under the key `golden_set`.

| Key            | Value   | Description                                                                                     |
|:---------------|:--------|:------------------------------------------------------------------------------------------------|
| `history_size` | integer | The number of previous assignments with known answers that are evaluated when processing rules. |

The following example evaluates worker responses to the last 10 assignments with known answers when processing the rules defined shortly below.

```yaml
quality_control:
  golden_set:
    history_size: 10
```

Use the key `ban_rules` under `quality_control` to ban workers based on their performance against the assignments with known answers. 

| Key                   | Value   | Description                                                                         |
|:----------------------|:--------|:------------------------------------------------------------------------------------|
| `incorrect_threshold` | integer | Percentage of incorrect assignments that will result in the worker getting banned.  |
| `ban_duration`        | integer | How long the worker will be banned from accessing the Task.                         |
| `ban_units`           | string  | Temporal unit that defines ban duration: `MINUTES`, `HOURS`, `DAYS` or `PERMANENT`. |

The following example bans workers who fail 90% of the last 10 assignments with known answers for 7 days.

```yaml
quality_control:
  golden_set:
    history_size: 10
    ban_rules:
      incorrect_threshold: 90
      ban_duration: 7
      ban_units: DAYS
```

Use the key `reject_rules` under `quality_control` to reject all work from workers based on their performance against the assignments with known answers.

| Key                   | Value   | Description                                                                                                |
|:----------------------|:--------|:-----------------------------------------------------------------------------------------------------------|
| `incorrect_threshold` | integer | Percentage of incorrect assignments that will result in rejecting all assignments submitted by the worker. |

The following example rejects all assignments submitted by workers who fail more than 50% of the last 10 assignments with known answers.

```yaml
quality_control:
  golden_set:
    history_size: 10
    reject_rules:
      incorrect_threshold: 50
```

Use the key `approve_rules` under `quality_control` to accept all work from workers based on their performance against the assignments with known answers.

| Key                 | Value   | Description                                                                                                |
|:--------------------|:--------|:-----------------------------------------------------------------------------------------------------------|
| `correct_threshold` | integer | Percentage of correct assignments that will result in accepting all submitted assignments from the worker. |

The following example accepts all assignments submitted by workers who answer correctly to more than 70% of the last 10 assignments with known answers.

```yaml
quality_control:
  golden_set:
    history_size: 10
    approve_rules:
      correct_threshold: 70
```

Use the key `skill_rules` under `quality_control` to grant skills to workers based on their performance against the assignments with known answers.

| Key                 | Value   | Description                                                    |
|:--------------------|:--------|:---------------------------------------------------------------|
| `correct_threshold` | integer | Percentage of correct assignments needed to receive the skill. |
| `skill_id`          | integer | A valid identifier for a skill.                                |
| `skill_value`       | integer | A value associated with a skill.                               |

The following example grants the skill 12345 with a value of 80 to all workers who answer correctly to more than 80% of the assignments with known answers.

```yaml
quality_control:
  golden_set:
    history_size: 10
    skill_rules:
      correct_threshold: 80
      skill_id: 12345
      skill_value: 80
```

## Combining Tasks into Task Sequences

One key functionality of 𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊 is the creation of Task Sequences, which allow moving assignments from one Task to another.

The connections between individual Tasks are defined in the YAML configuration under the top-level key `actions`.

The following key/value pairs can be provided under the key `actions`.

| Key            | Value      | Description                                                                                                                         |
|:---------------|:-----------|:------------------------------------------------------------------------------------------------------------------------------------|
| `on_submitted` | string     | The [name](#naming-a-task) of the Task or Action to which submitted assignments should be sent.                                     |
| `on_rejected`  | string     | The [name](#naming-a-task) of the Task or Action to which rejected assignments should be sent.                                      |
| `on_accepted`  | string     | The [name](#naming-a-task) of the Task or Action to which accepted assignments should be sent.                                      |
| `on_closed`    | string     | The [name](#naming-a-task) of the Task or Action to which assignments should be sent when the pool closes.                          |
| `on_result`    | dictionary | A dictionary that maps a particular output value to the [name](#naming-a-task) of a Task or Action to which the assignment is sent. |

The following example sets up three actions. All submitted assignment will be sent to a Task named `verification`. If an assignment is rejected, the assignment is sent to a Task named `annotation`. If the assignment is accepted, it will be sent to a Task named `segmentation`.

```yaml
actions:
  on_submitted: verification
  on_rejected: annotation
  on_accepted: segmentation
```

The following example illustrates the use of the `on_result` action. If the output value is `true`, the assignment will be sent to a Task named `next_task`. If the value is `false`, the task will be sent to a Task named `previous_task`.

```yaml
  on_result:
    true: next_task
    false: previous_task
```

## Processing Task outputs using Actions

In 𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊, Actions are used to process outputs from Tasks and other Actions.

### Forward

The Forward Action can be used to accept, reject and forward assignments *based on the output values*.

To create a Forward Action, initialise a Forward object that points towards the YAML configuration file and the Tasks or Actions to which the assignments will be forwarded to.

The following example creates a Forward action using a configuration file named `fwd_config.yaml` and a Toloka client named `client`. The argument `targets` takes the names of the *Python objects* (Tasks or Actions) to which the assignments will be forward to (`outline_img` and `classify_txt`).

```python
from abulafia.actions import Forward

fwd = Forward(configuration='fwd_config.yaml', 
              client=client, 
              targets=[outline_img, classify_txt])
```

To configure the Forward Action, use the following top-level keys in the YAML configuration file. 

| Key         | Value      | Description                                                                      |
|:------------|:-----------|:---------------------------------------------------------------------------------|
| `name`      | string     | A unique [name](#naming-a-task) for the Forward Action.                          |
| `data`      | string     | The name of the variable that contains the output data to be evaluated.          |
| `on_result` | dictionary | A dictionary that maps outputs to actions.                                       |
| `messages`  | dictionary | A dictionary that maps outputs to messages for accepted or rejected assignments. |
 
The following example defines a Forward Action named `fwd_results`, which processes incoming data stored under the variable `result`.

If the variable `result` in the incoming data contains the value `text`, the assignment is forwarded to a Task named `classify_text`. Conversely, if the variable `result` contains the value `image`, the assignment will be forwarded to a Task named `outline_image`.

```yaml
name: fwd_results
data: result
on_result:
  text: classify_text
  image: outline_image
```

The next example defines a Forward Action named `reject_accept` and uses the Forward Action to accept and reject incoming assignments based on their outputs.

If the variable `classification` in the incoming data contains the value `correct`, the assignment is accepted. If the value is `incorrect`, the assignment is rejected.

The messages associated with these outputs are defined under the top-level key `messages`.

```yaml
name: reject_accept
data: classification
on_result:
  correct: accept
  incorrect: reject
messages:
  correct: "Your assignment was classified as correct."
  incorrect: "Your assignment was classified as incorrect."
```

The final example defines a Forward Action named `accept_fwd` and shows how to accept/reject and forward incoming assignments based on their outputs.

If the variable `result` in the incoming data has the value `correct`, the assignment is accepted and forwarded to a Task named `classify_outlines`. If the value is `incorrect`, the assignment is rejected. If you want rejected assignments to be added automatically to the Task in which the incoming assignments originate, add the name of the Task under the key `on_rejected` when defining [actions](#combining-tasks-into-task-sequences). Finally, if the value is `human_error`, the assignment is accepted and forwarded to a Task named `fix_outlines`. 

The top-level key `messages` defines messages associated with all three outputs.

```yaml
name: accept_fwd
data: result
on_result:
  correct:
    - accept
    - classify_outlines
  incorrect: reject
  human_error:
    - accept
    - fix_outlines
messages:
  correct: "Your assignment was classified as correct."
  incorrect: "Your assignment was classified as incorrect."
  human_error: "Your assignment contained some errors, but you will be paid for the work."
```

For more examples on using the Forward Action, see the file [`examples/action_demo.py`](examples/action_demo.py) and the associated YAML configuration files. 

### Aggregate

The Aggregate Action can be used to aggregate outputs from crowdsourced workers using various algorithms implemented in the [*Crowd-Kit*](https://github.com/Toloka/crowd-kit/) library.

To create an Aggregate Action, initialise an Aggregate object that points towards a YAML configuration file, a Task object that contains the output to be aggregated, and a [Forward](#forward) object that is used to process the results.

The following example creates an Aggregate object using a configuration file named `agg_conf.yaml`. The argument `task` needs to be provided with the Task object that contains the outputs to be aggregated. The input for the argument `forward` is a Forward object, which will be used to process the aggregated results.

```python
from abulafia.actions import Aggregate

agg = Aggregate(configuration='agg_conf.yaml', 
                task=detect_text, 
                forward=fwd_agg_text)
```

The Aggregate Action may only be applied to Task outputs once the Task is complete and closed. To aggregate the outputs of a pool, provide the name of the Aggregate Action under the key top-level key [`actions`](#processing-task-outputs-using-actions) and the key `on_closed`.

The following example applies an Aggregate Action named `aggregate_action` to the Task output when the task is completed.

```yaml
actions:
  on_closed: aggregate_action
```

To configure the Aggregate Action, use the following top-level keys in the YAML configuration file.

| Key        | Value      | Description                                                                      |
|:-----------|:-----------|:---------------------------------------------------------------------------------|
| `name`     | string     | A unique [name](#naming-a-task) for the Aggregate Action.                        |
| `method`   | string     | The name of the aggregation algorithm to be used.                                |
| `messages` | dictionary | An optional dictionary that maps particular outputs to messages for the workers. |
 
The following aggregation methods are currently supported. Provide the name as the value for the `method` key.

| Name               | Method                                                                                                                              |
|:-------------------|:------------------------------------------------------------------------------------------------------------------------------------|
| `majority_vote`    | [Majority vote](https://toloka.ai/docs/crowd-kit/reference/crowdkit.aggregation.classification.majority_vote.MajorityVote/)         |
| `dawid_skene`      | [Dawid-Skene](https://toloka.ai/docs/crowd-kit/reference/crowdkit.aggregation.classification.dawid_skene.DawidSkene/)               |
| `mmsr`             | [M-MSR](https://toloka.ai/docs/crowd-kit/reference/crowdkit.aggregation.classification.m_msr.MMSR/)                                 |
| `wawa`             | [Wawa](https://toloka.ai/docs/crowd-kit/reference/crowdkit.aggregation.classification.wawa.Wawa/)                                   |
| `zero_based_skill` | [Zero-based skill](https://toloka.ai/docs/crowd-kit/reference/crowdkit.aggregation.classification.zero_based_skill.ZeroBasedSkill/) |
| `glad`             | [GLAD](https://toloka.ai/docs/crowd-kit/reference/crowdkit.aggregation.classification.glad.GLAD/)                                   |

The following example defines an Aggregate Action named `agg_ds`, which uses the Dawid-Skene algorithm for aggregating the outputs.

The top-level key `messages` defines three outputs and messages associated with them, which are added to input to the Forward Action.

```yaml
name: agg_ds
method: dawid_skene
messages:
  correct: "Your assignment was classified as correct."
  incorrect: "Your assignment was classified as incorrect."
  human_error: "Your assignment contained some errors, but you will be paid for the work."
```

### VerifyPolygon

The VerifyPolygon Action can be used to check that the bounding boxes submitted by crowdsourced workers are valid, that is, the lines of a polygon do not cross each other. This is performed automatically using the [Shapely](https://pypi.org/project/shapely/) library.

To create a VerifyPolygon Action, initialise a VerifyPolygon object that points towards a YAML configuration file, a Task object that contains the polygons to be validated, and a [Forward](#forward) object that is used to process the results.

The following example creates a VerifyPolygon object using a configuration file named `verify.yaml`. The argument `task` needs to be provided with the Task object that contains the outputs to be aggregated. The input for the argument `forward` is a Forward object, which will be used to process the results.

```python
from abulafia.actions import VerifyPolygon

vp = VerifyPolygon(configuration='verify.yaml',
                   task=outline_objects,
                   forward=verify_fwd)
```

The VerifyPolygon Action may only applied to Task outputs once the Task is complete and closed. To verify the polygons submitted by workers, provide the name of the VerifyPolygon Action under the top-levle key [`actions`](#processing-task-outputs-using-actions) and the key `on_closed`.

The following example applies a VerifyPolygon Action named `verify_polygon` to the Task outputs.

```yaml
actions:
  on_closed: verify_polygon
```

To configure the VerifyPolygon Action, use the following top-level keys in the YAML configuration file.


| Key      | Value  | Description                                                                                                            |
|:---------|:-------|:-----------------------------------------------------------------------------------------------------------------------|
| `name`   | string | A unique [name](#naming-a-task) for the VerifyPolygon Action.                                                          |
| `data`   | string | The name of the variable that contains the output data to be validated.                                                |
| `labels` | list   | A list of strings or dictionaries that define bounding box labels and their counts that should be present in the data. |

The following example creates a VerifyPolygon Action named `verify_poly`, which validates incoming bounding boxes stored under the variable `polygons`. The items provided in the list under the top-level key `labels` define that the incoming data must contain precisely one polygon labelled as `text` and an arbitrary number of polygons labelled as `graphics`.

```yaml
name: verify_poly
data: polygons
labels:
  - text: 1
  - graphics
```

For an additional example of using the VerifyPolygon Action, see the example in [segment_and_verify.py](segment_and_verify.py).

### SeparateBBoxes

The SeparateBBoxes Action can be used to separate groups of bounding boxes submitted by workers into individual bounding boxes. This Action is particularly useful if you need to ...

To create a SeparateBBoxes Action, initialise a SeparateBBoxes object that points towards a YAML configuration file and a Task object to which the individual bounding boxes will be forwarded.

The following example creates a SeparateBBox object using a configuration file named `sep.yaml`. The argument `target` defines the Task object to which the bounding boxes will be sent to. In this case, the bounding boxes are sent to a Task object named `describe_object`. 

```python
from abulafia.actions import SeparateBBoxes

sp = SeparateBBoxes(configuration='sep.yaml',
                    target=describe_object)
```

Optionally, you can also add labels to the bounding boxes by providing the argument `add_label` to the `SeparateBBoxes` object. The label should be a string, as exemplified below. The following example adds the label `source` to each bounding box.

```python
sp = SeparateBBoxes(configuration='sep.yaml',
                    target=describe_object,
                    label='source')
```

To configure the SeparateBBoxes Action, use the following top-level keys in the YAML configuration file.


| Key      | Value      | Description                                                                                                              |
|:---------|:-----------|:-------------------------------------------------------------------------------------------------------------------------|
| `name`   | string     | A unique [name](#naming-a-task) for the Aggregate Action.                                                                |
| `data`   | dictionary | A dictionary that defines the variable names that contain the images and bounding boxes within the incoming assignments. |

The following example creates a SeparateBBoxes Action named `sep_boxes`. The top-devel key `data` is used to declare the variables that contain the images and bounding boxes among the incoming assignments. In this case, the images are found under the variable `img`, whereas the bounding boxes are stored under the variable `box`.

```yaml
name: sep_boxes
data:
  image: img 
  bboxes: box
```

If you wish to load the bounding boxes to be separated from a file, provide the key `file` that points towards a TSV file under the key `data`. The following example loads data from a file named `bboxes.csv`. In this case, the keys `image` and `bboxes` refer to names of the columns in the input TSV file.

```yaml
data:
  image: img
  bboxes: box
  file: bboxes.csv
```

## Tutorials
### Creating a Task for classifying images

In this tutorial, we create a YAML configuration file for the `ImageClassification` class.

This example breaks down how 𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊 uses YAML files to create and configure Tasks. The complete configuration file referred to in this example may be found [here](config/classify_image.yaml).

First we define a unique name for the Task under the key `name`. In this case, we call the Task *classify_images*.

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

These labels are defined under the key `labels`. Each key under `labels` defines the value that will be stored when the worker selects the label, whereas the label defines what shown in the user interface. Here we set up two labels in the user interface, *Yes* and *No*, which store the values *true* and *false*, respectively.

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

Next, we configure a pool within the project to which the assignments will be uploaded. This configuration is provided under the key `pool`.

To begin with, we use the `estimated_time_per_suite` to estimate the time spent for completing each task suite (a group of one or more assignments) in seconds. This will allow 𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊 to estimate whether the payment for the work is fair.

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
