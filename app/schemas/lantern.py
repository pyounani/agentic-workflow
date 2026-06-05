from datetime import datetime

from pydantic import BaseModel

from app.enums import LanternStatus


class LanternCreateResponse(BaseModel):
    lantern_code: str
    name: str
    status: LanternStatus


class LanternDetailResponse(BaseModel):
    lantern_code: str
    name: str
    image_paths: list[str]
    background_music: str | None = None
    status: LanternStatus
    created_at: datetime
