import subprocess
from watchdog.events import FileModifiedEvent
import platform
import os
import json
import requests

from aind_watchdog_service.models.job_config import (
    WatchConfig,
    RunScriptConfig,
    VastTransferConfig,
)
from aind_watchdog_service.alert_bot import AlertBot
from aind_data_transfer_service.configs.job_configs import (
    ModalityConfigs,
    BasicUploadJobConfigs,
)


if platform.system() == "Windows":
    PLATFORM = "windows"
else:
    PLATFORM = "linux"


def copy_to_vast(vast_config: VastTransferConfig, config: WatchConfig) -> bool:
    """Determine platform and copy files to VAST

    Parameters
    ----------
    vast_config : VastTransferConfig
        configuration for VAST transfer
    config : WatchConfig
        Configuration for the watch service

    Returns
    -------
    bool
        status of the copy operation
    """
    parent_directory = vast_config.name
    destination = vast_config.destination
    modalities = vast_config.modalities
    for modality in modalities.keys():
        destination_directory = os.path.join(destination, parent_directory, modality)
        os.makedirs(destination_directory, exist_ok=True)
        for file in modalities[modality]:
            if os.path.isfile(file):
                if PLATFORM == "windows":
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
        run = subprocess.run(
            ["rsync", "-r", src, dest],
            check=False,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    else:
        run = subprocess.run(
            ["rsync", src, dest],
            check=False,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
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
            ["robocopy", src, dest, "/mt", "/z", "/e", "/r:5"],
            check=False,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    else:
        run = subprocess.run(
            [
                "robocopy",
                os.path.dirname(src),
                dest,
                os.path.basename(src),
                "/mt",
                "/z",
                "/r:5",
            ],
            check=False,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    if run.returncode != 1:
        return False
    return True


def trigger_transfer_service(vast_config: VastTransferConfig, alert: AlertBot) -> None:
    """Triggers aind-data-transfer-service

    Parameters
    ----------
    vast_config : VastTransferConfig
        VAST configuration
    alert : AlertBot
        Teams messenger
    """
    upload_job_configs = BasicUploadJobConfigs(
        s3_bucket=vast_config.s3_bucket,
        platform=vast_config.platform,
        subject_id=vast_config.subject_id,
        acquisition_datetime=vast_config.acquisition_datetime,
        modalities=[k for k in vast_config.modalities.keys()],
        metadata_dir="Come back to this",  # TODO: Add metadata directory
        model_config={"codeocean-process-capsule-id": vast_config.capsule_id},
    )

    # From aind-data-transfer-service README
    hpc_settings = json.dumps({})
    upload_job_settings = upload_job_configs.model_dump_json()
    script = ""

    hpc_job = {
        "upload_job_settings": upload_job_settings,
        "hpc_settings": hpc_settings,
        "script": script,
    }

    hpc_jobs = [hpc_job]

    post_request_content = {"jobs": hpc_jobs}
    submit_job_response = requests.post(
        url="http://aind-data-transfer-service/api/submit_hpc_jobs",
        json=post_request_content,
    )
    if submit_job_response.status_code != 200:
        alert.send_message("Error submitting job", vast_config.name)
    else:
        alert.send_message("Job submitted", vast_config.name)


def run_job(
    event: FileModifiedEvent, vast_config: VastTransferConfig, watch_config: WatchConfig
) -> None:
    """Triggers the vast transfer service

    Parameters
    ----------
    event : FileModifiedEvent
        modified event file
    vast_config : VastTransferConfig
        VAST configuration
    watch_config : WatchConfig
        Watchdog configuration
    """
    transfer = copy_to_vast(vast_config, watch_config)
    if not transfer:
        alert = AlertBot(watch_config.webhook_url)
        alert.send_message("Error copying files", vast_config.name)
    trigger_transfer_service(vast_config, alert)


def run_script(event: str, config: WatchConfig) -> None:
    """Run a custom script on file modification

    Parameters
    ----------
    event : str
        modified event file
    config : WatchConfig
        Watchdog configuration
    """
    pass
