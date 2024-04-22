import subprocess
from watchdog.events import FileModifiedEvent
import platform
import os
import json
import requests
from pathlib import Path, PurePosixPath
from typing import Union
from pprint import pprint

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
    for schema in vast_config.schemas:
        destination_directory = os.path.join(destination, parent_directory)
        if PLATFORM == "windows":
            transfer = execute_windows_command(schema, destination_directory)
        else:
            transfer = execute_linux_command(schema, destination_directory)
        if not transfer:
            alert.send_message("Error copying schema", schema)
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
    print(f"Executing command: {cmd}")
    subproc = subprocess.run(
        cmd, check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE
    )
    pprint(subproc.stdout)
    return subproc


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
            ["robocopy", src, dest, "/z", "/e", "/r:5"],
        )
    else:
        run = run_subprocess(
            [
                "robocopy",
                str(Path(src).parent),
                dest,
                Path(src).name,
                "/z",
                "/r:5",
            ]
        )
    # Robocopy return code documenttion:
    # https://learn.microsoft.com/en-us/troubleshoot/windows-server/backup-and-storage/return-codes-used-robocopy-utility
    if run.returncode > 7:
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


def trigger_transfer_service(config: Union[VastTransferConfig, RunScriptConfig]) -> None:
    """Triggers aind-data-transfer-service

    Parameters
    ----------
    config : VastTransferConfig
        VAST configuration
    """
    modality_configs = []
    for modality in config.modalities.keys():
        m = ModalityConfigs(
            source=PurePosixPath(config.destination) / config.name / modality,
            modality=modality,
        )
        modality_configs.append(m)
    upload_job_configs = BasicUploadJobConfigs(
        s3_bucket=config.s3_bucket,
        platform=config.platform,
        subject_id=str(config.subject_id),
        acq_datetime=config.acquisition_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        modalities=modality_configs,
        metadata_dir=PurePosixPath(config.destination) / config.name,
        # model_config=json.dumps({"codeocean-process-capsule-id":config.capsule_id})
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
    print(submit_job_response.json())
    if submit_job_response.status_code == 200:
        return True
    else:
        return False


def move_manifest_to_archive(src_path: str, archive: str) -> None:
    """Move manifest file to archive

    Parameters
    ----------
    src_path : str
        source path
    archive : str
        archive path
    """
    if PLATFORM == "windows":
        run_subprocess(
            [
                "robocopy",
                "/mov",
                os.path.dirname(src_path),
                archive,
                os.path.basename(src_path),
            ]
        )
    else:
        run_subprocess(["mv", src_path, archive])


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
    print("I MADE IT TO RUN JOB")
    alert = AlertBot(watch_config.webhook_url)
    alert.send_message("Running job", event.src_path)
    transfer = copy_to_vast(vast_config, alert)
    if not transfer:
        alert.send_message("Could not copy data to destination", event.src_path)
        return
    if not trigger_transfer_service(vast_config):
        alert.send_message("Could not trigger aind-data-transfer-service", event.src_path)
        return
    alert.send_message("Job complete", event.src_path)
    move_manifest_to_archive(event.src_path, watch_config.manifest_complete)


def run_script(
    event: FileModifiedEvent, config: RunScriptConfig, watch_config: WatchConfig
) -> None:
    """Run a custom script on file modification

    Parameters
    ----------
    event : FileModifiedEvent
        modified event file
    config : WatchConfig
        Watchdog configuration
    """
    alert = AlertBot(watch_config.webhook_url)
    alert.send_message("Running job", event.src_path)
    for command in config.script:
        run = subprocess.run(
            config.script[command],
        )
        if run.returncode != 0:
            alert.send_message(
                "Error running script", f"Could not execute {command} for {config.name}"
            )
            return
        else:
            alert.send_message("Script executed", f"Ran {command} for {config.name}")

    if not trigger_transfer_service(config):
        alert.send_message("Could not trigger aind-data-transfer-service", event.src_path)
        return
    alert.send_message("Job complete", event.src_path)
    move_manifest_to_archive(event.src_path, watch_config.manifest_complete)
