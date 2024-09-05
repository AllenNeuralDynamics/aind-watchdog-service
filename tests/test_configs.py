"""Example test template."""

import unittest
from datetime import datetime as dt
from pathlib import Path

import pydantic_core
import yaml
from aind_data_schema_models import modalities, platforms
from pydantic import ValidationError

from aind_watchdog_service.models.manifest_config import ManifestConfig
from aind_watchdog_service.models.watch_config import WatchConfig

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
        self.assertDictEqual(manifest_config.model_dump(), data)

        # Check transfer_time variants
        data["transfer_time"] = "12:00"
        with self.assertRaises(pydantic_core._pydantic_core.ValidationError):
            ManifestConfig(**data)
        del data["transfer_time"]
        data["schedule_time"] = dt.now().time()
        manifest_config = ManifestConfig(**data)
        self.assertDictEqual(manifest_config.model_dump(), data)

        data["platform"] = "cafe"
        with self.assertRaises(ValidationError):
            ManifestConfig(**data)

        data["platform"] = "multiplane-ophys"
        data["modalities"]["nikon"] = ["some file"]
        with self.assertRaises(ValidationError):
            ManifestConfig(**data)

    def test_manifest_from_platform_modalities(self):
        """Test the manifest from platform modalities."""

        modality = getattr(modalities.Modality, "BEHAVIOR", None)
        self.assertIsNotNone(modality)
        platform = getattr(platforms.Platform, "BEHAVIOR", None)
        self.assertIsNotNone(platform)

        def _create_manifest(modality, platform) -> ManifestConfig:
            return ManifestConfig(
                name="test",
                destination="path",
                modalities={modality: ["path"]},
                platform=platform,
                schemas=["path"],
                processor_full_name="na",
                subject_id="007",
                acquisition_datetime=dt(2024, 9, 3, 13, 38, 48, 36456),
                project_name="no project",
                mount=None,
                capsule_id=None,
            )

        self.assertEqual(
            _create_manifest(modality=modality, platform=platform),
            _create_manifest(
                modality=getattr(modality, "abbreviation"),
                platform=getattr(platform, "abbreviation"),
            ),
        )

    def test_manifest_config_posix_coercion(self):
        """Test the posix coercion."""
        # Open config for to pass and compare

        non_posix_file = r"c:/test/this_file.json"
        posix_file = Path(non_posix_file).as_posix()

        def _create_manifest(path: str) -> ManifestConfig:
            return ManifestConfig(
                name="test",
                destination=path,
                modalities={modalities.Modality.BEHAVIOR.abbreviation: [path]},
                platform=platforms.Platform.BEHAVIOR.abbreviation,
                schemas=[path],
                processor_full_name="na",
                subject_id="007",
                acquisition_datetime=dt(2024, 9, 3, 14, 16, 46, 181680),
                project_name="no project",
                mount=None,
                capsule_id=None,
            )

        self.assertEqual(_create_manifest(non_posix_file), _create_manifest(posix_file))
        self.assertEqual(
            _create_manifest(non_posix_file).destination,
            Path.as_posix(Path(non_posix_file)),
        )


if __name__ == "__main__":
    unittest.main()
