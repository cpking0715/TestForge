/** API 客户端契约：信封解包、错误传播、token 注入。 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, getToken, request, setToken } from './client'

function mockFetch(status: number, body: unknown) {
  return vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }),
  )
}

beforeEach(() => {
  setToken(null)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('request 信封处理', () => {
  it('code=0 时返回 data', async () => {
    vi.stubGlobal('fetch', mockFetch(200, { code: 0, msg: 'ok', data: { id: 1 } }))
    await expect(request('/api/v1/x')).resolves.toEqual({ id: 1 })
  })

  it('code≠0 时抛 ApiError 并携带 code/msg', async () => {
    vi.stubGlobal('fetch', mockFetch(200, { code: 1002, msg: '验证码错误', data: null }))
    const err = (await request("/api/v1/x").catch((e) => e)) as ApiError
    expect(err).toBeInstanceOf(ApiError)
    expect(err.message).toBe('验证码错误')
    expect(err.code).toBe(1002)
  })

  it('有 token 时注入 Authorization 头', async () => {
    setToken('abc123')
    const fetchMock = mockFetch(200, { code: 0, msg: 'ok', data: null })
    vi.stubGlobal('fetch', fetchMock)
    await request('/api/v1/x')
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(new Headers(init.headers).get('Authorization')).toBe('Bearer abc123')
  })

  it('401 时清除 token 并抛错', async () => {
    setToken('stale-token')
    vi.stubGlobal('fetch', mockFetch(401, { code: 401, msg: '未登录或登录已过期', data: null }))
    const err = (await request("/api/v1/x").catch((e) => e)) as ApiError
    expect(err.code).toBe(401)
    expect(getToken()).toBeNull()
  })
})
