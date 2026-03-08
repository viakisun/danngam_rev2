import type { ApiResponse, TokenResponse } from '@/types'
import apiClient from './client'

export const authApi = {
  sendSms: (phone: string) =>
    apiClient.post<ApiResponse<{ message: string }>>('/auth/sms/send', { phone }),

  verifySms: (phone: string, code: string) =>
    apiClient.post<ApiResponse<TokenResponse>>('/auth/sms/verify', { phone, code }),

  refreshToken: (refreshToken: string) =>
    apiClient.post<ApiResponse<{ access_token: string }>>('/auth/token/refresh', {
      refresh_token: refreshToken,
    }),
}
