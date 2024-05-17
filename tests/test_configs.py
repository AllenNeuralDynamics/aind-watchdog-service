"""Example test template."""

import unittest
import yaml
import pydantic_core
from pathlib import Path
from datetime import datetime as dt
from aind_watchdog_service.models.watch_config import WatchConfig
from aind_watchdog_service.models.job_configs import ManifestConfig


TEST_DIRECTORY = Path(__file__).resolve().parent


class TestWatchConfig(unittest.TestCase):
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


class TestManifestConfigs(unittest.TestCase):
    """Test the manifest configs"""

    @classmethod
    def setUp(cls) -> None:
        """Set up the test environment by defining the test data."""
        cls.path_to_manifest = TEST_DIRECTORY / "resources" / "manifest.yml"
        cls.path_to_run_script_manifest = (
            TEST_DIRECTORY / "resources" / "manifest_run_script.yml"
        )

    def test_manifest_config(self):
        """Test te ManifestConfig class."""
        # Open config for to pass and compare
        with open(self.path_to_manifest) as yam:
            data = yaml.safe_load(yam)
        # Check the the case where directories exist
        manifest_config = ManifestConfig(**data)
        self.assertEqual(manifest_config.model_dump(), data)

        # Check transfer_time variants
        data["transfer_time"] = "12:00"
        with self.assertRaises(pydantic_core._pydantic_core.ValidationError):
            ManifestConfig(**data)
        del data["transfer_time"]
        data["schedule_time"] = dt.now()
        manifest_config = ManifestConfig(**data)
        self.assertEqual(manifest_config.model_dump(), data)

        data["platform"] = "cafe"
        with self.assertRaises(AttributeError):
            ManifestConfig(**data)

        data["platform"] = "multiplane-ophys"
        data["modalities"]["nikon"] = ["some file"]
        with self.assertRaises(AttributeError):
            ManifestConfig(**data)


if __name__ == "__main__":
    unittest.main()
