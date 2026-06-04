from fastapi import APIRouter

from app.routers.lantern import router as lantern_router


def include_routers(v1: APIRouter) -> None:
    v1.include_router(lantern_router)
