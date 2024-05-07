"""Test main entry point."""

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
    WatchdogService,
    start_watchdog,
)
from aind_watchdog_service.event_handler import EventHandler


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

class MockWatchdogService:
    """Mock WatchdogService for testing WatchdogService"""

    def __init__(self, watch_config: WatchConfig):
        """init"""
        self.watch_config = watch_config

    def start_service(self):
        """start service"""
        pass

class MockObserver(Observer):
    """Mock Observer for testing WatchdogService"""
    def __init__(self):
        """init"""
        super().__init__()
    
    def start(self):
        """start"""
        pass

    def schedule(event_handler: EventHandler, watch_directory: str):
        """schedule"""
        pass
class TestWatchdogService(unittest.TestCase):
    """Test WatchdogService class"""

    @classmethod
    def setUp(cls) -> None:
        """Set up the test environment by defining the test data."""
        cls.path_to_config = TEST_DIRECTORY / "resources" / "rig_config_no_run_script.yml"
        cls.path_to_manifest = TEST_DIRECTORY / "resources" / "manifest.yml"

    @patch("aind_watchdog_service.main.WatchdogService._setup_logging")
    @patch("logging.error")
    @patch("logging.info")
    @patch("aind_watchdog_service.main.EventHandler")
    @patch(
        "time.sleep", side_effect=KeyboardInterrupt
    )  # Mock time.sleep to raise KeyboardInterrupt
    @patch("watchdog.observers.Observer")
    def test_initiate_observer(
        self,
        mock_observer: MagicMock,
        mock_sleep: MagicMock,
        mock_event_handler: MagicMock,
        mock_log_info: MagicMock,
        mock_log_err: MagicMock,
        mock_setup_logging: MagicMock
    ):
        """initiate observer test"""
        with open(self.path_to_config) as yam:
            config = yaml.safe_load(yam)
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                with patch.object(Path, "exists") as mock_exists:
                    mock_exists.return_value = True
                    watch_config = WatchConfig(
                        **config
                    )  # Provide necessary config parameters
                    mock_scheduler = MockScheduler()
                    mock_observer.return_value = MockObserver()
                    mock_event_handler.return_value = MockEventHandler(
                        mock_scheduler, watch_config
                    )
                    watchdog_service = WatchdogService(watch_config)
                    watchdog_service.start_service()
                    mock_setup_logging.assert_called_once()
                    mock_log_info.assert_called()
                    mock_log_err.assert_not_called()
                    mock_event_handler.assert_called_once()
                    mock_sleep.assert_called_once()
                    with self.assertRaises(KeyboardInterrupt):
                        signal.raise_signal(signal.SIGINT)
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False
            with self.assertRaises(FileNotFoundError):
                watchdog_service.initiate_observer()
                mock_log_err.assert_called_once()

    
    @patch("aind_watchdog_service.main.WatchdogService")
    def test_main(self, mock_watchdog: MagicMock):
        """Test main, WatchdogService constructor"""
        with open(self.path_to_config) as yam:
            config = yaml.safe_load(yam)
        mock_watchdog.return_value = MockWatchdogService(WatchConfig(**config))
        start_watchdog(config)
        mock_watchdog.assert_called_once()
 

if __name__ == "__main__":
    unittest.main()
        