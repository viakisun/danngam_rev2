# Backend — FastAPI

단감 API 서버. Python 3.11 + FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 16 + Redis 7.

## 실행

### 1. 환경 설정

```bash
cd backend
cp .env.example .env   # 환경변수 편집
```

### 2. 가상환경 + 의존성

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. DB 준비

PostgreSQL과 Redis가 실행 중이어야 합니다:

```bash
# Docker로 실행 (루트에서)
docker compose up postgres redis -d
```

### 4. 마이그레이션

```bash
alembic upgrade head
```

### 5. 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

API 문서: http://localhost:8000/docs

## 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `ENVIRONMENT` | 실행 환경 | `development` |
| `DATABASE_URL` | PostgreSQL 연결 문자열 | (필수) |
| `REDIS_URL` | Redis 연결 문자열 | `redis://localhost:6379` |
| `SECRET_KEY` | JWT 서명 키 (32자 이상) | (필수) |
| `ALGORITHM` | JWT 알고리즘 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 액세스 토큰 만료(분) | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 리프레시 토큰 만료(일) | `30` |
| `SMS_PROVIDER` | SMS 제공자 (`mock` / `aligo`) | `mock` |
| `ALLOWED_ORIGINS` | CORS 허용 도메인 | `http://localhost:5173` |

## 테스트

```bash
# 전체 테스트
pytest tests/ -v

# 커버리지 포함
pytest tests/ -v --cov=app --cov-report=term-missing

# 특정 모듈
pytest tests/test_auth.py -v
pytest tests/test_jobs.py -v
```

테스트는 SQLite in-memory DB를 사용합니다 (PostgreSQL 불필요).

## API 구조

| 라우터 | 경로 | 모듈 |
|--------|------|------|
| `auth.py` | `/api/v1/auth/*` | M01 — SMS 인증, JWT 발급/갱신 |
| `users.py` | `/api/v1/users/*` | M02 — 프로필 조회/수정, 역할 전환 |
| `jobs.py` | `/api/v1/jobs/*` | M03 — 작업 CRUD, 지원/선택, GPS 필터 |
| `drying.py` | `/api/v1/drying/*` | M04 — 건조시설 CRUD, 예약, 수율 계산 |
| `chat.py` | `/api/v1/chat/*` | M05 — 채팅방, 메시지, WebSocket |
| `notifications.py` | `/api/v1/notifications/*` | M06 — 알림 목록, 읽음 처리 |
| `reviews.py` | `/api/v1/reviews/*` | M07 — 평가 작성, 평균 평점 |
| `payments.py` | `/api/v1/payments/*` | M08 — 정산 기록, 확인 |
| `admin.py` | `/api/v1/admin/*` | M09 — 사용자/작업 관리, 통계 |

## 코딩 컨벤션

- **Formatter**: Black (line-length=88)
- **Linter**: Ruff
- **Type hints**: 모든 함수 필수
- **비동기**: DB 쿼리 포함 모든 I/O는 `async/await`
- **응답 형식**: `{"success": bool, "data": {}, "error": {"code": "DNNG-XXX-NNN", "message": "..."}}`

```bash
# 포맷팅
black app/

# 린트
ruff check app/
```
