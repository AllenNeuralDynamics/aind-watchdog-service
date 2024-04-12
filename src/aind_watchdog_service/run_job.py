import subprocess
from pathlib import Path
from typing import Union
from watchdog.events import FileModifiedEvent
import platform
import os

from aind_watchdog_service.models.job_config import (
    WatchConfig,
    RunScriptConfig,
    VastTransferConfig,
)
from aind_watchdog_service.alert_bot import AlertBot
from aind_data_transfer_service.configs.job_configs import ModalityConfigs, BasicUploadJobConfigs


if platform.system() == "Windows":
    PLATFORM = "windows"
else:
    PLATFORM = "linux"

def _check_schemas():
    pass

def copy_to_vast(
        vast_config: VastTransferConfig, config: WatchConfig
) -> bool:
    parent_directory = vast_config.name
    destination = vast_config.destination
    modalities = vast_config.modalities
    for modality in modalities.keys():
        destination_directory = os.path.join(destination, parent_directory, modality)
        os.makedirs(destination_directory, exist_ok=True)
        for file in modalities[modality]:
            if os.path.isfile(file):
                if platform == "windows":
                    transfer = subprocess_windows(file, destination_directory)
                else:
                    transfer = subprocess_linux(file, destination_directory)
                if not transfer:
                    alert_message = AlertBot(config.webhook_url)
                    alert_message.send_message("Error copying files", file)

                    return False
            else:
                alert_message = AlertBot(config.webhook_url)
                alert_message.send_message("File not found", file)

                return False
        return True

def subprocess_linux(src: str, dest: str) -> bool:
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
    if os.path.isdir(src):
        run = subprocess.run(["cp", "-r", src, dest], check=False)
    else:
        run = subprocess.run(["cp", src, dest], check=False)
    if run.returncode != 1:
        return False
    return True

def subprocess_windows(src: str, dest: str) -> bool:
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
    if os.path.isdir(src):
        run = subprocess.run(
            ["robocopy", src, dest, "/mt", "/z", "/e", "/r:5"], check=False
        )
    else:
        run = subprocess.run(
            ["robocopy", os.path.dirname(src), dest, os.path.basename(src), "/mt", "/z", "/r:5"], check=False
        )
    if run.returncode != 1:
        return False
    return True

def trigger_transfer_service(vast_config: VastTransferConfig, watch_config: WatchConfig) -> None:
    upload_job_configs = BasicUploadJobConfigs(
        s3_bucket=vast_config.s3_bucket,
        platform=vast_config.platform,
        subject_id=vast_config.subject_id,
        acquisition_datetime=vast_config.acquisition_datetime,
        modalities=[k for k in vast_config.modalities.keys()],
        metadata_dir="Come back to this", # TODO: Add metadata directory
    )


def run_job(
    event: FileModifiedEvent, vast_config: VastTransferConfig, watch_config: WatchConfig
) -> None:
    transfer = copy_to_vast(vast_config, watch_config)
    if not transfer:
        alert = AlertBot(watch_config.webhook_url)
        alert.send_message("Error copying files", vast_config.name)
    trigger_transfer_service(vast_config,watch_config)


def run_script(event: str, config: WatchConfig) -> None:
    pass
