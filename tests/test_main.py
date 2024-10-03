"""Test main entry point."""

import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.events import FileCreatedEvent
from watchdog.observers import Observer

from aind_watchdog_service.event_handler import EventHandler
from aind_watchdog_service.main import WatchdogService, main, parse_args, start_watchdog
from aind_watchdog_service.models.watch_config import WatchConfig

TEST_DIRECTORY = Path(__file__).resolve().parent


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


class MockScheduler(BackgroundScheduler):
    """Mock Scheduler for testing EventHandler"""

    def __init__(self):
        """init"""

    def shutdown(self):
        """mock scheduler shutdown"""
        pass


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

    def schedule(self, event_handler: EventHandler, watch_directory: str):
        """schedule"""
        pass


class TestWatchdogService(unittest.TestCase):
    """Test WatchdogService class"""

    @classmethod
    def setUp(cls) -> None:
        """Set up the test environment by defining the test data."""
        watch_config_fp = TEST_DIRECTORY / "resources" / "watch_config.yml"
        with open(watch_config_fp) as yam:
            cls.watch_config_dict = yaml.safe_load(yam)
        cls.watch_config = WatchConfig(**cls.watch_config_dict)
        cls.mock_event = MockFileCreatedEvent("/path/to/file.txt")

    @patch("aind_watchdog_service.main.WatchdogService._setup_logging")
    @patch("logging.error")
    @patch("logging.info")
    @patch("aind_watchdog_service.main.EventHandler")
    @patch("aind_watchdog_service.main.WatchdogService.initiate_observer")
    @patch.object(EventHandler, "_startup_manifest_check")
    def test_start(
        self,
        mock_startup_manifest_check: MagicMock,
        mock_observer: MagicMock,
        mock_event_handler: MagicMock,
        mock_log_info: MagicMock,
        mock_log_err: MagicMock,
        mock_setup_logging: MagicMock,
    ):
        """initiate observer test"""
        mock_startup_manifest_check.return_value = None
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                with patch.object(Path, "exists") as mock_exists:
                    mock_exists.return_value = True
                    mock_scheduler = MockScheduler()
                    mock_observer.return_value = MockObserver()
                    mock_event_handler.return_value = MockEventHandler(
                        mock_scheduler, self.watch_config
                    )
                    watchdog_service = WatchdogService(self.watch_config)
                    watchdog_service.start_service()
                    mock_setup_logging.assert_called_once()
                    mock_log_info.assert_called()
                    mock_log_err.assert_not_called()

    def test_parse_args(self):
        """Test parse_args"""
        args_list = ["--config-path", "config.yml"]
        expected_args = Namespace(
            config_path="config.yml",
            flag_dir=None,
            manifest_complete=None,
            webhook_url=None,
        )
        result = parse_args(args_list)
        self.assertEqual(result, expected_args)

        args_list = [
            "--flag-dir",
            "/some/dir",
            "--manifest-complete",
            "/some/dir/manifest_complete",
            "--webhook-url",
            "https://alleninstitute.webhook.office.com/webhookb2/70b02442-17e7-4273-b16d-c96e4bc584ec@32669cd6-737f-4b39-8bdd-d6951120d3fc/IncomingWebhook/c67df18b06aa470aa93f4d3a4cb8f4ce/b5d574af-077d-48d4-a6a5-232279015e6a",  # noqa
        ]
        result = parse_args(args_list)
        expected_args = Namespace(
            config_path=None,
            flag_dir="/some/dir",
            manifest_complete="/some/dir/manifest_complete",
            webhook_url="https://alleninstitute.webhook.office.com/webhookb2/70b02442-17e7-4273-b16d-c96e4bc584ec@32669cd6-737f-4b39-8bdd-d6951120d3fc/IncomingWebhook/c67df18b06aa470aa93f4d3a4cb8f4ce/b5d574af-077d-48d4-a6a5-232279015e6a",  # noqa
        )
        self.assertEqual(result, expected_args)

    @patch("aind_watchdog_service.main.parse_args")
    @patch("aind_watchdog_service.main.start_watchdog")
    @patch("os.getenv")
    @patch("aind_watchdog_service.main.read_config")
    @patch("logging.error")
    @patch("aind_watchdog_service.main.WatchdogService")
    def test_main(
        self,
        mock_watchdog: MagicMock,
        mock_log_error: MagicMock,
        mock_read_config: MagicMock,
        mock_env_var: MagicMock,
        mock_start_watchdog: MagicMock,
        mock_parse_args: MagicMock,
    ) -> None:
        """Test main function"""

        mock_watchdog.return_value = MockWatchdogService(self.watch_config)
        start_watchdog(self.watch_config_dict)
        mock_watchdog.assert_called_once()

        mock_parse_args.return_value = Namespace(
            config_path="config.yml",
            flag_dir=None,
            manifest_complete=None,
            webhook_url=None,
        )
        mock_start_watchdog.return_value = None

        mock_env_var.return_value = None

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            mock_read_config.return_value = self.watch_config_dict
            main()
            mock_start_watchdog.assert_called_once()

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False
            mock_read_config.return_value = self.watch_config_dict
            with self.assertRaises(FileNotFoundError):
                main()

        mock_env_var.return_value = "config.yml"
        mock_parse_args.return_value = Namespace(
            config_path=None,
            flag_dir=None,
            manifest_complete=None,
            webhook_url=None,
        )
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            mock_read_config.return_value = self.watch_config_dict
            main()
            mock_start_watchdog.assert_called()

        mock_env_var.return_value = None
        mock_parse_args.return_value = Namespace(
            config_path=None,
            flag_dir="some/dir",
            manifest_complete="some/dir/manifest_complete",
            webhook_url=None,
        )

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False
            mock_read_config.return_value = self.watch_config_dict
            main()
            mock_start_watchdog.assert_called()

        mock_parse_args.return_value = Namespace(
            config_path=None,
            flag_dir=None,
            manifest_complete="some/dir/manifest_complete",
            webhook_url=None,
        )
        mock_log_error.assert_called()

        mock_parse_args.return_value = Namespace(
            config_path=None,
            flag_dir="some/dir",
            manifest_complete=None,
            webhook_url=None,
        )
        mock_log_error.assert_called()


if __name__ == "__main__":
    unittest.main()
