from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from app.exceptions import ValidationException
from app.schemas.lantern import LanternCreateResponse, LanternDetailResponse
from app.services.lantern import create_lantern, get_lantern, process_mood_analysis

router = APIRouter(prefix="/lanterns", tags=["lanterns"])


@router.get("/{lantern_code}", response_model=LanternDetailResponse, status_code=200)
async def get_lantern_endpoint(lantern_code: str) -> LanternDetailResponse:
    return await get_lantern(lantern_code)


@router.post("", response_model=LanternCreateResponse, status_code=201)
async def post_lantern(
    background_tasks: BackgroundTasks,
    name: str = Form(..., min_length=1),
    images: list[UploadFile] = File(...),
) -> LanternCreateResponse:
    if len(images) != 3:
        raise ValidationException("Exactly 3 images are required")
    for image in images:
        if not image.content_type or not image.content_type.startswith("image/"):
            raise ValidationException(f"File '{image.filename}' is not an image")
    response = await create_lantern(name, images)
    background_tasks.add_task(process_mood_analysis, response.lantern_code)
    return response
