"""Request bodies for the API (input validation)."""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .engine import DAYS

_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _check_time(v: str) -> str:
    if not _HHMM.match(v):
        raise ValueError("time must look like HH:MM (24 hours), e.g. 22:30")
    return v


def _check_days(v: str) -> str:
    parts = [p.strip().lower() for p in v.split(",") if p.strip()]
    if not parts or any(p not in DAYS for p in parts):
        raise ValueError("days must be a comma list of mon,tue,wed,thu,fri,sat,sun")
    return ",".join(d for d in DAYS if d in parts)


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DevicePatch(_Body):
    display_name: str | None = Field(default=None, min_length=1, max_length=60)
    child_id: int | None = None
    known: bool | None = None

    @field_validator("display_name")
    @classmethod
    def _strip(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("display_name cannot be empty")
        return v


class ChildPatch(_Body):
    age_profile: Literal[8, 13, 16]


class RulePut(_Body):
    child_id: int | None = None
    category: str
    action: Literal["block", "allow"] | None = None


class ScheduleCreate(_Body):
    child_id: int
    name: str = Field(min_length=1, max_length=60)
    days: str
    start: str
    end: str

    @field_validator("days")
    @classmethod
    def _d(cls, v):
        return _check_days(v)

    @field_validator("start", "end")
    @classmethod
    def _t(cls, v):
        return _check_time(v)


class SchedulePatch(_Body):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    days: str | None = None
    start: str | None = None
    end: str | None = None
    enabled: bool | None = None

    @field_validator("days")
    @classmethod
    def _d(cls, v):
        return None if v is None else _check_days(v)

    @field_validator("start", "end")
    @classmethod
    def _t(cls, v):
        return None if v is None else _check_time(v)


class PauseBody(_Body):
    child_id: int | None = None
    minutes: int = Field(ge=1, le=1440)


class ResumeBody(_Body):
    child_id: int | None = None


class ApproveBody(_Body):
    minutes: int | None = Field(default=None, ge=1, le=1440)


class SettingsPatch(_Body):
    retention_days: int | None = Field(default=None, ge=1, le=365)
    approval_minutes_default: int | None = Field(default=None, ge=1, le=1440)
