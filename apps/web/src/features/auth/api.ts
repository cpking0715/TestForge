/** 认证域 API（调用只在本层）。 */

import { get, post } from '../../shared/api/client'

export interface CaptchaPayload {
  key: string
  img_base: string
}

export interface LoginResult {
  token: string
  user: { id: number; username: string; nickname: string; is_super: boolean; roles: string[] }
}

export interface MeInfo {
  id: number
  username: string
  nickname: string
  is_super: boolean
  roles: string[]
  permissions: string[]
}

export interface MenuItem {
  id: number
  parent_id: number | null
  name: string
  type: 'dir' | 'page' | 'button'
  path: string
  permission: string
  icon: string
  sort: number
  visible: boolean
  children: MenuItem[]
}

export const authApi = {
  getCaptcha: () => get<CaptchaPayload>('/api/v1/system/auth/captcha/get'),
  login: (body: { username: string; password: string; captcha_key: string; captcha: string }) =>
    post<LoginResult>('/api/v1/system/auth/login', body),
  me: () => get<MeInfo>('/api/v1/system/auth/me'),
  menus: () => get<MenuItem[]>('/api/v1/system/auth/menus'),
  logout: () => {
    localStorage.removeItem('tf_token')
    location.href = '/login'
  },
}
