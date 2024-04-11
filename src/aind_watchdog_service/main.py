import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from datetime import datetime as dt
from datetime import timedelta
import os
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

from aind_watchdog_service.run_job import run_job
from aind_watchdog_service.models.job_config import WatchConfig


class EventHandler(PatternMatchingEventHandler):
    def __init__(self, scheduler: BackgroundScheduler, pattern: str, config: WatchConfig):
        super().__init__(patterns=pattern)
        self.scheduler = scheduler
        self.config = config

    def _get_trigger_time(self, transfer_time: str) -> dt:
        hour = dt.strptime(transfer_time, "%H:%M").hour
        trigger_time = dt.now().replace(hour=hour, minute=0, second=0, microsecond=0)
        if (trigger_time - dt.now()).total_seconds() < 0:
            trigger_time = trigger_time + timedelta(days=1)
        return trigger_time

    def on_created(self, event) -> None:
        if self.config.transfer_time:
            trigger = self._get_trigger_time(self.config.transfer_time)
        self.scheduler.add_job(run_job, trigger, args=(event, self.config))

    def on_modified(self, event) -> None:
        if self.config.transfer_time:
            trigger = self._get_trigger_time(self.config.transfer_time)
        self.scheduler.add_job(run_job, trigger, args=(event, self.config))


def initiate_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.start()
    return scheduler


def initiate_observer(config: WatchConfig, scheduler: BackgroundScheduler) -> None:
    observer = Observer()
    pattern = config.flag_dir
    if config.flag_file:
        pattern = os.path.join(config.flag_dir, config.flag_file)
    event_handler = EventHandler(scheduler, pattern, config)
    observer.schedule(event_handler, config, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(5)
    except (KeyboardInterrupt, SyntaxError, SystemExit):
        observer.stop()
        scheduler.shutdown()
    observer.join()


def main(config: dict) -> None:
    # Load configuration
    watch_config = WatchConfig(**config)
    # Start APScheduler
    scheduler = initiate_scheduler()
    # Start watchdog observer
    initiate_observer(watch_config, scheduler)


if __name__ == "__main__":
    configuration = os.getenv("WATCH_CONFIG")
    if not configuration:
        raise AttributeError(
            "Environment variable WATCH_CONFIG not set. Please set and restart"
        )
    with open(configuration) as y:
        data = yaml.safe_load(y)
    main(data)
