""" Configuration for watchdog service"""

from typing import Optional, Union

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
    misfire_grace_time_s: Union[int, None] = Field(
        default=3 * 3600,
        description="If the job scheduler is busy, wait this long before skipping a job."
        + " If None, allow the job to run no matter how late it is",
        title="Scheduler grace time",
    )
