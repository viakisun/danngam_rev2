import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'providers/auth_provider.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/job_list_screen.dart';
import 'screens/job_detail_screen.dart';
import 'screens/job_create_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/my_apps_screen.dart';

void main() {
  runApp(const ProviderScope(child: DanGamApp()));
}

class DanGamApp extends ConsumerWidget {
  const DanGamApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);

    final router = GoRouter(
      initialLocation: '/',
      redirect: (context, state) {
        final isAuth = authState.status == AuthStatus.authenticated;
        final isUnknown = authState.status == AuthStatus.unknown;
        final isLoginPage = state.matchedLocation == '/login';

        if (isUnknown) return null;
        if (!isAuth && !isLoginPage) return '/login';
        if (isAuth && isLoginPage) return '/';
        return null;
      },
      routes: [
        GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
        GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
        GoRoute(path: '/jobs', builder: (_, __) => const JobListScreen()),
        GoRoute(
          path: '/jobs/:id',
          builder: (_, state) => JobDetailScreen(jobId: state.pathParameters['id']!),
        ),
        GoRoute(path: '/jobs/create', builder: (_, __) => const JobCreateScreen()),
        GoRoute(path: '/chat', builder: (_, __) => const ChatScreen()),
        GoRoute(
          path: '/chat/:roomId',
          builder: (_, state) => ChatScreen(roomId: state.pathParameters['roomId']),
        ),
        GoRoute(path: '/my-apps', builder: (_, __) => const MyAppsScreen()),
      ],
    );

    return MaterialApp.router(
      title: '단감',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      routerConfig: router,
    );
  }
}
