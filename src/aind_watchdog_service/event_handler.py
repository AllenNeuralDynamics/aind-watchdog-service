"""Event handler module"""

import yaml
from datetime import datetime as dt
from datetime import timedelta
from typing import Union
from pathlib import Path
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from aind_watchdog_service.models.job_configs import (
    VastTransferConfig,
    RunScriptConfig,
)
from aind_watchdog_service.models.watch_config import WatchConfig
from aind_watchdog_service.alert_bot import AlertBot
from aind_watchdog_service.run_job import RunJob


class EventHandler(FileSystemEventHandler):
    """Event handler for watchdog observer"""

    def __init__(self, scheduler: BackgroundScheduler, config: WatchConfig):
        """Initialize event handler"""
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
                logging.error("Error loading config %s", repr(e))
                self.alert.send_message("Error loading config", repr(e))
                return None

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
        if self.jobs.get(event.src_path, ""):
            logging.info("Removing job_id %s", self.jobs[event.src_path].id)
            del self.jobs[event.src_path]

            self.scheduler.remove_job(self.jobs[event.src_path].id)

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

    def schedule_job(
        self,
        event: FileModifiedEvent,
        job_config: Union[VastTransferConfig, RunScriptConfig],
    ) -> None:
        """Schedule job to run

        Parameters
        ----------
        event : FileModifiedEvent
            event to trigger job
        config : dict
            configuration for the job
        """
        if job_config.transfer_time == "now":
            logging.info("Schduling job to run now %s", event.src_path)
            run = RunJob(event, job_config, self.config)
            job_id = self.scheduler.add_job(run.run_job)

        else:
            trigger = self._get_trigger_time(job_config.transfer_time)
            logging.info("Schduling job to run at %s %s", trigger, event.src_path)
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
        if event.src_path in self.jobs:
            logging.info("Deleting job %s", event.src_path)
            del self.jobs[event.src_path]
        if self.jobs.get(event.src_path, ""):
            self._remove_job(self.jobs[event.src_path].id)
        logging.info("Jobs in queue %s", self.scheduler.get_jobs())

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

        if self.config.run_script:
            logging.info("Found job, executing custom script for %s", event.src_path)
            run_script_config = self._load_run_script_manifest(event)
            if run_script_config:
                self.schedule_job(event, run_script_config)
        else:
            logging.info("Found job, executing vast transfer for %s", event.src_path)
            vast_transfer_config = self._load_vast_transfer_manifest(event)
            if vast_transfer_config:
                self.schedule_job(event, vast_transfer_config)
