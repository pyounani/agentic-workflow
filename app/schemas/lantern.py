from pydantic import BaseModel

from app.enums import LanternStatus


class LanternCreateResponse(BaseModel):
    lantern_code: str
    name: str
    status: LanternStatus
