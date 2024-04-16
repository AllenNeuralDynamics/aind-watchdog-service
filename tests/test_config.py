"""Example test template."""

import unittest
from unittest.mock import patch
import yaml
from pathlib import Path

from aind_watchdog_service.models import job_config


TEST_DIRECTORY = Path(__file__).resolve().parent


class TestConfig(unittest.TestCase):
    """Parse config"""

    @classmethod
    def setUp(cls) -> None:
        cls.path_to_config = TEST_DIRECTORY / "resources" / "rig_config_no_run_script.yml"
        cls.path_to_manifest = TEST_DIRECTORY / "resources" / "manifest_file.yml"
        cls.path_to_run_script_manifest = TEST_DIRECTORY / "resources" / "manifest_run_script.yml"

    def test_rig_config(self):
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
        
        # Check run_script set to non-bool
        data["run_script"] = 12
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with self.assertRaises(ValueError):
                job_config.WatchConfig(**data)

    def test_manifest_config(self):
        """Example of how to test the truth of a statement."""
        # Open config for to pass and compare
        with open(self.path_to_manifest) as yam:
            data = yaml.safe_load(yam)
        # Check the the case where directories exist
        with patch.object(Path, "is_file") as mock_file:
            mock_file.return_value = True
            with patch.object(Path, "is_dir") as mock_dir:
                mock_dir.return_value = True
                manifest_config = job_config.VastTransferConfig(**data)
        self.assertEqual(manifest_config.model_dump(), data)

        # Check the case where directories don't exist
        with patch.object(Path, "is_file") as mock_file:
            mock_file.return_value = True
            with patch.object(Path, "is_dir") as mock_dir:
                mock_dir.return_value = False
                with self.assertRaises(ValueError):
                    job_config.VastTransferConfig(**data)

        # Check case where files don't exist
        with patch.object(Path, "is_file") as mock_file:
            mock_file.return_value = False
            with patch.object(Path, "is_dir") as mock_dir:
                mock_dir.return_value = True
                with self.assertRaises(ValueError):
                    job_config.VastTransferConfig(**data)

        
        # Check transfer_time varities
        data["transfer_time"] = "12:00:00"
        with patch.object(Path, "is_file") as mock_file:
            mock_file.return_value = True
            with patch.object(Path, "is_dir") as mock_dir:
                mock_dir.return_value = True
                with self.assertRaises(ValueError):
                    job_config.VastTransferConfig(**data)
        
        data["transfer_time"] = "11:00"
        with patch.object(Path, "is_file") as mock_file:
            mock_file.return_value = True
            with patch.object(Path, "is_dir") as mock_dir:
                mock_dir.return_value = True
                manifest_config = job_config.VastTransferConfig(**data)
        self.assertEqual(manifest_config.model_dump(), data)

    def test_run_script_config(self):
        with open(self.path_to_run_script_manifest) as yam:
            data = yaml.safe_load(yam)
        
        with patch.object(Path, "is_file") as mock_file:
            mock_file.return_value = True
            with patch.object(Path, "is_dir") as mock_dir:
                mock_dir.return_value = True
                manifest_config = job_config.RunScriptConfig(**data)
        self.assertEqual(manifest_config.model_dump(), data)