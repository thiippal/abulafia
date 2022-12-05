import json
import pytest
import toloka.client as toloka


@pytest.mark.api
@pytest.fixture
def api_client():

    # Read the credentials from the JSON file
    with open('creds.json') as cred_f:
        creds = json.loads(cred_f.read())
        client = toloka.TolokaClient(creds['token'], creds['mode'])

        return client


def test_client(api_client):

    pass