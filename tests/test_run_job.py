"""Test the run_job module"""

import unittest
from unittest.mock import patch, MagicMock
import yaml
from pathlib import Path
import subprocess
import requests
import json
from watchdog.events import FileModifiedEvent

from aind_watchdog_service.models.watch_config import WatchConfig
from aind_watchdog_service.models.job_configs import (
    VastTransferConfig,
    RunScriptConfig,
)
from aind_watchdog_service.run_job import RunJob


TEST_DIRECTORY = Path(__file__).resolve().parent


class MockFileModifiedEvent(FileModifiedEvent):
    """Mock FileModifiedEvent for testing EventHandler"""

    def __init__(self, src_path):
        """init"""
        super().__init__(src_path)


class TestRunSubprocess(unittest.TestCase):
    """test subrpcocess"""

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
        with open(cls.watch_config_fp) as yam:
            watch_config = yaml.safe_load(yam)
        with open(cls.vast_manifest) as yam:
            vast_config = yaml.safe_load(yam)
        with open(cls.script_manifest) as yam:
            script_config = yaml.safe_load(yam)
        cls.watch_config = WatchConfig(**watch_config)
        cls.vast_config = VastTransferConfig(**vast_config)
        cls.script_config = RunScriptConfig(**script_config)
        cls.mock_event = MockFileModifiedEvent("/path/to/file.txt")

    @patch("subprocess.run")
    def test_run_subprocess_vast(self, mock_subproc: MagicMock):
        """Test run_subprocess function"""

        # Test command
        cmd = ["ls", "-l"]
        # Mock mock_subproc to return a CompletedProcess object
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=cmd, returncode=8, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        execute_vast_config = RunJob(self.mock_event, self.vast_config, self.watch_config)
        result = execute_vast_config.run_subprocess(cmd)
        # # Assert that mock_subproc was called with the correct arguments
        mock_subproc.assert_called_once_with(
            cmd, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        # Assert the return value of the function
        self.assertEqual(result.args, cmd)
        self.assertEqual(result.returncode, 8)
        self.assertEqual(result.stdout, b"Mock stdout")
        self.assertEqual(result.stderr, b"Mock stderr")

    @patch("subprocess.run")
    def test_run_subprocess_script(self, mock_subproc: MagicMock):
        """Test run_subprocess function"""

        # Test command
        cmd = ["ls", "-l"]
        # Mock mock_subproc to return a CompletedProcess object
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=cmd, returncode=8, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        execute_script_config = RunJob(
            self.mock_event, self.vast_config, self.watch_config
        )
        result = execute_script_config.run_subprocess(cmd)
        # # Assert that mock_subproc was called with the correct arguments
        mock_subproc.assert_called_once_with(
            cmd, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        # Assert the return value of the function
        self.assertEqual(result.args, cmd)
        self.assertEqual(result.returncode, 8)
        self.assertEqual(result.stdout, b"Mock stdout")
        self.assertEqual(result.stderr, b"Mock stderr")

    @patch("subprocess.run")
    def test_os_calls(self, mock_subproc: MagicMock):
        """Test execute_windows_command and execute_linux_command functions"""
        src_dir = "/path/to/some_directory"
        src_file = "/path/to/some_file.txt"
        dest = "/some_place/on_a/hardrive"
        mock_subproc.return_value = subprocess.CompletedProcess(args=[], returncode=0)

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = True
            execute_vast_config = RunJob(
                self.mock_event, self.vast_config, self.watch_config
            )
            winx_dir = execute_vast_config.execute_windows_command(src_dir, dest)
            winx_file = execute_vast_config.execute_windows_command(src_file, dest)
            self.assertEqual(winx_dir, True)
            self.assertEqual(winx_file, True)
            mock_subproc.assert_called()

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = False
            execute_vast_config = RunJob(
                self.mock_event, self.vast_config, self.watch_config
            )
            winx_dir = execute_vast_config.execute_windows_command(src_dir, dest)
            winx_file = execute_vast_config.execute_windows_command(src_file, dest)
            self.assertEqual(winx_dir, False)
            self.assertEqual(winx_file, False)
            mock_subproc.assert_called()

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = True
            execute_vast_config = RunJob(
                self.mock_event, self.vast_config, self.watch_config
            )
            winx_dir = execute_vast_config.execute_linux_command(src_dir, dest)
            winx_file = execute_vast_config.execute_linux_command(src_file, dest)
            self.assertEqual(winx_dir, True)
            self.assertEqual(winx_file, True)
            mock_subproc.assert_called()

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = False
            execute_vast_config = RunJob(
                self.mock_event, self.vast_config, self.watch_config
            )
            winx_dir = execute_vast_config.execute_linux_command(src_dir, dest)
            winx_file = execute_vast_config.execute_linux_command(src_file, dest)
            self.assertEqual(winx_dir, False)
            self.assertEqual(winx_file, False)
            mock_subproc.assert_called()

    @patch("os.path.join")
    @patch("os.makedirs")
    @patch("aind_watchdog_service.run_job.RunJob.execute_windows_command")
    @patch("aind_watchdog_service.run_job.RunJob.execute_linux_command")
    @patch("aind_watchdog_service.alert_bot.AlertBot")
    @patch("logging.error")
    def test_copy_to_vast(
        self,
        mock_log_err: MagicMock,
        mock_join: MagicMock,
        mock_mkdir: MagicMock,
        mock_execute_windows: MagicMock,
        mock_execute_linux: MagicMock,
        mock_alert: MagicMock,
    ):
        """test copy to vast"""
        mock_join.return_value = "/path/to/join"
        mock_mkdir.return_value = None
        mock_execute_windows.return_value = True
        mock_execute_linux.return_value = True
        mock_alert.return_value = requests.Response
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "exists") as mock_file:
                mock_file.return_value = True
                result = RunJob(self.mock_event, self.vast_config, self.watch_config)
                mock_log_err.assert_not_called()
                response = result.copy_to_vast()
                self.assertEqual(response, True)

        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "exists") as mock_file:
                mock_file.return_value = False
                mock_execute_windows.return_value = False
                result = RunJob(self.mock_event, self.vast_config, self.watch_config)
                response = result.copy_to_vast()
                mock_log_err.assert_called()
                self.assertEqual(response, False)

    @patch("requests.post")
    def test_trigger_transfer_service(self, mock_post: MagicMock):
        """test trigger transfer service"""
        mock_response = requests.Response()
        mock_response.status_code = 200
        body = json.dumps(
            [
                {"_id": "abc123", "message": "hi"},
                {"_id": "efg456", "message": "hello"},
            ]
        )
        mock_response._content = json.dumps({"body": body}).encode("utf-8")
        mock_post.return_value = mock_response
        execute = RunJob(self.mock_event, self.vast_config, self.watch_config)
        response = execute.trigger_transfer_service()
        self.assertEqual(response, True)

    @patch("requests.post")
    def test_trigger_transfer_service_bad(self, mock_post: MagicMock):
        mock_response = requests.Response()
        mock_response.status_code = 404
        body = json.dumps(
            [
                {"_id": "abc123", "message": "hi"},
                {"_id": "efg456", "message": "hello"},
            ]
        )
        mock_response._content = json.dumps({"body": body}).encode("utf-8")
        mock_post.return_value = mock_response
        execute = RunJob(self.mock_event, self.vast_config, self.watch_config)
        response = execute.trigger_transfer_service()
        self.assertEqual(response, False)

    @patch("aind_watchdog_service.alert_bot.AlertBot.send_message")
    @patch("aind_watchdog_service.run_job.RunJob.copy_to_vast")
    @patch("aind_watchdog_service.run_job.RunJob.trigger_transfer_service")
    @patch("subprocess.run")
    @patch("aind_watchdog_service.run_job.RunJob.move_manifest_to_archive")
    def test_run_job(
        self,
        mock_move_mani: MagicMock,
        mock_subproc: MagicMock,
        mock_trigger_transfer: MagicMock,
        mock_copy_to_vast: MagicMock,
        mock_alert: MagicMock,
    ):
        """test run job"""
        mock_move_mani.return_value = None
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                mock_trigger_transfer.return_value = True
                mock_copy_to_vast.return_value = True
                mock_alert.return_value = requests.Response
                execute = RunJob(self.mock_event, self.vast_config, self.watch_config)
                execute.run_job()
                mock_alert.assert_called_with("Job complete", self.mock_event.src_path)
                mock_move_mani.assert_called_once()

                mock_trigger_transfer.return_value = False
                mock_copy_to_vast.return_value = True
                execute = RunJob(self.mock_event, self.vast_config, self.watch_config)
                execute.run_job()
                mock_alert.assert_called_with(
                    "Could not trigger aind-data-transfer-service",
                    self.mock_event.src_path,
                )

                mock_trigger_transfer.return_value = True
                mock_copy_to_vast.return_value = False
                execute = RunJob(self.mock_event, self.vast_config, self.watch_config)
                execute.run_job()
                mock_alert.assert_called_with(
                    "Could not copy data to destination", self.mock_event.src_path
                )

                mock_trigger_transfer.return_value = False
                mock_copy_to_vast.return_value = False
                execute = RunJob(self.mock_event, self.vast_config, self.watch_config)
                execute.run_job()

                mock_alert.assert_called_with(
                    "Could not copy data to destination", self.mock_event.src_path
                )

    @patch("os.mkdir")
    @patch("subprocess.run")
    @patch("aind_watchdog_service.run_job.RunJob.trigger_transfer_service")
    @patch("aind_watchdog_service.alert_bot.AlertBot.send_message")
    @patch("aind_watchdog_service.run_job.RunJob.move_manifest_to_archive")
    def test_run_script(
        self,
        mock_move_mani: MagicMock,
        mock_alert: MagicMock,
        mock_trigger_transfer: MagicMock,
        mock_subproc: MagicMock,
        mock_dir: MagicMock,
    ):
        """test run script"""
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        mock_alert.return_value = requests.Response
        mock_trigger_transfer.return_value = True
        mock_dir.return_value = True
        mock_move_mani.return_value = None
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                execute = RunJob(self.mock_event, self.script_config, self.watch_config)
                execute.run_job()
                mock_subproc.assert_called()
                mock_alert.assert_called_with("Job complete", self.mock_event.src_path)
                mock_move_mani.assert_called_once()

        mock_trigger_transfer.return_value = False
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                execute = RunJob(self.mock_event, self.script_config, self.watch_config)
                execute.run_job()
                mock_alert.assert_called_with(
                    "Could not trigger aind-data-transfer-service",
                    self.mock_event.src_path,
                )
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=[], returncode=8, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                mock_subproc.assert_called()
                execute = RunJob(self.mock_event, self.script_config, self.watch_config)
                execute.run_job()
                mock_alert.assert_called_with(
                    "Error running script",
                    f"Could not execute cmd1 for {self.script_config.name}",
                )

    @patch("aind_watchdog_service.run_job.RunJob.run_subprocess")
    @patch("aind_watchdog_service.run_job.PLATFORM", "windows")
    @patch("aind_watchdog_service.run_job.RunJob.execute_windows_command")
    def test_move_manifest_win(self, mock_execute: MagicMock, mock_subproc: MagicMock):
        """Test the move manifest function"""
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        mock_execute.return_value = True
        execute = RunJob(self.mock_event, self.script_config, self.watch_config)
        execute.move_manifest_to_archive()
        mock_subproc.assert_called_once()

    @patch("aind_watchdog_service.run_job.RunJob.run_subprocess")
    @patch("aind_watchdog_service.run_job.PLATFORM", "linux")
    def test_move_manifest_lin(self, mock_subproc: MagicMock):
        """Test the move manifest function"""
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        execute = RunJob(self.mock_event, self.script_config, self.watch_config)
        execute.move_manifest_to_archive()
        mock_subproc.assert_called_once()


if __name__ == "__main__":
    unittest.main()
