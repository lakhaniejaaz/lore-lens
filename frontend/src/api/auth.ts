import { apiRequest, type ApiResult } from './client'

export interface AuthUser {
  id: number
  first_name: string
  last_name: string
  username: string
  email: string
  created_at: string
}

export interface LoginResponse {
  status: string
  data: {
    user: AuthUser
  }
}

// Username must already be trimmed and password must be sent exactly as
// entered by the time this is called.
export function login(username: string, password: string): Promise<ApiResult<LoginResponse>> {
  return apiRequest<LoginResponse>('/auth/login', { username, password })
}
