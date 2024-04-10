import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from datetime import datetime as dt
import os
from pathlib import Path

from aind_watchdog_service import trigger_job
from aind_watchdog_service.models.job_config import WatchConfig


class FileObserver:
    def __init__(self, dir, pattern, recursive=True):
        self.observer = Observer()
        self.monitored_directory = dir
        self.recursive = recursive
        self.scheduler = trigger_job.Scheduler()
        self.pattern = pattern

    def run(self):
        event_handler = EventHandler(self.scheduler, self.pattern)
        self.observer.schedule(
            event_handler, self.monitored_directory, recursive=self.recursive
        )
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Stopping observer")

        self.observer.join()


class EventHandler(PatternMatchingEventHandler):
    def __init__(self, scheduler, pattern):
        super(EventHandler, self).__init__(self, pattern=pattern)
        self.scheduler = scheduler
    def on_created(self):
        pass
    def on_modified(self):
        pass

def initiate_watch(configuration: Path) -> None:
    pass


if __name__ == "__main__":
    configuration = os.getenv("WATCH_CONFIG")
    if not configuration:
        raise AttributeError(
            "Environment variable WATCH_CONFIG not set. Please set and restart"
        )
    initiate_watch(Path(configuration))
