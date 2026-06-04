from typing import Annotated, Optional

from pydantic import BaseModel, Field

from app.enums import LanternStatus


class LanternCreate(BaseModel):
    name: str = Field(min_length=1)
    image_paths: Annotated[list[str], Field(min_length=3, max_length=3)]
    background_music: Optional[str] = None


class LanternCreateResponse(BaseModel):
    lantern_code: str
    name: str
    status: LanternStatus
