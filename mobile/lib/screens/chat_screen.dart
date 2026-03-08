// TODO: Lv1 구현 예정 — WebSocket 채팅 UI
import 'package:flutter/material.dart';
import '../widgets/placeholder_screen.dart';

class ChatScreen extends StatelessWidget {
  final String? roomId;
  const ChatScreen({super.key, this.roomId});

  @override
  Widget build(BuildContext context) {
    return const PlaceholderScreen(
      title: '채팅',
      screenId: 'DG-chat-room',
      description: 'WebSocket 실시간 채팅 UI입니다. Lv1 구현 예정.',
    );
  }
}
