/** 공통 API 응답 래퍼 */
export interface ApiResponse<T> {
  success: boolean
  data: T
  error: ApiError | null
}

export interface ApiError {
  code: string
  message: string
}

/** 사용자 역할 */
export type UserRole = 'REQUESTER' | 'WORKER'

/** 사용자 */
export interface User {
  id: string
  phone: string
  name: string | null
  profile_image_url: string | null
  current_role: UserRole
  avg_rating: number
  is_active: boolean
  created_at: string
  updated_at: string
}

/** 작업 카테고리 */
export type JobCategory =
  | 'RICE_HARVESTING'
  | 'SWEET_POTATO_HARVESTING'
  | 'GARLIC_PLANTING'
  | 'DRONE_SPRAYING'
  | 'ROTARY_TILLAGE'
  | 'TRANSPLANTING'
  | 'ONION_HARVESTING'
  | 'CORN_HARVESTING'
  | 'OTHER'

/** 작업 상태 */
export type JobStatus = 'OPEN' | 'MATCHED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'

/** 보수 유형 */
export type PayType = 'PER_PYEONG' | 'PER_DAY' | 'FIXED' | 'NEGOTIABLE'

/** 작업 */
export interface Job {
  id: string
  requester_id: string
  title: string
  description: string | null
  category: JobCategory
  location_lat: number
  location_lng: number
  location_address: string | null
  area_pyeong: number | null
  pay_type: PayType
  pay_amount: number | null
  work_date: string | null
  is_urgent: boolean
  status: JobStatus
  distance_km: number | null
  created_at: string
  updated_at: string
}

/** 페이지네이션 (cursor-based) */
export interface CursorPage<T> {
  items: T[]
  next_cursor: string | null
}

/** 토큰 응답 */
export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  is_new_user: boolean
}

/** 채팅방 */
export interface ChatRoom {
  id: string
  job_id: string
  requester_id: string
  worker_id: string
  last_message: string | null
  last_message_at: string | null
  unread_count: number
  created_at: string
}

/** 채팅 메시지 */
export interface ChatMessage {
  id: string
  room_id: string
  sender_id: string
  content: string
  is_read: boolean
  read_at: string | null
  created_at: string
}
