"""Example test template."""

import unittest
from unittest.mock import patch
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
import logging

from aind_watchdog_service.logging_config import setup_logging
from aind_watchdog_service.run_job import run_subprocess

TEST_DIRECTORY = Path(__file__).resolve().parent


class TestMyModule(unittest.TestCase):
    
    @classmethod
    def setUp(cls) -> None:
        """set up files"""
        cls.path_to_manifest = TEST_DIRECTORY / "resources" / "manifest_file.yml"
    
    @patch('logging.getLogger')
    @patch('logging.StreamHandler')
    def test_logging(self, mock_stream_handler, mock_get_logger: MagicMock):
        # Create mock objects for logger and stream handler
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Call the function that sets up logging
        setup_logging()

        # Assert that the getLogger function was called
        mock_get_logger.assert_called_once()

        # Assert that the StreamHandler was created and added to the logger
        mock_stream_handler.assert_called_once()
        mock_logger.addHandler.assert_called_once_with(mock_stream_handler.return_value)

    @patch("subprocess.run")
    @patch('logging.getLogger')
    @patch('logging.StreamHandler')
    def test_os_calls(self, mock_stream_handler, mock_get_logger, mock_subproc: MagicMock):
        cmd = ["ls", "-l"]
        # Create mock objects for logger and stream handler
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Mock mock_subproc to return a CompletedProcess object
        mock_subproc.return_value = subprocess.CompletedProcess(
            args=cmd, returncode=8, stdout=b"Mock stdout", stderr=b"Mock stderr"
        )
        setup_logging()
        run_subprocess(cmd)
        
        mock_logger.info.assert_called_once_with(f"Executing command: {cmd}")
        # mock_logger.warning.assert_called_once_with('Warning message')
        # mock_logger.error.assert_called_once_with('Error message')
        # mock_logger.critical.assert_called_once_with('Critical message')
if __name__ == "__main__":
    unittest.main()
