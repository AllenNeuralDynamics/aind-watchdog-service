"""Event handler module"""

import logging
from datetime import datetime as dt
from datetime import timedelta
from pathlib import Path
from typing import Dict

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.events import FileModifiedEvent, FileSystemEventHandler

from aind_watchdog_service.alert_bot import AlertBot
from aind_watchdog_service.models.manifest_config import ManifestConfig
from aind_watchdog_service.models.watch_config import WatchConfig
from aind_watchdog_service.run_job import RunJob


class EventHandler(FileSystemEventHandler):
    """Event handler for watchdog observer"""

    def __init__(self, scheduler: BackgroundScheduler, config: WatchConfig):
        """Initialize event handler"""
        super().__init__()
        self.scheduler = scheduler
        self.config = config
        self.jobs: Dict[str, str] = {}
        if config.webhook_url:
            self.alert = AlertBot(config.webhook_url)
        else:
            raise ValueError("Webhook URL not provided")

    def _load_manifest(self, event: FileModifiedEvent) -> ManifestConfig:
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
                config = ManifestConfig(**data)
                return config
            except Exception as e:
                logging.error("Error loading config %s", repr(e))
                self.alert.send_message("Error loading config", repr(e))
                return None

    def _remove_job(self, event: FileModifiedEvent) -> None:
        """Removes job from scheduler queue

        Parameters
        ----------
        event : FileModifiedEvent
           event to remove
        """
        # TODO: check with on_deleted method
        if self.jobs.get(event.src_path, ""):
            logging.info("Removing job_id %s", self.jobs[event.src_path].id)
            del self.jobs[event.src_path]

            self.scheduler.remove_job(self.jobs[event.src_path].id)

    def _get_trigger_time(self, transfer_time: dt) -> dt:
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
        hour = transfer_time.time().hour
        trigger_time = dt.now().replace(hour=hour, minute=0, second=0, microsecond=0)
        if (trigger_time - dt.now()).total_seconds() < 0:
            trigger_time = trigger_time + timedelta(days=1)
        return trigger_time

    def schedule_job(self, event: FileModifiedEvent, job_config: ManifestConfig) -> None:
        """Schedule job to run

        Parameters
        ----------
        event : FileModifiedEvent
            event to trigger job
        job_config : ManifestConfig
            configuration for the job
        """
        if not job_config.schedule_time:
            logging.info("Scheduling job to run now %s", event.src_path)
            run = RunJob(event, job_config, self.config)
            job_id = self.scheduler.add_job(run.run_job)

        else:
            trigger = self._get_trigger_time(job_config.schedule_time)
            logging.info("Scheduling job to run at %s %s", trigger, event.src_path)
            run = RunJob(event, job_config, self.config)
            job_id = self.scheduler.add_job(run.run_job, "date", run_date=trigger)
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
        # TODO: review this method.
        if event.src_path in self.jobs:
            logging.info("Deleting job %s", event.src_path)
            del self.jobs[event.src_path]
        if self.jobs.get(event.src_path, ""):
            self._remove_job(self.jobs[event.src_path].id)
        logging.info("Jobs in queue %s", self.scheduler.get_jobs())
        # Comments:
        # When is self._remove_job(self.jobs[event.src_path].id) called?
        # Consider using pop instead of del?
        # job_id = self.jobs.pop(event.src_path, None)
        # if job_id is not None:
        #     logging.info("Deleting job %s", event.src_path)
        #     self._remove_job(job_id)
        # logging.info("Jobs in queue %s", self.scheduler.get_jobs())

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
        if Path(event.src_path).is_dir():
            return
        if "manifest" not in event.src_path:
            return
        # If scheduled manifest is being modified, remove original job
        if (
            self.jobs.get(event.src_path, "")
            and self.jobs[event.src_path].id in self.scheduler.get_jobs()
        ):
            self._remove_job(self.jobs[event.src_path])
        logging.info("Found event file %s", event.src_path)
        transfer_config = self._load_manifest(event)
        if transfer_config:
            self.schedule_job(event, transfer_config)
