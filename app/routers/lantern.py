from fastapi import APIRouter, File, Form, UploadFile

from app.exceptions import ValidationException
from app.schemas.lantern import LanternCreateResponse, LanternDetailResponse, LanternRandomListResponse
from app.services.lantern import create_lantern, dispatch_mood_pipeline, get_lantern, get_random_list

router = APIRouter(prefix="/lanterns", tags=["lanterns"])


@router.get("/{lantern_code}/random-list", response_model=LanternRandomListResponse, status_code=200)
async def get_random_list_endpoint(lantern_code: str) -> LanternRandomListResponse:
    return await get_random_list(lantern_code)


@router.get("/{lantern_code}", response_model=LanternDetailResponse, status_code=200)
async def get_lantern_endpoint(lantern_code: str) -> LanternDetailResponse:
    return await get_lantern(lantern_code)


@router.post("", response_model=LanternCreateResponse, status_code=201)
async def post_lantern(
    name: str = Form(..., min_length=1),
    images: list[UploadFile] = File(...),
) -> LanternCreateResponse:
    if len(images) != 3:
        raise ValidationException("Exactly 3 images are required")
    for image in images:
        if not image.content_type or not image.content_type.startswith("image/"):
            raise ValidationException(f"File '{image.filename}' is not an image")
    response = await create_lantern(name, images)
    dispatch_mood_pipeline(response.lantern_code)
    return response
