# 요구사항 문서 — 랜턴 서비스

## 프로젝트 개요

사용자가 이미지 3장과 이름을 업로드하면 고유한 랜턴 코드를 발급하고,
AI 이미지 분석으로 무드를 추출해 배경음을 연결해주는 서비스.
AI 처리는 CPU 바운드 작업이므로 비동기로 처리하며, 현재는 고정 배경음으로 스텁 처리한다.

---

## API 전체 요약

| 기능 | Method | Path |
|---|---|---|
| 랜턴 생성 | POST | `/api/v1/lanterns` |
| 랜덤 목록 조회 | GET | `/api/v1/lanterns/{lantern_code}/random-list` |
| 개인 랜턴 조회 | GET | `/api/v1/lanterns/{lantern_code}` |

---

## 도메인 모델

**DB (MongoDB - Lantern Document)**

| 필드 | 타입 | 설명 |
|---|---|---|
| `lantern_code` | string (UUID) | 고유 랜턴 식별자, 인덱스 |
| `name` | string | 사용자 이름 |
| `image_paths` | string[] | 로컬 파일시스템 이미지 경로 (3개) |
| `background_music` | string \| null | 배경음 파일명 (처리 완료 전 null) |
| `status` | enum | `pending` \| `completed` |
| `created_at` | datetime | 생성 시각 |

**파일시스템 구조**

```
/uploads/lanterns/{lantern_code}/
  ├── image_1.{ext}
  ├── image_2.{ext}
  └── image_3.{ext}
```

---

## 기능 1: 랜턴 생성

### 개요
이미지 3장 + 이름을 받아 랜턴을 생성한다.
AI 배경음 생성은 CPU 바운드 작업이므로 즉시 응답 후 백그라운드에서 비동기 처리한다.
현재 구현은 고정 배경음을 반환하는 스텁으로 대체한다.

### 처리 흐름

```
[동기 - 요청 처리]
1. 이미지 3장 + 이름 수신 및 유효성 검사
2. 랜턴 코드 자동 생성 (UUID)
3. 이미지를 로컬 파일시스템에 저장
4. DB에 저장 (status: "pending", background_music: null)
5. 즉시 응답 반환

[비동기 백그라운드 - FastAPI BackgroundTasks + ThreadPoolExecutor]
6. AI 무드 분석 → 배경음 선택 (스텁: 고정 파일명 반환)
7. DB 업데이트 (status: "completed", background_music: "default_bgm.mp3")
```

### API

```
POST /api/v1/lanterns
Content-Type: multipart/form-data

Body:
  name    string   (필수) 사용자 이름
  images  File[3]  (필수) 이미지 파일 정확히 3장

Response 201:
{
  "lantern_code": "550e8400-e29b-41d4-a716-446655440000",
  "name": "홍길동",
  "status": "pending"
}
```

### 예외 처리

| 조건 | HTTP |
|---|---|
| 이미지가 3장이 아닌 경우 | 422 |
| 이름이 비어있는 경우 | 422 |

---

## 기능 2: 랜덤 랜턴 목록 조회

### 개요
요청자의 랜턴을 포함해 전체 DB에서 최대 20개를 랜덤으로 섞어 반환한다.

### 처리 흐름

```
1. lantern_code 수신
2. lantern_code로 사용자 랜턴 조회 → 없으면 404
3. DB에서 해당 랜턴 제외 후 최대 19개 랜덤 샘플링
4. 사용자 랜턴 + 랜덤 19개 합산 → 순서 무작위로 섞기
5. 목록 반환
```

> DB 전체 랜턴이 20개 미만이면 있는 것 전부 반환한다.

### API

```
GET /api/v1/lanterns/{lantern_code}/random-list

Response 200:
{
  "total": 20,
  "items": [
    {
      "lantern_code": "550e8400-...",
      "name": "홍길동",
      "image_paths": ["/uploads/lanterns/.../image_1.jpg", "...", "..."],
      "background_music": "default_bgm.mp3",
      "is_mine": true
    },
    {
      "lantern_code": "661f9511-...",
      "name": "김철수",
      "image_paths": ["/uploads/lanterns/.../image_1.jpg", "...", "..."],
      "background_music": "default_bgm.mp3",
      "is_mine": false
    }
  ]
}
```

### 응답 항목 필드 (LanternListItem)

| 필드 | 타입 | 설명 |
|---|---|---|
| `lantern_code` | string | 랜턴 고유 코드 |
| `name` | string | 사용자 이름 |
| `image_paths` | string[] | 이미지 경로 3개 |
| `background_music` | string \| null | 배경음 파일명 |
| `is_mine` | boolean | 요청자 본인의 랜턴 여부 |

### 예외 처리

| 조건 | HTTP |
|---|---|
| `lantern_code`가 DB에 없는 경우 | 404 |

---

## 기능 3: 개인 랜턴 조회

### 개요
랜턴 코드로 본인의 랜턴 단건을 조회한다.
클라이언트는 이 API를 폴링해 `status: "completed"` 가 되면 `background_music`을 사용한다.

### API

```
GET /api/v1/lanterns/{lantern_code}

Response 200:
{
  "lantern_code": "550e8400-e29b-41d4-a716-446655440000",
  "name": "홍길동",
  "image_paths": [
    "/uploads/lanterns/550e8400-.../image_1.jpg",
    "/uploads/lanterns/550e8400-.../image_2.jpg",
    "/uploads/lanterns/550e8400-.../image_3.jpg"
  ],
  "background_music": "default_bgm.mp3",
  "status": "completed",
  "created_at": "2026-06-04T12:00:00Z"
}
```

### 응답 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `lantern_code` | string | 랜턴 고유 코드 |
| `name` | string | 사용자 이름 |
| `image_paths` | string[] | 이미지 경로 3개 |
| `background_music` | string \| null | 배경음 파일명 (pending 중 null) |
| `status` | string | `pending` \| `completed` |
| `created_at` | datetime | 생성 시각 |

### 예외 처리

| 조건 | HTTP |
|---|---|
| `lantern_code`가 DB에 없는 경우 | 404 |
