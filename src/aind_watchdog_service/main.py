""" Main module to start the watchdog observer and scheduler """

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from datetime import datetime as dt
from datetime import timedelta
import os
import yaml
from typing import Union
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
import logging

from aind_watchdog_service.models.job_config import (
    WatchConfig,
)
from aind_watchdog_service.event_handler import EventHandler
from aind_watchdog_service.logging_config import setup_logging


class WatchdogService:
    """Maintain and starts scheduler and observer"""

    def __init__(
        self,
        watch_config: WatchConfig,
        log_dir: Path = "C:/ProgramData/aind/aind-watchdog-service",
    ):
        """Construct WatchDogService, setup logging

        Parameters
        ----------
        watch_config : WatchConfig
            Configuration for scheduler and observer
        log_dir : Optional[Path]
            Directory to store logs
        """
        self.watch_config = watch_config
        self.scheduler = None
        self._setup_logging(log_dir)

    def _setup_logging(self, log_dir):
        log_fp = Path(log_dir)
        if not log_fp.exists():
            log_fp.mkdir(parents=True)
        setup_logging(log_file=log_fp / "aind-watchdog-service.log")

    def initiate_scheduler(self) -> None:
        """Starts APScheduler"""
        logging.info("Starting scheduler")
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def initiate_observer(self) -> None:
        """Starts Wathdog observer"""
        logging.info("Starting observer")
        observer = Observer()
        watch_directory = self.watch_config.flag_dir
        if not Path(watch_directory).exists():
            raise FileNotFoundError(f"Directory {watch_directory} does not exist")
        if not Path(self.watch_config.manifest_complete).exists():
            Path(self.watch_config.manifest_complete).mkdir(parents=True, exist_ok=True)
        event_handler = EventHandler(self.scheduler, self.watch_config)
        observer.schedule(event_handler, watch_directory)
        observer.start()
        try:
            while True:
                time.sleep(3)
        except (KeyboardInterrupt, SyntaxError, SystemExit):
            logging.info("Exiting program")
            observer.stop()
            self.scheduler.shutdown()
        observer.join()

    def start_service(self) -> None:
        """Initiate scheduler and observer"""
        self.initiate_scheduler()
        self.initiate_observer()


def main(config: dict) -> None:
    """Load configuration, initiate WatchdogService and start service"""
    watch_config = WatchConfig(**config)
    watchdog_service = WatchdogService(watch_config)
    watchdog_service.start_service()


if __name__ == "__main__":
    configuration = os.getenv("WATCH_CONFIG")
    if not configuration:
        raise AttributeError(
            "Environment variable WATCH_CONFIG not set. Please set and restart"
        )
    with open(configuration) as y:
        data = yaml.safe_load(y)
    main(data)
