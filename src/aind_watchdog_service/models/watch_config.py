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
    webhook_url: Optional[str] = Field(
        default=None,
        description="Teams webhook url for user notification",
        title="Teams webhook url",
    )
