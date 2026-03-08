# CLAUDE.md — Mobile (Flutter)

> 단감 프로젝트 Mobile 서브디렉토리 규칙

## 기술 스택
- Flutter 3.x, Dart, Riverpod, Dio, SharedPreferences, sqflite, 카카오맵 SDK

## 코딩 컨벤션
- Formatter: dart format
- Linter: flutter_lints (strict)
- Naming: camelCase (변수/함수), PascalCase (클래스/위젯)
- State: Riverpod (AsyncNotifierProvider 패턴)
- 디렉토리: feature-first (screens/models/providers 분리)

## 디렉토리 구조
```
lib/
  main.dart
  models/      # Dart 데이터 모델 (fromJson/toJson)
  providers/   # Riverpod 프로바이더
  screens/     # Screen ID 매핑 화면
  services/    # API 서비스 (Dio)
  widgets/     # 공통 위젯
  utils/       # 유틸리티 (날짜 포맷, KST 변환 등)
```

## Screen ID 매핑
- HomeScreen         → DG-main-dashboard
- JobListScreen      → DG-work-list
- JobDetailScreen    → DG-work-detail
- JobCreateScreen    → DG-work-create
- ChatScreen         → DG-chat-room
- MyAppsScreen       → DG-my-applications
- JobMapScreen       → DG-work-map

## 금지 사항
- setState() 직접 사용 금지 (Riverpod 사용)
- BuildContext across async gaps 금지
- 하드코딩 API URL 금지 (환경변수/flavor 사용)
