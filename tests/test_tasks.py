import pytest
from abulafia.task_specs import ImageClassification
from toloka.client import TolokaClient
import toloka.client as toloka


@pytest.fixture
def dummy_client():

    return TolokaClient('XXX', 'SANDBOX')


@pytest.fixture
def test_task(dummy_client):

    return ImageClassification(configuration='data/detect_text.yaml', client=dummy_client, test=True)


class TestTask:

    def test_condition(self, test_task):

        assert test_task.test is True

    def test_name(self, test_task):

        assert test_task.name == 'detect_text'

    def test_project_type(self, test_task):

        assert type(test_task.project) == toloka.Project

    def test_project_properties(self, test_task):

        assert test_task.project.public_description == 'Look at diagrams from science textbooks and state if they ' \
                                                       'contain text, letters or numbers.'

    # TODO Continue to write tests for CrowdsourcingTask attributes


