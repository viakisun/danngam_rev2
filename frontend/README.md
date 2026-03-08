# Frontend — React 백오피스 (Web Admin)

단감 관리자 웹 애플리케이션. React 18 + TypeScript + Vite + Tailwind CSS + Zustand + React Query.

## 실행

```bash
cd frontend
cp .env.example .env   # 환경변수 편집
npm install
npm run dev            # http://localhost:5173
```

## 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `VITE_API_BASE_URL` | Backend API 주소 | `http://localhost:8000/api/v1` |
| `VITE_WS_BASE_URL` | WebSocket 주소 | `ws://localhost:8000` |

## 스크립트

```bash
npm run dev        # 개발 서버
npm run build      # 프로덕션 빌드
npm run preview    # 빌드 미리보기
npm run lint       # ESLint
npm run typecheck  # TypeScript 검사
```

## 페이지 구조

| 파일 | Screen ID | 설명 |
|------|-----------|------|
| `Dashboard.tsx` | DG-main-dashboard | 관리자 대시보드 |
| `JobList.tsx` | DG-work-list | 작업 목록 |
| `JobDetail.tsx` | DG-work-detail | 작업 상세 |
| `JobCreate.tsx` | DG-work-create | 작업 등록 |
| `JobMap.tsx` | DG-work-map | 지도 뷰 |
| `ChatRoom.tsx` | DG-chat-room | 채팅 |
| `MyApps.tsx` | DG-my-applications | 내 지원 현황 |
| `Login.tsx` | — | 로그인 |

## 코딩 컨벤션

- **함수형 컴포넌트 only** (class 컴포넌트 금지)
- **Tailwind utility class only** (CSS 직접 작성 금지)
- **`any` 타입 사용 금지**
- Import: `@/components/...` (절대 경로)
