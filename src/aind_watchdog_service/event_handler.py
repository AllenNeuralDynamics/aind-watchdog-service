"""Event handler module"""

import logging
from datetime import datetime as dt
from datetime import time, timedelta
from pathlib import Path
from typing import Dict

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from watchdog.events import FileCreatedEvent, FileSystemEventHandler

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
        self.jobs: Dict[str, Job] = {}

    def _load_manifest(self, event: FileCreatedEvent) -> ManifestConfig:
        """Instructions to transfer to VAST

        Parameters
        ----------
        event : FileCreatedEvent
           file modified event

        Returns
        -------
        dict
           manifest configuration
        """
        with open(event.src_path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
                config = ManifestConfig(**data)
            except Exception as e:
                logging.error("Error loading config %s", repr(e))
        return config

    def _get_trigger_time(self, transfer_time: time) -> dt:
        """Get trigger time from the job

        Parameters
        ----------
        transfer_time : datetime.time
            time to trigger the job
        Returns
        -------
        dt
            datetime object
        """
        _now = dt.now()
        trigger_time = dt.combine(_now.date(), transfer_time)
        trigger_time = (
            trigger_time if trigger_time > _now else trigger_time + timedelta(days=1)
        )
        logging.info("Trigger time %s", trigger_time)
        return trigger_time

    def schedule_job(self, event: FileCreatedEvent, job_config: ManifestConfig) -> None:
        """Schedule job to run

        Parameters
        ----------
        event : FileCreatedEvent
            event to trigger job
        config : dict
            configuration for the job
        """
        if not job_config.schedule_time:
            logging.info("Scheduling job to run now %s", event.src_path)
            run = RunJob(event, job_config, self.config)
            job_id = self.scheduler.add_job(
                run.run_job,
                misfire_grace_time=self.config.misfire_grace_time_s,
            )

        else:
            trigger = self._get_trigger_time(job_config.schedule_time)
            logging.info("Scheduling job to run at %s %s", trigger, event.src_path)
            run = RunJob(event, job_config, self.config)
            job_id = self.scheduler.add_job(
                run.run_job,
                "date",
                run_date=trigger,
                misfire_grace_time=self.config.misfire_grace_time_s,
            )
        self.jobs[event.src_path] = job_id

    def on_deleted(self, event: FileCreatedEvent) -> None:
        """Event handler for file deleted event

        Parameters
        ----------
        event : FileCreatedEvent
            file deleted event

        Returns
        -------
        None
        """
        if event.src_path in self.jobs:
            logging.info("Deleting job %s", event.src_path)
            self.scheduler.remove_job(self.jobs[event.src_path].id)
            del self.jobs[event.src_path]
        logging.info("Jobs in queue %s", self.scheduler.get_jobs())

    def on_created(self, event: FileCreatedEvent) -> None:
        """Event handler for file modified event

        Parameters
        ----------
        event : FileCreatedEvent
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
        if event.src_path in self.jobs:
            logging.info("Deleting job %s", event.src_path)
            self.scheduler.remove_job(self.jobs[event.src_path].id)
            del self.jobs[event.src_path]
        logging.info("Found event file %s", event.src_path)
        transfer_config = self._load_manifest(event)
        if transfer_config:
            self.schedule_job(event, transfer_config)
