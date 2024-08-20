import unittest
from pathlib import Path

import yaml

from aind_watchdog_service.models.watch_config import WatchConfig

TEST_DIRECTORY = Path(__file__).resolve().parent


class TestCli(unittest.TestCase):
    """Load configuration test"""

    @classmethod
    def setUp(cls) -> None:
        """Set up the test environment by defining the test data."""
        cls.watch_config_fp = TEST_DIRECTORY / "resources" / "watch_config.yml"

    def test_watch_config_vast_transfer(self):
        """Test the WatchConfig class."""
        # Open config for to pass and compare
        with open(self.watch_config_fp) as yam:
            data = yaml.safe_load(yam)
        # Check the the case where directories exist
        watchdog_config = WatchConfig(**data)
        self.assertEqual(watchdog_config.model_dump(), data)
