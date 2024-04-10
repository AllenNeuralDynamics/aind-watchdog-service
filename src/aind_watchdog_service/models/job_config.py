from pydantic import BaseModel, Field, field_validator, validator
from typing import Optional, List, Dict, Union
from aind_data_schema.models.modalities import Modality
from datetime import datetime
from pathlib import Path

class WatchConfig(BaseModel):
    """Configuration for rig"""

    flag_dir: str = Field(
        description="Directory for watchdog to poll", title="Poll directory"
    )
    flag_file: Optional[str] = Field(
        default="FINISHED", description="flag file to watch for", title="Flag file"
    )
    schemas: Optional[str] = Field(
        description="Location of static schemas like rig / instrumentation json",
        title="Schema location",
    )
    schema_map: Optional[str] = Field(
        description="json file used for mapping", title="Schema map configuration"
    )
    rig_type: str = Field(
        description="Rig for data transfer and metdata mapping", title="Rig type"
    )
    webhook_url: Optional[str] = Field(
        description="Teams webhook url for notification after initiation of data transfer or error reporting",
        title="Teams webhook url",
    )
    transfer_time: Optional[str] = Field(
        description="Transfer time to schedule copy and upload, defaults to immediately",
        title="APScheduler transfer time",
    )
    destination: str = Field(
        description="where to send data to on VAST",
        title="VAST destination and maybe S3?",
    )
    modality_source: Dict[str, str] = Field(description="Where to find the modality source directories", title="Modality directories")
    modalities: Dict[str, List[str]] = Field(
        description="list of ModalityFile objects containing modality names and associated files",
        title="modality files",
    )

    @validator("modalities", "modality_source")
    def verify_modality_dirs(cls, data: Dict[str, str]) -> Dict[str, str]:
        for key in data.keys():
            if key.lower() not in Modality._abbreviation_map:
                raise ValueError(f"{key} not in accepted modalities")
        return data
    

    @field_validator("transfer_time")
    def verify_datetime(cls, data: str) -> str:
        try:
            datetime.strptime(data, "%H:%M").time()
        except ValueError:
            raise ValueError(f"Specify time in HH:MM format, not {data}")
        return data
    
    @validator("modality_source", "flag_dir", "destination")
    def verify_directories_exist(cls, data: Union[Dict[str, str], str]) -> Union[Dict[str, str], str]:
        if type(data) == dict:
            for k, v in data.items():
                if not Path(v).is_dir():
                    raise ValueError(f"Provide correct path for {data}")
        else:
            if not Path(data).is_dir():
                raise ValueError(f"Provide correct path for {data}")
        return data