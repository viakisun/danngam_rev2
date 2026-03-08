# CLAUDE.md — Frontend (React + TypeScript)

> 단감 프로젝트 Frontend 서브디렉토리 규칙

## 기술 스택
- React 18, TypeScript, Vite, Zustand, Tailwind CSS, Axios, React Query

## 코딩 컨벤션
- Formatter: Prettier
- Linter: ESLint (strict)
- Naming: camelCase (변수/함수), PascalCase (컴포넌트/타입)
- **함수형 컴포넌트 only** (class 컴포넌트 금지)
- 스타일: Tailwind utility class only (CSS 직접 작성 금지, globals.css 제외)
- Import: absolute path (`@/components/...`)
- **`any` 타입 사용 금지**

## 디렉토리 구조
```
src/
  components/   # 공유 컴포넌트
  pages/        # Screen ID 매핑 페이지
  hooks/        # 커스텀 훅
  stores/       # Zustand 스토어
  api/          # Axios 인스턴스 + API 함수
  types/        # TypeScript 타입 정의
```

## Screen ID 매핑
- Dashboard.tsx   → DG-main-dashboard
- JobList.tsx     → DG-work-list
- JobDetail.tsx   → DG-work-detail
- JobCreate.tsx   → DG-work-create
- ChatRoom.tsx    → DG-chat-room
- MyApps.tsx      → DG-my-applications

## 금지 사항
- `any` 타입 금지
- CSS 직접 작성 금지 (Tailwind only)
- console.log 커밋 금지
- shadow-lg, gradient, #000 사용 금지
