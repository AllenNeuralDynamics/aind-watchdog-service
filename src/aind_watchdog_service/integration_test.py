import argparse
import os
import subprocess
from pathlib import Path
from datetime import datetime as dt
from typing import Optional
import yaml

from aind_data_schema_models.platforms import Platform
from mpetk.mpeconfig import source_configuration
from mpetk.mpeconfig.python_3.mpeconfig import get_platform_paths

from aind_watchdog_service.models.manifest_config import ManifestConfig


def make_large_random_file(path: Path, size_mb: int = 50):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as file:
        file.write(os.urandom(size_mb * 1_000_000))


def make_dummy_data(folder: Path) -> tuple[dict[str, list[Path]], list[Path]]:
    """Make some files to be copied, both data (by modality) and metadata"""
    modalities = {
        "behavior": ["test.txt", "test2.txt"],
        "behavior-videos": ["test.txt", "test2.txt"],
    }
    for modality, files in modalities.items():
        files_actual = []
        for filename in files:
            path = folder / modality / filename
            if not path.exists():
                make_large_random_file(path)
            files_actual.append(str(path))
        modalities[modality] = files_actual  # replace with resolved path

    metadata_files = [folder / "session.json"]
    for path in metadata_files:
        make_large_random_file(path)

    return modalities, metadata_files


def run_test(
    test_data_dir: Optional[Path] = None,
    destination: str = r"\\allen\aind\scratch\SIPE\test_watchdog",
    transfer_endpoint: str = "http://aind-data-transfer-service-dev/api/v1/submit_jobs",
):

    watchdog_config = source_configuration(
        "aind_watchdog_service",
        send_start_log=False,
        fetch_logging_config=False,
    )

    manifest_directory = watchdog_config["flag_dir"]

    if test_data_dir is None:
        log_dir, config_dir = get_platform_paths(watchdog_config, "aind_watchdog_service")
        test_data_dir = Path(log_dir).parent / "test_data"
    test_data_dir = test_data_dir.resolve()

    # Generate some test data
    data_by_modality, metadata = make_dummy_data(test_data_dir)
    print(f"Data created at {test_data_dir}")

    now = dt.now()

    manifest = ManifestConfig(
        name="test_manifest_" + now.strftime("%Y-%m-%d_%H-%M-%S"),
        platform=Platform.MULTIPLANE_OPHYS,
        processor_full_name="Patrick Latimer",
        subject_id="614173",  # test mouse
        acquisition_datetime=now,
        # schedule_time=now
        s3_bucket="private",
        destination=destination,
        # capsule_id='',
        # mount=self.config["mount"],
        modalities=data_by_modality,
        schemas=[str(path) for path in metadata],
        project_name="Watchdog Test",
        transfer_endpoint=transfer_endpoint,
    )

    manifest_path = Path(manifest_directory) / f"{manifest.name}.yml"
    with open(manifest_path, "w") as file:
        yaml.safe_dump(
            manifest.model_dump(),
            file,
            default_flow_style=False,
            allow_unicode=True,
        )
    print(f"Manifest created at {manifest_path}")


if __name__ == "__main__":
    run_test()
