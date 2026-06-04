import mongomock
import pytest
from beanie import init_beanie
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.main import app
from app.models import all_models

# Beanie 2.x calls list_collection_names(authorizedCollections=True, nameOnly=True)
# which mongomock does not support; drop unknown kwargs to restore compatibility.
_orig_list_collection_names = mongomock.Database.list_collection_names


def _list_collection_names_compat(self, *args, **kwargs):
    kwargs.pop("authorizedCollections", None)
    kwargs.pop("nameOnly", None)
    return _orig_list_collection_names(self, *args, **kwargs)


mongomock.Database.list_collection_names = _list_collection_names_compat


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
