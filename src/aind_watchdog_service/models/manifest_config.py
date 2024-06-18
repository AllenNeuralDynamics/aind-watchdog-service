"""Job configs for VAST staging or executing a custom script"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from aind_data_schema_models.modalities import Modality
from aind_data_schema_models.platforms import Platform
from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    platform: str = Field(description="Platform type", title="Platform type")
    capsule_id: Optional[str] = Field(
        ..., description="Capsule ID of pipeline to run", title="Capsule"
    )
    mount: Optional[str] = Field(
        ..., description="Mount point for pipeline run", title="Mount point"
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
    modalities: Dict[str, List[str]] = Field(
        default={},
        description="list of ModalityFile objects containing modality names and associated files or directories",  # noqa
        title="modality files",
    )
    schemas: Optional[List[str]] = Field(
        default=[],
        description="Where schema files to be uploaded are saved",
        title="Schema directory",
    )
    script: Dict[str, List[str]] = Field(
        default={}, description="Set of commands to run in subprocess.", title="Commands"
    )

    @field_validator("platform")
    @classmethod
    def check_platform_string(cls, input_platform: str) -> str:
        """Checks if str can be converted to platform model"""
        if input_platform in Platform._abbreviation_map:
            return input_platform
        else:
            raise AttributeError(f"Unknown platform: {input_platform}")

    @field_validator("modalities")
    @classmethod
    def check_modality_string(
        cls, input_modality: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Checks if str can be converted to platform model"""
        for key in input_modality.keys():
            if key not in Modality._abbreviation_map:
                raise AttributeError(f"Unknown modality: {input_modality}")
        return input_modality