"""Job configs for VAST staging or executing a custom script"""

from datetime import datetime, time
from typing import Dict, List, Literal, Optional

from aind_data_schema_models.modalities import Modality
from aind_data_schema_models.platforms import Platform
from pydantic import BaseModel, ConfigDict, Field


class ManifestConfig(BaseModel):
    """Configuration for session: based on engineerings lims_scheduler_d manifest files"""

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
        description="acquisition datetime in YYYY-MM-DD HH:mm:ss format",
        title="Acquisition datetime",
    )
    schedule_time: Optional[time] = Field(
        default=None,
        description="Transfer time to schedule copy and upload. If None defaults to trigger the transfer immediately",  # noqa
        title="APScheduler transfer time",
    )
    platform: Literal[tuple(Platform._abbreviation_map.keys())] = Field(
        description="Platform type", title="Platform type"
    )
    capsule_id: Optional[str] = Field(
        default=None, description="Capsule ID of pipeline to run", title="Capsule"
    )
    mount: Optional[str] = Field(
        default=None, description="Mount point for pipeline run", title="Mount point"
    )
    s3_bucket: Optional[Literal["s3", "public", "private", "scratch"]] = Field(
        default=None, description="s3 endpoint", title="S3 endpoint"
    )
    project_name: str = Field(..., description="Project name", title="Project name")

    destination: Optional[str] = Field(
        default=None,
        description="where to send data to on VAST",
        title="VAST destination and maybe S3?",
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
