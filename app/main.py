from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.exceptions import register_exception_handlers
from app.models import all_models
from app.routers import include_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = await init_db(all_models)
    yield
    client.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)


@app.get("/health")
async def health():
    return {"status": "ok"}


v1 = APIRouter(prefix="/api/v1")
include_routers(v1)
app.include_router(v1)
