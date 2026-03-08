// TODO: Lv1 구현 예정
import 'package:flutter/material.dart';
import '../widgets/placeholder_screen.dart';

class JobDetailScreen extends StatelessWidget {
  final String jobId;
  const JobDetailScreen({super.key, required this.jobId});

  @override
  Widget build(BuildContext context) {
    return const PlaceholderScreen(title: '작업 상세', screenId: 'DG-work-detail');
  }
}
