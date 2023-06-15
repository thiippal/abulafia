# 𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊: A tool for fair and reproducible crowdsourcing

𝚊𝚋𝚞𝚕𝚊𝚏𝚒𝚊 is a tool for creating and deploying tasks on the the [Toloka](https://toloka.ai) crowdsourcing platform. 

The tool allows you to create crowdsourcing tasks using pre-defined task interfaces and to configure their settings using [YAML](https://en.wikipedia.org/wiki/YAML) files.

For a description of the tool and the motivation for its development, see this [publication](https://aclanthology.org/2022.latechclfl-1.2/).

Please cite the following publication if you use the tool in your research.

> Tuomo Hiippala, Helmiina Hotti, and Rosa Suviranta. 2022. Developing a tool for fair and reproducible use of paid crowdsourcing in the digital humanities. In *Proceedings of the 6th Joint SIGHUM Workshop on Computational Linguistics for Cultural Heritage, Social Sciences, Humanities and Literature*, pages 7–12, Gyeongju, Republic of Korea. International Conference on Computational Linguistics.

For convenience, you can use the BibTeX entry below.

```text
@inproceedings{hiippala-etal-2022-developing,
    title = "Developing a tool for fair and reproducible use of paid crowdsourcing in the digital humanities",
    author = "Hiippala, Tuomo and Hotti, Helmiina and Suviranta, Rosa",
    booktitle = "Proceedings of the 6th Joint SIGHUM Workshop on Computational Linguistics for Cultural Heritage, Social Sciences, Humanities and Literature",
    month = oct,
    year = "2022",
    address = "Gyeongju, Republic of Korea",
    publisher = "International Conference on Computational Linguistics",
    url = "https://aclanthology.org/2022.latechclfl-1.2",
    pages = "7--12",
    abstract = "This system demonstration paper describes ongoing work on a tool for fair and reproducible use of paid crowdsourcing in the digital humanities. Paid crowdsourcing is widely used in natural language processing and computer vision, but has been rarely applied in the digital humanities due to ethical concerns. We discuss concerns associated with paid crowdsourcing and describe how we seek to mitigate them in designing the tool and crowdsourcing pipelines. We demonstrate how the tool may be used to create annotations for diagrams, a complex mode of expression whose description requires human input.",
}
```

## Installation

You can install the tool from [PyPI](https://pypi.org/project/abulafia/) using the following command: `pip install abulafia`

Alternatively, you can clone this repository and install the tool locally. Move to the directory that contains the repository and type: `pip install .`

## Usage

See the directory [`examples`](/examples) for information on configuring crowdsourcing tasks and practical examples.

To deploy your crowdsourcing tasks to Toloka, the tool needs to read your credentials from a JSON file e.g. `creds.json`. Never add this file to version control. 

The file must contain the following key/value pairs in JSON:

```json
{
    "token": "YOUR_OAUTH_TOKEN",
    "mode": "SANDBOX"
}
```

When you have tested your tasks in the Toloka sandbox, change the value for `"mode"` from `"SANDBOX"` to `"PRODUCTION"` to deploy the tasks on Toloka.

The screenshot below illustrates tool in action.

<img src="https://s3.datacloud.helsinki.fi/crowdsrc:instructions/abulafia-screenshot.png" width=700>

## Pre-defined task interfaces

Crowdsourcing tasks are created using Python objects that define the input and output data, and the task interface. These properties are defined in a YAML configuration file, as shown in the [examples](examples/README.md).

```python
task = TextClassification(configuration='classify_text.yaml', client=client)
```

You can define additional task interfaces by inheriting the [`CrowdsourcingTask`](/task_specs/core_task.py) class, which defines the basic functionalities of a task.

The currently implemented task interfaces can be found in [`/task_specs/task_specs.py`](/task_specs/task_specs.py). These task interfaces are described in greater detail below.

### ImageClassification

A class for image classification tasks. The following input and output formats are supported.

|Input|Output|
|-----|------|
| `url` (image) | `boolean` (true/false) |
|               | `string` (for multiple labels) |

Configure the interface by adding the following keys under the top-level key `interface`.

|Key|Description|
|-----|------|
| `prompt` | A string that defines a text that is shown above the buttons on the interface. |
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

|input|output|
|-----|------|
|`url` (image) | `json` (bounding boxes) |
|`json` (bounding boxes) | `boolean` (optional checkbox) |

Configure the interface by adding the following keys under the top-level key `interface`.

|Key|Description|
|-----|------|
| `prompt` | A string that defines a text that is shown below the image annotation interface. |
| `tools`| A list of values that defines the annotation tools available for the interface. |
| `labels` (optional) | Key/value pairs that define the labels shown on the interface and the values stored in the data. |
| `checkbox` (optional) | A string that defines a text that is shown above the checkbox in the interface. |

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

|Input|Output|
|-----|------|
| `url` (image) | `boolean` (true/false) |
| `json` (bounding boxes) | `string` (for multiple labels) |
| `boolean` (checkbox) | |
| `string` (checkbox) | |

Configure the interface by adding the following keys under the top-level key `interface`.

|Key|Description|
|-----|------|
| `prompt` | A string that defines a text that is shown above the radio buttons on the interface. |
| `labels` | Key/value pairs that define the labels for the radio buttons and the values stored in the data. |
| `segmentation/labels` (optional) | Key/value pairs that define the labels for bounding boxes and the values stored in the data. |
| `checkbox` (optional) | A string that defines a text that is shown above the checkbox in the interface. |

The following example defines a prompt, an image segmentation interface with three labels for bounding boxes and two labels for the radio buttons.

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

|Input|Output|
|-----|------|
| `string` | `boolean` (true/false) |
|          | `string` (for multiple labels) |

Configure the interface by adding the following keys under the top-level key `interface`.

|Key|Description|
|-----|------|
| `prompt` | A string that defines a text that is shown above the buttons on the interface. |
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

|input|output|
|-----|------|
|`string`|`json`|

Configure the interface by adding the following keys under the top-level key `interface`.

|Key|Description|
|-----|------|
| `prompt` | A string that defines a text that is shown above the buttons on the interface. |
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
