import mongomock
import pytest
from beanie import init_beanie
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.main import app
from app.models import all_models


@pytest.fixture(scope="session", autouse=True)
def _patch_mongomock_compat():
    # Beanie 2.x calls list_collection_names(authorizedCollections=True, nameOnly=True)
    # which mongomock does not support; drop unknown kwargs to restore compatibility.
    _orig = mongomock.Database.list_collection_names

    def _compat(self, *args, **kwargs):
        kwargs.pop("authorizedCollections", None)
        kwargs.pop("nameOnly", None)
        return _orig(self, *args, **kwargs)

    mongomock.Database.list_collection_names = _compat
    yield
    mongomock.Database.list_collection_names = _orig


@pytest.fixture
async def client():
    mock_motor_client = AsyncMongoMockClient()
    await init_beanie(
        database=mock_motor_client["test_db"],
        document_models=all_models,
    )
    # httpx ASGITransport does not trigger the ASGI lifespan,
    # so init_db is never called and no real MongoDB connection is made.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
