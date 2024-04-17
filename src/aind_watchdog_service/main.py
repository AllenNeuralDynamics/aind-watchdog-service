import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from datetime import datetime as dt
from datetime import timedelta
import os
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

from aind_watchdog_service.run_job import run_job, run_script
from aind_watchdog_service.models.job_config import (
    WatchConfig,
    RunScriptConfig,
    VastTransferConfig,
)
from aind_watchdog_service.alert_bot import AlertBot


class EventHandler(FileSystemEventHandler):
    """Event handler for watchdog observer"""

    def __init__(self, scheduler: BackgroundScheduler, config: WatchConfig):
        super().__init__()
        self.scheduler = scheduler
        self.config = config
        self.jobs = {}
        self.alert = AlertBot(config.webhook_url)

    def _load_vast_transfer_manifest(self, event: FileModifiedEvent) -> dict:
        """Instructions to transfer to VAST

        Parameters
        ----------
        event : FileModifiedEvent
           file modified event

        Returns
        -------
        dict
           manifest configuration
        """
        with open(event.src_path, "r") as f:
            try:
                data = yaml.safe_load(f)
                config = VastTransferConfig(**data)
                return config
            except Exception as e:
                self.alert.send_message("Error loading config", e)

    def _load_run_script_manifest(self, event: FileModifiedEvent) -> dict:
        """Instructions to run a script

        Parameters
        ----------
        event : FileModifiedEvent
            file modified event

        Returns
        -------
        dict
            manifest configuration
        """
        with open(event.src_path, "r") as f:
            try:
                config = RunScriptConfig(**yaml.safe_load(f))
            except Exception as e:
                self.alert.send_message("Error loading config", e)
        return config

    def _remove_job(self, event: FileModifiedEvent) -> None:
        """Removes job from scheduler queue

        Parameters
        ----------
        event : FileModifiedEvent
           event being cancelled
        """
        job_id = self.jobs[event.src_path]
        del self.jobs[event.src_path]
        self.scheduler.remove_job(job_id)

    def _get_trigger_time(self, transfer_time: str) -> dt:
        """Get trigger time from the job

        Parameters
        ----------
        transfer_time : str
            In HH:MM format

        Returns
        -------
        dt
            datetime object
        """
        hour = dt.strptime(transfer_time, "%H:%M").hour
        trigger_time = dt.now().replace(hour=hour, minute=0, second=0, microsecond=0)
        if (trigger_time - dt.now()).total_seconds() < 0:
            trigger_time = trigger_time + timedelta(days=1)
        return trigger_time

    def schedule_job(self, event: FileModifiedEvent, config: dict) -> None:
        """Schedule job to run

        Parameters
        ----------
        event : FileModifiedEvent
            event to trigger job
        config : dict
            configuration for the job
        """
        if config.transfer_time == "now":
            job_id = self.scheduler.add_job(run_job, args=[event, config, self.config])

        else:
            trigger = self._get_trigger_time(config.transfer_time)
            job_id = self.scheduler.add_job(
                run_job, "date", run_date=trigger, args=[event, config]
            )
        self.jobs[event.src_path] = job_id

    def on_deleted(self, event: FileModifiedEvent) -> None:
        """Event handler for file deleted event

        Parameters
        ----------
        event : FileModifiedEvent
            file deleted event

        Returns
        -------
        None
        """
        print("IN ON DELETED")
        if self.jobs.get(event.src_path, ""):
            self._remove_job(event)
        
    def on_modified(self, event: FileModifiedEvent) -> None:
        """Event handler for file modified event

        Parameters
        ----------
        event : FileModifiedEvent
            file modified event

        Returns
        -------
        None
        """
        # Check if manifest file is being modified / created
        if not "manifest" in event.src_path:
            return
        # If scheduled manifest is being modified, remove original job
        print("IN ON MODIFIED")
        if self.jobs.get(event.src_path, ""):
            self._remove_job(event)
        if self.config.run_script:
            run_script_config = self._load_run_script_manifest(event)
            self.schedule_job(event, run_script_config)
        else:
            vast_transfer_config = self._load_vast_transfer_manifest(event)
            self.schedule_job(event, vast_transfer_config)


def initiate_scheduler() -> BackgroundScheduler:
    """Starts APScheduler

    Returns
    -------
    BackgroundScheduler
        Background schedule to upload jobs
    """
    scheduler = BackgroundScheduler()
    scheduler.start()
    return scheduler


def initiate_observer(config: WatchConfig, scheduler: BackgroundScheduler) -> None:
    """Starts Wathdog observer

    Parameters
    ----------
    config : WatchConfig
        Configuration for the observer
    scheduler : BackgroundScheduler
        scheduler to run jobs
    """
    observer = Observer()
    watch_directory = config.flag_dir
    event_handler = EventHandler(scheduler, config)
    observer.schedule(event_handler, watch_directory, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(3)
    except (KeyboardInterrupt, SyntaxError, SystemExit):
        observer.stop()
        scheduler.shutdown()
    observer.join()


def main(config: dict) -> None:
    """Main function to start the scheduler and observer procs"""
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
