from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings


async def init_db(document_models: list) -> AsyncIOMotorClient:
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=document_models,
    )
    return client
