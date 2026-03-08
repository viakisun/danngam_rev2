# Claude Code 이관 Instructions

> 단감(DAN-GAM) 프로젝트를 Claude Code에서 시작하기 위한 단계별 가이드
> 비아 방법론 v6 기준 | S2(ARCHITECT) → S4(BUILD) 순서

---

## 0단계: 사전 준비

### 필요 파일 (Cowork에서 생성 완료)
```
다운로드한 파일들을 프로젝트 루트에 배치:
├── CLAUDE.md                    ← 프로젝트 규칙서 (필수 5섹션)
├── docs/
│   ├── SDD_SKELETON.md          ← 모듈별 I/O + TC + AP
│   └── 단감_시스템_기획서_rev2.docx  ← 전체 기획서
```

### Claude Code 환경 설정
```bash
# 1. 프로젝트 디렉토리 생성
mkdir danngam && cd danngam

# 2. CLAUDE.md 배치 (이미 다운로드한 파일)
cp ~/Downloads/CLAUDE.md ./CLAUDE.md

# 3. Claude Code 시작
claude

# 4. 첫 명령어
/init
```

---

## 1단계: S2 ARCHITECT — 프로젝트 스캐폴딩

### Prompt 1-1: Monorepo 초기화
```
/plan

CLAUDE.md를 읽고, 단감(DAN-GAM) 프로젝트의 monorepo를 초기화해줘.

요구사항:
- CLAUDE.md 섹션 06 디렉토리 구조 그대로
- backend/: FastAPI + SQLAlchemy + Alembic
- frontend/: React 18 + TypeScript + Vite + Tailwind
- mobile/: Flutter (별도 init)
- docker-compose.yml: Type B (PostgreSQL + Redis + Traefik)
- .github/workflows/ci.yml: lint → test → build

각 서브디렉토리에 CLAUDE.md도 생성해줘 (해당 스택 규칙).
```

### Prompt 1-2: Docker Compose
```
/plan

docker-compose.yml을 생성해줘. 비아 방법론 Type B 구성:

services:
  backend: FastAPI (Python 3.11, port 8000)
  frontend: React (Vite dev server, port 5173)
  postgres: PostgreSQL 16 (port 5432)
  redis: Redis 7 (port 6379)
  traefik: Reverse Proxy (port 80)

환경변수는 .env.example로 분리.
볼륨: postgres_data, redis_data
네트워크: danngam_network
```

### Prompt 1-3: Backend 기본 구조
```
/plan

backend/ 기본 구조를 생성해줘:

- app/main.py: FastAPI app + CORS + router include
- app/config.py: pydantic-settings 기반 환경변수
- app/database.py: async SQLAlchemy engine + session
- app/dependencies.py: get_db, get_current_user
- requirements.txt: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic, python-jose, redis, httpx
- alembic.ini + alembic/env.py

CLAUDE.md 코딩 컨벤션 준수 (Black, Ruff, async only).
```

---

## 2단계: S4 BUILD — 모듈별 개발 (Molecular Prompt)

### 개발 순서 (의존성 기준)
```
M01 AUTH → M02 USER → M03 MATCHING → M04 DRYING → M05 CHAT → M06~M09 → M10 MOBILE
```

### Prompt 2-1: M01 AUTH (AP 5개)
```
/plan

SDD_SKELETON.md의 M01 AUTH 섹션을 참고해서 인증 모듈을 구현해줘.

AP-01: User 모델 + Alembic 마이그레이션
AP-02: SMS 발송 서비스 (개발용 mock, 프로덕션용 인터페이스)
AP-03: 인증 라우터 (/auth/sms/send, /auth/sms/verify)
AP-04: JWT 발급/검증 유틸리티
AP-05: 테스트 (AUTH-TC01~07)

Constraints:
- SMS 코드: 6자리, 3분 유효, 60초 쿨다운
- access_token: 1시간, refresh_token: 30일
- 실패 5회 → 30분 차단

1 AP씩 순차적으로 진행. 각 AP 완료 후 lint + test 실행.
```

### Prompt 2-2: M03 MATCHING (AP 6개)
```
/plan

SDD_SKELETON.md의 M03 MATCHING 섹션을 참고해서 농작업 매칭 모듈을 구현해줘.

핵심:
- JobCreate 스키마 (category, equipment_tags, location, area_pyeong, pay_type, is_urgent)
- GPS 반경 필터 (Haversine formula, 기본 5km)
- 지원/선택 상태 전이 (OPEN → MATCHED → IN_PROGRESS → COMPLETED)
- 농업 용어 정확히 사용: 벼베기, 고구마 캐기, 마늘 심기

AP-01부터 AP-06까지 순차 진행.
```

### Prompt 2-3: M04 DRYING (AP 5개)
```
/plan

SDD_SKELETON.md의 M04 DRYING 섹션을 참고해서 건조시설 예약 모듈을 구현해줘.

핵심 차별화:
- 수율 자동계산: output_kg / input_kg × 100
- 품질 기록: moisture_pct(수분함량), color_grade(색상), quality_grade(등급)
- 예약 상태: PENDING → APPROVED → IN_DRYING → COMPLETED

이 모듈이 단감의 핵심 차별화 포인트. 수율과 품질 데이터 정확성이 중요.
```

### Prompt 2-4: M05 CHAT (AP 5개)
```
/plan

SDD_SKELETON.md의 M05 CHAT 섹션을 참고해서 실시간 채팅 모듈을 구현해줘.

핵심:
- WebSocket 기반 1:1 채팅
- 매칭 성사 시 자동 채팅방 생성 (Job 연결)
- 읽음 표시
- 메시지 최대 1,000자
```

### Prompt 2-5: M10 MOBILE (AP 8개)
```
/plan

SDD_SKELETON.md의 M10 MOBILE 섹션을 참고해서 Flutter 앱을 구현해줘.

Screen Mapping:
- HomeScreen (DG-main-dashboard)
- JobListScreen (DG-work-list)
- JobDetailScreen (DG-work-detail)
- JobCreateScreen (DG-work-create)
- ChatScreen (DG-chat-room)
- MyAppsScreen (DG-my-applications)

State: Riverpod
HTTP: Dio
카카오맵: 지도 뷰 (JobMapScreen)
```

---

## 3단계: S5 VERIFY — 검증

### Prompt 3-1: 전체 테스트
```
전체 테스트를 실행하고 결과를 보고해줘:

1. Backend: pytest -v --cov=app
2. Frontend: npm run lint && npm run test
3. Flutter: flutter test
4. Docker: docker compose up --build (스모크 테스트)

실패하는 테스트가 있으면 수정해줘.
```

### Prompt 3-2: API 통합 테스트
```
다음 시나리오를 E2E로 검증해줘:

1. SMS 인증 → 로그인 → JWT 취득
2. 작업 등록 (벼베기, 3000평, 긴급)
3. 다른 사용자로 로그인 → 작업 목록 조회 (반경 5km)
4. 지원하기 → 의뢰자가 선택 → 매칭 완료
5. 채팅방 생성 확인 → 메시지 교환
6. 작업 완료 → 평가

각 단계의 응답 상태코드와 데이터를 확인.
```

---

## 핵심 규칙 요약

### 매 세션 시작 시
```
1. /clear (새 작업)
2. CLAUDE.md 자동 로드 확인
3. SDD에서 해당 모듈 AP 확인
4. /plan 으로 시작
```

### Context 관리
```
70% → /compact
90% → /clear
새 모듈 시작 → /clear
```

### 커밋 규칙
```
feat(M03): add job list GPS radius filter
fix(M01): handle SMS cooldown edge case
test(M04): add drying yield calculation tests
```

### MCP 서버 (권장)
```
- Context7: 실시간 공식 문서 참조 (FastAPI, Flutter, React)
- 필요 시 추가 MCP 설치
```

---

## 예상 일정

| Sprint | 기간 | 목표 |
|--------|------|------|
| Sprint 1 (W1-2) | 2주 | S2 완료 + M01/M02/M03 Lv1 |
| Sprint 2 (W3-4) | 2주 | M04/M05 Lv1 + M06~M09 Lv1 |
| Sprint 3 (W5-6) | 2주 | M10 Flutter 앱 + 통합 테스트 |
| Sprint 4 (W7-8) | 2주 | 버그 수정 + 내부 베타 + Phase 1 완료 |

> 비아 방법론 v6 기준 첫 파일럿 자동화율 ~47%
> Sprint 3부터 65%+ 도달 예상
