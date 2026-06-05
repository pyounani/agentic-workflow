import asyncio
import random
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.decorators import log_ai_task
from app.enums import LanternStatus
from app.exceptions import NotFoundException
from app.models.lantern import Lantern
from app.schemas.lantern import LanternCreateResponse, LanternDetailResponse, LanternListItem, LanternRandomListResponse

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "lanterns"


async def create_lantern(name: str, images: list[UploadFile]) -> LanternCreateResponse:
    lantern_code = str(uuid4())
    dir_path = UPLOAD_DIR / lantern_code
    dir_path.mkdir(parents=True, exist_ok=True)

    try:
        image_paths: list[str] = []
        for i, image in enumerate(images):
            safe_name = f"{i}_{Path(image.filename).name}" if image.filename else f"{i}.jpg"
            file_path = dir_path / safe_name
            content = await image.read()
            await asyncio.to_thread(file_path.write_bytes, content)
            image_paths.append(str(file_path))
    except Exception:
        await asyncio.to_thread(shutil.rmtree, dir_path, True)
        raise

    lantern = Lantern(
        lantern_code=lantern_code,
        name=name,
        image_paths=image_paths,
    )
    await lantern.insert()
    return LanternCreateResponse(
        lantern_code=lantern.lantern_code,
        name=lantern.name,
        status=lantern.status,
    )


async def get_lantern(lantern_code: str) -> LanternDetailResponse:
    lantern = await Lantern.find_one(Lantern.lantern_code == lantern_code)
    if lantern is None:
        raise NotFoundException(detail=f"Lantern '{lantern_code}' not found")
    return LanternDetailResponse.model_validate(lantern)


def _to_list_item(lantern: Lantern, is_mine: bool) -> LanternListItem:
    return LanternListItem(
        lantern_code=lantern.lantern_code,
        name=lantern.name,
        image_paths=lantern.image_paths,
        background_music=lantern.background_music,
        is_mine=is_mine,
    )


async def get_random_list(lantern_code: str) -> LanternRandomListResponse:
    my_lantern = await Lantern.find_one(Lantern.lantern_code == lantern_code)

    if my_lantern is not None:
        sample = await Lantern.aggregate(
            [
                {"$match": {"lantern_code": {"$ne": lantern_code}}},
                {"$sample": {"size": 19}},
            ],
            projection_model=Lantern,
        ).to_list()
        all_items = [_to_list_item(my_lantern, is_mine=True)] + [
            _to_list_item(lantern, is_mine=False) for lantern in sample
        ]
    else:
        sample = await Lantern.aggregate(
            [{"$sample": {"size": 20}}],
            projection_model=Lantern,
        ).to_list()
        all_items = [_to_list_item(lantern, is_mine=False) for lantern in sample]

    random.shuffle(all_items)
    return LanternRandomListResponse(total=len(all_items), items=all_items)


@log_ai_task
async def process_mood_analysis(lantern_code: str) -> None:
    lantern = await Lantern.find_one(Lantern.lantern_code == lantern_code)
    if lantern is None:
        return
    lantern.background_music = "default_bgm.mp3"
    lantern.status = LanternStatus.COMPLETED
    await lantern.save()
