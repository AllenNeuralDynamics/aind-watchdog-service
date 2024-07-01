"""Example test template."""

import logging
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aind_watchdog_service.logging_config import setup_logging

TEST_DIRECTORY = Path(__file__).resolve().parent


class TestMyModule(unittest.TestCase):

    @classmethod
    def setUp(cls) -> None:
        """set up files"""
        cls.path_to_manifest = TEST_DIRECTORY / "resources" / "manifest_file.yml"

    @patch("logging.getLogger")
    @patch("logging.StreamHandler")
    @patch("logging.FileHandler")
    def test_log_streamhandler(
        self,
        mock_file_handler: MagicMock,
        mock_stream_handler: MagicMock,
        mock_logger: MagicMock,
    ):
        """Test logging setup configuration"""
        # Set up mock objects for logger, stream handler and file handler
        mock_logger.return_value = logging.getLogger
        mock_stream_handler.return_value = logging.StreamHandler
        mock_file_handler.return_value = logging.FileHandler
        # Call the function that sets up logging
        setup_logging()

        # Assert that the getLogger function was called
        mock_logger.assert_called_once()


if __name__ == "__main__":
    unittest.main()
