"""Example test template."""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import yaml
from pathlib import Path

from aind_watchdog_service.models import watch_config


TEST_DIRECTORY = Path(__file__).resolve().parent


class TestConfig(unittest.TestCase):
    """Load configuration test"""

    @classmethod
    def setUp(cls) -> None:
        """Set up the test environment by defining the test data."""
        cls.path_to_config = TEST_DIRECTORY / "resources" / "rig_config_no_run_script.yml"
        cls.path_to_manifest = TEST_DIRECTORY / "resources" / "manifest_file.yml"
        cls.path_to_run_script_manifest = (
            TEST_DIRECTORY / "resources" / "manifest_run_script.yml"
        )

    def test_watch_config(self):
        """Test the WatchConfig class."""
        # Open config for to pass and compare
        with open(self.path_to_config) as yam:
            data = yaml.safe_load(yam)

        # Check the the case where directories exist
        watchdog_config = watch_config.WatchConfig(**data)
        self.assertEqual(watchdog_config.model_dump(), data)

        # Check run_script set to non-bool
        data["run_script"] = 10
        with self.assertRaises(ValueError):
            watch_config.WatchConfig(**data)

    def test_manifest_config(self):
        """Example of how to test the truth of a statement."""
        # Open config for to pass and compare
        with open(self.path_to_manifest) as yam:
            data = yaml.safe_load(yam)
        # Check the the case where directories exist
        manifest_config = watch_config.VastTransferConfig(**data)
        self.assertEqual(manifest_config.model_dump(), data)

        # Check transfer_time variants
        data["transfer_time"] = "12:00:00"
        with self.assertRaises(ValueError):
            watch_config.VastTransferConfig(**data)

        data["transfer_time"] = "11:00"
        manifest_config = watch_config.VastTransferConfig(**data)
        self.assertEqual(manifest_config.model_dump(), data)

        data["platform"] = "cafe"
        with self.assertRaises(ValueError):
            watch_config.VastTransferConfig(**data)

    def test_run_script_config(self):
        """test the runscript congig"""
        with open(self.path_to_run_script_manifest) as yam:
            data = yaml.safe_load(yam)

        manifest_config = watch_config.RunScriptConfig(**data)
        self.assertEqual(manifest_config.model_dump(), data)


if __name__ == "__main__":
    unittest.main()
