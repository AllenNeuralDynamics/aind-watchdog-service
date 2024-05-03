"""Example test template."""

import unittest
from unittest.mock import patch
from unittest.mock import patch, MagicMock
import yaml
from pathlib import Path
from watchdog.events import FileModifiedEvent
from watchdog.observers import Observer
from apscheduler.schedulers.background import BackgroundScheduler
import signal
from datetime import datetime as dt
from datetime import timedelta
import requests

from aind_watchdog_service.models.watch_config import (
    WatchConfig,
)
from aind_watchdog_service.main import (
    initiate_observer,
    initiate_scheduler,
    main,
)
from aind_watchdog_service.event_handler import EventHandler
from aind_watchdog_service.logging_config import setup_logging


TEST_DIRECTORY = Path(__file__).resolve().parent


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


class MockScheduler(BackgroundScheduler):
    """Mock Scheduler for testing EventHandler"""

    def __init__(self):
        """init"""
        super().__init__({})


class TestInitiate(unittest.TestCase):
    """Test initiate functions"""

    @classmethod
    def setUp(cls) -> None:
        """Set up the test environment by defining the test data."""
        cls.path_to_config = TEST_DIRECTORY / "resources" / "rig_config_no_run_script.yml"

    @patch("aind_watchdog_service.logging_config.setup_logging")
    @patch("aind_watchdog_service.main.EventHandler")
    @patch(
        "time.sleep", side_effect=KeyboardInterrupt
    )  # Mock time.sleep to raise KeyboardInterrupt
    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_initiate_observer(
        self,
        mock_scheduler: MagicMock,
        mock_sleep: MagicMock,
        mock_event_handler: MagicMock,
        mock_logging: MagicMock
    ):
        """initiate observer test"""
        with open(self.path_to_config) as yam:
            config = yaml.safe_load(yam)
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                watch_config = WatchConfig(
                    **config
                )  # Provide necessary config parameters
                mock_event_handler.return_value = MockEventHandler(
                    mock_scheduler, watch_config
                )
                initiate_observer(watch_config, mock_scheduler)
                mock_event_handler.assert_called_once()
                mock_sleep.assert_called_once()
                mock_scheduler.shutdown.assert_called_once()
                with self.assertRaises(KeyboardInterrupt):
                    signal.raise_signal(signal.SIGINT)

    def test_initiate_scheduler(self):
        """initiate scheduler test"""
        scheduler = initiate_scheduler()
        self.assertIsInstance(scheduler, BackgroundScheduler)


class TestDatetime(unittest.TestCase):
    """testing scheduler"""

    @classmethod
    def setUp(cls) -> None:
        """Set up the test environment by defining the test data."""
        cls.path_to_config = TEST_DIRECTORY / "resources" / "rig_config_no_run_script.yml"

    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_datetime(self, mock_scheduler: MagicMock):
        """testing scheduler trigger time"""
        # mock_scheduler.return_value = MockScheduler()
        with open(self.path_to_config) as yam:
            config = yaml.safe_load(yam)
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                watch_config = WatchConfig(
                    **config
                )  # Provide necessary config parameters
                event_handler = EventHandler(mock_scheduler, watch_config)

                # Test time trigger conditions for addition of one day when hour has already passed
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


class TestLoadManifest(unittest.TestCase):
    """Load manifest test"""

    @classmethod
    def setUp(cls) -> None:
        """set up the test environment by defining the test data."""
        cls.path_to_config = TEST_DIRECTORY / "resources" / "rig_config_no_run_script.yml"
        cls.path_to_manifest = TEST_DIRECTORY / "resources" / "manifest_file.yml"
        cls.path_to_run_script_manifest = (
            TEST_DIRECTORY / "resources" / "manifest_run_script.yml"
        )

    @patch("aind_watchdog_service.alert_bot.AlertBot.send_message")
    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_load_vast_manifest(self, mock_scheduler: MagicMock, mock_alert: MagicMock):
        """Test load manifest"""
        with open(self.path_to_manifest) as yam:
            manifest = yaml.safe_load(yam)
        with open(self.path_to_config) as yam:
            config = yaml.safe_load(yam)
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                watch_config = WatchConfig(**config)
            # Test config returns correctly
            event_handler = EventHandler(mock_scheduler, watch_config)
            mock_event = MockFileModifiedEvent(
                TEST_DIRECTORY / "resources" / "manifest_file.yml"
            )
            test_manifest = event_handler._load_vast_transfer_manifest(mock_event)
            self.assertEqual(test_manifest.model_dump(), manifest)

            # Test case where config load fails
            mock_alert.return_value = requests.Response
            with self.assertRaises(Exception):
                mock_alert.assert_called_with(
                    "Could not copy data to destination", mock_event.src_path
                )

    @patch("aind_watchdog_service.alert_bot.AlertBot.send_message")
    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_load_run_script_manifest(
        self, mock_scheduler: MagicMock, mock_alert: MagicMock
    ):
        """Test load run script manifest"""
        with open(self.path_to_run_script_manifest) as yam:
            manifest = yaml.safe_load(yam)
        with open(self.path_to_config) as yam:
            config = yaml.safe_load(yam)
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                watch_config = WatchConfig(**config)
            # Test config returns correctly
            event_handler = EventHandler(mock_scheduler, watch_config)
            mock_event = MockFileModifiedEvent(
                TEST_DIRECTORY / "resources" / "manifest_run_script.yml"
            )
            test_manifest = event_handler._load_run_script_manifest(mock_event)
            self.assertEqual(test_manifest.model_dump(), manifest)

            # Test case where config load fails
            mock_alert.return_value = requests.Response
            with self.assertRaises(Exception):
                mock_alert.assert_called_with(
                    "Could not copy data to destination", mock_event.src_path
                )


class TestMain(unittest.TestCase):
    """Test main function"""

    @classmethod
    def setUp(cls) -> None:
        """set up the test environment by defining the test data."""
        cls.path_to_config = TEST_DIRECTORY / "resources" / "rig_config_no_run_script.yml"
        cls.path_to_run_script_config = (
            TEST_DIRECTORY / "resources" / "rig_config_with_run_script.yml"
        )

    @patch("aind_watchdog_service.main.initiate_scheduler")
    @patch("aind_watchdog_service.main.initiate_observer")
    def test_main_vast_config(self, mock_observer: MagicMock, mock_scheduler: MagicMock):
        """test main function with vast config"""
        with open(self.path_to_config) as yam:
            config = yaml.safe_load(yam)
        mock_observer.return_value = True
        mock_scheduler.return_value = True
        main(config)
        mock_observer.assert_called_once()
        mock_scheduler.assert_called_once()

    @patch("aind_watchdog_service.main.initiate_scheduler")
    @patch("aind_watchdog_service.main.initiate_observer")
    def test_main_script_config(
        self, mock_observer: MagicMock, mock_scheduler: MagicMock
    ):
        """test main function with run script config"""
        with open(self.path_to_run_script_config) as yam:
            run_script_config = yaml.safe_load(yam)
        mock_observer.return_value = True
        mock_scheduler.return_value = True
        main(run_script_config)
        mock_observer.assert_called_once()
        mock_scheduler.assert_called_once()


class TestEventHandlerEvents(unittest.TestCase):
    """Test event handler events"""

    @classmethod
    def setUp(cls) -> None:
        """Set up the test environment by defining the test data."""
        cls.path_to_config = TEST_DIRECTORY / "resources" / "rig_config_no_run_script.yml"
        cls.path_to_manifest = TEST_DIRECTORY / "resources" / "manifest_file.yml"

    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_event_handler(self, mock_scheduler: MagicMock):
        """test event handler events"""
        mock_scheduler.return_value = MockScheduler
        with open(self.path_to_config) as yam:
            config = yaml.safe_load(yam)
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                watch_config = WatchConfig(
                    **config
                )  # Provide necessary config parameters
                event_handler = EventHandler(mock_scheduler, watch_config)
                mock_event = MockFileModifiedEvent("/path/to/file.txt")
                event_handler.on_modified(mock_event)
                # mock_scheduler.add_job.assert_called_once()
                # event_handler.on_deleted(mock_event)


if __name__ == "__main__":
    unittest.main()
        