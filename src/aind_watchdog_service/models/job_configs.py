"""Job configs for VAST staging or executing a custom script"""

from datetime import datetime
from typing import Dict, Optional, List

from aind_data_schema_models.platforms import Platform
from aind_data_schema_models.modalities import Modality
from pydantic import BaseModel, Field


class ManifestConfig(BaseModel):
    """Configuration for session: based on engineerings lims_scheduler_d manifest files"""

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
        description="acquisition datetime in YYYY-MM-DD HH:mm:ss format",
        title="Acquisition datetime",
    )
    schedule_time: Optional[datetime.time] = Field(
        default=None,
        description="Transfer time to schedule copy and upload. If None defaults to trigger the transfer immediately", # noqa
        title="APScheduler transfer time",
    )
    platform: Platform = Field(description="Platform type", title="Platform type")
    capsule_id: Optional[str] = Field(
        ..., description="Capsule ID of pipeline to run", title="Capsule"
    )
    s3_bucket: Optional[str] = Field(
        default=None, description="s3 endpoint", title="S3 endpoint"
    )
    project_name: str = Field(..., description="Project name", title="Project name")

    destination: str = Field(
        ...,
        description="where to send data to on VAST",
        title="VAST destination and maybe S3?",
    )
    modalities: Dict[Modality, List[str]] = Field(
        default={},
        description="list of ModalityFile objects containing modality names and associated files or directories",  # noqa
        title="modality files",
    )
    schemas: Optional[List[str]] = Field(
        default=[],
        description="Where schema files to be uploaded are saved",
        title="Schema directory",
    )
    script: Dict[str, list[str]] = Field(
        default={}, description="Set of commands to run in subprocess.", title="Commands"
    )

