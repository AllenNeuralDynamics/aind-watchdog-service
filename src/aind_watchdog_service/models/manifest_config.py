"""Job configs for VAST staging or executing a custom script"""

from datetime import datetime, time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from aind_data_schema_models import modalities, platforms
from aind_data_transfer_models.core import BucketType
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from typing_extensions import Annotated, Self

# This is a really bad idea, but until we can figure out a better solution
# from aind-data-schema we will settle for this.
# A relevant issue has been opened in the aind-data-schemas repo:
# https://github.com/AllenNeuralDynamics/aind-data-schema/issues/960

Platform = Literal[tuple(set(platforms.Platform.abbreviation_map.keys()))]
Modality = Annotated[
    Literal[tuple(set(modalities.Modality.abbreviation_map.keys()))],
    BeforeValidator(lambda x: "pophys" if x == "ophys" else x),
]


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
    platform: Platform = Field(description="Platform type", title="Platform type")
    capsule_id: Optional[str] = Field(
        default=None, description="Capsule ID of pipeline to run", title="Capsule"
    )
    mount: Optional[str] = Field(
        default=None, description="Mount point for pipeline run", title="Mount point"
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
    modalities: Dict[Modality, List[str]] = Field(
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

    @field_validator("modalities", mode="before")
    @classmethod
    def normalize_modalities(cls, value) -> Dict[Modality, List[str]]:
        """Normalize modalities"""
        if isinstance(value, dict):
            _ret: Dict[str, Any] = {}
            for modality, v in value.items():
                if isinstance(modality, getattr(modalities.Modality, "ALL")):
                    key = getattr(modality, "abbreviation", None)
                    if key is None:
                        _ret[modality] = v
                    else:
                        _ret[key] = v
                else:
                    _ret[modality] = v
            return _ret
        else:
            return value

    @field_validator("platform", mode="before")
    @classmethod
    def normalize_platform(cls, value) -> Platform:
        """Normalize modalities"""
        if isinstance(value, getattr(platforms.Platform, "ALL")):
            ret = getattr(value, "abbreviation", None)
            return ret if ret else value
        else:
            return value

    @field_validator("destination", mode="after")
    @classmethod
    def validate_destination_path(cls, value: str) -> str:
        return cls._path_to_posix(value)

    @field_validator("schemas", mode="after")
    @classmethod
    def validate_schema_paths(cls, value: List[str]) -> List[str]:
        return [cls._path_to_posix(path) for path in value]

    @field_validator("modalities", mode="after")
    @classmethod
    def validate_modality_paths(cls, value: Dict[Any, List[str]]) -> Dict[Any, List[str]]:
        return {
            modality: [cls._path_to_posix(path) for path in paths]
            for modality, paths in value.items()
        }

    @staticmethod
    def _path_to_posix(path: str) -> str:
        return str(Path(path).as_posix())
