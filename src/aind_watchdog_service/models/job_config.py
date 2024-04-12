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
    platform: Platform.ONE_OF = Field(description="Platform type", title="Platform type")
    webhook_url: Optional[str] = Field(
        default=None,
        description="Teams webhook url for notification after initiation of data transfer or error reporting",
        title="Teams webhook url",
    )
    modalities: list = Field(
        description="list of ModalityFile objects containing modality names and associated files",
        title="modality files",
    )
    s3_bucket: str = Field(description="s3 endpoint", title="S3 endpoint")
    destination: str = Field(
        description="where to send data to on VAST",
        title="VAST destination and maybe S3?",
    )
    run_script: bool = Field(description="Run custom upload script", title="Run script")

    @field_validator("modalities")
    @classmethod
    def verify_modality_dirs(cls, data: list) -> list:
        for modality in data:
            if modality.lower() not in Modality._abbreviation_map:
                raise ValueError(f"{modality} not in accepted modalities")
        return data

    @field_validator("platform")
    @classmethod
    def verify_modality_dirs(cls, data: Dict[str, str]) -> Dict[str, str]:
        for key in data.keys():
            if key.lower() not in Platform._abbreviation_map:
                raise ValueError(f"{key} not in accepted modalities")
        return data
    
    @field_validator("flag_dir", "destination")
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
        description="Unique name for session data assets. Should follow AINDs schema for naming data assets",
        title="Unique name",
    )
    subject_id: int = Field(description="Subject ID", title="Subject ID")
    acquisition_datetime: str = Field(
        description="acquisition datetime in YYYY-MM-DD HH:mm:ss format",
        title="Acquisition datetime",
    )
    transfer_time: Optional[str] = Field(
        default="23:00",
        description="Transfer time to schedule copy and upload, defaults to immediately",
        title="APScheduler transfer time",
    )
    platform: Platform.ONE_OF = Field(description="Platform type", title="Platform type")

    @field_validator("transfer_time")
    @classmethod
    def verify_datetime(cls, data: str) -> str:
        try:
            datetime.strptime(data, "%H:%M").time()
        except ValueError:
            raise ValueError(f"Specify time in HH:MM format, not {data}")
        return data


class VastTransferConfig(ManifestConfig):
    """Template to verify all files that need to be uploaded"""

    s3_bucket: str = Field(description="s3 endpoint", title="S3 endpoint")
    destination: str = Field(
        description="where to send data to on VAST",
        title="VAST destination and maybe S3?",
    )
    capsule_id: Optional[str] = Field(
        description="Capsule ID of pipeline to run", title="Capsule"
    )
    modalities: Dict[Modality.ONE_OF, List[str]] = Field(
        description="list of ModalityFile objects containing modality names and associated files",
        title="modality files",
    )

    @field_validator("transfer_time")
    @classmethod
    def verify_datetime(cls, data: str) -> str:
        try:
            datetime.strptime(data, "%H:%M").time()
        except ValueError:
            raise ValueError(f"Specify time in HH:MM format, not {data}")
        return data


class RunScriptConfig(ManifestConfig):
    """Upload data directly to cloud"""

    commands: Dict[Dict[str, list]] = Field(
        description="Set of commands to run in subprocess", title="Commands"
    )
