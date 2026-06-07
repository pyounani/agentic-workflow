from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import LanternStatus


class LanternCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lantern_code: str
    name: str
    status: LanternStatus


class LanternDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lantern_code: str
    name: str
    image_paths: list[str]
    background_music: str | None = None
    status: LanternStatus
    created_at: datetime


class LanternListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lantern_code: str
    name: str
    image_paths: list[str]
    background_music: str | None = None
    is_mine: bool


class LanternRandomListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    items: list[LanternListItem]


class LanternStatusEvent(BaseModel):
    status: LanternStatus
