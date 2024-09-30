""" Module to run jobs on file modification"""

import json
import logging
import os
import platform
import subprocess
from pathlib import Path, PurePosixPath
from typing import Optional

import requests
from aind_data_transfer_models.core import (
    BasicUploadJobConfigs,
    ModalityConfigs,
    SubmitJobRequest,
)

from aind_watchdog_service.alert_bot import AlertBot
from aind_watchdog_service.models.manifest_config import ManifestConfig
from aind_watchdog_service.models.watch_config import WatchConfig

if platform.system() == "Windows":
    PLATFORM = "windows"
else:
    PLATFORM = "linux"


class RunJob:
    """Run job class to stage files on VAST or run a custom script
    and trigger aind-data-transfer-service
    """

    def __init__(
        self,
        src_path: str,
        config: ManifestConfig,
        watch_config: WatchConfig,
    ):
        """initialize RunJob class"""
        self.src_path = src_path
        self.config = config
        self.watch_config = watch_config

    def _send_alert(self, title: str, message: Optional[str] = None) -> None:
        """wrapper for AlertBot configured

        Parameters
        ----------
        title : str
            message to send
        send : bool
            send to Teams
        message: str
            Message to go in Teams card
        """
        if self.watch_config.webhook_url:
            alert_bot = AlertBot(self.watch_config.webhook_url)
            alert_bot.send_message(title, message)

    def copy_to_vast(self) -> bool:
        """Determine platform and copy files to VAST

        Returns
        -------
        bool
            status of the copy operation
        """
        parent_directory = self.config.name
        destination = self.config.destination
        modalities = self.config.modalities
        for modality in modalities.keys():
            destination_directory = Path(destination) / parent_directory / modality
            if not destination_directory.is_dir():
                destination_directory.mkdir(parents=True)
            for file in modalities[modality]:
                if Path(file).exists():
                    if PLATFORM == "windows":
                        transfer = self.execute_windows_command(
                            file, destination_directory
                        )
                    else:
                        transfer = self.execute_linux_command(file, destination_directory)
                    if not transfer:
                        logging.error("Error copying files %s", file)
                        self._send_alert("Error copying files", str(file))
                        return False
                else:
                    logging.error("File not found %s", file)
                    self._send_alert("File not found", file)
                    return False
        for schema in self.config.schemas:
            destination_directory = os.path.join(destination, parent_directory)
            if PLATFORM == "windows":
                transfer = self.execute_windows_command(schema, destination_directory)
            else:
                transfer = self.execute_linux_command(schema, destination_directory)
            if not transfer:
                logging.error("Error copying schema %s", schema)
                self._send_alert("Error copying schema", schema)
                return False
        return True

    def run_subprocess(self, cmd: list) -> subprocess.CompletedProcess:
        """subprocess run command

        Parameters
        ----------
        cmd : list
            command to execute

        Returns
        -------
        subprocess.CompletedProcess
            subprocess completed process
        """
        logging.info("Executing command: %s", cmd)
        subproc = subprocess.run(
            cmd, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        return subproc

    def execute_windows_command(self, src: str, dest: str) -> bool:
        """copy files using windows robocopy command

        Parameters
        ----------
        src : str
            source file or directory
        dest : str
            destination directory

        Returns
        -------
        bool
            True if copy was successful, False otherwise
        """
        # Robocopy used over xcopy for better performance
        # /j: unbuffered I/O (to speed up copy)
        # /e: copy subdirectories (includes empty subdirs), /r:5: retry 5 times
        if not Path(src).exists():
            return False
        if Path(src).is_dir():
            run = self.run_subprocess(
                ["robocopy", src, dest, "/z", "/e", "/j", "/r:5"],
            )
        else:
            run = self.run_subprocess(
                [
                    "robocopy",
                    str(Path(src).parent),
                    dest,
                    Path(src).name,
                    "/j",
                    "/r:5",
                ]
            )
        # Robocopy return code documenttion:
        # https://learn.microsoft.com/en-us/troubleshoot/windows-server/backup-and-storage/return-codes-used-robocopy-utility # noqa
        if run.returncode > 7:
            return False
        return True

    def execute_linux_command(self, src: str, dest: str) -> bool:
        """copy files using linux cp command

        Parameters
        ----------
        src : str
            source file or directory
        dest : str
            destination directory

        Returns
        -------
        bool
            True if copy was successful, False otherwise
        """
        # Rsync used over cp for better performance
        # -r: recursive, -t: preserve modification times
        if not Path(src).exists():
            return False
        if Path(src).is_dir():
            run = self.run_subprocess(["rsync", "-r", "-t", src, dest])
        else:
            run = self.run_subprocess(["rsync", "-t", src, dest])
        if run.returncode != 0:
            return False
        return True

    def trigger_transfer_service(self) -> bool:
        """Triggers aind-data-transfer-service"""
        modality_configs = []
        for modality in self.config.modalities.keys():
            m = ModalityConfigs(
                source=PurePosixPath(self.config.destination)
                / self.config.name
                / modality,
                modality=modality,
            )
            modality_configs.append(m)

        upload_job_configs = BasicUploadJobConfigs(
            s3_bucket=self.config.s3_bucket,
            platform=self.config.platform,
            subject_id=str(self.config.subject_id),
            acq_datetime=self.config.acquisition_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            modalities=modality_configs,
            metadata_dir=PurePosixPath(self.config.destination) / self.config.name,
            process_capsule_id=self.config.capsule_id,
            project_name=self.config.project_name,
            input_data_mount=self.config.mount,
            force_cloud_sync=self.config.force_cloud_sync,
        )
        logging.info("Submitting job to aind-data-transfer-service")
        submit_request = SubmitJobRequest(upload_jobs=[upload_job_configs])
        post_request_content = json.loads(submit_request.model_dump_json(round_trip=True))
        submit_job_response = requests.post(
            url=self.config.transfer_endpoint, json=post_request_content, timeout=5
        )

        if submit_job_response.status_code == 200:
            return True
        else:
            return False

    def move_manifest_to_archive(self) -> None:
        """Move manifest file to archive"""
        archive = self.watch_config.manifest_complete
        if PLATFORM == "windows":
            copy_file = self.execute_windows_command(self.src_path, archive)
            if not copy_file:
                logging.error("Error copying manifest file %s", self.src_path)
                self._send_alert(
                    "Error copying manifest file",
                    self.src_path,
                )
                return
            os.remove(self.src_path)
        else:
            self.run_subprocess(["mv", self.src_path, archive])

    def run_job(self) -> None:
        """Triggers the vast transfer service

        Parameters
        ----------
        event : FileCreatedEvent
            modified event file
        """
        logging.info("Running job for %s", self.src_path)
        self._send_alert("Running job", self.src_path)
        if self.config.script:
            for command in self.config.script:
                logging.info("Found job, executing custom script for %s", self.src_path)
                run = subprocess.run(
                    self.config.script[command],
                )
                if run.returncode != 0:
                    logging.error("Error running script %s", command)
                    self._send_alert(
                        "Error running script",
                        f"Could not execute {command} for {self.config.name}",
                    )
                    return
                else:
                    self._send_alert(
                        "Script executed",
                        f"Ran {command} for {self.config.name}",
                    )

        else:
            transfer = self.copy_to_vast()
            if not transfer:
                self._send_alert(
                    "Could not copy data to destination",
                    self.src_path,
                )
                return
        logging.info("Data copied to VAST for %s", self.src_path)
        if not self.trigger_transfer_service():
            logging.error(
                "Could not trigger aind-data-transfer-service for %s", self.src_path
            )
            self._send_alert(
                "Could not trigger aind-data-transfer-service",
                self.src_path,
            )
            return
        self._send_alert("Job complete", self.src_path)
        logging.info("Job complete for %s", self.src_path)
        self.move_manifest_to_archive()
