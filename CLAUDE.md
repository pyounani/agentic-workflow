# CLAUDE.md

## Git

Write commit messages in English using Conventional Commits:
- `feat:` new feature
- `fix:` bug fix
- `chore:` build/config changes
- `docs:` documentation
- `test:` tests

## Commands

```bash
uv run fastapi dev app/main.py   # 개발 서버 (hot reload)
uv run pytest -v                 # 테스트
docker compose up --build        # API + MongoDB 동시 기동
```

## Architecture

단방향 의존: Router → Service → Model, Router ↔ Schema

| Layer | Path | Role |
|---|---|---|
| Schema | `app/schemas/{domain}.py` | API 입출력 전용 Pydantic 모델 |
| Model | `app/models/{domain}.py` | Beanie Document (MongoDB 매핑) |
| Service | `app/services/{domain}.py` | 비즈니스 로직, DB 조작 |
| Router | `app/routers/{domain}.py` | HTTP 엔드포인트, 서비스 호출 |

## Adding a Domain

새 도메인 `foo` 추가 시 건드릴 파일:

1. `app/models/foo.py` — `class Foo(Document)` 정의
2. `app/models/__init__.py` — `all_models`에 `Foo` 추가
3. `app/schemas/foo.py` — `FooCreate`, `FooUpdate`, `FooResponse` 정의
4. `app/services/foo.py` — async 함수로 비즈니스 로직 작성
5. `app/routers/foo.py` — `router = APIRouter()` + 엔드포인트 정의
6. `app/routers/__init__.py` — `include_routers()`에 한 줄 추가

`app/main.py`는 건드리지 않는다.

## Exceptions

`app/exceptions.py`에서 import:
- `NotFoundException` → 404
- `ConflictException` → 409
- 새 예외: `HTTPException` 서브클래스로 추가

## Testing

테스트 DB는 `mongomock-motor`로 모킹 (`tests/conftest.py`).
`patch("app.main.init_db", mock_init_db)`로 lifespan의 실제 MongoDB 연결을 교체.
새 도메인 테스트 파일: `tests/test_{domain}.py`.

## Language
모든 응답은 한국어로 작성한다.
