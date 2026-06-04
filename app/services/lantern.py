from app.models.lantern import Lantern
from app.schemas.lantern import LanternCreate, LanternCreateResponse


async def create_lantern(data: LanternCreate) -> LanternCreateResponse:
    lantern = Lantern(
        name=data.name,
        image_paths=data.image_paths,
        background_music=data.background_music,
    )
    await lantern.insert()
    return LanternCreateResponse(
        lantern_code=lantern.lantern_code,
        name=lantern.name,
        status=lantern.status,
    )
