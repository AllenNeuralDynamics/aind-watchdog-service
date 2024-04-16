import subprocess
from watchdog.events import FileModifiedEvent
import platform
import os
import json
import requests
from pathlib import Path
from typing import Union
from aind_data_transfer_service.configs.job_configs import (
    BasicUploadJobConfigs,
    ModalityConfigs,
)

from aind_watchdog_service.models.job_config import (
    WatchConfig,
    RunScriptConfig,
    VastTransferConfig,
)
from aind_watchdog_service.alert_bot import AlertBot


if platform.system() == "Windows":
    PLATFORM = "windows"
else:
    PLATFORM = "linux"


def copy_to_vast(vast_config: VastTransferConfig, alert=AlertBot) -> bool:
    """Determine platform and copy files to VAST

    Parameters
    ----------
    vast_config : VastTransferConfig
        configuration for VAST transfer
    alert : AlertBot
        Message service

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
                    transfer = execute_windows_command(file, destination_directory)
                else:
                    transfer = execute_linux_command(file, destination_directory)
                if not transfer:
                    alert.send_message("Error copying files", file)

                    return False
            else:
                alert.send_message("File not found", file)

                return False
        return True


def run_subprocess(cmd: list) -> subprocess.CompletedProcess:
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
    return subprocess.run(
        cmd, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE
    )


def execute_windows_command(src: str, dest: str) -> bool:
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
    # /mt: multi-threaded, /z: restartable mode,
    # /e: copy subdirectories (includes empty subdirs), /r:5: retry 5 times
    if not Path(src).exists():
        return False
    if Path(src).is_dir():
        run = run_subprocess(
            ["robocopy", src, dest, "/mt", "/z", "/e", "/r:5"],
        )
    else:
        run = run_subprocess(
            [
                "robocopy",
                Path(src).parent.name,
                dest,
                Path(src).name,
                "/mt",
                "/z",
                "/r:5",
            ]
        )
    if run.returncode != 0:
        return False
    return True


def execute_linux_command(src: str, dest: str) -> bool:
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
        run = run_subprocess(["rsync", "-r", "-t", src, dest])
    else:
        run = run_subprocess(["rsync", "-t", src, dest])
    if run.returncode != 0:
        return False
    return True


def trigger_transfer_service(
    config: Union[VastTransferConfig, RunScriptConfig], alert: AlertBot
) -> None:
    """Triggers aind-data-transfer-service

    Parameters
    ----------
    config : VastTransferConfig
        VAST configuration
    alert : AlertBot
        Teams message service
    """
    modality_configs = []
    for modality in config.modalities.keys():
        m = ModalityConfigs(
            source=os.path.join(
                config.destination, config.name, config.modalities[modality]
            )
        )
        modality_configs.append(m)
    if not config.schema_directory:
        config.schema_directory = os.path.join(config.destination, config.name)
    upload_job_configs = BasicUploadJobConfigs(
        s3_bucket=config.s3_bucket,
        platform=config.platform,
        subject_id=config.subject_id,
        acquisition_datetime=config.acquisition_datetime,
        modalities=modality_configs,
        metadata_dir=config.schema_directory,
        model_config={"codeocean-process-capsule-id": config.capsule_id},
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
        alert.send_message("Error submitting job", config.name)
    else:
        alert.send_message("Job submitted", config.name)


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
    alert = AlertBot(watch_config.webhook_url)
    alert.send_message("Running job", f"Triggering event from {event.src_path}")
    transfer = copy_to_vast(vast_config, alert)
    if transfer:
        trigger_transfer_service(vast_config, alert)


def run_script(event: str, config: RunScriptConfig, watch_config: WatchConfig) -> None:
    """Run a custom script on file modification

    Parameters
    ----------
    event : str
        modified event file
    config : WatchConfig
        Watchdog configuration
    """
    alert = AlertBot(watch_config.webhook_url)
    alert.send_message("Running job", f"Triggering event from {event.src_path}")
    for command in config.script:
        run = subprocess.run(
            config.script[command],
            check=False,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        if run.returncode != 1:
            alert.send_message(
                "Error running script", f"Could not execute {command} for {config.name}"
            )
            return
        else:
            alert.send_message("Script executed", f"Ran {command} for {config.name}")

    trigger_transfer_service(config, alert)
