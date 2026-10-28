import pytest

from undoom.config import reset_config


@pytest.fixture(autouse=True)
def _reset_undoom_config():
    reset_config()
    yield
    reset_config()
