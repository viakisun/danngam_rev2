import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';

enum _LoginStep { phone, otp }

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  _LoginStep _step = _LoginStep.phone;
  final _phoneCtrl = TextEditingController();
  final _otpCtrl = TextEditingController();
  bool _loading = false;
  String? _error;

  Future<void> _sendSms() async {
    setState(() { _loading = true; _error = null; });
    try {
      await apiService.dio.post('/auth/sms/send', data: {'phone': _phoneCtrl.text});
      setState(() { _step = _LoginStep.otp; });
    } catch (e) {
      setState(() { _error = _parseError(e, 'SMS 발송에 실패했습니다.'); });
    } finally {
      setState(() { _loading = false; });
    }
  }

  Future<void> _verifyOtp() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await apiService.dio.post('/auth/sms/verify', data: {
        'phone': _phoneCtrl.text,
        'code': _otpCtrl.text,
      });
      final data = res.data['data'] as Map<String, dynamic>;
      await ref.read(authProvider.notifier).login(
        data['access_token'] as String,
        data['refresh_token'] as String,
      );
      if (mounted) context.go('/');
    } catch (e) {
      setState(() { _error = _parseError(e, '인증에 실패했습니다.'); });
    } finally {
      setState(() { _loading = false; });
    }
  }

  String _parseError(Object e, String fallback) {
    try {
      final data = (e as dynamic).response?.data as Map<String, dynamic>?;
      return data?['error']?['message'] as String? ?? fallback;
    } catch (_) {
      return fallback;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(32),
            child: Column(
              children: [
                const Text(
                  '단감',
                  style: TextStyle(
                    fontSize: 36,
                    fontWeight: FontWeight.bold,
                    color: Colors.green,
                  ),
                ),
                const SizedBox(height: 4),
                Text('농작업 O2O 플랫폼', style: TextStyle(color: Colors.grey[500])),
                const SizedBox(height: 48),
                if (_step == _LoginStep.phone) ...[
                  TextField(
                    controller: _phoneCtrl,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(
                      labelText: '휴대폰 번호',
                      hintText: '01012345678',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (_error != null)
                    Text(_error!, style: const TextStyle(color: Colors.red, fontSize: 12)),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _loading ? null : _sendSms,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: _loading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Text('인증번호 받기', style: TextStyle(color: Colors.white)),
                    ),
                  ),
                ] else ...[
                  Text(
                    '${_phoneCtrl.text}으로\n인증번호가 발송되었습니다.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey[700]),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _otpCtrl,
                    keyboardType: TextInputType.number,
                    maxLength: 6,
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 24, letterSpacing: 8),
                    decoration: const InputDecoration(
                      labelText: '인증번호 6자리',
                      border: OutlineInputBorder(),
                      counterText: '',
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (_error != null)
                    Text(_error!, style: const TextStyle(color: Colors.red, fontSize: 12)),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _loading ? null : _verifyOtp,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: _loading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Text('로그인', style: TextStyle(color: Colors.white)),
                    ),
                  ),
                  TextButton(
                    onPressed: () => setState(() { _step = _LoginStep.phone; _otpCtrl.clear(); _error = null; }),
                    child: const Text('번호 다시 입력'),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
