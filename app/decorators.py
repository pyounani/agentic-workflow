import functools
import logging

logger = logging.getLogger(__name__)


def log_ai_task(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info("AI task started: %s", func.__name__)
        try:
            result = await func(*args, **kwargs)
            logger.info("AI task completed: %s", func.__name__)
            return result
        except Exception:
            logger.exception("AI task failed: %s", func.__name__)
            raise
    return wrapper
