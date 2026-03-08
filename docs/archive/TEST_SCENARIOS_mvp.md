# 단감(DAN-GAM) E2E 테스트 시나리오

> 작성일: 2026-03-07
> 범위: Lv1 MVP (M01~M09 백엔드 + 프론트엔드 스모크)

---

## 실행 환경

```bash
# 서비스 기동
docker compose up -d

# 헬스체크
curl http://localhost:8000/health
# → {"success": true, "data": {"status": "healthy"}, "error": null}
```

---

## 시나리오 1: 기본 인증 플로우 (M01 AUTH)

### S01-01 — SMS 발송 성공

```
요청: POST /api/v1/auth/sms/send
      { "phone": "01011112222" }

기대: 200 OK
      { "success": true, "data": { "message": "..." }, "error": null }
```

### S01-02 — 신규 사용자 OTP 인증 → JWT 취득

```
전제: S01-01 완료 후 OTP 수신
요청: POST /api/v1/auth/sms/verify
      { "phone": "01011112222", "code": "<6자리>" }

기대: 200 OK
      {
        "success": true,
        "data": {
          "access_token": "<JWT>",
          "refresh_token": "<JWT>",
          "token_type": "bearer",
          "is_new_user": true
        }
      }
확인: is_new_user == true (최초 로그인)
```

### S01-03 — 기존 사용자 재인증

```
전제: 이미 가입된 전화번호로 재인증
요청: 동일 (S01-01 → S01-02)
기대: is_new_user == false
```

### S01-04 — 토큰 갱신

```
요청: POST /api/v1/auth/token/refresh
      { "refresh_token": "<refresh_token>" }

기대: 200 OK
      { "success": true, "data": { "access_token": "<새 JWT>" } }
```

### S01-05 — [오류] OTP 5회 실패 → 30분 차단

```
전제: 동일 번호 오류 OTP 5회 전송
요청: POST /api/v1/auth/sms/verify (6번째)
기대: 429 Too Many Requests (또는 400)
      { "success": false, "error": { "code": "DNNG-AUTH-005", ... } }
```

### S01-06 — [오류] 만료된 OTP 사용 (3분 초과)

```
전제: SMS 발송 후 3분 이상 경과
요청: POST /api/v1/auth/sms/verify
기대: 400 Bad Request
      { "success": false, "error": { "code": "DNNG-AUTH-003", ... } }
```

---

## 시나리오 2: 작업 매칭 완전 플로우 (M03 MATCHING + M05 CHAT)

### 사전 준비

```
사용자 A: 의뢰자 (phone: "01033334444")
사용자 B: 작업자 (phone: "01055556666")
A 위치: 충남 논산시 (lat=36.19, lng=127.09)
B 위치: 논산시 인근 (A로부터 3km)
```

### S02-01 — 의뢰자 A: 벼베기 작업 등록

```
요청: POST /api/v1/jobs  [Auth: A의 access_token]
      {
        "title": "논산 벼베기 작업 구합니다",
        "category": "RICE_HARVESTING",
        "location_lat": 36.19,
        "location_lng": 127.09,
        "location_address": "충남 논산시 강경읍",
        "area_pyeong": 3000,
        "pay_type": "PER_PYEONG",
        "pay_amount": 5000,
        "work_date": "2026-09-15",
        "is_urgent": true
      }

기대: 201 Created
      { "success": true, "data": { "id": "<job_id>", "status": "OPEN", ... } }
확인: status == "OPEN", is_urgent == true
```

### S02-02 — 작업자 B: 반경 5km 내 작업 목록 조회 → A의 작업 확인

```
요청: GET /api/v1/jobs?lat=36.17&lng=127.10&radius_km=5  [Auth: B]
기대: 200 OK, items에 S02-01에서 등록한 작업 포함
확인: distance_km < 5.0, is_urgent == true 작업 목록 최상단
```

### S02-03 — 작업자 B: WORKER 역할로 전환 후 지원

```
역할 전환:
  PATCH /api/v1/users/me/role-switch
  { "role": "WORKER" }
  → 200 OK

지원:
  POST /api/v1/jobs/<job_id>/applications
  { "message": "콤바인 보유, 논산 지역 경험 10년" }
  → 201 Created
  { "success": true, "data": { "status": "PENDING", ... } }
```

### S02-04 — 의뢰자 A: 지원 목록 확인 → B 선택

```
지원 목록 조회:
  GET /api/v1/jobs/<job_id>/applications  [Auth: A]
  → B의 지원 확인

B 선택:
  POST /api/v1/jobs/<job_id>/applications/<B_user_id>/select
  → 200 OK
  { "success": true, "data": { "status": "SELECTED", ... } }
```

### S02-05 — 시스템: 매칭 완료 + 채팅방 자동 생성 확인

```
작업 상태 확인:
  GET /api/v1/jobs/<job_id>
  → status == "MATCHED"

채팅방 목록 조회 (A 또는 B):
  GET /api/v1/chat/rooms
  → items에 job_id가 <job_id>인 채팅방 존재 확인
```

### S02-06 — A↔B: WebSocket으로 메시지 교환

```
A 연결: WS /api/v1/chat/ws/chat/<room_id>?token=<A_access_token>
B 연결: WS /api/v1/chat/ws/chat/<room_id>?token=<B_access_token>

A 발송:
  { "type": "message", "content": "안녕하세요, 언제 오실 수 있나요?" }

B 수신 확인:
  { "type": "message", "sender_id": "<A_id>", "content": "안녕하세요..." }

B 발송:
  { "type": "message", "content": "9월 15일 오전 6시 가능합니다." }

A 수신 확인: 메시지 정상 수신
```

### S02-07 — 의뢰자 A: IN_PROGRESS → COMPLETED 상태 전이

```
PATCH /api/v1/jobs/<job_id>/status  [Auth: A]
{ "status": "IN_PROGRESS" }
→ 200 OK, status == "IN_PROGRESS"

PATCH /api/v1/jobs/<job_id>/status
{ "status": "COMPLETED" }
→ 200 OK, status == "COMPLETED"
```

### S02-08 — A→B 후기 작성

```
요청: POST /api/v1/reviews  [Auth: A]
      {
        "job_id": "<job_id>",
        "reviewee_id": "<B_id>",
        "rating": 5,
        "comment": "정말 빠르게 해주셨어요. 내년에도 꼭 부탁드릴게요."
      }

기대: 201 Created
확인: B의 avg_rating 업데이트 확인
  GET /api/v1/reviews/users/<B_id>
  → avg_rating > 0
```

### S02-09 — [오류] 반경 30km 외 작업자 → 목록 미표시

```
요청: GET /api/v1/jobs?lat=37.50&lng=127.00&radius_km=5  (서울 위치)
기대: items 비어있음 또는 논산 작업 미포함
```

### S02-10 — [오류] 의뢰자 A가 본인 작업에 지원 시도

```
요청: POST /api/v1/jobs/<job_id>/applications  [Auth: A]
기대: 403 Forbidden
      { "success": false, "error": { "code": "DNNG-MATCH-003", ... } }
```

---

## 시나리오 3: 건조시설 예약 및 수율 기록 (M04 DRYING)

### 사전 준비

```
사용자 C: 건조시설 운영자 (phone: "01077778888")
사용자 A: 의뢰자 (S02에서 사용한 계정)
```

### S03-01 — 운영자 C: 건조시설 등록

```
요청: POST /api/v1/drying/facilities  [Auth: C]
      {
        "name": "논산 중앙 건조장",
        "location_address": "충남 논산시 중앙로 100",
        "location_lat": 36.19,
        "location_lng": 127.09,
        "capacity_kg": 5000,
        "available_crops": ["벼", "보리", "콩"],
        "description": "최신 순환식 건조기 보유"
      }

기대: 201 Created
      { "success": true, "data": { "id": "<facility_id>", ... } }
```

### S03-02 — 의뢰자 A: 건조시설 예약

```
요청: POST /api/v1/drying/reservations  [Auth: A]
      {
        "facility_id": "<facility_id>",
        "input_kg": 1000,
        "scheduled_date": "2026-09-20",
        "notes": "벼베기 직후 반입 예정"
      }

기대: 201 Created
      { "success": true, "data": { "status": "PENDING", ... } }
```

### S03-03 — 운영자 C: 예약 승인

```
요청: PATCH /api/v1/drying/reservations/<reservation_id>/approve  [Auth: C]
기대: 200 OK
      { "success": true, "data": { "status": "APPROVED", ... } }
```

### S03-04 — 운영자 C: 건조 완료 기록

```
요청: PATCH /api/v1/drying/reservations/<reservation_id>/complete  [Auth: C]
      {
        "output_kg": 850,
        "moisture_pct": 14.5,
        "color_grade": "A",
        "quality_grade": "1등급"
      }

기대: 200 OK
      {
        "success": true,
        "data": {
          "status": "COMPLETED",
          "output_kg": 850,
          "moisture_pct": 14.5,
          ...
        }
      }
```

### S03-05 — 시스템: 수율 자동계산 확인

```
응답에서 yield_pct 확인:
  yield_pct = (850 / 1000) × 100 = 85.00

기대: yield_pct == 85.0
```

### S03-06 — [오류] output_kg > input_kg

```
요청: PATCH /api/v1/drying/reservations/<id>/complete
      { "output_kg": 1100, "moisture_pct": 14.5 }  (input_kg=1000)

기대: 400 Bad Request
      { "success": false, "error": { "code": "DNNG-DRY-003", ... } }
```

---

## 시나리오 4: 오류 처리 및 경계값 테스트

### S04-01 — [경계] 채팅 메시지 정확히 1000자 → 성공

```
WebSocket 발송:
  { "type": "message", "content": "a" × 1000 }

기대: 정상 브로드캐스트
      { "type": "message", "content": "aaa...aaa" (1000자) }
```

### S04-02 — [경계] 채팅 메시지 1001자 → 거부

```
WebSocket 발송:
  { "type": "message", "content": "a" × 1001 }

기대: 오류 응답
      { "type": "error", "error": "메시지는 1000자를 초과할 수 없습니다." }
```

### S04-03 — [경계] 반경 30km 초과 요청 → 30km로 clamping

```
요청: GET /api/v1/jobs?lat=36.19&lng=127.09&radius_km=100
기대: 200 OK (30km 기준으로 자동 clamping, 오류 아님)
확인: 반환된 작업들의 distance_km <= 30.0
```

### S04-04 — [권한] WORKER 역할 사용자가 작업 등록 시도

```
전제: current_role == "WORKER"인 사용자
요청: POST /api/v1/jobs
기대: 403 Forbidden
      { "success": false, "error": { "code": "DNNG-MATCH-002", ... } }
```

### S04-05 — [권한] 타인 작업에 select_applicant 시도

```
전제: 작업 소유자가 아닌 사용자 D
요청: POST /api/v1/jobs/<job_id>/applications/<user_id>/select  [Auth: D]
기대: 403 Forbidden
      { "success": false, "error": { "code": "DNNG-MATCH-005", ... } }
```

### S04-06 — [인증] 만료된 access_token 사용

```
요청: GET /api/v1/users/me  [Authorization: Bearer <expired_token>]
기대: 401 Unauthorized
      { "success": false, "error": { "code": "DNNG-AUTH-002", ... } }
```

### S04-07 — [정산] 의뢰자가 협의 금액 기록

```
전제: job status == "MATCHED" 이상
요청: PATCH /api/v1/jobs/<job_id>/payment  [Auth: A]
      { "agreed_amount": 150000, "notes": "3000평 × 50원" }

기대: 200 OK
      { "success": true, "data": { "agreed_amount": 150000, "status": "PENDING" } }

정산 확인:
  POST /api/v1/jobs/<job_id>/payment/confirm
  → { "status": "CONFIRMED", "confirmed_at": "..." }
```

### S04-08 — [알림] FCM 토큰 등록

```
요청: POST /api/v1/notifications/fcm-token  [Auth: A]
      { "token": "fake-fcm-token-for-test", "device_type": "android" }

기대: 200 OK
      { "success": true, "data": { "message": "FCM 토큰이 등록되었습니다." } }
```

### S04-09 — [관리자] 비관리자가 admin 엔드포인트 접근

```
요청: GET /api/v1/admin/stats  [Auth: 일반 사용자 토큰]
기대: 403 Forbidden
      { "success": false, "error": { "code": "DNNG-ADMIN-001", ... } }
```

---

## 검증 스크립트 (curl 기반)

```bash
# 1. 인증
PHONE="01099990000"
curl -s -X POST http://localhost:8000/api/v1/auth/sms/send \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\"}" | jq .

# OTP는 개발 환경에서 로그 확인
# docker logs danngam_rev2-backend-1 | grep "OTP"

# 2. 인증 후 토큰 획득 (OTP를 실제 값으로 교체)
RESP=$(curl -s -X POST http://localhost:8000/api/v1/auth/sms/verify \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\", \"code\": \"123456\"}")
TOKEN=$(echo $RESP | jq -r '.data.access_token')

# 3. 작업 등록
curl -s -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "논산 벼베기 테스트",
    "category": "RICE_HARVESTING",
    "location_lat": 36.19,
    "location_lng": 127.09,
    "area_pyeong": 3000,
    "pay_type": "PER_PYEONG",
    "is_urgent": true
  }' | jq .

# 4. Swagger UI 확인
open http://localhost:8000/docs
```

---

## 자동화 테스트 실행

```bash
# Backend 단위 테스트
cd backend
pytest tests/ -v --tb=short

# 특정 모듈 테스트
pytest tests/test_auth.py -v        # M01 AUTH
pytest tests/test_users.py -v       # M02 USER
pytest tests/test_jobs.py -v        # M03 MATCHING
pytest tests/test_drying.py -v      # M04 DRYING
pytest tests/test_chat.py -v        # M05 CHAT
pytest tests/test_reviews.py -v     # M07 REVIEW

# Frontend 빌드 확인
cd frontend && npm install && npm run build

# Flutter 정적 분석
cd mobile && flutter analyze
```
