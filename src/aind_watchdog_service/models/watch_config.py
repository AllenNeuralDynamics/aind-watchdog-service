""" Configuration for watchdog service"""

from pydantic import BaseModel, Field
from typing import Optional, Union
from pathlib import Path


class WatchConfig(BaseModel):
    """Configuration for rig"""

    flag_dir: Union[str, Path] = Field(
        description="Directory for watchdog to poll", title="Poll directory"
    )
    manifest_complete: Union[str, Path] = Field(
        description="Manifest directory for triggered data",
        title="Manifest complete directory",
    )
    schema_map: Optional[str] = Field(
        default=None,
        description="json file used for mapping; ignored for now until metadata mapper is implemented",  # noqa
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


