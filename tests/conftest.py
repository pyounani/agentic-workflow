import pytest
from beanie import init_beanie
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient
from unittest.mock import patch

from app.main import app
from app.models import all_models


@pytest.fixture
async def client():
    mock_motor_client = AsyncMongoMockClient()

    async def mock_init_db(document_models):
        await init_beanie(
            database=mock_motor_client["test_db"],
            document_models=document_models,
        )
        return mock_motor_client

    with patch("app.main.init_db", mock_init_db):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
