from fastapi import APIRouter


def include_routers(v1: APIRouter) -> None:
    # 새 라우터 추가 방법:
    # 1. app/routers/{domain}.py 생성, router = APIRouter() 정의
    # 2. 아래에 import + v1.include_router() 한 줄 추가
    pass
