import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'

type Step = 'phone' | 'otp'

export default function Login() {
  const navigate = useNavigate()
  const { setTokens } = useAuthStore()

  const [step, setStep] = useState<Step>('phone')
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSendSms = async () => {
    setError(null)
    setLoading(true)
    try {
      await authApi.sendSms(phone)
      setStep('otp')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error
          ?.message ?? 'SMS 발송에 실패했습니다.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOtp = async () => {
    setError(null)
    setLoading(true)
    try {
      const res = await authApi.verifySms(phone, code)
      const { access_token, refresh_token } = res.data.data
      setTokens(access_token, refresh_token)
      navigate('/')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error
          ?.message ?? '인증에 실패했습니다.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-2xl p-8 w-full max-w-sm border border-gray-100">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary-600">단감</h1>
          <p className="text-gray-500 text-sm mt-1">농작업 O2O 플랫폼</p>
        </div>

        {step === 'phone' ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">휴대폰 번호</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="01012345678"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            {error && <p className="text-red-500 text-xs">{error}</p>}
            <button
              onClick={handleSendSms}
              disabled={loading || phone.length < 10}
              className="w-full bg-primary-600 text-white py-2.5 rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary-700 transition-colors"
            >
              {loading ? '발송 중...' : '인증번호 받기'}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              <span className="font-medium">{phone}</span>으로 인증번호가 발송되었습니다.
            </p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">인증번호 6자리</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="000000"
                maxLength={6}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 text-center tracking-widest text-lg"
              />
            </div>
            {error && <p className="text-red-500 text-xs">{error}</p>}
            <button
              onClick={handleVerifyOtp}
              disabled={loading || code.length !== 6}
              className="w-full bg-primary-600 text-white py-2.5 rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary-700 transition-colors"
            >
              {loading ? '확인 중...' : '로그인'}
            </button>
            <button
              onClick={() => { setStep('phone'); setCode(''); setError(null) }}
              className="w-full text-sm text-gray-500 hover:text-gray-700"
            >
              번호 다시 입력
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
