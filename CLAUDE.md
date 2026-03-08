# CLAUDE.md — 단감(DAN-GAM) 프로젝트

> 비아 방법론 v6 기준 필수 5섹션 + 단감 특화 규칙

---

## 01. 프로젝트 개요

- **프로젝트명**: 단감 (DAN-GAM)
- **코드명**: DNNG
- **유형**: Type B (Backend + Frontend + PostgreSQL + Redis + Proxy)
- **한줄 설명**: 농작업을 필요로 하는 사람과 농작업을 제공하는 사람을 연결하는 양방향 O2O 플랫폼
- **핵심 도메인**: 농기계 작업 매칭, 건조시설 예약(수율/품질), 지자체 정책 연계
- **타겟**: 농업인(의뢰자) + 장비보유자(작업자) + 건조시설 운영자 + 전문 사업자
- **현재 Phase**: Phase 1 (Lv1 MVP)
- **개발 방식**: Claude Code + AI Prompt 기반 (비아 방법론 v6)

### 모듈 구조 (10개 × 4레벨)

| ID  | 모듈       | Lv1 MVP 핵심                     |
|-----|-----------|----------------------------------|
| M01 | AUTH      | 핸드폰 인증 + JWT                 |
| M02 | USER      | 기본 프로필 + 역할 전환             |
| M03 | MATCHING  | 수동 매칭 + GPS 반경 필터           |
| M04 | DRYING    | 시설 등록 + 예약 + 투입/산출 기록    |
| M05 | CHAT      | 1:1 텍스트 채팅 + 읽음 표시         |
| M06 | NOTIFY    | 앱 푸시 알림 + 알림 목록            |
| M07 | REVIEW    | 별점 + 한줄 후기                   |
| M08 | PAYMENT   | 금액 협의 기록 + 정산 확인           |
| M09 | ADMIN     | 사용자/작업 조회 + 기본 통계         |
| M10 | MOBILE    | Flutter 앱 (로그인~채팅~지원현황)    |

---

## 02. 기술 스택

### Backend
- **Framework**: FastAPI (Python 3.11)
- **ORM**: SQLAlchemy 2.0 + Alembic (마이그레이션)
- **DB**: PostgreSQL 16
- **Cache/Session**: Redis 7
- **Auth**: JWT (access + refresh token)
- **WebSocket**: FastAPI WebSocket (채팅)
- **API 문서**: 자동 생성 (Swagger/ReDoc)

### Frontend (Web Admin)
- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **State**: Zustand
- **Styling**: Tailwind CSS
- **HTTP**: Axios + React Query

### Mobile
- **Framework**: Flutter 3.x + Dart
- **State**: Riverpod
- **HTTP**: Dio
- **Local**: SharedPreferences + sqflite

### Infrastructure
- **Container**: Docker Compose
- **Proxy**: Traefik
- **CI/CD**: GitHub Actions
- **Map**: 카카오맵 API

---

## 04. 핵심 운영 규칙

### 비즈니스 로직

1. **양방향 역할**: 모든 사용자는 의뢰자이면서 작업자가 될 수 있음. 역할 전환은 앱 내에서 자유롭게.
2. **매칭 플로우**: 작업등록 → 알림 → 지원 → 선택 → 채팅협의 → 작업수행 → 평가 → 정산
3. **건조 수율 계산**: `수율(%) = (산출량 / 투입량) × 100`. 투입량과 산출량은 kg 단위. 수분함량, 색상, 등급은 품질 지표.
4. **GPS 반경**: 기본 반경 5km, 최대 30km. 반경 내 작업만 알림 발송.
5. **긴급 작업**: `is_urgent=true`인 작업은 목록 최상단 + 별도 애니메이션 배지 + 즉시 푸시 알림.
6. **신뢰도 점수**: `(완료작업수 × 0.4) + (평균평점 × 0.3) + (응답률 × 0.3)`. Lv2에서 구현.

### 농업 도메인 용어 (정확한 현장 용어 사용)

| 일반 표현     | 현장 용어      | 설명                          |
|-------------|--------------|-------------------------------|
| 벼 수확      | 벼베기        | 벼는 '베다' 동사 사용            |
| 고구마 수확   | 고구마 캐기    | 땅속 작물은 '캐다'              |
| 마늘 파종     | 마늘 심기     | 쪽을 하나씩 심으므로 '심기'       |
| 드론 방제     | 드론 방제     | 그대로 사용 (정확)              |
| 로터리 작업   | 로터리 작업    | 그대로 사용 (경운 작업)          |
| 면적 단위     | 평           | 현장에서는 평 단위 사용          |

### API 설계 규칙

- RESTful: `POST /api/v1/jobs`, `GET /api/v1/jobs/{id}`
- 응답 포맷: `{ "success": bool, "data": {}, "error": { "code": str, "message": str } }`
- 페이지네이션: cursor-based (`?cursor=xxx&limit=20`)
- 에러 코드: `DNNG-{MODULE}-{NUMBER}` (예: `DNNG-AUTH-001`)
- 날짜/시간: ISO 8601 (UTC 저장, 클라이언트에서 KST 변환)

---

## 06. 디렉토리 구조

```
danngam/
├── CLAUDE.md                    # 이 파일 (프로젝트 전역)
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── CLAUDE.md                # Backend 서브디렉토리 규칙
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/              # SQLAlchemy 모델
│   │   │   ├── user.py
│   │   │   ├── job.py           # 작업 (매칭)
│   │   │   ├── drying.py        # 건조시설 + 예약
│   │   │   ├── chat.py
│   │   │   └── review.py
│   │   ├── schemas/             # Pydantic 스키마
│   │   ├── routers/             # API 라우터 (모듈별)
│   │   │   ├── auth.py          # M01
│   │   │   ├── users.py         # M02
│   │   │   ├── jobs.py          # M03
│   │   │   ├── drying.py        # M04
│   │   │   ├── chat.py          # M05
│   │   │   ├── notifications.py # M06
│   │   │   ├── reviews.py       # M07
│   │   │   └── payments.py      # M08
│   │   ├── services/            # 비즈니스 로직
│   │   ├── utils/
│   │   └── dependencies.py
│   ├── alembic/                 # DB 마이그레이션
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── CLAUDE.md                # Frontend 서브디렉토리 규칙
│   ├── src/
│   │   ├── components/          # 공유 컴포넌트
│   │   ├── pages/               # Screen ID 매핑
│   │   │   ├── Dashboard.tsx    # DG-main-dashboard
│   │   │   ├── JobCreate.tsx    # DG-work-create
│   │   │   ├── JobList.tsx      # DG-work-list
│   │   │   ├── JobDetail.tsx    # DG-work-detail
│   │   │   ├── JobMap.tsx       # DG-work-map
│   │   │   ├── MyApps.tsx       # DG-my-applications
│   │   │   ├── ChatRoom.tsx     # DG-chat-room
│   │   │   ├── BizUpgrade.tsx   # DG-business-upgrade
│   │   │   ├── ServiceReg.tsx   # DG-service-register
│   │   │   ├── ServiceMgmt.tsx  # DG-service-manage
│   │   │   └── MyRequests.tsx   # DG-my-requests
│   │   ├── hooks/
│   │   ├── stores/
│   │   ├── api/
│   │   └── types/
│   └── package.json
├── mobile/
│   ├── CLAUDE.md                # Flutter 서브디렉토리 규칙
│   ├── lib/
│   │   ├── main.dart
│   │   ├── models/
│   │   ├── providers/
│   │   ├── screens/             # Screen ID 매핑
│   │   ├── services/
│   │   ├── widgets/
│   │   └── utils/
│   └── pubspec.yaml
└── docs/
    ├── SDD/                     # Spec-Driven Definition
    │   ├── M01_AUTH.md
    │   ├── M03_MATCHING.md
    │   ├── M04_DRYING.md
    │   └── ...
    ├── demo/                    # Demo Scenarios
    └── api/                     # API 명세 보조
```

---

## 08. 코딩 컨벤션

### Python (Backend)
- **Formatter**: Black (line-length=88)
- **Linter**: Ruff
- **Type hints**: 모든 함수에 필수
- **Naming**: snake_case (변수/함수), PascalCase (클래스/모델)
- **Import 순서**: stdlib → third-party → local (isort)
- **Docstring**: Google style
- **비동기**: async/await 사용 (sync 함수 금지, DB 쿼리 포함)

### TypeScript (Frontend)
- **Formatter**: Prettier
- **Linter**: ESLint (strict)
- **Naming**: camelCase (변수/함수), PascalCase (컴포넌트/타입)
- **컴포넌트**: 함수형 컴포넌트 only (class 컴포넌트 금지)
- **스타일**: Tailwind utility class only (CSS 직접 작성 금지, globals.css 제외)
- **Import**: absolute path (`@/components/...`)

### Flutter (Mobile)
- **Formatter**: dart format
- **Linter**: flutter_lints (strict)
- **Naming**: camelCase (변수/함수), PascalCase (클래스/위젯)
- **State**: Riverpod (Provider 패턴)
- **디렉토리**: feature-first (screens/models/providers 분리)

### Git
- **Branch**: `feature/{MODULE_ID}-{description}` (예: `feature/M03-job-matching`)
- **Commit**: `{type}({scope}): {description}` (예: `feat(M03): add job list filter`)
- **PR**: 최소 1인 리뷰 후 머지
- **금지**: main 직접 push, force push, --no-verify

### 금지 사항
- ❌ `any` 타입 사용 금지 (TypeScript)
- ❌ CSS 직접 작성 금지 (Tailwind only)
- ❌ console.log 커밋 금지
- ❌ 하드코딩 URL/비밀키 금지 (환경변수 사용)
- ❌ sync DB 쿼리 금지 (async only)
- ❌ shadow-lg, gradient, #000 사용 금지 (디자인 시스템 준수)

---

## 부록: AI 개발 워크플로우

### 일일 루틴
```
09:00  Daily Standup (15분)
09:15  SDD 확인 → CLAUDE.md 규칙 확인
09:30  AI Coding Session
       Plan Mode → 계획 확인
       Molecular Prompt → 1Goal씩 생성
       Verify → lint + test + 수동확인
       반복 (AP 1개당 ~20분)
12:00  PR 생성 + Peer Review 요청
17:00  작업 로그 + /compact 또는 /clear
```

### Context 관리
- 0~50%: 자유롭게 작업
- 50~70%: 주의, 큰 작업 시작 자제
- 70~90%: `/compact` 필수
- 90%+: `/clear` 필수

### Molecular Prompt 규칙
- 1 Goal + 1~3 Files + 10분 검증
- Plan Mode First (타협 없음)
- 검증 후 커밋 (lint + type check + 수동 확인)
