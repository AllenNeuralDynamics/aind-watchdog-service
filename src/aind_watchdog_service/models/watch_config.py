""" Configuration for watchdog service"""

from typing import Optional

from pydantic import BaseModel, Field


class WatchConfig(BaseModel):
    """Configuration for rig"""

    flag_dir: str = Field(
        ..., description="Directory for watchdog to poll", title="Poll directory"
    )
    manifest_complete: str = Field(
        ...,
        description="Manifest directory for triggered data",
        title="Manifest complete directory",
    )
    # Not in use. Will be used for metadata mapping in the future
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
