# CLAUDE.md — Backend (FastAPI)

> 단감 프로젝트 Backend 서브디렉토리 규칙

## 기술 스택
- Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 16, Redis 7

## 코딩 컨벤션
- Formatter: Black (line-length=88)
- Linter: Ruff
- Type hints: 모든 함수 필수
- Naming: snake_case (변수/함수), PascalCase (클래스/모델)
- Import: stdlib → third-party → local (isort)
- Docstring: Google style
- **비동기 필수**: DB 쿼리 포함 모든 I/O는 async/await

## 디렉토리 구조
```
app/
  main.py          # FastAPI 앱 엔트리포인트
  config.py        # pydantic-settings 환경변수
  database.py      # async SQLAlchemy engine + session
  dependencies.py  # get_db, get_current_user
  models/          # SQLAlchemy ORM 모델
  schemas/         # Pydantic 스키마
  routers/         # API 라우터 (모듈별)
  services/        # 비즈니스 로직
  utils/           # 유틸리티
alembic/           # DB 마이그레이션
tests/             # pytest 테스트
```

## API 설계 규칙
- 응답: `{ "success": bool, "data": {}, "error": { "code": str, "message": str } }`
- 에러 코드: `DNNG-{MODULE}-{NUMBER}`
- 페이지네이션: cursor-based (`?cursor=xxx&limit=20`)
- 날짜: ISO 8601 UTC 저장

## 금지 사항
- sync DB 쿼리 금지 (`session.execute()` 아닌 `await session.execute()`)
- 하드코딩 비밀키 금지 (환경변수만)
- `print()` 디버그 금지 (logging 사용)
