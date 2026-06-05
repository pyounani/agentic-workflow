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

### 비동기 + SSE

#### API 서버 (Celery + Redis)

- [x] celery, redis 의존성 추가 (pyproject.toml)
- [x] Redis 서비스 docker-compose.yml에 추가
- [x] Celery 워커 서비스 docker-compose.yml에 추가
- [x] app/celery_app.py 생성 — Celery 인스턴스 및 LLM 추론 태스크 정의
- [x] process_mood_analysis BackgroundTasks → Celery task로 교체
- [ ] SSE 엔드포인트 추가 — GET /lanterns/{lantern_code}/status/stream

#### AI 서버 (Celery + Redis)

- [ ] Celery 설치 및 celery.py 설정 파일 생성
- [ ] worker_concurrency = 1 설정 (GPU 1개당 워커 1개, VRAM OOM 방지)
- [ ] worker_prefetch_multiplier = 1 설정 (작업 미리 가져오기 금지)
- [ ] task_time_limit / task_soft_time_limit 설정 (모델별 측정 후 결정)
- [ ] task_acks_late = True (작업 완료 후 ACK, 크래시 시 재큐)
- [ ] task_reject_on_worker_lost = True (워커 유실 시 작업 재큐)
- [ ] worker_max_tasks_per_child = 200 (GPU 메모리 누수 방지용 워커 재시작)
- [ ] result_expires = 3600 (Redis 결과 1시간 후 만료)
- [ ] 큐 분리 — yolo 큐 / musicgen 큐 각각 정의
- [ ] Celery chain으로 YOLO → MusicGen 파이프라인 구성
- [ ] Redis maxmemory, maxmemory-policy allkeys-lru 설정
