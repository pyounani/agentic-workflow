import logging

from celery import chain, shared_task

from app.celery_app import get_loop

logger = logging.getLogger(__name__)


# ── async 헬퍼 (실제 AI/DB 작업) ──

async def _fetch_mood(lantern_code: str) -> dict:
    # TODO: httpx로 AI 서버 POST /mood 호출
    return {"mood": "calm", "intensity": 0.7}


async def _fetch_bgm(mood_data: dict, lantern_code: str) -> str:
    # TODO: httpx로 AI 서버 POST /bgm 호출
    return f"bgm_{mood_data['mood']}.mp3"


async def _save_completed(bgm_path: str, lantern_code: str) -> None:
    from app.enums import LanternStatus
    from app.models.lantern import Lantern

    lantern = await Lantern.find_one(Lantern.lantern_code == lantern_code)
    if lantern is None:
        return
    lantern.background_music = bgm_path
    lantern.status = LanternStatus.COMPLETED
    await lantern.save()


async def _save_failed(lantern_code: str) -> None:
    from app.enums import LanternStatus
    from app.models.lantern import Lantern

    lantern = await Lantern.find_one(Lantern.lantern_code == lantern_code)
    if lantern is None:
        return
    lantern.status = LanternStatus.FAILED
    await lantern.save()


# ── Celery Tasks ──

@shared_task(bind=True, max_retries=3, default_retry_delay=10, name="tasks.analyze_mood")
def analyze_mood_task(self, lantern_code: str) -> dict:
    logger.info("[analyze_mood] start: %s", lantern_code)
    try:
        result = get_loop().run_until_complete(_fetch_mood(lantern_code))
        logger.info("[analyze_mood] done: %s -> %s", lantern_code, result)
        return result
    except Exception as exc:
        logger.exception("[analyze_mood] failed: %s", lantern_code)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10, name="tasks.generate_bgm")
def generate_bgm_task(self, mood_data: dict, lantern_code: str) -> str:
    logger.info("[generate_bgm] start: %s mood=%s", lantern_code, mood_data)
    try:
        result = get_loop().run_until_complete(_fetch_bgm(mood_data, lantern_code))
        logger.info("[generate_bgm] done: %s -> %s", lantern_code, result)
        return result
    except Exception as exc:
        logger.exception("[generate_bgm] failed: %s", lantern_code)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10, name="tasks.finalize_lantern")
def finalize_lantern_task(self, bgm_path: str, lantern_code: str) -> None:
    logger.info("[finalize_lantern] start: %s bgm=%s", lantern_code, bgm_path)
    try:
        get_loop().run_until_complete(_save_completed(bgm_path, lantern_code))
        logger.info("[finalize_lantern] done: %s", lantern_code)
    except Exception as exc:
        logger.exception("[finalize_lantern] failed: %s", lantern_code)
        raise self.retry(exc=exc)


@shared_task(name="tasks.mark_failed")
def mark_failed_task(request, exc, traceback, lantern_code: str) -> None:
    """chain.on_error 콜백. (request, exc, traceback)은 Celery가 자동 주입."""
    logger.error("[mark_failed] pipeline failed for %s: %s", lantern_code, exc)
    get_loop().run_until_complete(_save_failed(lantern_code))


# ── 디스패처 ──

def dispatch_mood_pipeline(lantern_code: str) -> None:
    pipeline = chain(
        analyze_mood_task.s(lantern_code),
        generate_bgm_task.s(lantern_code),
        finalize_lantern_task.s(lantern_code),
    ).on_error(mark_failed_task.s(lantern_code=lantern_code))
    pipeline.delay()
