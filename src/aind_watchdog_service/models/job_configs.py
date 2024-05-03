"""Job configs for VAST staging or executing a custom script"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
from aind_data_schema.models.platforms import Platform
from datetime import datetime


class ManifestConfig(BaseModel):
    """Configuration for session: based on engineerings lims_scheduler_d manifest files"""

    name: str = (
        Field(
            description="Unique name for session data assets",
            title="Unique name",
        ),
    )
    processor_full_name: str = Field(
        description="User who processed the data", title="Processor name"
    )
    subject_id: int = Field(description="Subject ID", title="Subject ID")
    acquisition_datetime: datetime = Field(
        description="acquisition datetime in YYYY-MM-DD HH:mm:ss format",
        title="Acquisition datetime",
    )
    transfer_time: Optional[str] = Field(
        default="now",
        description="Transfer time to schedule copy and upload, defaults to immediately",
        title="APScheduler transfer time",
    )
    platform: str = Field(description="Platform type", title="Platform type")
    capsule_id: Optional[str] = Field(
        description="Capsule ID of pipeline to run", title="Capsule"
    )
    s3_bucket: str = (
        Field(default=None, description="s3 endpoint", title="S3 endpoint"),
    )
    project_name: str = Field(description="Project name", title="Project name")

    @field_validator("transfer_time")
    @classmethod
    def verify_datetime(cls, data: str) -> str:
        """Verify that datetime is in correct format"""
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
        """Verify that platform is in accepted platforms list"""
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
        description="list of ModalityFile objects containing modality names and associated files",  # noqa
        title="modality files",
    )
    schemas: list = Field(
        description="Where schema files to be uploaded are saved",
        title="Schema directory",
    )


class RunScriptConfig(ManifestConfig):
    """Upload data directly to cloud"""

    script: Dict[str, list] = Field(
        description="Set of commands to run in subprocess", title="Commands"
    )
