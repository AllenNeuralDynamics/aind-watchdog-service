"""Test EventHandler constructor."""

import unittest
from unittest.mock import patch, MagicMock
import yaml
from pathlib import Path
from watchdog.events import FileModifiedEvent
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime as dt
from datetime import timedelta


from aind_watchdog_service.models.watch_config import (
    WatchConfig,
)
from aind_watchdog_service.models.job_configs import (
    VastTransferConfig,
    RunScriptConfig,
)
from aind_watchdog_service.event_handler import EventHandler


class MockFileModifiedEvent(FileModifiedEvent):
    """Mock FileModifiedEvent for testing EventHandler"""

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
        cls.watch_config_fp = (
            TEST_DIRECTORY / "resources" / "rig_config_no_run_script.yml"
        )
        cls.watch_config_script = (
            TEST_DIRECTORY / "resources" / "rig_config_run_script.yml"
        )
        cls.vast_manifest = TEST_DIRECTORY / "resources" / "manifest.yml"
        cls.script_manifest = TEST_DIRECTORY / "resources" / "manifest_run_script.yml"

    @patch("logging.info")
    @patch(
        "aind_watchdog_service.event_handler.EventHandler._load_vast_transfer_manifest"
    )
    @patch("aind_watchdog_service.event_handler.EventHandler.schedule_job")
    def test_event_handler_on_modified(
        self,
        mock_schedule_job: MagicMock,
        mock_vast_transfer: MagicMock,
        mock_log_info: MagicMock,
    ):
        """Test on_modified method"""
        with open(self.watch_config_fp) as yam:
            config = yaml.safe_load(yam)
        with open(self.vast_manifest) as yam:
            vast_config = yaml.safe_load(yam)
        mock_vast_transfer.return_value = VastTransferConfig(**vast_config)
        mock_scheduler = MockScheduler()

        watch_config = WatchConfig(**config)
        event_handler = EventHandler(mock_scheduler, watch_config)
        mock_event = MockFileModifiedEvent("/path/to/manifest.txt")
        event_handler.on_modified(mock_event)
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = False
            mock_log_info.assert_called_with(
                "Found job, executing vast transfer for %s", mock_event.src_path
            )
            mock_vast_transfer.assert_called_once()
            mock_schedule_job.assert_called_once()
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True

    @patch("logging.info")
    @patch("aind_watchdog_service.event_handler.EventHandler._load_run_script_manifest")
    @patch("aind_watchdog_service.event_handler.EventHandler.schedule_job")
    def test_event_handler_on_modified_script(
        self,
        mock_schedule_job: MagicMock,
        mock_script_transfer: MagicMock,
        mock_log_info: MagicMock,
    ):
        """Test on_modified method for script execution"""
        with open(self.watch_config_script) as yam:
            watch_script_config = yaml.safe_load(yam)
        with open(self.script_manifest) as yam:
            script_config = yaml.safe_load(yam)
        mock_scheduler = MockScheduler()
        watch_config = WatchConfig(**watch_script_config)
        event_handler = EventHandler(mock_scheduler, watch_config)
        mock_event = MockFileModifiedEvent("/path/to/manifest.txt")
        event_handler.on_modified(mock_event)
        mock_script_transfer.return_value = RunScriptConfig(**script_config)
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = False
            mock_log_info.assert_called_with(
                "Found job, executing custom script for %s", mock_event.src_path
            )
            mock_schedule_job.assert_called_once()

    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_datetime(self, mock_scheduler: MagicMock):
        """testing scheduler trigger time"""
        # mock_scheduler.return_value = MockScheduler()
        with open(self.watch_config_fp) as yam:
            config = yaml.safe_load(yam)
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                watch_config = WatchConfig(
                    **config
                )  # Provide necessary config parameters
                event_handler = EventHandler(mock_scheduler, watch_config)

                # Test time trigger conditions for addition of one day when hour has already passed # noqa
                time_now = dt.now().hour - 2
                trigger_time = str(time_now).zfill(2) + ":00"
                trigger_time = event_handler._get_trigger_time(trigger_time)
                test_time = dt.now().replace(
                    hour=dt.now().hour - 2, minute=0, second=0, microsecond=0
                )
                test_time = test_time + timedelta(days=1)
                self.assertEqual(trigger_time, test_time)

                # Test trigger time when hour has not passed
                time_now = dt.now().hour + 2
                trigger_time = str(time_now).zfill(2) + ":00"
                trigger_time = event_handler._get_trigger_time(trigger_time)
                test_time = dt.now().replace(
                    hour=dt.now().hour + 2, minute=0, second=0, microsecond=0
                )
                self.assertEqual(trigger_time, test_time)


if __name__ == "__main__":
    unittest.main()
