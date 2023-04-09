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

```yaml
interface:
  prompt: "Does the image contain text, letters or numbers?"
  labels:
    true: "Yes"
    false: "No" 
```

```yaml
project:
  setup:
    public_name: "Check if an image contains text, letters or numbers"
    public_description: "Look at diagrams from science textbooks and state if they
      contain text, letters or numbers."
  instructions: instructions/detect_text_instructions.html
```

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
