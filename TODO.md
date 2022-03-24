# List of things to do

## Resources

- Documentation for [Toloka-Kit](https://toloka.ai/docs/toloka-kit/)
- Repository for Toloka-Kit [examples](https://github.com/Toloka/toloka-kit/tree/main/examples)
- [Toloka Sandbox](https://sandbox.toloka.yandex.com/) and [documentation](https://toloka.ai/docs/guide/concepts/sandbox.html)

## Bigger things

- Design and build validation mechanisms that estimate hourly earnings to prevent sweatshop pricing ⛔
- Generate documentation automatically from docstrings (for potential tools, see [here](https://wiki.python.org/moin/DocumentationTools)) ⛔
- Create a suite of tests e.g. using [nose](https://nose.readthedocs.io/en/latest/) for the entire tool ⛔

## Smaller things

- Enable user to configure task forwarding based on assignment result (e.g. if the result is True, forward to pool X; if False, forward to pool Y). ⛔
- Implement aggregation methods e.g. using [Crowd-Kit](https://github.com/Toloka/crowd-kit) into the [Actions](https://github.com/crowdsrc-uh/abulafia/blob/main/actions/actions.py) submodule ⛔
- Add new interfaces for various basic tasks (text annotation, classification, etc.) ⛔
- Remove deprecated [filters](https://toloka.ai/docs/guide/concepts/filters.html?lang=en), such as [rating](https://github.com/crowdsrc-uh/abulafia/blob/c186307d53d4f584e1bc4de939f0c56f6116bc70/task_specs/core_task.py#L413) ⛔
- Implement any filters that have not been added yet to the [CrowdsourcingTask](https://github.com/crowdsrc-uh/abulafia/blob/c186307d53d4f584e1bc4de939f0c56f6116bc70/task_specs/core_task.py#L351) class ⛔
- Implement any [quality control](https://toloka.ai/docs/guide/concepts/control.html?lang=en) mechanisms that have not been added yet to the CrowdsourcingTask class ⛔ 
- Add warning to the use of highly-rated performers to avoid [hidden qualification labour](https://aclanthology.org/2021.acl-short.44.pdf) ⛔ 

## Nice-to-haves

- Improved pool tracking (e.g. prevent printing updates to stdout if no progress has been made) ⛔
- Improved pool tracking for [pool progress](https://github.com/crowdsrc-uh/abulafia/blob/main/functions/core_functions.py#L449) ⛔
- Better handling of Toloka-specific errors (e.g. "operation not allowed" etc.) ⛔
