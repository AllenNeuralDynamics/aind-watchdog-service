"""Event handler module"""

import logging
import time
from datetime import datetime as dt
from datetime import time as t
from datetime import timedelta
from pathlib import Path
from typing import Dict

import yaml
from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
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
        self._startup_manifest_check()

    def _startup_manifest_check(self) -> None:
        """ " Check for manifests to process in the manifest directory on startup"""
        manifest_dir = Path(self.config.flag_dir).glob("*manifest*.*")
        for manifest in manifest_dir:
            transfer_config = self._load_manifest(manifest)
            if transfer_config:
                self.schedule_job(manifest, transfer_config)

    def _load_manifest(self, src_path: str) -> ManifestConfig:
        """Instructions to transfer to VAST

        Parameters
        ----------
        src_path : str
            manifest file path to trigger

        Returns
        -------
        dict
           manifest configuration
        """
        logging.info("Loading manifest %s", src_path)
        with open(src_path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
                logging.info("Loaded manifest %s", data)
                config = ManifestConfig(**data)
            except Exception as e:
                logging.error("Error loading config %s", repr(e))
        return config

    def _get_trigger_time(self, transfer_time: t) -> dt:
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

    def schedule_job(self, src_path: str, job_config: ManifestConfig) -> None:
        """Schedule job to run

        Parameters
        ----------
        src_path : str
            manifest file path to trigger
        config : dict
            configuration for the job
        """
        if not job_config.schedule_time:
            logging.info("Scheduling job to run now %s", src_path)
            run = RunJob(src_path, job_config, self.config)
            job_id = self.scheduler.add_job(run.run_job)

        else:
            trigger = self._get_trigger_time(job_config.schedule_time)
            logging.info("Scheduling job to run at %s %s", trigger, src_path)
            run = RunJob(src_path, job_config, self.config)
            job_id = self.scheduler.add_job(run.run_job, "date", run_date=trigger)
        self.jobs[src_path] = job_id

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
        time.sleep(20)  # Wait for file to be written
        transfer_config = self._load_manifest(event.src_path)
        if transfer_config:
            self.schedule_job(event.src_path, transfer_config)
