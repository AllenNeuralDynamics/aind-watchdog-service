from aind_watchdog_service.models import manifest_config
from aind_watchdog_service.run_job import RunJob
from aind_watchdog_service.models import watch_config
from pathlib import Path
import yaml
import time

with open(r"\\meso1acq\c\ProgramData\aind\aind-watchdog-service\watch_config.yml") as f:
    watch_config = watch_config.WatchConfig(**yaml.safe_load(f))
fp = Path(r"\\meso1acq\c\Users\svc_mesoscope\Documents\aind_watchdog_service\manifest_complete")
for file in fp.glob("manifest_*.yml"):
    if not "manifest_20240915080503.yml" in str(file):
        with open(file, "r") as f:
            manifest = manifest_config.ManifestConfig(**yaml.safe_load(f))
        run_job = RunJob(file, manifest, watch_config)
        job = run_job.trigger_transfer_service()
        print(f"File: {file}, Job status: {job}")
        time.sleep(2)
