"""Tests for `hivesense2mqtt` package."""

import pytest

from hivesense2mqtt.app.ha_manager import HA_MANAGER


@pytest.fixture
def class_instance() -> HA_MANAGER:
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    return HA_MANAGER()


def test_content(class_instance: HA_MANAGER) -> None:
    """Sample pytest test function with the pytest fixture as an argument."""
    pass
