import asyncio
import pytest
from unittest.mock import MagicMock, patch

from app.enums import LanternStatus
from app.models.lantern import Lantern
from app.tasks.lantern import (
    _save_completed,
    _save_failed,
    _set_processing,
    dispatch_pipeline,
    finalize_lantern_task,
    mark_failed_task,
    process_pipeline_task,
)


@pytest.fixture
async def db_lantern(client):
    lantern = Lantern(name="Test", image_paths=["/a.jpg", "/b.jpg", "/c.jpg"])
    await lantern.insert()
    return lantern


# ── Tier 1: async 헬퍼 ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_processing_updates_status(db_lantern):
    await _set_processing(db_lantern.lantern_code)
    updated = await Lantern.find_one(Lantern.lantern_code == db_lantern.lantern_code)
    assert updated.status == LanternStatus.PROCESSING


@pytest.mark.asyncio
async def test_set_processing_ignores_missing_lantern(client):
    await _set_processing("nonexistent-code")


@pytest.mark.asyncio
async def test_save_completed_updates_status_and_bgm(db_lantern):
    await _save_completed("bgm_test.mp3", db_lantern.lantern_code)
    updated = await Lantern.find_one(Lantern.lantern_code == db_lantern.lantern_code)
    assert updated.status == LanternStatus.COMPLETED
    assert updated.background_music == "bgm_test.mp3"


@pytest.mark.asyncio
async def test_save_failed_updates_status(db_lantern):
    await _save_failed(db_lantern.lantern_code)
    updated = await Lantern.find_one(Lantern.lantern_code == db_lantern.lantern_code)
    assert updated.status == LanternStatus.FAILED


# ── Tier 2: Celery 태스크 래퍼 ─────────────────────────────────────────────


def test_process_pipeline_task_success():
    mock_lantern = MagicMock()
    mock_lantern.status = LanternStatus.PENDING

    mock_loop = MagicMock()
    mock_loop.run_until_complete.side_effect = [mock_lantern, None, "bgm_abc.mp3"]
    with patch("app.tasks.lantern.get_loop", return_value=mock_loop):
        result = process_pipeline_task.apply(args=["abc"]).get()
    assert result == "bgm_abc.mp3"
    assert mock_loop.run_until_complete.call_count == 3


def test_process_pipeline_task_skips_if_completed():
    mock_lantern = MagicMock()
    mock_lantern.status = LanternStatus.COMPLETED
    mock_lantern.background_music = "existing_bgm.mp3"

    mock_loop = MagicMock()
    mock_loop.run_until_complete.return_value = mock_lantern
    with patch("app.tasks.lantern.get_loop", return_value=mock_loop):
        result = process_pipeline_task.apply(args=["abc"]).get()
    assert result == "existing_bgm.mp3"
    assert mock_loop.run_until_complete.call_count == 1


def test_process_pipeline_task_retries_on_error():
    def close_and_raise(coro):
        if asyncio.iscoroutine(coro):
            coro.close()
        raise RuntimeError("ai error")

    mock_loop = MagicMock()
    mock_loop.run_until_complete.side_effect = close_and_raise
    with patch("app.tasks.lantern.get_loop", return_value=mock_loop):
        result = process_pipeline_task.apply(args=["abc"])
    assert result.failed()


def test_finalize_lantern_task_success():
    mock_loop = MagicMock()
    with patch("app.tasks.lantern.get_loop", return_value=mock_loop):
        finalize_lantern_task.apply(args=["bgm_test.mp3", "abc"]).get()
    mock_loop.run_until_complete.assert_called_once()


def test_mark_failed_task_calls_save_failed():
    mock_loop = MagicMock()
    with patch("app.tasks.lantern.get_loop", return_value=mock_loop):
        mark_failed_task.apply(
            args=[None, Exception("fail"), None],
            kwargs={"lantern_code": "abc"},
        )
    mock_loop.run_until_complete.assert_called_once()


# ── Tier 3: dispatch_pipeline on_error 배선 ────────────────────────────────


def test_dispatch_pipeline_wires_on_error():
    with (
        patch("app.tasks.lantern.chain") as mock_chain,
        patch.object(process_pipeline_task, "s") as mock_ps,
        patch.object(finalize_lantern_task, "s") as mock_fs,
        patch.object(mark_failed_task, "s") as mock_ms,
    ):
        mock_pipeline = MagicMock()
        mock_chain.return_value.on_error.return_value = mock_pipeline

        dispatch_pipeline("abc123")

        mock_chain.assert_called_once_with(mock_ps.return_value, mock_fs.return_value)
        mock_ms.assert_called_once_with(lantern_code="abc123")
        mock_chain.return_value.on_error.assert_called_once_with(mock_ms.return_value)
        mock_pipeline.delay.assert_called_once()
