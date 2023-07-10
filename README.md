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

See the directory [`examples`](/examples) for documentation and practical examples.

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

## Contact

If you have questions about the tool, feel free to contact tuomo.hiippala (at) helsinki.fi or open an issue on GitHub.
