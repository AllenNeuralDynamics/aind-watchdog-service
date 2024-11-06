""" Configuration for watchdog service"""

from typing import Optional, Union

from pydantic import BaseModel, Field


class WatchConfig(BaseModel, extra="ignore"):
    """Configuration for rig"""

    flag_dir: str = Field(
        ..., description="Directory for watchdog to poll", title="Poll directory"
    )
    manifest_complete: str = Field(
        ...,
        description="Manifest directory for triggered data",
        title="Manifest complete directory",
    )
    misfire_grace_time_s: Union[int, None] = Field(
        default=3 * 3600,
        description="If the job scheduler is busy, wait this long before skipping a job."
        + " If None, allow the job to run no matter how late it is",
        title="Scheduler grace time",
    )
