"""Job configs for VAST staging or executing a custom script"""

from datetime import datetime
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
    schedule_time: Optional[datetime] = Field(
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

    destination_root: Optional[str] = Field(
        default="s3://aind-stage/",
        description="network path to VAST",
        title="VAST destination",
    )
    destination_subdir: Optional[str] = Field(
        default="",
        description="subdirectory on VAST",
        title="VAST subdirectory",
    )
    # numworkers: Optional[int] = Field(
    #     default=64,
    #     description="Number of workers to use for transfer",
    #     title="Number of workers",
    # )
    modalities: Dict[
        Literal[tuple(Modality._abbreviation_map.keys())], List[str]
    ] = Field(
        default={},
        description="list of ModalityFile objects containing modality names and associated files or directories",  # noqa
        title="modality files",
    )
    schemas: List[str] = Field(
        default=[],
        description="Where schema files to be uploaded are saved",
        title="Schema directory",
    )
    script: Dict[str, List[str]] = Field(
        default={}, description="Set of commands to run in subprocess.", title="Commands"
    )
    force_cloud_sync: Optional[bool] = Field(
        default=False,
        description="Upload data even if it's already in the cloud",
        title="Force cloud sync",
    )
    max_attempts: Optional[int] = Field(default=10, description="Number of retries", title="Retries")