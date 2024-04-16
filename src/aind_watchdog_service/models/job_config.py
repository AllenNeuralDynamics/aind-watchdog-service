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
        description="json file used for mapping; ignored for now until metadata mapper is implemented",
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
                    raise ValueError(f"Provide valid path for {data}")
        else:
            if not Path(data).is_dir():
                raise ValueError(f"Provide valid path for {data}")
        return data

    @field_validator("run_script")
    @classmethod
    def verify_run_script(cls, data: bool) -> bool:
        if type(data) != bool:
            raise ValueError("run_script must be a boolean")
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
    capsule_id: Optional[str] = Field(
        description="Capsule ID of pipeline to run", title="Capsule"
    )
    s3_bucket: str = Field(None, description="s3 endpoint", title="S3 endpoint")
    @field_validator("transfer_time")
    @classmethod
    def verify_datetime(cls, data: str) -> str:
        if data == "now":
            return data
        try:
            datetime.strptime(data, "%H:%M").time()
        except ValueError:
            raise ValueError(
                "Specify time in HH:MM format or use 'now' to transfer data now"
            )
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

    destination: str = Field(
        description="where to send data to on VAST",
        title="VAST destination and maybe S3?",
    )
    modalities: Dict[str, list] = Field(
        description="list of ModalityFile objects containing modality names and associated files",
        title="modality files",
    )
    schemas: list = Field(
        description="Where schema files to be uploaded are saved",
        title="Schema directory",
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

    @field_validator("modalities")
    @classmethod
    def verify_modalities(cls, data: Dict[str, list]) -> Dict[str, list]:
        for modality, files in data.items():
            if not isinstance(files, list):
                raise ValueError(f"Files for {modality} must be a list")
            for file in files:
                if not Path(file).is_file():
                    raise ValueError(f"{file} does not exist")
        return data

    @field_validator("schemas")
    @classmethod
    def verify_schemas(cls, data: list) -> list:
        for schema in data:
            if not Path(schema).is_file():
                raise ValueError(f"{schema} does not exist")
        return data
    

class RunScriptConfig(ManifestConfig):
    """Upload data directly to cloud"""

    script: Dict[str, list] = Field(
        description="Set of commands to run in subprocess", title="Commands"
    )
