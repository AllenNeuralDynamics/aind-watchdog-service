import unittest
from unittest.mock import patch, MagicMock
import yaml
from pathlib import Path
import subprocess
import requests

from aind_watchdog_service.models import job_config
from aind_watchdog_service import run_job


TEST_DIRECTORY = Path(__file__).resolve().parent

class TestRunSubprocess(unittest.TestCase):
    @patch("subprocess.run")
    def test_run_subprocess(self, mock_subproc: MagicMock):
        # Command to execute
        cmd = ["ls", "-l"]

        # Mock mock_subproc to return a CompletedProcess object
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )

        # Call the function
        result = run_job.run_subprocess(cmd)

        # Assert that mock_subproc was called with the correct arguments
        mock_subproc.assert_called_once_with(
            cmd, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        # Assert the return value of the function
        self.assertEqual(result.args, cmd)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"Mock stdout")
        self.assertEqual(result.stderr, b"Mock stderr")

    def test_windows_call(self):
        src_dir = "/path/to/some_directory"
        src_file = "/path/to/some_file.txt"
        dest = "/some_place/on_a/hardrive"

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = True
            run_job.run_subprocess = MagicMock(
                return_value=subprocess.CompletedProcess(args=[], returncode=0)
            )
            winx_dir = run_job.execute_windows_command(src_dir, dest)
            winx_file = run_job.execute_windows_command(src_file, dest)
            self.assertEqual(winx_dir, True)
            self.assertEqual(winx_file, True)

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = False
            run_job.run_subprocess = MagicMock(
                return_value=subprocess.CompletedProcess(args=[], returncode=0)
            )
            winx_dir = run_job.execute_windows_command(src_dir, dest)
            winx_file = run_job.execute_windows_command(src_file, dest)
            self.assertEqual(winx_dir, False)
            self.assertEqual(winx_file, False)

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = True
            run_job.run_subprocess = MagicMock(
                return_value=subprocess.CompletedProcess(args=[], returncode=1)
            )
            winx_dir = run_job.execute_windows_command(src_dir, dest)
            winx_file = run_job.execute_windows_command(src_file, dest)
            self.assertEqual(winx_dir, False)
            self.assertEqual(winx_file, False)

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = True
            run_job.run_subprocess = MagicMock(
                return_value=subprocess.CompletedProcess(args=[], returncode=0)
            )
            winx_dir = run_job.execute_linux_command(src_dir, dest)
            winx_file = run_job.execute_linux_command(src_file, dest)
            self.assertEqual(winx_dir, True)
            self.assertEqual(winx_file, True)

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = False
            run_job.run_subprocess = MagicMock(
                return_value=subprocess.CompletedProcess(args=[], returncode=0)
            )
            winx_dir = run_job.execute_linux_command(src_dir, dest)
            winx_file = run_job.execute_linux_command(src_file, dest)
            self.assertEqual(winx_dir, False)
            self.assertEqual(winx_file, False)

        with patch.object(Path, "exists") as mock_file:
            mock_file.return_value = True
            run_job.run_subprocess = MagicMock(
                return_value=subprocess.CompletedProcess(args=[], returncode=1)
            )
            winx_dir = run_job.execute_linux_command(src_dir, dest)
            winx_file = run_job.execute_linux_command(src_file, dest)
            self.assertEqual(winx_dir, False)
            self.assertEqual(winx_file, False)


class TestCopyToVast(unittest.TestCase):
    @classmethod
    def setUp(cls) -> None:
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
        mock_join.return_value = "/path/to/join"
        mock_mkdir.return_value = None
        mock_execute_windows.return_value = True
        mock_execute_linux.return_value = True
        mock_alert.return_value = requests.Response
        with open(self.path_to_manifest) as yam:
            manifest_data = yaml.safe_load(yam)

        vast_config = job_config.VastTransferConfig(**manifest_data)
        response = run_job.copy_to_vast(vast_config, mock_alert)
        self.assertEqual(response, True)

        mock_execute_windows.return_value = False
        response = run_job.copy_to_vast(vast_config, mock_alert)
        self.assertEqual(response, False)


if __name__ == "__main__":
    unittest.main()
