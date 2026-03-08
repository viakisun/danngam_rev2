# SDD_SKELETON.md — 단감(DAN-GAM) 모듈별 명세

> Spec-Driven Definition | 비아 방법론 v6 | Phase 1 (Lv1 MVP)
> 에러 코드 형식: `DNNG-{MODULE}-{NUMBER}`
> 응답 형식: `{ "success": bool, "data": {}, "error": { "code": str, "message": str } }`

---

## M01 AUTH — 핸드폰 인증 + JWT

### 개요
- **역할**: SMS OTP 인증 기반 회원가입/로그인, JWT 발급
- **의존**: 없음 (최초 모듈)
- **Redis 사용**: OTP 저장, 쿨다운, 실패 횟수 카운터

### API Endpoints

#### POST /api/v1/auth/sms/send
```
Request:
  { "phone": "01012345678" }

Response 200:
  { "success": true, "data": { "cooldown_seconds": 60 } }

Errors:
  DNNG-AUTH-001: 잘못된 전화번호 형식
  DNNG-AUTH-002: 쿨다운 중 (60초)
  DNNG-AUTH-003: 30분 차단 (실패 5회 초과)
```

#### POST /api/v1/auth/sms/verify
```
Request:
  { "phone": "01012345678", "code": "123456" }

Response 200:
  {
    "success": true,
    "data": {
      "access_token": "...",
      "refresh_token": "...",
      "token_type": "bearer",
      "is_new_user": true
    }
  }

Errors:
  DNNG-AUTH-004: 코드 불일치
  DNNG-AUTH-005: 코드 만료 (3분)
  DNNG-AUTH-006: 실패 횟수 증가 (n/5)
  DNNG-AUTH-003: 30분 차단
```

#### POST /api/v1/auth/token/refresh
```
Request:
  { "refresh_token": "..." }

Response 200:
  { "success": true, "data": { "access_token": "...", "token_type": "bearer" } }

Errors:
  DNNG-AUTH-007: 만료된 refresh_token
  DNNG-AUTH-008: 유효하지 않은 refresh_token
```

### 비즈니스 로직 제약사항
- SMS OTP: 6자리 숫자, 유효 시간 3분, Redis TTL=180s
- 발송 쿨다운: 60초, Redis key `sms:cooldown:{phone}` TTL=60s
- 실패 카운터: Redis key `sms:fail:{phone}`, 5회 초과 시 30분 차단
- 차단 key: `sms:block:{phone}` TTL=1800s
- access_token: 1시간 (HS256)
- refresh_token: 30일, DB 저장 (revoke 가능)
- 전화번호 정규화: 01X-XXXX-XXXX → 01XXXXXXXXX (10-11자리)

### Test Cases

| TC | 시나리오 | 입력 | 기대 결과 |
|----|---------|------|---------|
| TC01 | SMS 정상 발송 | 올바른 전화번호 | 200, cooldown_seconds=60 |
| TC02 | 쿨다운 중 재발송 | 60초 이내 재요청 | 400, DNNG-AUTH-002 |
| TC03 | OTP 정상 인증 | 올바른 코드 | 200, tokens 반환 |
| TC04 | 잘못된 OTP | 틀린 코드 | 400, DNNG-AUTH-004 |
| TC05 | 만료 OTP | 3분 후 코드 | 400, DNNG-AUTH-005 |
| TC06 | 5회 실패 → 차단 | 5회 틀린 코드 | 400, DNNG-AUTH-003 |
| TC07 | refresh_token 갱신 | 유효한 refresh_token | 200, 새 access_token |

### Atomic Prompts

**AP-01**: `app/models/user.py` — User 모델
```python
# 필드: id(UUID), phone(unique), name, profile_image_url,
#       current_role(ENUM: requester/worker), is_active, created_at, updated_at
# refresh_token 컬럼 포함
# Alembic 마이그레이션: alembic revision --autogenerate -m "create_user_table"
```

**AP-02**: `app/services/sms_service.py` — SMS 서비스
```python
# AbstractSMSService (interface)
# MockSMSService (개발용: 코드를 Redis에 저장 + 로그 출력)
# settings.SMS_PROVIDER로 분기 (dev=mock, prod=coolsms)
```

**AP-03**: `app/routers/auth.py` — 인증 라우터
```python
# POST /api/v1/auth/sms/send → send_sms_code()
# POST /api/v1/auth/sms/verify → verify_sms_code()
# POST /api/v1/auth/token/refresh → refresh_access_token()
# 모든 Redis 조작은 async
```

**AP-04**: `app/utils/jwt.py` — JWT 유틸리티
```python
# create_access_token(user_id, role) → str
# create_refresh_token(user_id) → str
# verify_token(token) → TokenPayload
# TokenPayload: user_id, role, exp, type("access"/"refresh")
```

**AP-05**: `tests/test_auth.py` — 인증 테스트 (TC01~07)
```python
# pytest-asyncio 사용
# TestClient or AsyncClient (httpx)
# Redis mock (fakeredis)
```

---

## M02 USER — 기본 프로필 + 역할 전환

### 개요
- **역할**: 사용자 프로필 조회/수정, 역할(의뢰자↔작업자) 전환
- **의존**: M01 AUTH (User 모델, JWT)

### API Endpoints

#### GET /api/v1/users/me
```
Headers: Authorization: Bearer {access_token}

Response 200:
  {
    "success": true,
    "data": {
      "id": "uuid",
      "phone": "01012345678",
      "name": "홍길동",
      "profile_image_url": null,
      "current_role": "requester",
      "created_at": "2026-03-07T00:00:00Z"
    }
  }
```

#### PUT /api/v1/users/me
```
Request:
  { "name": "홍길동", "profile_image_url": "https://..." }

Response 200:
  { "success": true, "data": { ...updated_user } }

Errors:
  DNNG-USER-001: 이름 1~20자 제한
```

#### POST /api/v1/users/me/role-switch
```
Request:
  { "role": "worker" }  # or "requester"

Response 200:
  { "success": true, "data": { "current_role": "worker" } }

Errors:
  DNNG-USER-002: 이미 해당 역할
  DNNG-USER-003: 유효하지 않은 역할값
```

### 비즈니스 로직 제약사항
- 역할: `requester`(의뢰자) / `worker`(작업자) — 동일 계정이 양쪽 가능
- 역할 전환은 즉시 반영, 이력 미저장 (Lv1)
- 프로필 이미지: URL만 저장 (업로드 서버 별도, Lv2)
- 이름 필드: 1~20자, 공백 불가

### Test Cases

| TC | 시나리오 | 기대 결과 |
|----|---------|---------|
| TC01 | 내 프로필 조회 | 200, user 정보 반환 |
| TC02 | 이름 수정 | 200, 수정된 name 반환 |
| TC03 | 이름 빈값 | 400, DNNG-USER-001 |
| TC04 | requester → worker 전환 | 200, current_role=worker |
| TC05 | 동일 역할로 전환 | 400, DNNG-USER-002 |

### Atomic Prompts

**AP-01**: `app/schemas/user.py`
```python
# UserResponse, UserUpdate(name, profile_image_url), RoleSwitchRequest
```

**AP-02**: `app/routers/users.py`
```python
# GET /api/v1/users/me → get_my_profile()
# PUT /api/v1/users/me → update_my_profile()
# POST /api/v1/users/me/role-switch → switch_role()
# 모두 get_current_user dependency 사용
```

**AP-03**: `app/services/user_service.py`
```python
# get_user_by_id(db, user_id) → User
# update_user(db, user, update_data) → User
# switch_user_role(db, user, new_role) → User
```

**AP-04**: `tests/test_users.py` (TC01~05)

---

## M03 MATCHING — 농작업 매칭

### 개요
- **역할**: 작업 등록, GPS 반경 필터 목록, 지원/선택, 상태 전이
- **의존**: M01 AUTH, M02 USER

### API Endpoints

#### POST /api/v1/jobs
```
Request:
  {
    "title": "벼베기 작업 구합니다",
    "category": "rice_harvesting",
    "description": "...",
    "location_lat": 36.1234,
    "location_lng": 127.5678,
    "location_address": "충남 논산시 ...",
    "area_pyeong": 3000,
    "desired_date": "2026-09-15",
    "pay_type": "per_pyeong",
    "pay_amount": 5000,
    "equipment_tags": ["콤바인"],
    "is_urgent": false
  }

Response 201:
  { "success": true, "data": { ...job } }
```

#### GET /api/v1/jobs
```
Query params:
  ?lat=36.12&lng=127.56&radius_km=5&category=rice_harvesting
  &cursor=xxx&limit=20

Response 200:
  {
    "success": true,
    "data": {
      "items": [...jobs],
      "next_cursor": "xxx",
      "total": 42
    }
  }
```

#### GET /api/v1/jobs/{job_id}
```
Response 200: { "success": true, "data": { ...job_detail } }
Errors: DNNG-MATCH-001: 작업 없음
```

#### POST /api/v1/jobs/{job_id}/apply
```
Request: { "message": "작업 가능합니다. 경력 5년입니다." }
Response 201: { "success": true, "data": { ...application } }
Errors:
  DNNG-MATCH-002: 이미 지원함
  DNNG-MATCH-003: 본인 작업에 지원 불가
  DNNG-MATCH-004: 마감된 작업
```

#### POST /api/v1/jobs/{job_id}/select/{applicant_id}
```
Response 200: { "success": true, "data": { "status": "MATCHED" } }
Errors:
  DNNG-MATCH-005: 권한 없음 (작업 등록자만)
  DNNG-MATCH-006: 이미 매칭됨
```

#### PATCH /api/v1/jobs/{job_id}/status
```
Request: { "status": "IN_PROGRESS" }  # or "COMPLETED"
Response 200: { "success": true, "data": { "status": "IN_PROGRESS" } }
```

### 비즈니스 로직 제약사항

**작업 카테고리 (농업 용어 정확히)**:
```
rice_harvesting → 벼베기
sweet_potato_digging → 고구마 캐기
garlic_planting → 마늘 심기
drone_spraying → 드론 방제
rotary_work → 로터리 작업
other → 기타
```

**상태 전이**:
```
OPEN → MATCHED (select 호출)
MATCHED → IN_PROGRESS (작업 시작)
IN_PROGRESS → COMPLETED (작업 완료)
OPEN → CANCELLED (취소)
```

**GPS 필터 (Haversine)**:
- 기본 반경 5km, 최대 30km
- `?radius_km` 미제공 시 5km 적용
- is_urgent=true 작업은 목록 최상단 정렬

**면적 단위**: `area_pyeong` (평) — 1평 = 3.3058 m²

**페이 타입**: `per_pyeong`(평당), `total`(총액), `negotiable`(협의)

### Test Cases

| TC | 시나리오 | 기대 결과 |
|----|---------|---------|
| TC01 | 작업 등록 | 201, job 반환 |
| TC02 | GPS 반경 내 목록 조회 | 200, 반경 내 작업만 |
| TC03 | 반경 외 작업 미포함 | 200, 결과 없음 |
| TC04 | 긴급 작업 최상단 | 200, is_urgent 먼저 |
| TC05 | 작업 지원 | 201, application 반환 |
| TC06 | 중복 지원 | 400, DNNG-MATCH-002 |
| TC07 | 작업자 선택 | 200, status=MATCHED |
| TC08 | 상태 전이 (COMPLETED) | 200, status=COMPLETED |

### Atomic Prompts

**AP-01**: `app/models/job.py`
```python
# Job: id(UUID), requester_id(FK→User), title, category(Enum),
#      description, location_lat, location_lng, location_address,
#      area_pyeong, desired_date, pay_type(Enum), pay_amount,
#      equipment_tags(ARRAY), is_urgent, status(Enum), created_at
# JobApplication: id, job_id(FK), applicant_id(FK), message,
#                 status(Enum: pending/selected/rejected), created_at
# Alembic migration
```

**AP-02**: `app/schemas/job.py`
```python
# JobCreate, JobResponse, JobListResponse(cursor-based),
# ApplicationCreate, ApplicationResponse
```

**AP-03**: `app/utils/geo.py`
```python
# haversine(lat1, lng1, lat2, lng2) → float(km)
# filter_jobs_by_radius(jobs, center_lat, center_lng, radius_km) → list
```

**AP-04**: `app/routers/jobs.py`
```python
# POST /api/v1/jobs → create_job() [requester 역할 필요]
# GET  /api/v1/jobs → list_jobs() [GPS 파라미터 + cursor]
# GET  /api/v1/jobs/{id} → get_job()
# POST /api/v1/jobs/{id}/apply → apply_job() [worker 역할 필요]
# POST /api/v1/jobs/{id}/select/{app_id} → select_applicant()
# PATCH /api/v1/jobs/{id}/status → update_job_status()
```

**AP-05**: `app/services/matching_service.py`
```python
# create_job(db, requester_id, job_data) → Job
# list_jobs_by_gps(db, lat, lng, radius_km, cursor, limit) → (jobs, next_cursor)
# apply_to_job(db, job_id, applicant_id, message) → JobApplication
# select_applicant(db, job_id, requester_id, applicant_id) → Job
# update_job_status(db, job_id, user_id, new_status) → Job
```

**AP-06**: `tests/test_jobs.py` (TC01~08)

---

## M04 DRYING — 건조시설 예약 (핵심 차별화)

### 개요
- **역할**: 건조시설 등록, 예약, 수율/품질 기록
- **의존**: M01 AUTH, M02 USER
- **차별화**: 수율 자동계산 + 품질 데이터 축적

### API Endpoints

#### POST /api/v1/drying/facilities
```
Request:
  {
    "name": "논산 건조시설",
    "location_address": "충남 논산시 ...",
    "location_lat": 36.1234,
    "location_lng": 127.5678,
    "capacity_kg": 5000,
    "price_per_kg": 50,
    "description": "...",
    "available_crops": ["rice", "barley"]
  }

Response 201: { "success": true, "data": { ...facility } }
```

#### GET /api/v1/drying/facilities
```
Query: ?lat=36.12&lng=127.56&radius_km=10&cursor=xxx&limit=20
Response 200: cursor-based 목록
```

#### POST /api/v1/drying/reservations
```
Request:
  {
    "facility_id": "uuid",
    "crop_type": "rice",
    "input_kg": 1000.0,
    "scheduled_date": "2026-09-20",
    "notes": "..."
  }

Response 201: { "success": true, "data": { ...reservation } }
Errors:
  DNNG-DRY-001: 시설 없음
  DNNG-DRY-002: 예약 불가 날짜 (용량 초과)
```

#### PATCH /api/v1/drying/reservations/{id}/complete
```
Request:
  {
    "output_kg": 850.0,
    "moisture_pct": 14.5,
    "color_grade": "A",
    "quality_grade": "1등급",
    "notes": "..."
  }

Response 200:
  {
    "success": true,
    "data": {
      "yield_pct": 85.0,
      "output_kg": 850.0,
      "moisture_pct": 14.5,
      "color_grade": "A",
      "quality_grade": "1등급"
    }
  }
```

#### GET /api/v1/drying/reservations/{id}
```
Response 200: 예약 상세 + 수율/품질 정보
```

### 비즈니스 로직 제약사항

**수율 계산**: `yield_pct = (output_kg / input_kg) * 100` (소수점 2자리)
- output_kg > input_kg 금지 (에러: DNNG-DRY-003)
- yield_pct < 50% 경고 플래그 설정

**예약 상태 전이**:
```
PENDING → APPROVED (시설 운영자 승인)
APPROVED → IN_DRYING (건조 시작)
IN_DRYING → COMPLETED (complete API 호출 → 수율 계산)
PENDING → CANCELLED
```

**품질 지표**:
- `moisture_pct`: 수분함량 (%), 벼 기준 14~15% 적정
- `color_grade`: 색상 등급 (A/B/C)
- `quality_grade`: 품질 등급 (1등급/2등급/등외)

### Test Cases

| TC | 시나리오 | 기대 결과 |
|----|---------|---------|
| TC01 | 시설 등록 | 201, facility 반환 |
| TC02 | 예약 생성 | 201, status=PENDING |
| TC03 | 예약 완료 + 수율 계산 | 200, yield_pct=85.0 |
| TC04 | 수율 계산 정확도 | input=1000, output=850 → 85.00% |
| TC05 | output > input | 400, DNNG-DRY-003 |

### Atomic Prompts

**AP-01**: `app/models/drying.py`
```python
# DryingFacility: id, operator_id(FK→User), name, location_*,
#                 capacity_kg, price_per_kg, available_crops(ARRAY), is_active
# DryingReservation: id, facility_id(FK), requester_id(FK), crop_type,
#                    input_kg, output_kg(nullable), scheduled_date,
#                    status(Enum), yield_pct(nullable, computed),
#                    moisture_pct, color_grade, quality_grade, notes
# Alembic migration
```

**AP-02**: `app/schemas/drying.py`
```python
# FacilityCreate, FacilityResponse
# ReservationCreate, ReservationResponse, ReservationComplete
```

**AP-03**: `app/routers/drying.py`
```python
# POST /api/v1/drying/facilities → register_facility()
# GET  /api/v1/drying/facilities → list_facilities()
# POST /api/v1/drying/reservations → create_reservation()
# GET  /api/v1/drying/reservations/{id} → get_reservation()
# PATCH /api/v1/drying/reservations/{id}/complete → complete_reservation()
# PATCH /api/v1/drying/reservations/{id}/approve → approve_reservation()
```

**AP-04**: `app/services/drying_service.py`
```python
# calculate_yield(input_kg, output_kg) → float  # 핵심 비즈니스 로직
# create_reservation(db, facility_id, requester_id, data) → DryingReservation
# complete_reservation(db, reservation_id, operator_id, complete_data) → DryingReservation
```

**AP-05**: `tests/test_drying.py` (TC01~05)
```python
# calculate_yield 단위 테스트 필수
# 소수점 2자리 정확도 검증
```

---

## M05 CHAT — 실시간 1:1 채팅

### 개요
- **역할**: WebSocket 기반 1:1 채팅, 매칭 성사 시 자동 채팅방 생성
- **의존**: M01 AUTH, M03 MATCHING (Job → ChatRoom 연결)

### API Endpoints

#### GET /api/v1/chat/rooms
```
Response 200:
  {
    "success": true,
    "data": {
      "items": [
        {
          "id": "uuid",
          "job_id": "uuid",
          "job_title": "벼베기 작업 구합니다",
          "other_user": { "id": "uuid", "name": "홍길동" },
          "last_message": "안녕하세요",
          "last_message_at": "...",
          "unread_count": 2
        }
      ]
    }
  }
```

#### GET /api/v1/chat/rooms/{room_id}/messages
```
Query: ?cursor=xxx&limit=30
Response 200: cursor-based 메시지 목록 (최신순)
```

#### POST /api/v1/chat/rooms/{room_id}/read
```
Response 200: { "success": true, "data": { "read_count": 5 } }
```

#### WebSocket: ws://host/ws/chat/{room_id}?token={access_token}

```
Connect: JWT 검증 → 참여자 확인
Send: { "type": "message", "content": "안녕하세요" }
Receive: {
  "type": "message",
  "message_id": "uuid",
  "sender_id": "uuid",
  "content": "안녕하세요",
  "created_at": "..."
}
Receive (read): { "type": "read", "reader_id": "uuid" }
```

### 비즈니스 로직 제약사항
- 채팅방 생성: M03 MATCHING의 `select_applicant()` 성공 시 자동 생성
- 채팅방 참여자: job.requester_id + selected applicant_id (2인)
- 메시지 최대 길이: 1,000자
- 읽음 처리: WebSocket 연결 시 + POST /read 호출 시
- 메시지 저장: PostgreSQL (영구 보관)
- 실시간 브로드캐스트: FastAPI WebSocket ConnectionManager
- 오프라인 사용자: DB 저장 후 연결 시 히스토리 조회

### Test Cases

| TC | 시나리오 | 기대 결과 |
|----|---------|---------|
| TC01 | 매칭 성사 → 채팅방 자동 생성 | ChatRoom 생성 확인 |
| TC02 | 채팅방 목록 조회 | 200, 참여 채팅방 반환 |
| TC03 | 메시지 히스토리 조회 | 200, cursor-based |
| TC04 | 읽음 처리 | 200, unread_count=0 |
| TC05 | 1001자 메시지 | 400, DNNG-CHAT-001 |

### Atomic Prompts

**AP-01**: `app/models/chat.py`
```python
# ChatRoom: id, job_id(FK→Job), requester_id(FK), worker_id(FK), created_at
# ChatMessage: id, room_id(FK), sender_id(FK), content(max 1000),
#              is_read, read_at(nullable), created_at
# Alembic migration
```

**AP-02**: `app/schemas/chat.py`
```python
# ChatRoomResponse, ChatMessageResponse, SendMessageRequest
# WebSocket message schemas (TypedDict or Pydantic)
```

**AP-03**: `app/routers/chat.py`
```python
# GET  /api/v1/chat/rooms → list_chat_rooms()
# GET  /api/v1/chat/rooms/{id}/messages → get_messages()
# POST /api/v1/chat/rooms/{id}/read → mark_as_read()
```

**AP-04**: `app/routers/chat_ws.py`
```python
# ConnectionManager class (연결 풀 관리)
# WS /ws/chat/{room_id}?token=... → websocket_endpoint()
# JWT 검증 → 참여자 확인 → 메시지 DB 저장 + 브로드캐스트
```

**AP-05**: `tests/test_chat.py` (TC01~05)
```python
# WebSocket 테스트: starlette.testclient.TestClient WebSocket context
```

---

## M06 NOTIFY — 앱 푸시 알림 (개요)

### Lv1 MVP 범위
- FCM(Firebase Cloud Messaging) 기반 푸시
- 알림 목록 API (읽음/안읽음)
- 트리거: 작업 지원, 매칭 성사, 채팅 메시지

### 주요 API
- `POST /api/v1/notifications/fcm-token` — 디바이스 토큰 등록
- `GET /api/v1/notifications` — 알림 목록 (cursor-based)
- `POST /api/v1/notifications/{id}/read` — 읽음 처리

---

## M07 REVIEW — 별점 + 한줄 후기 (개요)

### Lv1 MVP 범위
- 작업 완료(COMPLETED) 후 쌍방 평가
- 별점(1~5) + 한줄 후기(최대 200자)
- 평균 평점 집계 (User 모델에 avg_rating 컬럼)

### 주요 API
- `POST /api/v1/reviews` — 후기 작성
- `GET /api/v1/reviews/users/{user_id}` — 사용자 후기 목록

---

## M08 PAYMENT — 금액 협의 + 정산 확인 (개요)

### Lv1 MVP 범위
- 실제 결제 없음 (금액 협의 기록만)
- 채팅 내에서 협의된 금액을 Job에 기록
- 정산 확인 상태 (requester 확인 완료)

### 주요 API
- `PATCH /api/v1/jobs/{id}/payment` — 협의 금액 기록
- `POST /api/v1/jobs/{id}/payment/confirm` — 정산 확인

---

## M09 ADMIN — 관리자 대시보드 (개요)

### Lv1 MVP 범위
- 사용자 목록/조회/정지
- 작업 목록/조회/삭제
- 기본 통계 (일별 가입자, 작업 등록수, 매칭 성공률)

### 주요 API
- `GET /api/v1/admin/users` — 사용자 목록
- `GET /api/v1/admin/jobs` — 작업 목록
- `GET /api/v1/admin/stats` — 기본 통계

---

## M10 MOBILE — Flutter 앱 (개요)

### Lv1 MVP 범위
- **Screen Mapping**:
  - `HomeScreen` → DG-main-dashboard (역할별 진입점)
  - `JobListScreen` → DG-work-list (GPS 기반 작업 목록)
  - `JobDetailScreen` → DG-work-detail (지원하기 포함)
  - `JobCreateScreen` → DG-work-create (작업 등록)
  - `ChatScreen` → DG-chat-room (WebSocket)
  - `MyAppsScreen` → DG-my-applications (내 지원 현황)
  - `JobMapScreen` → DG-work-map (카카오맵)

- **State**: Riverpod (AsyncNotifierProvider)
- **HTTP**: Dio + Retrofit
- **로컬 저장**: SharedPreferences (토큰)
- **지도**: 카카오맵 Flutter SDK

### Atomic Prompts (요약)

**AP-01**: `pubspec.yaml` 의존성 + 프로젝트 구조
**AP-02**: `lib/services/api_service.dart` — Dio 클라이언트 + 인터셉터
**AP-03**: M01 AUTH 화면 (전화번호 입력 → OTP → 홈)
**AP-04**: M03 MATCHING 화면 (JobList + JobDetail + JobCreate)
**AP-05**: M05 CHAT 화면 (ChatRoom + WebSocket)
**AP-06**: M02 USER 화면 (프로필 + 역할 전환)
**AP-07**: 카카오맵 통합 (JobMapScreen)
**AP-08**: 통합 테스트 + 빌드 검증

---

## 공통 에러 코드 참조

| 모듈 | 코드 | 설명 |
|------|------|------|
| AUTH | DNNG-AUTH-001 | 잘못된 전화번호 형식 |
| AUTH | DNNG-AUTH-002 | SMS 쿨다운 중 |
| AUTH | DNNG-AUTH-003 | 계정 30분 차단 |
| AUTH | DNNG-AUTH-004 | OTP 불일치 |
| AUTH | DNNG-AUTH-005 | OTP 만료 |
| AUTH | DNNG-AUTH-006 | OTP 실패 횟수 경고 |
| AUTH | DNNG-AUTH-007 | refresh_token 만료 |
| AUTH | DNNG-AUTH-008 | refresh_token 무효 |
| USER | DNNG-USER-001 | 이름 길이 제한 |
| USER | DNNG-USER-002 | 동일 역할 전환 시도 |
| USER | DNNG-USER-003 | 유효하지 않은 역할값 |
| MATCH | DNNG-MATCH-001 | 작업 없음 |
| MATCH | DNNG-MATCH-002 | 중복 지원 |
| MATCH | DNNG-MATCH-003 | 본인 작업 지원 불가 |
| MATCH | DNNG-MATCH-004 | 마감된 작업 |
| MATCH | DNNG-MATCH-005 | 권한 없음 |
| MATCH | DNNG-MATCH-006 | 이미 매칭됨 |
| DRY | DNNG-DRY-001 | 시설 없음 |
| DRY | DNNG-DRY-002 | 예약 불가 날짜 |
| DRY | DNNG-DRY-003 | output_kg > input_kg |
| CHAT | DNNG-CHAT-001 | 메시지 길이 초과 (1000자) |
| CHAT | DNNG-CHAT-002 | 채팅방 참여자 아님 |
