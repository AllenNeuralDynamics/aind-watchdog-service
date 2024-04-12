import subprocess
from pathlib import Path
from typing import Union

from aind_watchdog_service.models.job_config import WatchConfig, RunScriptConfig, VastTransferConfig
from aind_watchdog_service.alert_bot import AlertBot
import aind_data_transfer_service


def _check_source(src_directory: Path) -> bool:
    return src_directory.is_dir()


def _check_files(src_directory: Path, files: list) -> Union[bool, list]:
    pass


def _check_schemas():
    pass


def check_files(event: str, config: WatchConfig) -> bool:
    event_src_path = Path(event.src_path)
    if not event_src_path.is_dir():
        event_src_path = event_src_path.parent
    modalities = config.modalities
    modality_src = config.modality_source


def copy_to_destination():
    pass


def trigger_transfer_service():
    pass


def run_job(event: str, config: WatchConfig) -> None:
    print("I MADE IT HERE")
    check_files(event, config)
    copy_to_destination()
    trigger_transfer_service()

def run_script(event: str, config: WatchConfig) -> None:
    pass