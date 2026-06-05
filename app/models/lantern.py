import uuid
from datetime import UTC, datetime
from typing import Annotated

from beanie import Document
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.enums import LanternStatus


class Lantern(Document):
    lantern_code: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(min_length=1)
    image_paths: Annotated[list[str], Field(min_length=3, max_length=3)]
    background_music: str | None = None
    status: LanternStatus = LanternStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "lanterns"
        indexes = [IndexModel([("lantern_code", ASCENDING)], unique=True)]
