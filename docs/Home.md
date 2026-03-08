# 단감(DANNGAM) — 농기계·농작업 매칭 O2O 플랫폼

## 프로젝트 개요

농기계를 보유한 작업자와 농작업이 필요한 의뢰자를 연결하는 양방향 O2O 플랫폼.

## EP 로드맵

| EP | 이름 | 마감일 | 핵심 기능 |
|----|------|--------|-----------|
| EP1 | 초기데이터 + 작업자 온보딩 | 2026-05-30 | 소셜로그인, 장비DB, 백오피스, 장비등록/조회, 홈 화면 |
| EP2 | 매칭/거래 + 건조위탁 + 결제 | 2026-09-12 | 필지, 캘린더, 매칭, 채팅, 에스크로, 건조위탁, 정산 |
| EP3 | 보조금 + 대행단 | 2026-12-26 | 보조금 CRUD, 리포트, 대행단 생성/수주/할당/정산 |
| EP4 | 제조사/R&D 연계 | 2027-03-12 | 제조사 포털, 시험포, 실증사업 |
| EP5 | 데이터/AI + 스케줄링 | 2027-06-27 | 대시보드, AI 예측, Agent, 전국 스케줄링 |

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Backend | FastAPI + SQLAlchemy 2.0 + Alembic (Python 3.11) |
| Database | PostgreSQL 16 + Redis 7 |
| Mobile | Flutter 3.x + Riverpod + Dio + go_router |
| Web Admin | React 18 + TypeScript + Vite + Tailwind + Zustand |
| Infra | Docker Compose + Traefik + GitHub Actions |
| 결제 | 토스페이먼츠 (에스크로) |

## 모듈 구조

| ID | Module | EP |
|----|--------|----|
| M01 | AUTH — 인증 | EP1 |
| M02 | USER — 사용자/필지 | EP2 |
| M03 | MATCHING — 매칭 | EP2 |
| M04 | DRYING — 건조시설 | EP2 |
| M05 | CHAT — 채팅 | EP2 |
| M06 | PAYMENT — 결제/정산 | EP2 |
| M07 | SUBSIDY — 보조금 | EP3 |
| M08 | MFG-RND — 제조사 | EP4 |
| M09 | ANALYTICS — 분석/관리 | EP1(init), EP5 |
| M10 | MOBILE — 모바일앱 | EP2 |
| M11 | CREW — 대행단 | EP3 |
| M12 | SCHEDULING — 스케줄링 | EP5 |

## 데모 시나리오

- [[EP1 Demo Scenario]]
- [[EP2 Demo Scenario]]
- [[EP3 Demo Scenario]]
- [[EP4 Demo Scenario]]
- [[EP5 Demo Scenario]]
