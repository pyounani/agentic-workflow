import mongomock
import pytest
from beanie import init_beanie
from beanie.odm.queries.aggregation import AggregationQuery
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

from app.main import app
from app.models import all_models


@pytest.fixture(scope="session", autouse=True)
def _patch_beanie_aggregate_cursor():
    # Beanie awaits collection.aggregate(), but Motor 3.x / mongomock-motor returns
    # a LatentCommandCursor directly (not a coroutine). Remove the await.
    _orig = AggregationQuery.get_cursor

    async def _patched(self):
        pipeline = self.get_aggregation_pipeline()
        return self.document_model.get_pymongo_collection().aggregate(
            pipeline, session=self.session, **self.pymongo_kwargs
        )

    AggregationQuery.get_cursor = _patched
    yield
    AggregationQuery.get_cursor = _orig


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


@pytest.fixture(autouse=True)
def _mock_dispatch_pipeline(monkeypatch):
    """모든 테스트에서 Celery pipeline 실행을 막아 Redis 연결 시도를 차단."""
    monkeypatch.setattr("app.routers.lantern.dispatch_mood_pipeline", lambda code: None)


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
