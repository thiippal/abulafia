from abulafia.task_specs import read_configuration, check_io
import toloka.client as toloka


def test_read_configuration():
    """
    Test that YAML configuration files are read successfully.
    """

    assert type(read_configuration('data/detect_text.yaml')) == dict


def test_check_io():
    """
    Test that the inputs/outputs defined in the YAML configuration files
    are successfully converted into Toloka data specifications.
    """

    # Read configuration from disk
    conf = read_configuration('data/detect_text.yaml')

    # Create expected inputs/outputs based on configuration
    expected_in, expected_out = {'url'}, {'bool'}

    # Define Toloka data specifications
    spec_in = {'image': toloka.project.UrlSpec(required=True, hidden=False)}
    spec_out = {'result': toloka.project.BooleanSpec(required=True, hidden=False)}

    # Apply the function to be tested
    result = check_io(conf, expected_in, expected_out)

    assert type(result) == tuple
    assert len(result) == 4
    assert result[0] == spec_in
    assert result[1] == spec_out
    assert result[2] == {'url': 'image'}
    assert result[3] == {'bool': 'result'}
