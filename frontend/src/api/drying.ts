import type { ApiResponse } from '@/types'
import apiClient from './client'

export const dryingApi = {
  listFacilities: (params?: { lat?: number; lng?: number }) =>
    apiClient.get<ApiResponse<{ items: unknown[] }>>('/drying/facilities', { params }),

  createFacility: (data: unknown) =>
    apiClient.post<ApiResponse<unknown>>('/drying/facilities', data),

  createReservation: (data: unknown) =>
    apiClient.post<ApiResponse<unknown>>('/drying/reservations', data),

  getReservation: (id: string) =>
    apiClient.get<ApiResponse<unknown>>(`/drying/reservations/${id}`),

  approveReservation: (id: string) =>
    apiClient.patch<ApiResponse<unknown>>(`/drying/reservations/${id}/approve`),

  completeReservation: (id: string, data: unknown) =>
    apiClient.patch<ApiResponse<unknown>>(`/drying/reservations/${id}/complete`, data),
}
