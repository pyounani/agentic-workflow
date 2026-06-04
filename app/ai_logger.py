import json
import logging
import time
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path


def _setup() -> logging.Logger:
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger("ai_tasks")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.FileHandler("logs/ai_tasks.jsonl", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    return logger


_logger = _setup()


def _summarize(kwargs: dict) -> dict:
    """Convert kwargs to a JSON-safe input summary."""
    summary = {}
    for k, v in kwargs.items():
        if k == "lantern_code":
            continue
        if isinstance(v, list):
            summary[k] = f"{len(v)} items"
        elif isinstance(v, (str, int, float, bool)) or v is None:
            summary[k] = v
        else:
            summary[k] = type(v).__name__
    return summary


def log_ai_task(task_name: str):
    """Decorator that logs AI task input, output, errors, and duration.

    Each call appends one JSON line to logs/ai_tasks.jsonl for
    reproducibility and error tracing.

    Usage:
        @log_ai_task("mood_analysis")
        async def analyze_mood(lantern_code: str, image_paths: list[str]) -> str:
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.monotonic()
            entry: dict = {
                "task": task_name,
                "lantern_code": kwargs.get("lantern_code"),
                "timestamp": datetime.now(UTC).isoformat(),
                "input": _summarize(kwargs),
            }
            try:
                result = await func(*args, **kwargs)
                entry["status"] = "success"
                entry["output"] = result
                return result
            except Exception as exc:
                entry["status"] = "error"
                entry["error"] = {"type": type(exc).__name__, "message": str(exc)}
                raise
            finally:
                entry["duration_ms"] = round((time.monotonic() - start) * 1000)
                _logger.info(json.dumps(entry, ensure_ascii=False))

        return wrapper
    return decorator
