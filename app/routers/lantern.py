from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.schemas.lantern import LanternCreateResponse
from app.services.lantern import create_lantern, process_mood_analysis

router = APIRouter(prefix="/lanterns", tags=["lanterns"])


@router.post("", response_model=LanternCreateResponse, status_code=201)
async def post_lantern(
    background_tasks: BackgroundTasks,
    name: str = Form(..., min_length=1),
    images: list[UploadFile] = File(...),
) -> LanternCreateResponse:
    if len(images) != 3:
        raise HTTPException(status_code=422, detail="Exactly 3 images are required")
    response = await create_lantern(name, images)
    background_tasks.add_task(process_mood_analysis, response.lantern_code)
    return response
