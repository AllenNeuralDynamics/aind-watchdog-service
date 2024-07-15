"""Logging configuration"""

import logging
from logging.handlers import RotatingFileHandler


def setup_logging(log_file=None, log_level=logging.INFO):
    """Create log handler

    Parameters
    ----------
    log_file : filepath to send logging, optional
        by default None
    log_level : configure logging level, optional
        by default logging.INFO
    """
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Create a formatter and set the format for logs
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Create a console handler and set level to debug
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # If log_file is provided, add a file handler
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=10
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
