from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
from datetime import datetime as dt

class Scheduler:
    def __init__(self, upload_time='now'):
        self.upload_time = upload_time

    @property
    def start_scheduler(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        try:
            while True:
                sleep(3)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
    
    def run_job(self):
        pass


def submit_job()
def display(msg):
    print(msg)

scheduler = BackgroundScheduler()
job_id = scheduler.add_job(display, "interval", seconds = 3, args=["hello"])
job_id = scheduler.add_job(display, "date", run_date = (2024, 4, 9, 12, 0, 0), seconds = 3, args=["good bye"])
scheduler.start()