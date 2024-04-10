"""Example test template."""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import yaml
from aind_watchdog_service.models import job_config
from pathlib import Path
from datetime import datetime
from pydantic import ValidationError

TEST_DIRECTORY = Path(__file__).resolve().parent

class TestConfig(unittest.TestCase):
    """Parse config"""

    @classmethod
    def setUp(cls) -> None:
        cls.path_to_config = TEST_DIRECTORY / "resources" / "rig_config.yml"
    
    def test_config(self):
        """Example of how to test the truth of a statement."""
        # Open config for to pass and compare
        with open(self.path_to_config) as yam:
                data = yaml.safe_load(yam)
        # Check the the case where directories exist
        with patch.object(Path, "is_dir") as mock_dir:  # +
            mock_dir.return_value = True
            watchdog_config = job_config.WatchConfig(**data)
        self.assertEqual(watchdog_config.model_dump(), data)
        
        # Check the case where directories don't exist
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = False
            with self.assertRaises(ValueError):
                 job_config.WatchConfig(**data)

class TestUpload(unittest.TestCase):
    """test upload"""

if __name__ == "__main__":
    unittest.main()
