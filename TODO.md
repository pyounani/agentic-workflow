## Current TODO

### AI

- [x] 로깅 훅 구축하기

### 설계

- [x] 요구사항 정리하기
- [x] API 설계하기
- [x] ERD 설계하기

### 요구사항 구현

#### model

- [x] Lantern 모델 생성(Beanie Document)
- [x] all_models에 Lantern 추가

#### schemas

- [x] LanternCreateResponse: lantern_code, name, status
- [x] LanternDetailResponse: lantern_code, name, image_paths, background_music, status, created_at
- [x] LanternListItem: lantern_code, name, image_paths, background_music, is_mine
- [x] LanternRandomListResponse: total, items: list[LanternListItem]

#### service

- [x] create_lantern(name, files): UUID 생성, 이미지 저장(uploads/lanterns/{code}/), DB insert, 201 반환
- [x] get_lantern(lantern_code): 단건 조회, 없으면 NotFoundException
- [x] get_random_list(lantern_code): 대상 lantern 확인 후 전체에서 최대 19개 랜덤 샘플링 + 본인 포함 셔플
- [x] process_mood_analysis(lantern_code): 스텁: 고정 background_music 배정 후 status → "completed" 업데이트 (@log_ai_task 데코레이터 사용)

#### router

- [x] POST /lanterns — multipart(name + images 3장 검증) → create_lantern → BackgroundTasks로 process_mood_analysis 등록 → 201
- [x] GET /lanterns/{lantern_code} — get_lantern → 200
- [x] GET /lanterns/{lantern_code}/random-list — get_random_list → 200
- [x] include_routers()에 lantern_router 등록

#### test

- [x] tests/test_lantern.py 작성: create → get → random-list 흐름 단위 테스트 (mongomock)
- [x] uv run pytest -v — 전체 테스트 통과 확인

### 비동기 (Celery + Redis)

#### API 서버 (Celery + Redis)

- [x] celery, redis 의존성 추가 (pyproject.toml)
- [x] Redis 서비스 docker-compose.yml에 추가
- [x] Celery 워커 서비스 docker-compose.yml에 추가 (--concurrency=1 — AI 서버 동시 호출 방지)
- [x] app/celery_app.py 생성 — Celery 인스턴스 및 LLM 추론 태스크 정의
  - [x] worker_prefetch_multiplier = 1 설정 (작업 미리 가져오기 금지)
  - [x] task_soft_time_limit = 40, task_time_limit = 60 설정 (전체 파이프라인 실측 30초 기준)
  - [x] task_acks_late = True (작업 완료 후 ACK, 크래시 시 재큐)
  - [x] task_reject_on_worker_lost = True (워커 유실 시 작업 재큐)
  - [x] worker_max_tasks_per_child = 50
  - [x] result_expires = 300 (완료 즉시 MongoDB에 저장되므로 5분으로 충분)
  - [x] 단일 큐 사용 (큐 분리 실익 없음 — 멀티 AI 서버 스케일아웃 시점에 재검토)
  - [x] Redis maxmemory 128mb, maxmemory-policy volatile-lru 설정 (브로커 메시지 보호, 결과값만 LRU 제거)
  - [x] AI 서버 단일 엔드포인트 호출로 단순화 (무드→캡션→BGM 내부 처리, API 서버는 BGM 경로만 수신)
- [x] process_mood_analysis BackgroundTasks → Celery task로 교체

### SSE

- [x] SSE 엔드포인트 추가 — GET /lanterns/{lantern_code}/status/stream
  - [x] poll_interval = 2초 — MongoDB 상태 폴링 간격 (파이프라인 30~60초 기준, 적절한 응답성)
  - [x] connection_timeout = 150초 — SSE 연결 최대 유지 시간 (process time_limit 60 + retry 1회 시 130초 → 여유 포함 150초)
  - [x] keepalive_interval = 15초 — `:ping` 코멘트 전송 간격 (nginx default read timeout 60초보다 충분히 짧게)
  - [x] retry: 3000 (ms) — SSE 스펙 `retry:` 필드, 클라이언트 재연결 대기 시간
  - [x] 응답 헤더: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`, `Connection: keep-alive`
  - [x] 종료 조건: status == COMPLETED 또는 FAILED 시 스트림 close
  - [x] 404 처리: lantern_code 없으면 즉시 스트림 종료 (error 이벤트 후 close)
