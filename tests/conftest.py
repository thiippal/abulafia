import pytest


def pytest_addoption(parser):
    parser.addoption("--api", action='store_true', help="Run API tests on Toloka sandbox. To "
                                                        "enable these tests, use the flag "
                                                        "--api when running pytest, and place "
                                                        "your Toloka sandbox credentials "
                                                        "into a file named 'creds.json'.")


def pytest_configure(config):
    config.addinivalue_line("markers", "api: mark test as requiring access to Toloka API")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--api"):

        # Do not skip tests, simply return.
        return

    skip_api = pytest.mark.skip(reason="Use flag --api to run API tests on Toloka sandbox")

    for item in items:

        if "api" in item.keywords:

            item.add_marker(skip_api)
