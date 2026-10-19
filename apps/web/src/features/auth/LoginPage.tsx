/** 登录页：账号密码 + 算术验证码，点击图片刷新。 */

import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi, type CaptchaPayload } from './api'
import { ApiError, setToken } from '../../shared/api/client'

export default function LoginPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [captcha, setCaptcha] = useState('')
  const [captchaImg, setCaptchaImg] = useState<CaptchaPayload | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const refreshCaptcha = useCallback(async () => {
    setCaptchaImg(await authApi.getCaptcha())
    setCaptcha('')
  }, [])

  useEffect(() => {
    refreshCaptcha().catch(() => setError('验证码加载失败，请点击刷新'))
  }, [refreshCaptcha])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!captchaImg || loading) return
    setError('')
    setLoading(true)
    try {
      const result = await authApi.login({
        username,
        password,
        captcha_key: captchaImg.key,
        captcha,
      })
      setToken(result.token)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '登录失败，请重试')
      await refreshCaptcha()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100">
      <form
        onSubmit={onSubmit}
        className="w-90 rounded-xl bg-white p-8 shadow-md"
        aria-label="登录 TestForge"
      >
        <h1 className="mb-1 text-2xl font-semibold text-slate-800">TestForge</h1>
        <p className="mb-6 text-sm text-slate-500">内部一站式测试平台</p>

        <label className="mb-1 block text-sm text-slate-600" htmlFor="username">
          用户名
        </label>
        <input
          id="username"
          className="mb-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          required
        />

        <label className="mb-1 block text-sm text-slate-600" htmlFor="password">
          密码
        </label>
        <input
          id="password"
          type="password"
          className="mb-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />

        <label className="mb-1 block text-sm text-slate-600" htmlFor="captcha">
          验证码
        </label>
        <div className="mb-4 flex gap-2">
          <input
            id="captcha"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
            value={captcha}
            onChange={(e) => setCaptcha(e.target.value)}
            placeholder="输入计算结果"
            required
          />
          {captchaImg && (
            <button
              type="button"
              onClick={() => refreshCaptcha()}
              className="shrink-0 overflow-hidden rounded-lg border border-slate-300"
              title="点击刷新验证码"
              aria-label="点击刷新验证码"
            >
              <img src={captchaImg.img_base} alt="验证码" className="h-9 w-30" />
            </button>
          )}
        </div>

        {error && (
          <p role="alert" className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-slate-800 py-2.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {loading ? '登录中…' : '登录'}
        </button>
      </form>
    </div>
  )
}
