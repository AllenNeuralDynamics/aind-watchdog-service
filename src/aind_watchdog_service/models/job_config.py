from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Union
from aind_data_schema.models.modalities import Modality
from aind_data_schema.models.platforms import Platform
from datetime import datetime
from pathlib import Path


class WatchConfig(BaseModel):
    """Configuration for rig"""

    flag_dir: str = Field(
        description="Directory for watchdog to poll", title="Poll directory"
    )
    schema_map: Optional[str] = Field(
        default=None,
        description="json file used for mapping",
        title="Schema map configuration",
    )
    webhook_url: Optional[str] = Field(
        default=None,
        description="Teams webhook url for user notification",
        title="Teams webhook url",
    )
    run_script: bool = Field(
        description="Run custom script for upload", title="Run script"
    )

    @field_validator("flag_dir")
    @classmethod
    def verify_directories_exist(
        cls, data: Union[Dict[str, str], str]
    ) -> Union[Dict[str, str], str]:
        if type(data) == dict:
            for k, v in data.items():
                if not Path(v).is_dir():
                    raise ValueError(f"Provide correct path for {data}")
        else:
            if not Path(data).is_dir():
                raise ValueError(f"Provide correct path for {data}")
        return data


class ManifestConfig(BaseModel):
    """Configuration for session: based on engineerings lims_scheduler_d manifest files"""

    name: str = Field(
        description="Unique name for session data assets",
        title="Unique name",
    )
    subject_id: int = Field(description="Subject ID", title="Subject ID")
    acquisition_datetime: str = Field(
        description="acquisition datetime in YYYY-MM-DD HH:mm:ss format",
        title="Acquisition datetime",
    )
    transfer_time: Optional[str] = Field(
        description="Transfer time to schedule copy and upload, defaults to immediately",
        title="APScheduler transfer time",
    )
    platform: str = Field(description="Platform type", title="Platform type")

    @field_validator("transfer_time")
    @classmethod
    def verify_datetime(cls, data: str) -> str:
        if data == "now":
            return data
        try:
            datetime.strptime(data, "%H:%M").time()
        except ValueError:
            raise ValueError(f"Specify time in HH:MM format, not {data}")
        return data

    @field_validator("platform")
    @classmethod
    def verify_platform(cls, data: str) -> str:
        if "_" in data:
            data = data.replace("_", "-")
        if data.lower() not in Platform._abbreviation_map:
            raise ValueError(f"{data} not in accepted platforms")
        return data


class VastTransferConfig(ManifestConfig):
    """Template to verify all files that need to be uploaded"""

    s3_bucket: str = Field(description="s3 endpoint", title="S3 endpoint")
    destination: str = Field(
        description="where to send data to on VAST",
        title="VAST destination and maybe S3?",
    )
    capsule_id: Optional[str] = Field(
        default=None, description="Capsule ID of pipeline to run", title="Capsule"
    )
    modalities: Dict[str, list] = Field(
        description="list of ModalityFile objects containing modality names and associated files",
        title="modality files",
    )

    @field_validator("destination")
    @classmethod
    def verify_destination(cls, data: str) -> str:
        if not Path(data).is_dir():
            try:
                Path(data).mkdir(parents=True)
            except:
                raise ValueError(f"Could not create destination directory")
        return data


class RunScriptConfig(ManifestConfig):
    """Upload data directly to cloud"""

    commands: Dict[str, list] = Field(
        description="Set of commands to run in subprocess", title="Commands"
    )
