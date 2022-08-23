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

        assert isinstance(test_task.project, toloka.Project)

    def test_project_desc_type(self, test_task):

        assert isinstance(test_task.project.public_description, str)

    def test_project_conf_type(self, test_task):

        assert isinstance(test_task.conf, dict)

    def test_project_client_type(self, test_task):

        assert isinstance(test_task.client, TolokaClient)

    def test_project_data_conf(self, test_task):

        assert isinstance(test_task.data_conf, dict)

    def test_project_proj_conf(self, test_task):

        assert isinstance(test_task.project_conf, dict)

    def test_project_action_conf(self, test_task):

        assert isinstance(test_task.action_conf, dict) or isinstance(test_task.action_conf, type(None))

    def test_project_pool_conf(self, test_task):

        assert isinstance(test_task.pool_conf, dict)

    def test_project_train_conf(self, test_task):

        assert isinstance(test_task.train_conf, dict) or isinstance(test_task.train_conf, type(None))

    def test_project_qual_conf(self, test_task):

        assert isinstance(test_task.qual_conf, dict) or isinstance(test_task.qual_conf, type(None))

    def test_training_type(self, test_task):

        assert isinstance(test_task.training, toloka.Training) or isinstance(test_task.training, type(None))

    def test_pool_type(self, test_task):

        assert isinstance(test_task.pool, toloka.Pool)

    def test_tasks_type(self, test_task):

        assert isinstance(test_task.tasks, list)

    def test_tasks_object_types(self, test_task):

        assert all(isinstance(x, toloka.Task) for x in test_task.tasks)

