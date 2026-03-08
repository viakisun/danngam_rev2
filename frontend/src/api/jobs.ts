import type { ApiResponse, CursorPage, Job } from '@/types'
import apiClient from './client'

export interface JobListParams {
  lat: number
  lng: number
  radius_km?: number
  category?: string
  cursor?: string
  limit?: number
}

export const jobsApi = {
  list: (params: JobListParams) =>
    apiClient.get<ApiResponse<CursorPage<Job>>>('/jobs', { params }),

  get: (id: string) => apiClient.get<ApiResponse<Job>>(`/jobs/${id}`),

  create: (data: Partial<Job>) => apiClient.post<ApiResponse<Job>>('/jobs', data),

  updateStatus: (id: string, status: string) =>
    apiClient.patch<ApiResponse<Job>>(`/jobs/${id}/status`, { status }),

  apply: (id: string, message?: string) =>
    apiClient.post(`/jobs/${id}/applications`, { message }),

  selectApplicant: (jobId: string, applicantId: string) =>
    apiClient.post(`/jobs/${jobId}/applications/${applicantId}/select`),
}
