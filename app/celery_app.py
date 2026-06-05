import asyncio
import logging

from celery import Celery
from celery.signals import worker_process_init

from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "agentic_workflow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.lantern"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

_loop: asyncio.AbstractEventLoop | None = None
_db_client = None


@worker_process_init.connect
def init_worker(**kwargs):
    global _loop, _db_client
    from app.database import init_db
    from app.models import all_models

    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _db_client = _loop.run_until_complete(init_db(all_models))
    logger.info("Celery worker DB initialized")


def get_loop() -> asyncio.AbstractEventLoop:
    if _loop is None:
        raise RuntimeError("Worker event loop not initialized")
    return _loop
