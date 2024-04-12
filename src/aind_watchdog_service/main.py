import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileModifiedEvent
from datetime import datetime as dt
from datetime import timedelta
import os
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

from aind_watchdog_service.run_job import run_job, run_script
from aind_watchdog_service.models.job_config import WatchConfig, RunScriptConfig, VastTransferConfig


class EventHandler(PatternMatchingEventHandler):
    """Event handler for watchdog observer"""
    def __init__(self, scheduler: BackgroundScheduler, pattern: str, config: WatchConfig):
        super().__init__(patterns=[pattern])
        self.scheduler = scheduler
        self.config = config
        self.jobs = {}
    
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
            config = VastTransferConfig(**yaml.safe_load(f))
        return config
    
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
            config = RunScriptConfig(**yaml.safe_load(f))
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
        if self.jobs.get(event.src_path, ""):
            self._remove_job(event)
        if self.config.run_script:
            run_script_config = self._load_run_script_manifest(event)
            trigger = self._get_trigger_time(run_script_config.transfer_time)
            job_id = self.scheduler.add_job(run_script, "data", run_date=trigger, args=[event, run_script_config])
        else:
            vast_transfer_config = self._load_vast_transfer_manifest(event)
            trigger = self._get_trigger_time(vast_transfer_config.transfer_time)
            job_id = self.scheduler.add_job(run_job, "date", run_date=trigger, args=[event, vast_transfer_config])
        self.jobs[event.src_path] = job_id


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
    flag_file = "FINISHED"
    if config.flag_file:
        flag_file = config.flag_file
    event_handler = EventHandler(scheduler, flag_file, config)
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
