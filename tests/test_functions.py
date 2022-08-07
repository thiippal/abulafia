import pytest
import yaml
from abulafia.task_specs import read_configuration, check_io
import toloka.client as toloka


@pytest.fixture
def task_conf():

    with open('data/detect_text.yaml') as conf_file:

        conf = yaml.safe_load(conf_file)

        return conf


def test_read_configuration(task_conf):
    """
    Test that YAML configuration files are read successfully.
    """

    assert read_configuration('data/detect_text.yaml') == task_conf


def test_check_io_outputs(task_conf):

    # Create expected inputs/outputs based on configuration
    expected_in, expected_out = {'url'}, {'bool'}

    # Apply the function to be tested
    result = check_io(task_conf, expected_in, expected_out)

    assert result[2] == {'url': 'image'}
    assert result[3] == {'bool': 'result'}


def test_check_io_specs(task_conf):

    # Create expected inputs/outputs based on configuration
    expected_in, expected_out = {'url'}, {'bool'}

    # Define Toloka data specifications
    spec_in = {'image': toloka.project.UrlSpec(required=True, hidden=False)}
    spec_out = {'result': toloka.project.BooleanSpec(required=True, hidden=False)}

    # Apply the function to be tested
    result = check_io(task_conf, expected_in, expected_out)

    assert result[0] == spec_in
    assert result[1] == spec_out


def test_check_io_type(task_conf):

    # Create expected inputs/outputs based on configuration
    expected_in, expected_out = {'url'}, {'bool'}

    # Apply the function to be tested
    result = check_io(task_conf, expected_in, expected_out)

    assert isinstance(result, tuple)


def test_check_io_len(task_conf):

    # Create expected inputs/outputs based on configuration
    expected_in, expected_out = {'url'}, {'bool'}

    # Apply the function to be tested
    result = check_io(task_conf, expected_in, expected_out)

    assert len(result) == 4

