import type { ApiResponse, ChatMessage, ChatRoom, CursorPage } from '@/types'
import apiClient from './client'

export const chatApi = {
  listRooms: () =>
    apiClient.get<ApiResponse<{ items: ChatRoom[] }>>('/chat/rooms'),

  getMessages: (roomId: string, params?: { cursor?: string; limit?: number }) =>
    apiClient.get<ApiResponse<CursorPage<ChatMessage>>>(`/chat/rooms/${roomId}/messages`, {
      params,
    }),

  markAsRead: (roomId: string) =>
    apiClient.post<ApiResponse<{ read_count: number }>>(`/chat/rooms/${roomId}/read`),
}

/** WebSocket 채팅 연결 헬퍼 */
export function createChatWebSocket(roomId: string, token: string): WebSocket {
  const wsBase = import.meta.env.VITE_WS_BASE_URL ?? `ws://${window.location.host}`
  return new WebSocket(`${wsBase}/api/v1/chat/ws/chat/${roomId}?token=${token}`)
}
