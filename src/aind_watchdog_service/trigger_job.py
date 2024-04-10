import subprocess
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

from aind_watchdog_service.models.job_config import WatchConfig
from aind_watchdog_service import alert_bot
import aind_data_transfer_service

def check_files():
    pass

def copy_to_destination():
    pass

def trigger_transfer_service():
    pass

def run_job(scheduler: BackgroundScheduler, config: WatchConfig) -> None:
    check_files()
    copy_to_destination()
    trigger_transfer_service()
# from time import sleep
# from apscheduler.schedulers.background import BackgroundScheduler
# # from apscheduler.executors.pool import ThreadPoolExecutor
# # from datetime import datetime as dt
# # import platform
# # from pathlib import Path

# def display(msg):
#     print(msg)


# # job_id = scheduler.add_job(display, "interval", seconds = 3, args=["hello"])
# # job_id = scheduler.add_job(display, "date", run_date = (2024, 4, 9, 12, 0, 0), seconds = 3, args=["good bye"])


# def main():
#     scheduler = BackgroundScheduler()
#     try:
#         while True:
#             scheduler.start()
#     except (KeyboardInterrupt,SystemError):
#         scheduler.shutdown()


# if __name__ == "__main__":
#     main()