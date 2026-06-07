import logging

import httpx
from celery import chain, shared_task

from app.celery_app import get_loop
from app.config import settings
from app.enums import LanternStatus
from app.models.lantern import Lantern

logger = logging.getLogger(__name__)


# ── async 헬퍼 (실제 AI/DB 작업) ──

async def _set_processing(lantern_code: str) -> None:
    lantern = await Lantern.find_one(Lantern.lantern_code == lantern_code)
    if lantern is None:
        return
    lantern.status = LanternStatus.PROCESSING
    await lantern.save()


async def _process_pipeline(lantern_code: str) -> str:
    async with httpx.AsyncClient(timeout=50.0) as client:
        response = await client.post(
            f"{settings.AI_SERVER_URL}/process",
            json={"lantern_code": lantern_code},
        )
        response.raise_for_status()
        return response.json()["bgm_path"]


async def _save_completed(bgm_path: str, lantern_code: str) -> None:
    lantern = await Lantern.find_one(Lantern.lantern_code == lantern_code)
    if lantern is None:
        return
    lantern.background_music = bgm_path
    lantern.status = LanternStatus.COMPLETED
    await lantern.save()


async def _save_failed(lantern_code: str) -> None:
    lantern = await Lantern.find_one(Lantern.lantern_code == lantern_code)
    if lantern is None:
        return
    lantern.status = LanternStatus.FAILED
    await lantern.save()


# ── Celery Tasks ──

@shared_task(
    bind=True, max_retries=3, default_retry_delay=30,
    name="tasks.process_pipeline",
    soft_time_limit=40, time_limit=60,
)
def process_pipeline_task(self, lantern_code: str) -> str:
    logger.info("[process_pipeline] start: %s", lantern_code)
    loop = get_loop()
    try:
        lantern = loop.run_until_complete(
            Lantern.find_one(Lantern.lantern_code == lantern_code)
        )
        if lantern and lantern.status == LanternStatus.COMPLETED:
            logger.info("[process_pipeline] already completed, skipping: %s", lantern_code)
            return lantern.background_music

        loop.run_until_complete(_set_processing(lantern_code))
        result = loop.run_until_complete(_process_pipeline(lantern_code))
        logger.info("[process_pipeline] done: %s -> %s", lantern_code, result)
        return result
    except Exception as exc:
        logger.exception("[process_pipeline] failed: %s", lantern_code)
        raise self.retry(exc=exc)


@shared_task(
    bind=True, max_retries=3, default_retry_delay=10,
    name="tasks.finalize_lantern",
    soft_time_limit=10, time_limit=30,
)
def finalize_lantern_task(self, bgm_path: str, lantern_code: str) -> None:
    logger.info("[finalize_lantern] start: %s bgm=%s", lantern_code, bgm_path)
    try:
        get_loop().run_until_complete(_save_completed(bgm_path, lantern_code))
        logger.info("[finalize_lantern] done: %s", lantern_code)
    except Exception as exc:
        logger.exception("[finalize_lantern] failed: %s", lantern_code)
        raise self.retry(exc=exc)


@shared_task(
    name="tasks.mark_failed",
    soft_time_limit=10, time_limit=30,
)
def mark_failed_task(request, exc, traceback, lantern_code: str) -> None:
    """chain.on_error 콜백. (request, exc, traceback)은 Celery가 자동 주입."""
    logger.error("[mark_failed] pipeline failed for %s: %s", lantern_code, exc)
    get_loop().run_until_complete(_save_failed(lantern_code))


# ── 디스패처 ──

def dispatch_pipeline(lantern_code: str) -> None:
    pipeline = chain(
        process_pipeline_task.s(lantern_code),
        finalize_lantern_task.s(lantern_code),
    ).on_error(mark_failed_task.s(lantern_code=lantern_code))
    pipeline.delay()
