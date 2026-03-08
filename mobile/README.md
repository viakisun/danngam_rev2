# Mobile — Flutter 앱

단감 모바일 애플리케이션. Flutter 3.x + Riverpod + Dio + go_router.

## 실행

```bash
cd mobile
flutter pub get
flutter run           # 기본 디바이스
flutter run -d chrome # 웹 디버깅
```

## 화면 구조

| 파일 | Screen ID | 설명 |
|------|-----------|------|
| `home_screen.dart` | DG-main-dashboard | 홈 화면 |
| `job_list_screen.dart` | DG-work-list | 작업 목록 |
| `job_detail_screen.dart` | DG-work-detail | 작업 상세 |
| `job_create_screen.dart` | DG-work-create | 작업 등록 |
| `chat_screen.dart` | DG-chat-room | 1:1 채팅 |
| `my_apps_screen.dart` | DG-my-applications | 내 지원 현황 |
| `login_screen.dart` | — | 로그인 |

## 상태 관리

Riverpod 패턴 사용:
- `providers/` — Riverpod Provider 정의
- `services/` — Dio 기반 API 서비스
- `models/` — Dart 데이터 모델 (fromJson/toJson)

## 코딩 컨벤션

- **Riverpod** 상태 관리 (setState 금지)
- **go_router** 네비게이션
- **dart format** 포매팅
- API URL 하드코딩 금지 (환경변수/flavor)
