from fastapi import APIRouter

from app.schemas.lantern import LanternCreate, LanternCreateResponse
from app.services.lantern import create_lantern

router = APIRouter(prefix="/lanterns", tags=["lanterns"])


@router.post("", response_model=LanternCreateResponse, status_code=201)
async def post_lantern(body: LanternCreate) -> LanternCreateResponse:
    return await create_lantern(body)
