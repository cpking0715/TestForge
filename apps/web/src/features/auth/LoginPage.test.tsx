/** 登录页交互：验证码加载 → 提交成功写 token → 失败提示并刷新验证码。 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LoginPage from './LoginPage'
import { authApi } from './api'
import { ApiError } from '../../shared/api/client'
import { getToken } from '../../shared/api/client'

vi.mock('./api', () => ({
  authApi: {
    getCaptcha: vi.fn(),
    login: vi.fn(),
    me: vi.fn(),
    menus: vi.fn(),
    logout: vi.fn(),
  },
}))

const getCaptcha = vi.mocked(authApi.getCaptcha)
const login = vi.mocked(authApi.login)

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  getCaptcha.mockResolvedValue({ key: 'k1', img_base: 'data:image/png;base64,xxx' })
})

function renderPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  it('挂载时自动加载验证码图片', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByAltText('验证码')).toBeInTheDocument())
    expect(getCaptcha).toHaveBeenCalledTimes(1)
  })

  it('登录成功后写入 token', async () => {
    login.mockResolvedValue({
      token: 'tok-1',
      user: { id: 1, username: 'admin', nickname: '管理员', is_super: true, roles: ['super_admin'] },
    })
    renderPage()
    await screen.findByAltText('验证码')

    await userEvent.type(screen.getByLabelText('用户名'), 'admin')
    await userEvent.type(screen.getByLabelText('密码'), 'admin123')
    await userEvent.type(screen.getByLabelText('验证码'), '9')
    await userEvent.click(screen.getByRole('button', { name: '登录' }))

    await waitFor(() => expect(getToken()).toBe('tok-1'))
    expect(login).toHaveBeenCalledWith({
      username: 'admin',
      password: 'admin123',
      captcha_key: 'k1',
      captcha: '9',
    })
  })

  it('登录失败展示错误信息并刷新验证码', async () => {
    login.mockRejectedValue(new ApiError('验证码错误', 1002))
    renderPage()
    await screen.findByAltText('验证码')

    await userEvent.type(screen.getByLabelText('用户名'), 'admin')
    await userEvent.type(screen.getByLabelText('密码'), 'admin123')
    await userEvent.type(screen.getByLabelText('验证码'), '1')
    await userEvent.click(screen.getByRole('button', { name: '登录' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('验证码错误')
    await waitFor(() => expect(getCaptcha).toHaveBeenCalledTimes(2))
    expect(getToken()).toBeNull()
  })
})
