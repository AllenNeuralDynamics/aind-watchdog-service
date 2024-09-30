"""Test EventHandler constructor."""

import unittest
from datetime import datetime as dt
from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.events import FileCreatedEvent

from aind_watchdog_service.event_handler import EventHandler
from aind_watchdog_service.models.manifest_config import ManifestConfig
from aind_watchdog_service.models.watch_config import WatchConfig


class MockFileCreatedEvent(FileCreatedEvent):
    """Mock FileCreatedEvent for testing EventHandler"""

    def __init__(self, src_path):
        """init"""
        super().__init__(src_path)


class MockEventHandler(EventHandler):
    """mock EventHandler for testing EventHandler"""

    def __init__(self, scheduler, config):
        """init"""
        super().__init__(scheduler, config)
        self.jobs = {}

    def _remove_job(self, job_id):
        """remove job"""
        pass


class MockScheduler(BackgroundScheduler):
    """Mock Scheduler for testing EventHandler"""

    def __init__(self):
        """init"""
        super().__init__({})

    def get_jobs(self):
        """mock job ids"""
        return ["1234"]


TEST_DIRECTORY = Path(__file__).resolve().parent


class TestEventHandler(unittest.TestCase):
    """testing scheduler"""

    @classmethod
    def setUp(cls) -> None:
        """Set up the test environment by defining the test data."""
        watch_config_fp = TEST_DIRECTORY / "resources" / "watch_config.yml"
        vast_manifest = TEST_DIRECTORY / "resources" / "manifest.yml"
        with open(watch_config_fp) as yam:
            cls.config = yaml.safe_load(yam)
        with open(vast_manifest) as yam:
            cls.manifest_config = yaml.safe_load(yam)

    @patch("logging.info")
    @patch("aind_watchdog_service.event_handler.EventHandler._load_manifest")
    @patch("aind_watchdog_service.event_handler.EventHandler.schedule_job")
    def test_event_handler_on_created(
        self,
        mock_schedule_job: MagicMock,
        mock_vast_transfer: MagicMock,
        mock_log_info: MagicMock,
    ):
        """Test on_created method"""

        mock_vast_transfer.return_value = ManifestConfig(**self.manifest_config)
        mock_scheduler = MockScheduler()

        watch_config = WatchConfig(**self.config)
        event_handler = EventHandler(mock_scheduler, watch_config)
        mock_event = MockFileCreatedEvent("/path/to/manifest.txt")
        event_handler.on_created(mock_event)
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = False
            mock_log_info.assert_called_with("Found event file %s", mock_event.src_path)
            mock_vast_transfer.assert_called_once()
            mock_schedule_job.assert_called_once()
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True

    @patch.object(EventHandler, "_startup_manifest_check")
    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_datetime(
        self, mock_scheduler: MagicMock, mock_startup_manifest_check: MagicMock
    ):
        """testing scheduler trigger time"""
        # mock_scheduler.return_value = MockScheduler()
        mock_startup_manifest_check.return_value = None
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                watch_config = WatchConfig(
                    **self.config
                )  # Provide necessary config parameters
                event_handler = EventHandler(mock_scheduler, watch_config)

                # Test time trigger conditions for addition of one day when hour has already passed # noqa
                # TODO we should consider a test fixture that freezes time here. This test is NOT deterministic # noqa
                date_now = dt.now()
                trigger_date = event_handler._get_trigger_time(
                    (date_now - timedelta(minutes=1)).time()
                )
                self.assertEqual(trigger_date, date_now + timedelta(days=1, minutes=-1))

                # Test trigger time when hour has not passed
                trigger_time = event_handler._get_trigger_time(
                    (date_now + timedelta(minutes=1)).time()
                )
                self.assertEqual(trigger_time, date_now + timedelta(minutes=1))


if __name__ == "__main__":
    unittest.main()
