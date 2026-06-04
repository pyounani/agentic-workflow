from pydantic import BaseModel

from app.models.lantern import LanternStatus


class LanternCreateResponse(BaseModel):
    lantern_code: str
    name: str
    status: LanternStatus
