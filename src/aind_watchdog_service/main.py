""" Main module to start the watchdog observer and scheduler """

import argparse
import logging
import os
import sys
import time
import mpetk
from pathlib import Path

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import ValidationError
from watchdog.observers import Observer

from aind_watchdog_service.event_handler import EventHandler
from aind_watchdog_service.models.watch_config import WatchConfig

from aind_watchdog_service import __version__


class WatchdogService:
    """Maintain and starts scheduler and observer"""

    def __init__(
        self,
        watch_config: WatchConfig,
        log_dir: Path = Path(os.getenv("PROGRAMDATA", "C:/ProgramData"))
        / "aind/aind-watchdog-service",
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


def parse_args(args_list: list[str]) -> argparse.Namespace:
    """read in arguments from the command line

    Parameters
    ----------
    args_list : list[str]
        args read in by the command line

    Returns
    -------
    argparse.Namespace
        parsed arguments
    """

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

    return parser.parse_args(args_list)


def read_config(config_path: str) -> WatchConfig:
    """read yaml configuration file

    Parameters
    ----------
    config_path : str
        path to configuration file

    Returns
    -------
    WatchConfig
        watchdog model
    """
    with open(config_path, encoding="UTF-8") as y:
        data = yaml.safe_load(y)
        try:
            return WatchConfig(**data)
        except ValidationError as e:
            logging.error("Error loading config %s", e)
            sys.exit(1)


def main():
    """Main function to parse arguments and start watchdog service"""

    args = parse_args(sys.argv[1:])

    if args.config_path:
        args.flag_dir = None
        args.manifest_complete = None

    if (args.flag_dir is None) ^ (args.manifest_complete is None):
        logging.error("If passing --flag-dir or --manifest-complete, both are required!")
        sys.exit(1)

    zk_config = mpetk.mpeconfig.source_configuration("aind_watchdog_service", version=__version__)

    watch_config: WatchConfig
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
        if "flag_dir" not in zk_config or "manifest_complete" not in zk_config:
            raise ValueError(f"Zookeeper configuration configured incorrectly. "
                             f"Missing either flag_dir or manifest_complete fields")
        webhook_url = zk_config["webhook_url"] if "webhook_url" in zk_config else None
        watch_config = WatchConfig(flag_dir=zk_config["flag_dir"], manifest_complete=zk_config["manifest_complete"], webhook_url=webhook_url)

    start_watchdog(watch_config)


if __name__ == "__main__":
    main()
