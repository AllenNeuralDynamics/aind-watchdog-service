import subprocess
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

from aind_watchdog_service.models.job_config import WatchConfig
from aind_watchdog_service.alert_bot import AlertBot
import aind_data_transfer_service


def check_files(event: str, modality_src: dict) -> bool:
    pass


def copy_to_destination():
    pass


def trigger_transfer_service():
    pass


def run_job(event: str, config: WatchConfig) -> None:
    check_files()
    copy_to_destination()
    trigger_transfer_service()