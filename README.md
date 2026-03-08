# 단감(DANNGAM)

> 농기계를 보유한 작업자와 농작업이 필요한 의뢰자를 연결하는 양방향 O2O 플랫폼

시기별 농작업-농기계 매칭, 필지 기반 자동추천, 건조시설 위탁, 에스크로 결제, 농작업 대행단 그룹 수주/자동할당, 전국 대형장비 스케줄링, 보조금 자동정산까지 농업의 전 과정을 디지털화합니다.

## 주요 기능

| EP | 핵심 기능 | 마감일 |
|----|-----------|--------|
| [EP1](https://github.com/viakisun/danngam_rev2/milestone/1) | 소셜로그인, 농기계-농작업 DB, 백오피스, 장비 등록/조회, 홈 화면 | 2026-05-30 |
| [EP2](https://github.com/viakisun/danngam_rev2/milestone/2) | 필지 등록, 매칭, 채팅/계약, 에스크로 결제, 건조위탁, 정산 | 2026-09-12 |
| [EP3](https://github.com/viakisun/danngam_rev2/milestone/3) | 지자체 보조금, 리포트, 대행단 생성/수주/할당/정산 | 2026-12-26 |
| [EP4](https://github.com/viakisun/danngam_rev2/milestone/4) | 제조사 포털, 시험포, R&D 실증사업 | 2027-03-12 |
| [EP5](https://github.com/viakisun/danngam_rev2/milestone/5) | 데이터 대시보드, AI 예측, Agent, 전국 스케줄링 | 2027-06-27 |

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Backend | FastAPI + SQLAlchemy 2.0 + Alembic (Python 3.11) |
| Database | PostgreSQL 16 + Redis 7 |
| Mobile | Flutter 3.x + Riverpod + Dio + go_router |
| Web Admin | React 18 + TypeScript + Vite + Tailwind CSS + Zustand |
| Infra | Docker Compose + Traefik + GitHub Actions |
| 결제 | 토스페이먼츠 (에스크로) |

## 디렉토리 구조

```
danngam_rev2/
├── backend/          # FastAPI API 서버
│   ├── app/
│   │   ├── models/   # SQLAlchemy ORM
│   │   ├── schemas/  # Pydantic 스키마
│   │   ├── routers/  # API 라우터 (M01~M09)
│   │   ├── services/ # 비즈니스 로직
│   │   └── utils/    # JWT, Geo 등
│   ├── alembic/      # DB 마이그레이션
│   └── tests/        # pytest
├── frontend/         # React 백오피스 (Web Admin)
│   └── src/
│       ├── pages/    # 페이지 컴포넌트
│       ├── api/      # Axios API 클라이언트
│       └── stores/   # Zustand 상태
├── mobile/           # Flutter 모바일 앱
│   └── lib/
│       ├── screens/  # 화면
│       ├── providers/# Riverpod 상태
│       └── services/ # API 서비스
└── docs/             # 프로젝트 문서
```

## 시작하기

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (백엔드 개별 실행 시)
- Node.js 20+ (프론트엔드 개별 실행 시)
- Flutter 3.13+ (모바일 개별 실행 시)

### Docker Compose (권장)

```bash
# 환경변수 설정
cp .env.example .env

# 전체 서비스 실행 (PostgreSQL + Redis + Backend + Frontend)
docker compose up -d

# 서비스 확인
# Backend API:  http://localhost:8000
# Frontend:     http://localhost:5173
# Traefik:      http://localhost:8080
```

### 개별 실행

각 서브 프로젝트의 README를 참조하세요:

- [backend/README.md](backend/README.md) — FastAPI 서버
- [frontend/README.md](frontend/README.md) — React 백오피스
- [mobile/README.md](mobile/README.md) — Flutter 앱

## API 문서

서버 실행 후 자동 생성되는 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API 모듈

| 모듈 | 경로 | 설명 |
|------|------|------|
| M01 AUTH | `/api/v1/auth/*` | 인증 (SMS, JWT) |
| M02 USER | `/api/v1/users/*` | 사용자 프로필 |
| M03 MATCHING | `/api/v1/jobs/*` | 작업 매칭 |
| M04 DRYING | `/api/v1/drying/*` | 건조시설/예약 |
| M05 CHAT | `/api/v1/chat/*` | 1:1 채팅 (WebSocket) |
| M06 NOTIFY | `/api/v1/notifications/*` | 알림 |
| M07 REVIEW | `/api/v1/reviews/*` | 평가/후기 |
| M08 PAYMENT | `/api/v1/payments/*` | 정산 |
| M09 ADMIN | `/api/v1/admin/*` | 관리자 |

## 환경변수

`.env.example`을 복사하여 `.env`를 생성하세요. 주요 변수:

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 연결 | `postgresql+asyncpg://danngam:danngam_secret@localhost:5432/danngam` |
| `REDIS_URL` | Redis 연결 | `redis://localhost:6379` |
| `SECRET_KEY` | JWT 서명 키 | (필수 설정) |
| `SMS_PROVIDER` | SMS 제공자 | `mock` |

## CI/CD

GitHub Actions로 자동화:

- **Backend**: Ruff lint + Black format + pytest (PostgreSQL + Redis)
- **Frontend**: ESLint + TypeScript check + Vite build

## 프로젝트 관리

- [Issues](https://github.com/viakisun/danngam_rev2/issues) — WBS 기반 태스크 (AP 코드별 그룹)
- [Milestones](https://github.com/viakisun/danngam_rev2/milestones) — EP1~EP5 Gate
- [Labels](https://github.com/viakisun/danngam_rev2/labels) — EP, 모듈(M01~M12), 레이어, 사이즈

## 라이선스

Private repository. All rights reserved.
