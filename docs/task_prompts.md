# 단감(DANNGAM) Claude Code AI 태스크 프롬프트 v2

> rev2 project_danngam.md 기준 · 5 EP × 56 프롬프트 · 비아 방법론 v6

---

## 공통 규칙

### Context 파일
모든 프롬프트에서 아래 파일을 참조:
- `@CLAUDE.md` — 프로젝트 전역 규칙
- `@docs/project_danngam.md` — rev2 프로젝트 데이터 (EP, 데모, WBS)

### 커밋 컨벤션
```
{type}({scope}): {description}

type: feat | fix | refactor | test | docs | chore
scope: M01~M12 또는 EP1~EP5
```

### Context 관리
- 0~50%: 자유롭게 작업
- 50~70%: 주의, 큰 작업 시작 자제
- 70~90%: `/compact` 필수
- 90%+: `/clear` 후 재시작

### Molecular Prompt 원칙
- **1 Goal + 1~3 Files + 10분 검증**
- Plan Mode → 계획 확인 → 구현 → lint + test + 수동확인 → 커밋

### EP ↔ Module 매핑 (rev2)

| EP | Module | 코드 경로 |
|----|--------|----------|
| EP1 | M01 AUTH | `backend/app/routers/auth.py`, `mobile/lib/screens/login_screen.dart` |
| EP1 | M09-init ADMIN | `frontend/src/pages/admin/` |
| EP1 | 초기데이터 | `backend/app/routers/equipment.py`, `backend/app/models/equipment.py` |
| EP2 | M02 USER | `backend/app/routers/users.py`, `mobile/lib/screens/` |
| EP2 | M03 MATCHING | `backend/app/routers/jobs.py`, `mobile/lib/screens/` |
| EP2 | M04 DRYING | `backend/app/routers/drying.py`, `mobile/lib/screens/` |
| EP2 | M05 CHAT | `backend/app/routers/chat.py`, `mobile/lib/screens/` |
| EP2 | M06 PAYMENT | `backend/app/routers/payments.py`, `mobile/lib/screens/` |
| EP2 | M10 MOBILE | `mobile/lib/` |
| EP3 | M07 SUBSIDY | `backend/app/routers/subsidy.py`, `frontend/src/pages/admin/subsidy/` |
| EP3 | M11 CREW | `backend/app/routers/crew.py`, `mobile/lib/screens/` |
| EP4 | M08 MFG-RND | `backend/app/routers/manufacturer.py`, `frontend/src/pages/admin/mfg/` |
| EP5 | M09 ANALYTICS | `backend/app/routers/analytics.py`, `frontend/src/pages/admin/analytics/` |
| EP5 | M12 SCHEDULING | `backend/app/routers/scheduling.py`, `frontend/src/pages/admin/scheduling/` |

### 디렉토리 구조 (현재 실제)
```
backend/app/
  routers/       ← 플랫 파일 (auth.py, users.py, jobs.py, ...)
  models/        ← user.py, job.py, drying.py, chat.py, ...
  services/      ← sms_service.py, matching_service.py, ...
  schemas/       ← auth.py, user.py, job.py, ...
  utils/         ← jwt.py, geo.py

frontend/src/
  pages/         ← Dashboard.tsx, JobList.tsx, ... (기존)
  pages/admin/   ← 백오피스 페이지 (신규)
  api/           ← client.ts, auth.ts, jobs.ts, ...
  components/    ← Layout.tsx, PlaceholderPage.tsx

mobile/lib/
  screens/       ← login_screen.dart, home_screen.dart, ...
  providers/     ← auth_provider.dart
  services/      ← api_service.dart
  widgets/       ← placeholder_screen.dart
```

---

## STEP 0: 프로젝트 셋업 + 마이그레이션 (AP-01 준비)

> 기존 MVP 코드를 rev2 구조로 전환. 새 모듈 파일 생성, AUTH 확장, 스키마 확장.

---

### P-000: 프로젝트 구조 확인 + 신규 모듈 스캐폴딩

**Goal**: rev2 모듈 매핑에 맞춰 빈 파일/디렉토리 생성. 기존 코드 변경 없음.

**Files (생성)**:
```
backend/app/routers/equipment.py      ← 장비 카테고리/매칭 DB
backend/app/routers/subsidy.py        ← M07 보조금
backend/app/routers/crew.py           ← M11 대행단
backend/app/routers/manufacturer.py   ← M08 제조사
backend/app/routers/analytics.py      ← M09 분석
backend/app/routers/scheduling.py     ← M12 스케줄링

backend/app/models/equipment.py       ← EquipmentCategory, FarmTask, TaskEquipmentMatch
backend/app/models/field.py           ← Field (필지)
backend/app/models/contract.py        ← Contract (계약)
backend/app/models/subsidy.py         ← SubsidyProgram, SubsidyApplication
backend/app/models/crew.py            ← Crew, CrewMember, CrewOrder
backend/app/models/manufacturer.py    ← Manufacturer, TrialFarm
backend/app/models/scheduling.py      ← EquipmentSchedule, RouteOptimization

backend/app/schemas/equipment.py
backend/app/schemas/field.py
backend/app/schemas/contract.py
backend/app/schemas/subsidy.py
backend/app/schemas/crew.py
backend/app/schemas/manufacturer.py
backend/app/schemas/scheduling.py

backend/app/services/equipment_service.py
backend/app/services/subsidy_service.py
backend/app/services/crew_service.py
backend/app/services/manufacturer_service.py
backend/app/services/analytics_service.py
backend/app/services/scheduling_service.py
backend/app/services/payment_service.py     ← 에스크로 로직

frontend/src/pages/admin/DataMgmt.tsx        ← 백오피스 초기데이터
frontend/src/pages/admin/SubsidyDashboard.tsx
frontend/src/pages/admin/MfgPortal.tsx
frontend/src/pages/admin/Analytics.tsx
frontend/src/pages/admin/ScheduleBoard.tsx
```

**Action**: 각 파일에 모듈 docstring + 빈 라우터/모델 stub만 생성. `main.py`에 라우터 등록은 아직 하지 않음.

**Commit**: `chore: scaffold rev2 module files (M07-M12)`

---

### P-001: AUTH 확장 — 다중 인증 (소셜 + SMS + 이메일)

**Goal**: 기존 SMS-only 인증에 카카오/네이버 소셜 + 이메일 인증 추가.

**WBS**: AP-01 (카카오/네이버 소셜로그인, SMS 알리고, 이메일, JWT, 위치권한)

**Files (수정)**:
- `backend/app/models/user.py` — 필드 추가
- `backend/app/routers/auth.py` — 엔드포인트 추가
- `backend/app/schemas/auth.py` — 스키마 추가

**Files (생성)**:
- `backend/app/services/social_auth_service.py` — 소셜 OAuth 로직
- `backend/app/services/email_service.py` — 이메일 인증 로직

**Schema 확장** (User 모델):
```python
# 기존 필드 유지 + 아래 추가
social_provider: Mapped[str | None]     # "kakao" | "naver" | None
social_id: Mapped[str | None]           # 소셜 고유 ID
email: Mapped[str | None]               # 이메일 (인증용)
email_verified: Mapped[bool]            # 이메일 인증 여부
location_lat: Mapped[float | None]      # GPS 위도
location_lng: Mapped[float | None]      # GPS 경도
```

**API (추가)**:
```
POST /api/v1/auth/social/kakao     ← 카카오 access_token → JWT
POST /api/v1/auth/social/naver     ← 네이버 access_token → JWT
POST /api/v1/auth/email/send       ← 이메일 인증코드 발송
POST /api/v1/auth/email/verify     ← 이메일 인증코드 확인 → JWT
PUT  /api/v1/auth/location         ← GPS 좌표 업데이트
```

**Test**: 소셜 토큰 mock → JWT 발급 확인, 이메일 인증 flow, 기존 SMS 테스트 통과

**Commit**: `feat(M01): add social login (kakao/naver) + email auth`

---

### P-002: Alembic 마이그레이션 — User 확장 + Payment 에스크로 준비

**Goal**: P-001 스키마 변경분 마이그레이션 생성. Payment 모델에 에스크로 필드 추가.

**Files (수정)**:
- `backend/app/models/payment.py` — 에스크로 필드 추가

**Schema 확장** (Payment 모델):
```python
# 기존 필드 유지 + 아래 추가
class PaymentStatus(str, PyEnum):
    PENDING = "PENDING"
    ESCROW_HELD = "ESCROW_HELD"    # 에스크로 보관 중
    RELEASED = "RELEASED"          # 정산 완료
    REFUNDED = "REFUNDED"          # 환불
    CONFIRMED = "CONFIRMED"        # 확인 완료 (기존)

# Payment 모델 추가 필드
pg_transaction_id: Mapped[str | None]   # PG 거래 ID
escrow_amount: Mapped[int | None]       # 에스크로 보관 금액
platform_fee: Mapped[int | None]        # 플랫폼 수수료
settlement_amount: Mapped[int | None]   # 최종 정산 금액
settled_at: Mapped[datetime | None]     # 정산 완료 시각
```

**Action**:
```bash
cd backend && alembic revision --autogenerate -m "extend_user_social_email_payment_escrow"
alembic upgrade head
```

**Test**: 마이그레이션 up/down 정상 동작, 기존 테스트 통과

**Commit**: `feat(M01,M06): migration for social auth + escrow payment fields`

---

## STEP 1: EP1 — 시스템 초기 데이터 구축 + 작업자 온보딩

> 목표일: 2026-05-30 (W13) | WBS: AP-01~AP-07

---

### P-003: 농작업-농기계 매칭 DB 스키마 설계

**Goal**: 시기별 농작업 × 필요 농기계 × 스펙 범위 매칭 DB 모델 구현.

**WBS**: AP-02 (농작업-농기계 매칭 DB 스키마 설계, 시기별 마스터, 카테고리+스펙, 매칭 규칙)

**Files (수정/구현)**:
- `backend/app/models/equipment.py`

**Schema**:
```python
class FarmTask(Base):
    """시기별 농작업 마스터."""
    __tablename__ = "farm_tasks"
    id: UUID PK
    name: str                  # "로터리 작업", "벼베기", "드론 방제"
    season_start_month: int    # 시작 월 (3)
    season_end_month: int      # 종료 월 (4)
    crop_type: str             # "벼", "고구마", "마늘"
    description: str | None

class EquipmentCategory(Base):
    """농기계 카테고리 + 스펙."""
    __tablename__ = "equipment_categories"
    id: UUID PK
    name: str                  # "트랙터", "콤바인", "드론"
    brand: str | None          # "대동", "쿠보타"
    model_name: str | None     # "RX7630"
    horsepower: int | None     # 76
    spec_json: dict | None     # {"4wd": true, "attachment": ["로터리","쟁기"]}
    image_urls: list[str] | None

class TaskEquipmentMatch(Base):
    """농작업-농기계 매칭 규칙."""
    __tablename__ = "task_equipment_matches"
    id: UUID PK
    farm_task_id: UUID FK
    equipment_category_id: UUID FK
    min_horsepower: int | None
    max_horsepower: int | None
    price_per_pyeong_min: int | None  # 평당 최소 가격
    price_per_pyeong_max: int | None  # 평당 최대 가격
    priority: int              # 추천 우선순위
```

**Test**: 모델 생성, FK 관계, 매칭 조회 쿼리

**Commit**: `feat(EP1): add farm task + equipment category + match rule models`

---

### P-004: 농작업-농기계 매칭 DB API

**Goal**: FarmTask, EquipmentCategory, TaskEquipmentMatch CRUD API.

**WBS**: AP-02

**Files**:
- `backend/app/routers/equipment.py` — CRUD 엔드포인트
- `backend/app/schemas/equipment.py` — Pydantic 스키마
- `backend/app/services/equipment_service.py` — 비즈니스 로직

**API**:
```
# 농작업 마스터
GET    /api/v1/equipment/tasks                    ← 시기별 농작업 목록 (?month=3)
POST   /api/v1/equipment/tasks                    ← 농작업 등록 (admin)
# 농기계 카테고리
GET    /api/v1/equipment/categories               ← 카테고리 목록 (?name=트랙터)
POST   /api/v1/equipment/categories               ← 카테고리 등록 (admin)
# 매칭 규칙
GET    /api/v1/equipment/matches                  ← 매칭 규칙 조회 (?task_id=xx)
POST   /api/v1/equipment/matches                  ← 매칭 규칙 등록 (admin)
# 시기별 추천
GET    /api/v1/equipment/recommendations          ← 현재 월 기준 추천 작업+장비
```

**Commit**: `feat(EP1): equipment CRUD API + recommendations endpoint`

---

### P-005: 백오피스 프레임워크 + 데이터 관리 UI

**Goal**: 관리자 백오피스 레이아웃 + 농작업-농기계 DB CRUD UI.

**WBS**: AP-03 (백오피스 프레임워크, CRUD UI, 카테고리 관리)

**Files**:
- `frontend/src/pages/admin/DataMgmt.tsx` — 매칭 DB 관리
- `frontend/src/pages/admin/AdminLayout.tsx` — 관리자 레이아웃 (사이드바)
- `frontend/src/api/equipment.ts` — API 클라이언트
- `frontend/src/App.tsx` — 라우트 추가 (`/admin/*`)

**UI**:
- 사이드바: "초기 데이터", "농기계 카테고리", "매칭 규칙"
- 테이블 CRUD: 생성/수정/삭제 모달
- 이미지 업로드 (농기계 카테고리)

**Commit**: `feat(M09): admin layout + farm task/equipment CRUD UI`

---

### P-006: 백오피스 엑셀 업로드

**Goal**: 초기 데이터 엑셀 일괄 업로드 + 유효성 검사.

**WBS**: AP-03 (엑셀 일괄 업로드 + 유효성 검사, 초기 데이터 50건)

**Files**:
- `backend/app/routers/equipment.py` — 엑셀 업로드 엔드포인트 추가
- `backend/app/services/equipment_service.py` — 파싱 + 유효성 검사
- `frontend/src/pages/admin/DataMgmt.tsx` — 업로드 UI 추가

**API**:
```
POST /api/v1/equipment/upload    ← multipart/form-data (xlsx)
     Response: { success_count, error_count, errors: [{row, field, message}] }
```

**Dependencies**: `openpyxl` (backend/requirements.txt에 추가)

**Test**: 정상 50건 업로드, 중복 모델명 오류, 필수 필드 누락 오류

**Commit**: `feat(EP1): excel bulk upload with validation for equipment data`

---

### P-007: 모바일 로그인 화면 업데이트 (다중 인증)

**Goal**: login_screen.dart를 4가지 인증 방식 지원으로 업데이트.

**WBS**: AP-01 (카카오/네이버 소셜로그인, SMS, 이메일)

**Files (수정)**:
- `mobile/lib/screens/login_screen.dart` — UI 리디자인
- `mobile/lib/providers/auth_provider.dart` — 소셜/이메일 로직 추가
- `mobile/lib/services/api_service.dart` — 인증 API 호출 추가

**UI**:
- "카카오로 시작하기" (노란 버튼)
- "네이버로 시작하기" (초록 버튼)
- "휴대폰 번호로 시작" (회색)
- "이메일로 시작" (회색)
- 위치 권한 요청 모달 (로그인 성공 후)

**Commit**: `feat(M01): multi-auth login screen (kakao/naver/sms/email)`

---

### P-008: 모바일 홈 화면 + 위치 기반

**Goal**: 홈 화면에 주변 장비 배너 + 시기별 추천 작업 카드 표시.

**WBS**: AP-04 (홈 화면 레이아웃, 위치 기반 반경 검색, 시기별 추천 카드)

**Files (수정)**:
- `mobile/lib/screens/home_screen.dart` — 홈 화면 구현
- `mobile/lib/services/api_service.dart` — 장비/추천 API 호출

**UI**:
- 상단: "주변 5km 장비 N건" 배너
- 중간: "N월 추천 작업" 카드 리스트 (로터리 작업, 벼베기 등)
- 하단: BottomNavigationBar (홈, 장비, 내작업, 채팅, 프로필)

**API 호출**:
```
GET /api/v1/equipment/recommendations?lat=xx&lng=xx&radius=5
```

**Commit**: `feat(M10): home screen with nearby equipment + seasonal recommendations`

---

### P-009: 장비 리스트 + 상세 + 필터 화면

**Goal**: 주변 장비 조회 리스트, 상세 화면, 필터 기능.

**WBS**: AP-05 (장비 리스트, 상세, 필터)

**Files**:
- `mobile/lib/screens/equipment_list_screen.dart` — 장비 리스트
- `mobile/lib/screens/equipment_detail_screen.dart` — 장비 상세

**UI (리스트)**:
- 카드: 사진 + 모델명 + 보유자 + 거리 + 평점
- 필터: 카테고리, 거리(5/10/20/30km), 마력 범위

**UI (상세)**:
- 장비 사진 갤러리
- 스펙: 모델명, 마력, 부착 장비
- 보유자 정보: 이름, 경력, 평점
- "의뢰하기" / "채팅하기" 버튼

**Commit**: `feat(M10): equipment list + detail + filter screens`

---

### P-010: 내 장비 등록 화면 + API

**Goal**: 작업자가 자신의 장비를 등록하는 폼 + 백엔드 API.

**WBS**: AP-06 (내 장비 등록 폼, 사진 업로드, 부착 장비+지역/가격)

**Files**:
- `backend/app/models/equipment.py` — UserEquipment 모델 추가
- `backend/app/routers/equipment.py` — 개인 장비 CRUD 추가
- `mobile/lib/screens/equipment_register_screen.dart` — 등록 폼

**Schema (추가)**:
```python
class UserEquipment(Base):
    """사용자 보유 장비."""
    __tablename__ = "user_equipments"
    id: UUID PK
    owner_id: UUID FK → users
    category_id: UUID FK → equipment_categories  # 카테고리 선택 → 스펙 자동입력
    custom_spec: str | None       # 직접 입력 스펙
    photo_urls: list[str] | None  # 장비 사진 (최대 10장)
    attachments: list[str] | None # 부착 장비 ["로터리", "쟁기", "배토기"]
    service_area_km: int          # 작업 가능 반경 (km)
    price_per_pyeong: int | None  # 희망 평당 가격
    is_active: bool
```

**API**:
```
POST   /api/v1/equipment/mine          ← 내 장비 등록
GET    /api/v1/equipment/mine          ← 내 장비 목록
PUT    /api/v1/equipment/mine/{id}     ← 수정
DELETE /api/v1/equipment/mine/{id}     ← 삭제
POST   /api/v1/equipment/mine/{id}/photos ← 사진 업로드
```

**UI (모바일)**:
- 카테고리 선택 → 모델 선택 → 스펙 자동 입력
- 사진 업로드 (최대 10장)
- 부착 장비 체크박스 (로터리, 쟁기, 배토기 등)
- 작업 가능 지역 (반경 설정)
- 희망 가격 입력

**Commit**: `feat(EP1): user equipment registration (model + API + mobile UI)`

---

### P-011: 시기별 알림 설정

**Goal**: 특정 시기의 농작업 의뢰 알림을 사전 설정.

**WBS**: AP-06 (시기별 알림 설정)

**Files**:
- `backend/app/routers/notifications.py` — 알림 설정 엔드포인트 추가
- `backend/app/models/notification.py` — 알림 설정 모델 추가
- `mobile/lib/screens/home_screen.dart` — "알림 설정" 버튼

**API**:
```
POST /api/v1/notifications/subscribe   ← { task_type: "rice_harvesting", month: 9 }
GET  /api/v1/notifications/subscribe   ← 내 알림 설정 목록
DELETE /api/v1/notifications/subscribe/{id}
```

**Commit**: `feat(M06): seasonal task notification subscription`

---

### P-012: EP1 E2E 테스트

**Goal**: EP1 데모 시나리오 Micro Steps 1~10 전체를 커버하는 통합 테스트.

**WBS**: AP-07

**Files**:
- `backend/tests/test_ep1_e2e.py`

**Test Scenario**:
1. 관리자 로그인 → 농작업-농기계 데이터 등록 (3건)
2. 카테고리 등록 (트랙터 RX7630)
3. 엑셀 업로드 (50건 중 48건 성공, 2건 오류)
4. 소셜 로그인 (카카오) → JWT 발급
5. 위치 업데이트 (김제시 부량면)
6. 홈: 주변 장비 조회 (반경 5km)
7. 장비 상세 조회
8. 내 장비 등록 (트랙터 + 로터리)
9. 시기별 추천 확인
10. 시기별 알림 설정 (9월 벼베기)

**Commit**: `test(EP1): e2e test covering demo scenario micro steps 1-10`

---

## STEP 2: EP2 — 의뢰자 온보딩 + 매칭/거래 + 건조위탁 + 결제

> 목표일: 2026-09-12 (W28) | WBS: AP-08~AP-17

---

### P-013: 필지 등록 모델 + API

**Goal**: 의뢰자 필지(농지) 등록 — 주소 + 면적 + 작물 + 지도 좌표.

**WBS**: AP-08

**Files**:
- `backend/app/models/field.py` — Field 모델 구현
- `backend/app/routers/users.py` — 필지 엔드포인트 추가 (또는 별도 field.py 라우터)
- `backend/app/schemas/field.py`

**Schema**:
```python
class Field(Base):
    """의뢰자 필지(농지)."""
    __tablename__ = "fields"
    id: UUID PK
    owner_id: UUID FK → users
    address: str                    # "전북 김제시 부량면 신용리 산 12번지"
    area_pyeong: int                # 3000
    crop_type: str                  # "벼"
    location_lat: float
    location_lng: float
    polygon_json: dict | None       # 카카오맵 폴리곤 좌표
    created_at: datetime
```

**API**:
```
POST   /api/v1/fields               ← 필지 등록
GET    /api/v1/fields               ← 내 필지 목록
GET    /api/v1/fields/{id}          ← 필지 상세
PUT    /api/v1/fields/{id}          ← 수정
DELETE /api/v1/fields/{id}          ← 삭제
```

**Commit**: `feat(M02): field (farmland) registration model + API`

---

### P-014: 필지 등록 모바일 화면 (카카오맵)

**Goal**: 필지 등록 UI — 주소 검색 + 카카오맵 핀/폴리곤 + 면적 입력.

**WBS**: AP-08 (카카오맵 연동)

**Files**:
- `mobile/lib/screens/field_register_screen.dart`

**UI**:
- 주소 검색 (카카오맵 API)
- 지도에 핀/폴리곤 마킹
- 면적 입력 (평)
- 작물 선택 (벼, 고구마, 마늘 등)

**Commit**: `feat(M10): field registration screen with KakaoMap`

---

### P-015: 연간 농작업 캘린더

**Goal**: 필지별 연간 작업 캘린더 자동 추천 + 등록.

**WBS**: AP-09

**Files**:
- `backend/app/services/matching_service.py` — 캘린더 추천 로직 추가
- `backend/app/routers/jobs.py` — 캘린더 엔드포인트 추가
- `mobile/lib/screens/calendar_screen.dart` — 캘린더 UI

**API**:
```
GET  /api/v1/jobs/calendar/recommend?field_id=xx  ← AI 추천 연간 일정
POST /api/v1/jobs/calendar                         ← 캘린더 등록 (전체 수락)
GET  /api/v1/jobs/calendar                         ← 내 캘린더 조회
```

**추천 로직**: 필지 작물 + 시기별 농작업 DB → "3월 로터리, 5월 모내기, 6~8월 방제, 9월 벼베기, 10월 건조위탁"

**Commit**: `feat(M03): annual farm calendar recommendation + registration`

---

### P-016: 의뢰 등록 + 가격 통계

**Goal**: 의뢰 등록 폼 + 최근 평균 거래 가격 안내.

**WBS**: AP-10

**Files (수정)**:
- `backend/app/routers/jobs.py` — 의뢰 등록 확장 (필지 연동, 가격 통계)
- `backend/app/services/matching_service.py` — 가격 통계 쿼리
- `mobile/lib/screens/job_create_screen.dart` — UI 업데이트

**API (추가/수정)**:
```
GET  /api/v1/jobs/price-stats?category=rice_harvesting&region=김제  ← 평균 가격
POST /api/v1/jobs                ← 의뢰 등록 (field_id 연동 추가)
```

**UI**: 필지 정보 자동 입력 → 작업 선택 → 희망일 → "최근 평균: 평당 4,500원" 표시 → 예산 입력

**Commit**: `feat(M03): job creation with field auto-fill + price statistics`

---

### P-017: 자동 매칭 추천 알고리즘

**Goal**: 의뢰 등록 시 작업자를 자동 추천하는 스코어링 알고리즘.

**WBS**: AP-11

**Files**:
- `backend/app/services/matching_service.py` — 추천 알고리즘 구현

**알고리즘**:
```
score = (거리_점수 × 0.3) + (장비_적합도 × 0.3) + (평점 × 0.2) + (응답률 × 0.1) + (가격_적합도 × 0.1)
```
- 거리: haversine 기반, 가까울수록 높은 점수
- 장비 적합도: TaskEquipmentMatch + UserEquipment 매칭
- 평점: avg_rating
- 응답률: 지원 후 24h 내 응답 비율
- 가격: 희망 가격 차이

**API**:
```
GET /api/v1/jobs/{id}/recommendations  ← 추천 작업자 리스트 (스코어 순)
```

**Commit**: `feat(M03): auto-matching recommendation algorithm with scoring`

---

### P-018: 추천 작업자 리스트 + 지원/선택 UI

**Goal**: 추천 작업자 리스트 모바일 화면 + 지원/선택 플로우.

**WBS**: AP-11, AP-12

**Files**:
- `mobile/lib/screens/recommended_workers_screen.dart` — 추천 리스트
- `mobile/lib/screens/job_detail_screen.dart` — 수정 (지원자 목록)

**UI (추천 리스트)**: 이철수(4.8점, 2km, 콤바인), 박영호(4.5점, 5km) ...
**UI (작업자 앱)**: 푸시 알림 → "지원하기" → 메시지 입력
**UI (의뢰자)**: "지원자 3명" → 선택 → 매칭 완료 → 채팅방 생성

**Commit**: `feat(M10): recommended workers + apply/select flow UI`

---

### P-019: 채팅 확장 (이미지 + 읽음)

**Goal**: 기존 텍스트 채팅에 이미지 전송 + 읽음 표시 추가.

**WBS**: AP-13

**Files (수정)**:
- `backend/app/models/chat.py` — image_url 필드 추가
- `backend/app/routers/chat.py` — 이미지 업로드 + 읽음 표시
- `mobile/lib/screens/chat_screen.dart` — UI 확장

**Commit**: `feat(M05): chat image support + read receipts`

---

### P-020: 인앱 계약 체결

**Goal**: 채팅 내에서 계약서 생성 + 양측 전자 서명.

**WBS**: AP-13

**Files**:
- `backend/app/models/contract.py` — Contract 모델 구현
- `backend/app/routers/chat.py` — 계약 엔드포인트 추가
- `backend/app/schemas/contract.py`
- `mobile/lib/screens/contract_screen.dart` — 계약서 UI

**Schema**:
```python
class ContractStatus(str, PyEnum):
    DRAFT = "DRAFT"
    SIGNED_BY_REQUESTER = "SIGNED_BY_REQUESTER"
    SIGNED_BY_WORKER = "SIGNED_BY_WORKER"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Contract(Base):
    __tablename__ = "contracts"
    id: UUID PK
    job_id: UUID FK
    chat_room_id: UUID FK
    requester_id: UUID FK
    worker_id: UUID FK
    work_type: str           # "벼베기"
    area_pyeong: int
    total_amount: int        # 1,500만원
    work_date: date
    terms_text: str          # 계약 조건 텍스트
    requester_signed_at: datetime | None
    worker_signed_at: datetime | None
    status: ContractStatus
```

**API**:
```
POST /api/v1/contracts                    ← 계약서 생성
PUT  /api/v1/contracts/{id}/sign          ← 서명 (양측)
GET  /api/v1/contracts/{id}               ← 계약서 조회
```

**Commit**: `feat(M05): in-app contract creation + digital signature`

---

### P-021: 에스크로 결제 — PG 연동 (토스페이먼츠)

**Goal**: 토스페이먼츠 에스크로 결제 연동 — 결제 → 보관 → 정산.

**WBS**: AP-13a

**Files**:
- `backend/app/services/payment_service.py` — PG API 연동
- `backend/app/routers/payments.py` — 결제 엔드포인트 확장
- `backend/app/schemas/payment.py` — 스키마 확장

**API**:
```
POST /api/v1/payments/escrow/create       ← 에스크로 결제 요청 (의뢰자)
POST /api/v1/payments/escrow/confirm      ← PG 결제 확인 콜백
POST /api/v1/payments/escrow/{id}/release ← 에스크로 해제 (작업확인 후)
POST /api/v1/payments/escrow/{id}/refund  ← 환불
GET  /api/v1/payments/{id}                ← 결제 상태 조회
```

**Flow**: 계약 체결 → 에스크로 결제(의뢰자) → PG 보관 → 작업 완료 확인 → 수수료 3% 차감 → 작업자 정산

**Commit**: `feat(M06): toss payments escrow integration`

---

### P-022: 에스크로 결제 모바일 UI

**Goal**: 결제 화면 + 정산 상태 확인 UI.

**WBS**: AP-13a

**Files**:
- `mobile/lib/screens/payment_screen.dart` — 결제 UI
- `mobile/lib/screens/payment_status_screen.dart` — 상태 확인

**UI**: "토스페이먼츠 / 카드결제 / 계좌이체" → 결제 → "에스크로 보관 중" → "정산 완료"

**Commit**: `feat(M10): escrow payment + settlement status UI`

---

### P-023: 건조시설 검색 + 상세

**Goal**: 주변 건조시설 리스트 + 상세 (가용량, 가동률, 건조 방식).

**WBS**: AP-14a

**Files (수정)**:
- `backend/app/models/drying.py` — DryingFacility 확장 (건조방식, 가동률 등)
- `backend/app/routers/drying.py` — 검색 API 확장
- `mobile/lib/screens/drying_search_screen.dart` — 검색 화면
- `mobile/lib/screens/drying_detail_screen.dart` — 상세 화면

**Schema 확장** (DryingFacility):
```python
# 기존 필드 유지 + 추가
drying_method: str | None      # "순환식", "평상식"
price_per_gama: int | None     # 가마당 가격
current_capacity_gama: int     # 현재 가용 가마 수
estimated_days: int            # 평균 건조 소요일
```

**API**:
```
GET /api/v1/drying/facilities/search?lat=xx&lng=xx&radius=10  ← 주변 시설 검색
GET /api/v1/drying/facilities/{id}                             ← 시설 상세
```

**Commit**: `feat(M04): drying facility search with capacity + pricing`

---

### P-024: 건조 위탁 플로우 (신청→입고→진행→출고)

**Goal**: 건조 위탁 전체 플로우 — 신청, 입고 확인, 건조 진행, 수율/품질 기록, 출고.

**WBS**: AP-14b

**Files (수정)**:
- `backend/app/models/drying.py` — DryingReservation 확장 (위탁 플로우 상태)
- `backend/app/routers/drying.py` — 위탁 API 확장
- `backend/app/services/drying_service.py` — 수율 계산 + 품질 기록

**Schema 확장** (DryingReservation):
```python
# 기존 필드 유지 + 추가
input_gama: int | None            # 투입 가마 수
output_gama: int | None           # 산출 가마 수
target_moisture_pct: float | None # 목표 수분율 (14%)
current_moisture_pct: float | None # 현재 수분율
crack_rate_pct: float | None      # 동할미율
estimated_completion: date | None  # 예상 완료일
received_at: datetime | None       # 입고 확인 시각
completed_at: datetime | None      # 건조 완료 시각
released_at: datetime | None       # 출고 시각
```

**API**:
```
POST /api/v1/drying/consign                    ← 건조 위탁 신청
PUT  /api/v1/drying/consign/{id}/receive       ← 입고 확인 (시설 운영자)
PUT  /api/v1/drying/consign/{id}/progress      ← 건조 진행 상태 업데이트
PUT  /api/v1/drying/consign/{id}/complete      ← 건조 완료 + 수율/품질 기록
PUT  /api/v1/drying/consign/{id}/release       ← 출고 확인
GET  /api/v1/drying/consign/{id}               ← 위탁 상태 조회
```

**수율 계산**: `yield_pct = (output_gama / input_gama) * 100`

**Commit**: `feat(M04): drying consignment full flow (apply→receive→dry→quality→release)`

---

### P-025: 건조 위탁 모바일 UI

**Goal**: 건조 위탁 신청 + 진행 현황 + 완료 결과 모바일 화면.

**WBS**: AP-14b

**Files**:
- `mobile/lib/screens/drying_consign_screen.dart` — 위탁 신청
- `mobile/lib/screens/drying_status_screen.dart` — 진행 현황

**UI (신청)**: 시설 선택 → 입고 예정일 → 수량(가마) → 목표 수분율 → 신청
**UI (현황)**: 입고 50가마 / 현재 수분 22% → 목표 14% / 예상 완료 09-19
**UI (완료)**: 수율 86% / 1등급 / 수분 13.8% / 동할미 2.1%

**Commit**: `feat(M10): drying consignment mobile screens`

---

### P-026: 작업 완료 + 평가

**Goal**: 작업 완료 보고 + 의뢰자 확인 + 별점/후기 평가.

**WBS**: AP-14

**Files (수정)**:
- `backend/app/routers/jobs.py` — 작업 완료 보고 API
- `backend/app/routers/reviews.py` — 평가 API 확장 (건조 포함)
- `mobile/lib/screens/job_complete_screen.dart` — 완료 보고 UI
- `mobile/lib/screens/review_screen.dart` — 평가 UI

**API**:
```
PUT  /api/v1/jobs/{id}/complete          ← 작업 완료 보고 (사진, 면적, 시간)
PUT  /api/v1/jobs/{id}/confirm           ← 의뢰자 작업 확인
POST /api/v1/reviews                     ← 평가 (별점 + 후기)
```

**Commit**: `feat(M03,M07): job completion report + review with drying integration`

---

### P-027: 자동 정산 + 수익 대시보드 + 리더보드

**Goal**: 에스크로 정산 + 작업자 수익 대시보드 + 리더보드.

**WBS**: AP-15, AP-16

**Files**:
- `backend/app/services/payment_service.py` — 자동 정산 로직
- `backend/app/routers/payments.py` — 수익/리더보드 API
- `mobile/lib/screens/earnings_screen.dart` — 수익 대시보드
- `mobile/lib/screens/leaderboard_screen.dart` — 리더보드

**API**:
```
GET /api/v1/payments/earnings            ← 내 수익 (이번주/이번달/누적)
GET /api/v1/payments/leaderboard         ← 이번주 우리동네 수입왕
```

**정산 로직**: 작업확인 → 에스크로 해제 → 수수료 3% 차감 → 작업자 정산

**Commit**: `feat(M06): auto-settlement + earnings dashboard + leaderboard`

---

### P-028: EP2 E2E 테스트

**Goal**: EP2 데모 시나리오 Micro Steps 1~17 전체 커버.

**WBS**: AP-17

**Files**:
- `backend/tests/test_ep2_e2e.py`

**Test Scenario**:
1. 필지 등록 (부량면 3,000평 벼)
2. 캘린더 자동 추천 → 전체 수락
3. 벼베기 의뢰 등록 (평당 5,000원)
4. 자동 추천 → 이철수 선택
5. 채팅 → 계약 체결
6. 에스크로 결제 (1,500만원)
7. 작업 완료 보고
8. 건조 위탁 신청 → 입고 → 건조 → 수율/품질 → 출고
9. 작업 확인 → 평가 (★5)
10. 에스크로 정산 (수수료 3% 차감)
11. 수익 대시보드 + 리더보드

**Commit**: `test(EP2): e2e test covering demo scenario micro steps 1-17`

---

## STEP 3: EP3 — 지자체 보조금 + 농작업 대행단

> 목표일: 2026-12-26 (W43) | WBS: AP-18~AP-23d

---

### P-029: 보조금 사업 등록 — 지자체 관리자 포털

**Goal**: 지자체 관리자가 보조금 사업을 등록/관리하는 백오피스.

**WBS**: AP-18

**Files**:
- `backend/app/models/subsidy.py` — 모델 구현
- `backend/app/routers/subsidy.py` — CRUD API
- `backend/app/schemas/subsidy.py`
- `frontend/src/pages/admin/SubsidyDashboard.tsx` — 관리자 UI

**Schema**:
```python
class SubsidyProgram(Base):
    __tablename__ = "subsidy_programs"
    id: UUID PK
    gov_agency: str             # "김제시청"
    name: str                   # "항공방제 보조금"
    budget: int                 # 500,000,000 (5억)
    target_work_type: str       # "drone_spraying"
    subsidy_rate_pct: int       # 70
    max_per_person: int         # 5,000,000 (500만)
    start_date: date
    end_date: date
    status: str                 # "active", "closed"
    spent_amount: int           # 집행 금액
    created_at: datetime

class SubsidyApplication(Base):
    __tablename__ = "subsidy_applications"
    id: UUID PK
    program_id: UUID FK
    applicant_id: UUID FK → users
    field_id: UUID FK → fields
    estimated_cost: int         # 예상 비용 300만
    subsidy_amount: int         # 보조금 210만
    self_pay_amount: int        # 자부담 90만
    status: str                 # "pending", "approved", "rejected", "completed", "settled"
    job_id: UUID FK | None      # 매칭된 작업
    approved_at: datetime | None
    settled_at: datetime | None
```

**API**:
```
POST /api/v1/subsidy/programs              ← 사업 등록 (admin)
GET  /api/v1/subsidy/programs              ← 사업 목록
PUT  /api/v1/subsidy/programs/{id}         ← 수정
GET  /api/v1/subsidy/programs/{id}/stats   ← 집행 현황
```

**Commit**: `feat(M07): subsidy program model + admin CRUD + dashboard`

---

### P-030: 보조금 신청 (농업인 모바일)

**Goal**: 농업인이 보조금을 신청하고 승인을 받는 플로우.

**WBS**: AP-19

**Files**:
- `backend/app/routers/subsidy.py` — 신청/승인 API 추가
- `backend/app/services/subsidy_service.py` — 신청 비즈니스 로직
- `mobile/lib/screens/subsidy_apply_screen.dart` — 신청 UI

**API**:
```
POST /api/v1/subsidy/applications                      ← 보조금 신청
GET  /api/v1/subsidy/applications                      ← 내 신청 목록
PUT  /api/v1/subsidy/applications/{id}/approve         ← 승인 (admin)
PUT  /api/v1/subsidy/applications/{id}/reject          ← 반려 (admin)
```

**UI**: 필지 선택 → 예상 비용 자동 계산 → "보조금 210만 / 자부담 90만" → 신청

**Commit**: `feat(M07): subsidy application + approval workflow`

---

### P-031: 보조금 연계 매칭

**Goal**: 보조금 승인된 작업에 대해 작업자 매칭 (대행단 우선 추천).

**WBS**: AP-20

**Files**:
- `backend/app/services/matching_service.py` — 보조금 연계 매칭 로직 추가
- `backend/app/routers/subsidy.py` — 보조금 계약 API

**로직**: 승인된 보조금 → 자동 의뢰 생성 → 대행단 우선 추천 → 채팅 → 보조금 연계 계약

**Commit**: `feat(M07): subsidy-linked matching with crew priority`

---

### P-032: 보조금 리포트 자동 생성

**Goal**: 작업 완료 → GPS/사진/면적/날짜 기반 PDF 보고서 자동 생성 → 지자체 발송.

**WBS**: AP-21

**Files**:
- `backend/app/services/subsidy_service.py` — 리포트 생성 로직
- `backend/app/routers/subsidy.py` — 리포트 API

**API**:
```
POST /api/v1/subsidy/applications/{id}/report          ← 리포트 생성
GET  /api/v1/subsidy/applications/{id}/report           ← 리포트 조회/다운로드
POST /api/v1/subsidy/applications/{id}/report/send      ← 지자체 발송
```

**Dependencies**: `reportlab` 또는 `weasyprint` (PDF 생성)

**Commit**: `feat(M07): auto-generate subsidy report (PDF) + gov API delivery`

---

### P-033: 보조금 정산 + 집행 현황

**Goal**: 보조금 정산 워크플로우 + 지자체 집행 현황 대시보드.

**WBS**: AP-22

**Files**:
- `backend/app/routers/subsidy.py` — 정산 API
- `frontend/src/pages/admin/SubsidyDashboard.tsx` — 집행 현황 확장

**API**:
```
PUT  /api/v1/subsidy/applications/{id}/settle    ← 정산 승인 (admin)
GET  /api/v1/subsidy/programs/{id}/dashboard     ← 집행 현황 (총예산/집행/잔여/수혜자/완료건)
```

**Commit**: `feat(M07): subsidy settlement + execution dashboard`

---

### P-034: 대행단 생성 + 멤버 관리

**Goal**: 청년농 대행단 생성 + 멤버 초대/수락/관리.

**WBS**: AP-23a

**Files**:
- `backend/app/models/crew.py` — 모델 구현
- `backend/app/routers/crew.py` — CRUD API
- `backend/app/schemas/crew.py`
- `backend/app/services/crew_service.py`
- `mobile/lib/screens/crew_create_screen.dart` — 생성 UI
- `mobile/lib/screens/crew_manage_screen.dart` — 관리 UI

**Schema**:
```python
class Crew(Base):
    __tablename__ = "crews"
    id: UUID PK
    name: str                   # "부량 콤바인팀"
    leader_id: UUID FK → users  # 대표자
    specialty: list[str]        # ["벼베기", "로터리"]
    service_area: str           # "김제시 전체"
    service_radius_km: int      # 30
    logo_url: str | None
    gallery_urls: list[str] | None
    avg_rating: float
    total_completed: int
    is_active: bool
    created_at: datetime

class CrewMember(Base):
    __tablename__ = "crew_members"
    id: UUID PK
    crew_id: UUID FK → crews
    user_id: UUID FK → users
    role: str                   # "leader", "member"
    equipment_ids: list[UUID]   # 보유 장비 IDs
    joined_at: datetime
    status: str                 # "invited", "active", "left"

class CrewOrder(Base):
    __tablename__ = "crew_orders"
    id: UUID PK
    crew_id: UUID FK
    total_area_pyeong: int      # 총 면적
    total_amount: int           # 총 금액
    job_count: int              # 의뢰 건수
    status: str                 # "pending", "accepted", "in_progress", "completed"
    created_at: datetime
```

**API**:
```
POST /api/v1/crews                         ← 대행단 생성
GET  /api/v1/crews/{id}                    ← 대행단 상세 (프로필)
POST /api/v1/crews/{id}/members/invite     ← 멤버 초대
PUT  /api/v1/crews/{id}/members/{uid}/accept ← 초대 수락
GET  /api/v1/crews/{id}/members            ← 멤버 목록
```

**Commit**: `feat(M11): crew creation + member invite/accept management`

---

### P-035: 대행단 프로필 페이지

**Goal**: 대행단 홍보 카드 + 갤러리 + 후기 페이지.

**WBS**: AP-23a (프로필)

**Files**:
- `mobile/lib/screens/crew_profile_screen.dart`

**UI**: "부량 콤바인팀 | 멤버 5명 | 콤바인 3대 + 트랙터 2대 | 평점 4.9 | 47건 완료" + 갤러리 + 후기 목록

**Commit**: `feat(M11): crew profile page (card + gallery + reviews)`

---

### P-036: 그룹 수주 시스템

**Goal**: 대규모 의뢰 → 대행단 우선 추천 → 그룹 수주.

**WBS**: AP-23b

**Files**:
- `backend/app/services/crew_service.py` — 그룹 수주 로직
- `backend/app/routers/crew.py` — 수주 API

**API**:
```
GET  /api/v1/crews/{id}/orders             ← 대행단 수주 목록
POST /api/v1/crews/{id}/orders/{oid}/accept ← 수주 수락
```

**로직**: 5,000평+ 의뢰 → 대행단 우선 추천 → 대표 수주 확인

**Commit**: `feat(M11): crew group order system with large-area priority`

---

### P-037: 내부 자동 할당 엔진

**Goal**: 수주 확정 후 멤버별 자동 할당 (장비/위치/일정 기반).

**WBS**: AP-23b

**Files**:
- `backend/app/services/crew_service.py` — 자동 할당 알고리즘

**알고리즘**:
```
할당점수 = (장비_적합도 × 0.4) + (위치_근접도 × 0.3) + (가용_일정 × 0.3)
```

**API**:
```
POST /api/v1/crews/{id}/orders/{oid}/auto-assign  ← 자동 할당 실행
PUT  /api/v1/crews/{id}/orders/{oid}/assignments   ← 할당 수정 (대표 확인/수정)
PUT  /api/v1/crews/{id}/orders/{oid}/confirm       ← 할당 확정
```

**Commit**: `feat(M11): crew auto-assignment engine (equipment/location/schedule scoring)`

---

### P-038: 대행단 수익 관리 + 멤버별 배분

**Goal**: 그룹 매출/정산/멤버별 배분 대시보드.

**WBS**: AP-23c

**Files**:
- `backend/app/services/crew_service.py` — 배분 로직
- `backend/app/routers/crew.py` — 정산 API
- `mobile/lib/screens/crew_earnings_screen.dart` — 대시보드

**API**:
```
GET  /api/v1/crews/{id}/earnings           ← 대행단 수익 대시보드
GET  /api/v1/crews/{id}/earnings/members   ← 멤버별 배분 내역
POST /api/v1/crews/{id}/earnings/settle    ← 그룹 정산 실행
```

**Commit**: `feat(M11): crew earnings dashboard + member distribution`

---

### P-039: 보조금 단체 매칭

**Goal**: 지자체가 대행단에 일괄 위탁하는 보조금 단체 계약.

**WBS**: AP-23c

**Files**:
- `backend/app/services/subsidy_service.py` — 단체 매칭 로직
- `backend/app/routers/subsidy.py` — 단체 매칭 API

**API**:
```
POST /api/v1/subsidy/programs/{id}/crew-match   ← 대행단 일괄 위탁
```

**Commit**: `feat(M07,M11): subsidy bulk matching to crew`

---

### P-040: EP3 E2E 테스트

**Goal**: EP3 데모 시나리오 A(보조금 10 Steps) + B(대행단 8 Steps) 전체 커버.

**WBS**: AP-23d

**Files**:
- `backend/tests/test_ep3_e2e.py`

**Test Scenario A (보조금)**:
1. 보조금 사업 등록 (항공방제, 5억)
2. 농업인 신청 (3,000평, 보조금 210만)
3. 승인
4. 보조금 연계 매칭 (대행단 우선)
5. 작업 완료 → 리포트 생성 → 지자체 발송
6. 정산 승인
7. 집행 현황 확인

**Test Scenario B (대행단)**:
1. 대행단 생성 (부량 콤바인팀, 5명)
2. 멤버 초대/수락
3. 그룹 수주 (12건, 36,000평)
4. 자동 할당 → 대표 수정 → 확정
5. 작업 완료
6. 그룹 정산 (멤버별 배분)

**Commit**: `test(EP3): e2e test for subsidy + crew demo scenarios`

---

## STEP 4: EP4 — 제조사·R&D 연계

> 목표일: 2027-03-12 (W54) | WBS: AP-24~AP-28

---

### P-041: 제조사 포털 + 제품 등록

**Goal**: 제조사 포털 기본 구조 + 제품(농기계) 등록 시스템.

**WBS**: AP-24

**Files**:
- `backend/app/models/manufacturer.py` — 모델 구현
- `backend/app/routers/manufacturer.py` — CRUD API
- `backend/app/schemas/manufacturer.py`
- `frontend/src/pages/admin/MfgPortal.tsx` — 제조사 포털 UI

**Schema**:
```python
class Manufacturer(Base):
    __tablename__ = "manufacturers"
    id: UUID PK
    name: str                   # "대동"
    contact_email: str
    products: relationship → ManufacturerProduct

class ManufacturerProduct(Base):
    __tablename__ = "manufacturer_products"
    id: UUID PK
    manufacturer_id: UUID FK
    name: str                   # "RX8040"
    category: str               # "트랙터"
    horsepower: int             # 80
    spec_json: dict
    catalog_url: str | None
    image_urls: list[str] | None

class TrialFarm(Base):
    __tablename__ = "trial_farms"
    id: UUID PK
    product_id: UUID FK
    title: str                  # "RX8040 시험포 모집"
    region: str                 # "전북"
    max_participants: int       # 10
    duration_months: int        # 3
    benefit_text: str           # "3개월 무상 대여"
    min_area_pyeong: int        # 2000
    status: str                 # "recruiting", "in_progress", "completed"
    created_at: datetime
```

**API**:
```
POST /api/v1/manufacturers                     ← 제조사 등록
POST /api/v1/manufacturers/{id}/products       ← 제품 등록
GET  /api/v1/manufacturers/{id}/products       ← 제품 목록
```

**Commit**: `feat(M08): manufacturer portal + product registration`

---

### P-042: 시험포 모집 + 신청

**Goal**: 제조사 시험포 모집 등록 + 농업인 시험포 신청 + 선정.

**WBS**: AP-25

**Files**:
- `backend/app/routers/manufacturer.py` — 시험포 API
- `backend/app/services/manufacturer_service.py`
- `mobile/lib/screens/trial_farm_screen.dart` — 신청 UI
- `frontend/src/pages/admin/MfgPortal.tsx` — 모집/선정 UI

**API**:
```
POST /api/v1/trials                            ← 시험포 모집 등록
GET  /api/v1/trials                            ← 모집 목록 (농업인용)
POST /api/v1/trials/{id}/apply                 ← 시험 참여 신청
PUT  /api/v1/trials/{id}/applicants/{uid}/select ← 선정 (제조사)
GET  /api/v1/trials/{id}/applicants            ← 신청자 목록
```

**Commit**: `feat(M08): trial farm recruitment + application + selection`

---

### P-043: 시험 데이터 수집 + 리포트

**Goal**: 시험 기간 중 주간 리포트 수집 + 종합 리포트 자동 생성.

**WBS**: AP-26

**Files**:
- `backend/app/routers/manufacturer.py` — 리포트 API
- `mobile/lib/screens/trial_report_screen.dart` — 주간 리포트 입력

**API**:
```
POST /api/v1/trials/{id}/reports               ← 주간 리포트 제출
GET  /api/v1/trials/{id}/reports               ← 리포트 목록
GET  /api/v1/trials/{id}/summary               ← 종합 리포트 (만족도, 연비, 피드백)
```

**Commit**: `feat(M08): trial data collection + summary report generation`

---

### P-044: 국가 R&D 실증사업 연동

**Goal**: 국가 R&D 실증사업 목록 + 마을 단위 신청 + 첨단 농가 DB.

**WBS**: AP-27

**Files**:
- `backend/app/routers/manufacturer.py` — R&D API 추가
- `mobile/lib/screens/rnd_apply_screen.dart` — 마을 신청 UI

**API**:
```
GET  /api/v1/rnd/programs                      ← 실증사업 목록
POST /api/v1/rnd/programs/{id}/village-apply    ← 마을 단위 신청
GET  /api/v1/rnd/advanced-farms                ← 첨단 농가 DB
```

**Commit**: `feat(M08): national R&D program village application + advanced farm DB`

---

### P-045: EP4 E2E 테스트

**Goal**: EP4 데모 시나리오 Micro Steps 1~8 전체 커버.

**WBS**: AP-28

**Files**:
- `backend/tests/test_ep4_e2e.py`

**Test Scenario**:
1. 제조사 포털 → 시험포 모집 등록 (RX8040)
2. 농업인 시험 신청 → 선정
3. 주간 리포트 제출 × 3회
4. 종합 리포트 생성
5. R&D 실증사업 마을 신청
6. 첨단 농가 DB 등록

**Commit**: `test(EP4): e2e test covering manufacturer + R&D demo scenario`

---

## STEP 5: EP5 — 데이터 플랫폼 + AI + 전국 스케줄링

> 목표일: 2027-06-27 (W69) | WBS: AP-29~AP-36

---

### P-046: 전국 거래 현황 대시보드

**Goal**: 전국 히트맵 + 거래량/가격 추이 + 지역별 수급 분석.

**WBS**: AP-29

**Files**:
- `backend/app/routers/analytics.py` — 분석 API
- `backend/app/services/analytics_service.py`
- `frontend/src/pages/admin/Analytics.tsx` — 대시보드 UI

**API**:
```
GET /api/v1/analytics/overview                 ← 전국 현황 (사용자, 장비, 거래, 거래액)
GET /api/v1/analytics/heatmap                  ← 지역별 거래 히트맵
GET /api/v1/analytics/trends                   ← 거래량/가격 추이 (월별)
GET /api/v1/analytics/supply-demand            ← 수급 분석 (지역별 작업자 vs 의뢰)
```

**Commit**: `feat(M09): national analytics dashboard (heatmap + trends + supply-demand)`

---

### P-047: 다차원 분석 뷰

**Goal**: 작물별, 장비별, 계절별, 지역별 다차원 분석.

**WBS**: AP-29

**Files**:
- `backend/app/services/analytics_service.py` — 다차원 쿼리
- `frontend/src/pages/admin/Analytics.tsx` — 분석 뷰 확장

**Commit**: `feat(M09): multi-dimensional analytics view (crop/equipment/season/region)`

---

### P-048: AI 수요 예측 엔진

**Goal**: 과거 데이터 기반 시즌별 수요 예측.

**WBS**: AP-30

**Files**:
- `backend/app/services/ai_prediction_service.py` — 예측 엔진
- `backend/app/routers/analytics.py` — 예측 API

**API**:
```
GET /api/v1/analytics/predict/demand    ← 수요 예측 (지역별, 작업별)
     Response: { region: "김제", task: "벼베기", predicted_count: 420, worker_count: 85, shortage_pct: 15 }
```

**Commit**: `feat(M09): AI demand prediction engine`

---

### P-049: AI 가격 예측 (건조비 포함)

**Goal**: 작업 유형별 가격 예측 + 건조 위탁비 예측.

**WBS**: AP-30

**Files**:
- `backend/app/services/ai_prediction_service.py` — 가격 예측 추가

**API**:
```
GET /api/v1/analytics/predict/price     ← 가격 예측
     Response: { task: "벼베기", region: "김제", predicted_price: 4800, change_pct: +6.7, drying_price: 3200 }
```

**Commit**: `feat(M09): AI price prediction engine (including drying costs)`

---

### P-050: AI Agent — 자동 매칭 + 수급 탐지

**Goal**: AI Agent가 수급 불균형 감지 → 인근 지역 작업자에게 자동 알림.

**WBS**: AP-31

**Files**:
- `backend/app/services/ai_agent_service.py` — AI Agent 로직
- `backend/app/routers/analytics.py` — Agent API

**로직**:
1. 수요 예측 → 부족률 15%+ 감지
2. 인근 지역 (익산, 정읍) 작업자 탐색
3. 자동 푸시 알림 발송
4. 수급 경보 생성

**Commit**: `feat(M09): AI agent for auto-matching + supply-demand alert`

---

### P-051: 정책 리포트 + 데이터 API

**Goal**: 지자체/중앙부처용 정책 분석 리포트 + 외부 데이터 API.

**WBS**: AP-32, AP-33

**Files**:
- `backend/app/services/analytics_service.py` — 리포트 생성
- `backend/app/routers/analytics.py` — API 키 관리

**API**:
```
POST /api/v1/analytics/reports/policy          ← 정책 리포트 생성 (지역 선택)
GET  /api/v1/analytics/reports/{id}            ← 리포트 조회
POST /api/v1/analytics/reports/{id}/send       ← 지자체 발송
POST /api/v1/analytics/api-keys               ← API 키 발급
GET  /api/v1/data/v1/{resource}               ← 오픈 데이터 API
```

**Commit**: `feat(M09): policy report generation + open data API`

---

### P-052: 수출 이력 추적 + QR 증명서

**Goal**: 작업 이력 → 건조 이력 → 유통까지 수출 품질 이력 추적.

**WBS**: AP-34

**Files**:
- `backend/app/routers/analytics.py` — 이력 추적 API

**API**:
```
GET  /api/v1/analytics/trace/{field_id}        ← 필지 기준 전체 이력
POST /api/v1/analytics/trace/{field_id}/qr     ← QR 수출 이력 증명서 생성
```

**Commit**: `feat(M09): export quality trace (work→drying→QR certificate)`

---

### P-053: 전국 대형장비 스케줄 보드

**Goal**: 초고가 대형 장비 전국 이동 스케줄 캘린더 + 가용 여부 실시간 체크.

**WBS**: AP-35a

**Files**:
- `backend/app/models/scheduling.py` — 모델 구현
- `backend/app/routers/scheduling.py` — API
- `backend/app/schemas/scheduling.py`
- `backend/app/services/scheduling_service.py`
- `frontend/src/pages/admin/ScheduleBoard.tsx` — 스케줄 보드 UI

**Schema**:
```python
class EquipmentSchedule(Base):
    __tablename__ = "equipment_schedules"
    id: UUID PK
    crew_id: UUID FK → crews           # 보유 대행단
    equipment_id: UUID FK → user_equipments
    equipment_type: str                # "6조식 콤바인", "드론 편대"
    region: str                        # "해남"
    start_date: date
    end_date: date
    status: str                        # "scheduled", "in_transit", "working", "available"
    notes: str | None

class RouteOptimization(Base):
    __tablename__ = "route_optimizations"
    id: UUID PK
    crew_id: UUID FK
    season: str                        # "2027-가을"
    route_json: dict                   # [{"region":"해남","dates":"9/5~10"}, ...]
    total_distance_km: int
    empty_transit_days: int            # 공차 이동일
    optimized_at: datetime
```

**API**:
```
GET  /api/v1/scheduling/board                  ← 전국 스케줄 보드 (지도 + 마커)
GET  /api/v1/scheduling/availability           ← 가용 여부 체크 (?type=콤바인&date=9/15~20&region=김제)
POST /api/v1/scheduling/schedules              ← 스케줄 등록
PUT  /api/v1/scheduling/schedules/{id}         ← 스케줄 수정
```

**Commit**: `feat(M12): national equipment schedule board + availability check`

---

### P-054: AI 경로 최적화 + 장비 공유

**Goal**: 남→북 시즌 이동 최적 경로 추천 + 대행단 간 장비 공유 스케줄링.

**WBS**: AP-35b

**Files**:
- `backend/app/services/scheduling_service.py` — AI 경로 최적화
- `backend/app/routers/scheduling.py` — 경로/공유 API

**API**:
```
POST /api/v1/scheduling/optimize-route         ← AI 경로 최적화 실행
     Request: { crew_id, season, current_schedules }
     Response: { optimized_route, saved_distance_km, saved_days }
POST /api/v1/scheduling/share                  ← 장비 공유 요청
GET  /api/v1/scheduling/share/available        ← 공유 가능 장비 조회
```

**Commit**: `feat(M12): AI route optimization + inter-crew equipment sharing`

---

### P-055: EP5 E2E 테스트 + 종합 데모

**Goal**: EP5 데모 시나리오 A(데이터/AI 8 Steps) + B(스케줄링 6 Steps) 전체 커버.

**WBS**: AP-36

**Files**:
- `backend/tests/test_ep5_e2e.py`

**Test Scenario A (데이터/AI)**:
1. 전국 히트맵 + 추이 조회
2. AI 수요 예측 (김제 벼베기 420건, 부족 15%)
3. AI Agent 인근 지역 알림
4. 가격 예측 (건조비 포함)
5. 정책 리포트 생성 → 발송
6. 데이터 API 키 발급 → 조회
7. 수출 이력 추적 → QR 증명서
8. 종합 현황 (45,000명, 102,000건, 2,340억)

**Test Scenario B (스케줄링)**:
1. 전국 스케줄 보드 조회
2. 대형 장비 가용 여부 체크 (9/15~20, 김제, 6조식 콤바인)
3. 의뢰 신청
4. AI 경로 최적화 (공차 2일→1일)
5. 대행단 수락 → 스케줄 확정
6. 장비 공유 스케줄링

**Commit**: `test(EP5): e2e test for analytics + AI + scheduling demo scenarios`

---

## 부록: WBS ↔ 프롬프트 매핑 체크리스트

| AP | WBS 태스크 | 프롬프트 | ✓ |
|----|-----------|---------|---|
| AP-01 | 카카오/네이버 소셜로그인 | P-001, P-007 | ✓ |
| AP-01 | SMS 알리고 | P-001 | ✓ |
| AP-01 | 이메일 인증 | P-001 | ✓ |
| AP-01 | JWT 토큰 | P-001 | ✓ |
| AP-01 | 위치 권한 + GPS | P-001, P-007 | ✓ |
| AP-02 | 매칭 DB 스키마 | P-003 | ✓ |
| AP-02 | 시기별 농작업 마스터 | P-003, P-004 | ✓ |
| AP-02 | 농기계 카테고리 + 스펙 | P-003, P-004 | ✓ |
| AP-02 | 매칭 규칙 테이블 | P-003, P-004 | ✓ |
| AP-03 | 백오피스 프레임워크 | P-005 | ✓ |
| AP-03 | CRUD UI | P-005 | ✓ |
| AP-03 | 카테고리 관리 + 이미지 | P-005 | ✓ |
| AP-03 | 엑셀 업로드 | P-006 | ✓ |
| AP-03 | 초기 데이터 50건 | P-006 | ✓ |
| AP-04 | 홈 화면 | P-008 | ✓ |
| AP-04 | 위치 기반 반경 검색 | P-008 | ✓ |
| AP-04 | 시기별 추천 카드 | P-008 | ✓ |
| AP-05 | 장비 리스트/상세/필터 | P-009 | ✓ |
| AP-06 | 장비 등록 폼 + 사진 + 부착 | P-010 | ✓ |
| AP-06 | 시기별 알림 | P-011 | ✓ |
| AP-07 | EP1 E2E 테스트 | P-012 | ✓ |
| AP-08 | 필지 등록 + 카카오맵 | P-013, P-014 | ✓ |
| AP-09 | 캘린더 추천 + UI | P-015 | ✓ |
| AP-10 | 의뢰 등록 + 가격 통계 | P-016 | ✓ |
| AP-11 | 자동 매칭 + 추천 리스트 | P-017, P-018 | ✓ |
| AP-12 | 지원/선택 | P-018 | ✓ |
| AP-13 | 채팅 (이미지) + 계약 | P-019, P-020 | ✓ |
| AP-13a | PG 연동 + 에스크로 | P-021, P-022 | ✓ |
| AP-14 | 작업 완료 + 평가 | P-026 | ✓ |
| AP-14a | 건조시설 검색 | P-023 | ✓ |
| AP-14b | 건조 위탁 플로우 + 수율/품질 | P-024, P-025 | ✓ |
| AP-15 | 자동 정산 + 수익 대시보드 | P-027 | ✓ |
| AP-16 | 평판 시스템 | P-027 | ✓ |
| AP-17 | EP2 E2E 테스트 | P-028 | ✓ |
| AP-18 | 지자체 포털 + 사업 등록 | P-029 | ✓ |
| AP-19 | 보조금 신청 + 승인 | P-030 | ✓ |
| AP-20 | 보조금 매칭 + 계약 | P-031 | ✓ |
| AP-21 | 리포트 + PDF + 발송 | P-032 | ✓ |
| AP-22 | 보조금 정산 + 집행 현황 | P-033 | ✓ |
| AP-23a | 대행단 생성 + 프로필 | P-034, P-035 | ✓ |
| AP-23b | 그룹 수주 + 자동 할당 | P-036, P-037 | ✓ |
| AP-23c | 대행단 정산 + 보조금 단체 | P-038, P-039 | ✓ |
| AP-23d | EP3 E2E 테스트 | P-040 | ✓ |
| AP-24 | 제조사 포털 + 제품 | P-041 | ✓ |
| AP-25 | 시험포 모집/신청/선정 | P-042 | ✓ |
| AP-26 | 시험 데이터 + 리포트 | P-043 | ✓ |
| AP-27 | R&D 실증 + 첨단 농가 | P-044 | ✓ |
| AP-28 | EP4 E2E 테스트 | P-045 | ✓ |
| AP-29 | 대시보드 + 다차원 분석 | P-046, P-047 | ✓ |
| AP-30 | AI 수요/가격 예측 | P-048, P-049 | ✓ |
| AP-31 | AI Agent + 수급 탐지 | P-050 | ✓ |
| AP-32 | 정책 리포트 | P-051 | ✓ |
| AP-33 | 데이터 API | P-051 | ✓ |
| AP-34 | 수출 이력 + QR | P-052 | ✓ |
| AP-35 | 수급 경보 | P-050 | ✓ |
| AP-35a | 스케줄 보드 + 가용 체크 | P-053 | ✓ |
| AP-35b | AI 경로 + 장비 공유 | P-054 | ✓ |
| AP-36 | EP5 E2E 테스트 | P-055 | ✓ |
