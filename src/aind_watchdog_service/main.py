""" Main module to start the watchdog observer and scheduler """

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import ValidationError
from watchdog.observers import Observer

from aind_watchdog_service.event_handler import EventHandler
from aind_watchdog_service.logging_config import setup_logging
from aind_watchdog_service.models.watch_config import WatchConfig


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
        """Setup logging
        Parameters
        ----------
        log_dir : Path
            Directory to store logs
        """
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
        """Starts Watchdog observer"""
        logging.info("Starting observer")
        observer = Observer()
        watch_directory = self.watch_config.flag_dir
        if not Path(watch_directory).exists():
            logging.error("Directory %s does not exist", watch_directory)
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


def start_watchdog(watch_config: WatchConfig) -> None:
    """Load configuration, initiate WatchdogService and start service"""

    watchdog_service = WatchdogService(watch_config)
    watchdog_service.start_service()


def main():
    """Main function to parse arguments and start watchdog service"""

    parser = argparse.ArgumentParser(description="Watchdog service")
    parser.add_argument(
        "-c",
        "--config-path",
        type=str,
        help="Configuration file for watchdog service. Takes precedence over environment \
            variable WATCH_CONFIG and other arguments",
    )
    parser.add_argument(
        "-f", "--flag-dir", type=str, help="Directory for watchdog to poll"
    )
    parser.add_argument(
        "-m",
        "--manifest-complete",
        type=str,
        help="Manifest directory for triggered data",
    )
    parser.add_argument(
        "-w", "--webhook-url", type=str, help="Teams webhook url for user notification"
    )

    args = parser.parse_args()

    if args.config_path:
        args.flag_dir = None
        args.manifest_complete = None

    if (args.flag_dir is None) ^ (args.manifest_complete is None):
        logging.error("If passing --flag-dir or --manifest-complete, both are required!")
        sys.exit(1)

    if (args.flag_dir is not None) and (args.manifest_complete is not None):
        try:
            watch_config = WatchConfig(
                flag_dir=args.flag_dir,
                manifest_complete=args.manifest_complete,
                webhook_url=args.webhook_url,
            )
        except ValidationError as e:
            logging.error(
                "Error constructing WatchConfig model from cli arguments: %s", e
            )
    else:
        configuration = (
            args.config_path if args.config_path else os.getenv("WATCH_CONFIG")
        )

        if not configuration:
            logging.error(
                "Environment variable WATCH_CONFIG not set and a path was not passed.\
                    Please set and restart"
            )
            raise AttributeError(
                "Environment variable WATCH_CONFIG not set. Please set and restart"
            )
        if not Path(configuration).exists():
            logging.error("Configuration file %s does not exist", configuration)
            raise FileNotFoundError(f"Configuration file {configuration} does not exist")

        with open(configuration, encoding="UTF-8") as y:
            data = yaml.safe_load(y)
            try:
                watch_config = WatchConfig(**data)
            except ValidationError as e:
                logging.error("Error loading config %s", e)
                sys.exit(1)

        start_watchdog(watch_config)


if __name__ == "__main__":
    main()
