import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthState {
  final AuthStatus status;
  final String? userId;
  final String? userRole;

  const AuthState({
    this.status = AuthStatus.unknown,
    this.userId,
    this.userRole,
  });

  AuthState copyWith({
    AuthStatus? status,
    String? userId,
    String? userRole,
  }) =>
      AuthState(
        status: status ?? this.status,
        userId: userId ?? this.userId,
        userRole: userRole ?? this.userRole,
      );
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier() : super(const AuthState()) {
    _init();
  }

  Future<void> _init() async {
    final valid = await apiService.hasValidToken();
    state = state.copyWith(
      status: valid ? AuthStatus.authenticated : AuthStatus.unauthenticated,
    );
  }

  Future<void> login(String accessToken, String refreshToken) async {
    await apiService.saveTokens(accessToken, refreshToken);
    state = state.copyWith(status: AuthStatus.authenticated);
  }

  Future<void> logout() async {
    await apiService.clearTokens();
    state = state.copyWith(
      status: AuthStatus.unauthenticated,
      userId: null,
      userRole: null,
    );
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (_) => AuthNotifier(),
);
