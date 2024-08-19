"""Job configs for VAST staging or executing a custom script"""

from datetime import datetime, time
from typing import Dict, List, Literal, Optional, Self

from aind_data_schema_models.modalities import Modality
from aind_data_schema_models.platforms import Platform
from aind_data_transfer_models.core import BucketType
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ManifestConfig(BaseModel):
    """Job configs for data transfer to VAST and executing a custom script"""

    model_config = ConfigDict(extra="forbid")
    name: str = Field(
        ...,
        description="Unique name for session data assets",
        title="Unique name",
    )
    processor_full_name: str = Field(
        ..., description="User who processed the data", title="Processor name"
    )
    subject_id: int = Field(..., description="Subject ID", title="Subject ID")
    acquisition_datetime: datetime = Field(
        description="Acquisition datetime",
        title="Acquisition datetime",
    )
    schedule_time: Optional[time] = Field(
        default=None,
        description="Transfer time to schedule copy and upload. If None defaults to trigger the transfer immediately",  # noqa
        title="APScheduler transfer time",
    )
    force_cloud_sync: bool = Field(
        default=False,
        description="Overwrite data in AWS",
        title="Force cloud sync",
    )
    transfer_endpoint: str = Field(
        default="http://aind-data-transfer-service/api/v1/submit_jobs",
        description="Transfer endpoint for data transfer",
        title="Transfer endpoint",
    )
    platform: Literal[tuple(Platform._abbreviation_map.keys())] = Field(
        description="Platform type", title="Platform type"
    )
    capsule_id: Optional[str] = Field(
        ..., description="Capsule ID of pipeline to run", title="Capsule"
    )
    mount: Optional[str] = Field(
        ..., description="Mount point for pipeline run", title="Mount point"
    )
    s3_bucket: BucketType = Field(
        default=BucketType.PRIVATE, description="s3 endpoint", title="S3 endpoint"
    )
    project_name: str = Field(..., description="Project name", title="Project name")
    destination: str = Field(
        ...,
        description="Remote directory on VAST where to copy the data to.",
        title="Destination directory",
        examples=[r"\\allen\aind\scratch\test"],
    )
    modalities: Dict[Literal[tuple(Modality._abbreviation_map.keys())], List[str]] = (
        Field(
            default={},
            description="list of ModalityFile objects containing modality names and associated files or directories",  # noqa
            title="modality files",
        )
    )
    schemas: List[str] = Field(
        default=[],
        description="Where schema files to be uploaded are saved",
        title="Schema directory",
    )
    script: Dict[str, List[str]] = Field(
        default={}, description="Set of commands to run in subprocess.", title="Commands"
    )

    @field_validator("schedule_time", mode="before")
    @classmethod
    def normalized_scheduled_time(cls, value) -> Optional[time]:
        """Normalize scheduled time"""
        if value is None:
            return value
        else:
            if isinstance(value, datetime):
                return value.time()
            elif isinstance(value, str):
                return datetime.strptime(value, "%H:%M:%S").time()
            elif isinstance(value, time):
                return value
            else:
                raise ValueError("Invalid time format")

    @model_validator(mode="after")
    def validate_capsule(self) -> Self:
        """Validate capsule and mount"""
        if (self.capsule_id is None) ^ (self.mount is None):
            raise ValueError(
                "Both capsule and mount must be provided, or must both be None"
            )
        return self
