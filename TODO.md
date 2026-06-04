## Current TODO

### AI

- [x] 로깅 훅 구축하기

### 설계

- [x] 요구사항 정리하기
- [x] API 설계하기
- [x] ERD 설계하기

### 요구사항 구현

#### model

- [ ] Lantern 모델 생성(Beanine Document)
- [ ] all_models에 Lantern 추가

#### schemas

- [ ] LanternCreateResponse: lantern_code, name, status
- [ ] LanternDetailResponse: lantern_code, name, image_paths, background_music, status, created_at
- [ ] LanternListItem: lantern_code, name, image_paths, background_music, is_mine
- [ ] LanternRandomListResponse: items: list[LanternListItem]

#### service

- [ ] create_lantern(name, files): UUID 생성, 이미지 저장(uploads/lanterns/{code}/), DB insert, 201 반환
- [ ] get_lantern(lantern_code): 단건 조회, 없으면 NotFoundException
- [ ] get_random_list(lantern_code): 대상 lantern 확인 후 전체에서 최대 19개 랜덤 샘플링 + 본인 포함 셔플
- [ ] process_mood_analysis(lantern_code): 스텁: 고정 background_music 배정 후 status → "completed" 업데이트 (@log_ai_task 데코레이터 사용)

#### router

- [ ] POST /lanterns — multipart(name + images 3장 검증) → create_lantern → BackgroundTasks로 process_mood_analysis 등록 → 201
- [ ] GET /lanterns/{lantern_code} — get_lantern → 200
- [ ] GET /lanterns/{lantern_code}/random-list — get_random_list → 200
- [ ] include_routers()에 lantern_router 등록

#### test

- [ ] tests/test_lantern.py 작성: create → get → random-list 흐름 단위 테스트 (mongomock)
- [ ] uv run pytest -v — 전체 테스트 통과 확인
