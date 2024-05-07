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

    @patch("subprocess.run")
    def test_run_subprocess(self, mock_subproc: MagicMock):
        """Test run_subprocess function"""
        
        cmd = ["ls", "-l"]

        # Mock mock_subproc to return a CompletedProcess object
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=cmd, returncode=8, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        mock_event = MockFileModifiedEvent("/path/to/file.txt")
        result = RunJob.run_subprocess(cmd)
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
            winx_dir = RunJob.execute_windows_command(src_dir, dest)
            winx_file = RunJob.execute_windows_command(src_file, dest)
            self.assertEqual(winx_dir, True)
            self.assertEqual(winx_file, True)
            mock_subproc.assert_called()

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = False
            winx_dir = RunJob.execute_windows_command(src_dir, dest)
            winx_file = RunJob.execute_windows_command(src_file, dest)
            self.assertEqual(winx_dir, False)
            self.assertEqual(winx_file, False)
            mock_subproc.assert_called()

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = True
            winx_dir = RunJob.execute_linux_command(src_dir, dest)
            winx_file = RunJob.execute_linux_command(src_file, dest)
            self.assertEqual(winx_dir, True)
            self.assertEqual(winx_file, True)
            mock_subproc.assert_called()

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = False
            winx_dir = RunJob.execute_linux_command(src_dir, dest)
            winx_file = RunJob.execute_linux_command(src_file, dest)
            self.assertEqual(winx_dir, False)
            self.assertEqual(winx_file, False)
            mock_subproc.assert_called()


class TestCopyToVast(unittest.TestCase):
    """test copy to vast"""

    @classmethod
    def setUp(cls) -> None:
        """set up files"""
        cls.path_to_manifest = TEST_DIRECTORY / "resources" / "manifest_file.yml"

    @patch("os.path.join")
    @patch("os.makedirs")
    @patch("aind_watchdog_service.run_job.execute_windows_command")
    @patch("aind_watchdog_service.run_job.execute_linux_command")
    @patch("aind_watchdog_service.alert_bot.AlertBot")
    def test_copy_to_vast(
        self,
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
        with open(self.path_to_manifest) as yam:
            manifest_data = yaml.safe_load(yam)

        vast_config = VastTransferConfig(**manifest_data)
        response = RunJob.copy_to_vast(vast_config, mock_alert)
        self.assertEqual(response, True)

        mock_execute_windows.return_value = False
        response = RunJob.copy_to_vast(vast_config, mock_alert)
        self.assertEqual(response, False)


class TestTriggerTransferService(unittest.TestCase):
    """test trigger transfer service"""

    @classmethod
    def setUp(cls) -> None:
        """set up files"""
        cls.path_to_manifest = TEST_DIRECTORY / "resources" / "manifest_file.yml"

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
        with open(self.path_to_manifest) as yam:
            manifest_data = yaml.safe_load(yam)
        vast_config = VastTransferConfig(**manifest_data)
        response = RunJob.trigger_transfer_service(vast_config)
        self.assertEqual(response, True)

        mock_response.status_code = 404
        mock_post.return_value = mock_response
        response = RunJob.trigger_transfer_service(vast_config)
        self.assertEqual(response, False)


class TestRunJob(unittest.TestCase):
    """test run job"""

    @classmethod
    def setUp(cls) -> None:
        """set up files"""
        cls.path_to_config = TEST_DIRECTORY / "resources" / "rig_config_no_run_script.yml"
        cls.path_to_manifest = TEST_DIRECTORY / "resources" / "manifest_file.yml"
        cls.path_to_config_run_script = (
            TEST_DIRECTORY / "resources" / "manifest_run_script.yml"
        )

    @patch("aind_watchdog_service.alert_bot.AlertBot.send_message")
    @patch("aind_watchdog_service.run_job.copy_to_vast")
    @patch("aind_watchdog_service.run_job.trigger_transfer_service")
    @patch("subprocess.run")
    @patch("aind_watchdog_service.run_job.move_manifest_to_archive")
    def test_run_job(
        self,
        mock_move_mani: MagicMock,
        mock_subproc: MagicMock,
        mock_trigger_transfer: MagicMock,
        mock_copy_to_vast: MagicMock,
        mock_alert: MagicMock,
    ):
        """test run job"""
        with open(self.path_to_config) as yam:
            config_data = yaml.safe_load(yam)
        with open(self.path_to_manifest) as yam:
            manifest_data = yaml.safe_load(yam)
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        mock_move_mani.return_value = None
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                watch_config = WatchConfig(**config_data)
                vast_config = VastTransferConfig(**manifest_data)
                mock_event = MockFileModifiedEvent("/path/to/file.txt")
                mock_trigger_transfer.return_value = True
                mock_copy_to_vast.return_value = True
                mock_alert.return_value = requests.Response
                RunJob.run_job(mock_event, vast_config, watch_config)
                mock_alert.assert_called_with("Job complete", mock_event.src_path)
                mock_move_mani.assert_called_once()

                mock_trigger_transfer.return_value = False
                mock_copy_to_vast.return_value = True
                RunJob.run_job(mock_event, vast_config, watch_config)
                mock_alert.assert_called_with(
                    "Could not trigger aind-data-transfer-service", mock_event.src_path
                )

                mock_trigger_transfer.return_value = True
                mock_copy_to_vast.return_value = False
                RunJob.run_job(mock_event, vast_config, watch_config)
                mock_alert.assert_called_with(
                    "Could not copy data to destination", mock_event.src_path
                )

                mock_trigger_transfer.return_value = False
                mock_copy_to_vast.return_value = False
                RunJob.run_job(mock_event, vast_config, watch_config)

                mock_alert.assert_called_with(
                    "Could not copy data to destination", mock_event.src_path
                )

    @patch("os.mkdir")
    @patch("subprocess.run")
    @patch("aind_watchdog_service.run_job.trigger_transfer_service")
    @patch("aind_watchdog_service.alert_bot.AlertBot.send_message")
    @patch("aind_watchdog_service.run_job.move_manifest_to_archive")
    def test_run_script(
        self,
        mock_move_mani: MagicMock,
        mock_alert: MagicMock,
        mock_trigger_transfer: MagicMock,
        mock_subproc: MagicMock,
        mock_dir: MagicMock,
    ):
        """test run script"""
        with open(self.path_to_config) as yam:
            config_data = yaml.safe_load(yam)
        with open(self.path_to_config_run_script) as yam:
            manifest_data = yaml.safe_load(yam)
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
                watch_config = WatchConfig(**config_data)
                run_config = RunScriptConfig(**manifest_data)
                mock_event = MockFileModifiedEvent("/path/to/file.txt")
                RunJob.run_job(mock_event, run_config, watch_config)
                mock_subproc.assert_called()
                mock_alert.assert_called_with("Job complete", mock_event.src_path)
                mock_move_mani.assert_called_once()

        mock_trigger_transfer.return_value = False
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                watch_config = watch_config.WatchConfig(**config_data)
                run_config = watch_config.RunScriptConfig(**manifest_data)
                mock_event = MockFileModifiedEvent("/path/to/file.txt")
                RunJob.run_job(mock_event, run_config, watch_config)
                mock_alert.assert_called_with(
                    "Could not trigger aind-data-transfer-service", mock_event.src_path
                )
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=[], returncode=8, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        with patch.object(Path, "is_dir") as mock_dir:
            mock_dir.return_value = True
            with patch.object(Path, "is_file") as mock_file:
                mock_file.return_value = True
                watch_config = watch_config.WatchConfig(**config_data)
                run_config = watch_config.RunScriptConfig(**manifest_data)
                mock_event = MockFileModifiedEvent("/path/to/file.txt")
                mock_subproc.assert_called()
                RunJob.run_job(mock_event, run_config, watch_config)
                mock_alert.assert_called_with(
                    "Error running script",
                    f"Could not execute cmd1 for {run_config.name}",
                )

    @patch("aind_watchdog_service.run_job.run_subprocess")
    @patch("aind_watchdog_service.run_job.PLATFORM", "windows")
    def test_move_manifest_win(self, mock_subproc: MagicMock):
        """Test the move manifest function"""
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        src = "/path/to/src"
        dest = "/path/to/dest"
        RunJob.move_manifest_to_archive(src, dest)
        mock_subproc.assert_called_once()

    @patch("aind_watchdog_service.run_job.run_subprocess")
    @patch("aind_watchdog_service.run_job.PLATFORM", "linux")
    def test_move_manifest_lin(self, mock_subproc: MagicMock):
        """Test the move manifest function"""
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        src = "/path/to/src"
        dest = "/path/to/dest"
        RunJob.move_manifest_to_archive(src, dest)
        mock_subproc.assert_called_once()


if __name__ == "__main__":
    unittest.main()
