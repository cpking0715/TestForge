/** 用户管理页：列表 + 新建（RBAC 核心闭环的最小可视化）。 */

import { useCallback, useEffect, useState } from 'react'
import { get, post } from '../../shared/api/client'

interface UserRow {
  id: number
  username: string
  nickname: string
  email: string
  status: boolean
  is_super: boolean
  roles: { id: number; name: string }[]
  created_at: string | null
}

export default function UsersPage() {
  const [rows, setRows] = useState<UserRow[]>([])
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ username: '', password: '', nickname: '' })

  const load = useCallback(async () => {
    try {
      const data = await get<{ total: number; items: UserRow[] }>('/api/v1/system/user/list')
      setRows(data.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function onCreate() {
    setError('')
    try {
      await post('/api/v1/system/user/create', form)
      setForm({ username: '', password: '', nickname: '' })
      setCreating(false)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : '创建失败')
    }
  }

  return (
    <section>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-800">用户管理</h1>
        <button
          onClick={() => setCreating((v) => !v)}
          className="rounded-md bg-slate-800 px-3 py-1.5 text-sm text-white hover:bg-slate-700"
        >
          {creating ? '取消' : '新建用户'}
        </button>
      </div>

      {creating && (
        <div className="mb-4 flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 bg-white p-4">
          <input
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            placeholder="用户名"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
          />
          <input
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            placeholder="密码（≥6 位）"
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          <input
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            placeholder="昵称（可选）"
            value={form.nickname}
            onChange={(e) => setForm({ ...form, nickname: e.target.value })}
          />
          <button
            onClick={onCreate}
            className="rounded-md bg-slate-800 px-3 py-1.5 text-sm text-white hover:bg-slate-700"
          >
            保存
          </button>
        </div>
      )}

      {error && (
        <p role="alert" className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
          {error}
        </p>
      )}

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
            <tr>
              <th className="px-4 py-2.5">用户名</th>
              <th className="px-4 py-2.5">昵称</th>
              <th className="px-4 py-2.5">角色</th>
              <th className="px-4 py-2.5">状态</th>
              <th className="px-4 py-2.5">创建时间</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((u) => (
              <tr key={u.id} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-2.5 font-medium text-slate-700">{u.username}</td>
                <td className="px-4 py-2.5">{u.nickname || '-'}</td>
                <td className="px-4 py-2.5">{u.roles.map((r) => r.name).join('、') || '-'}</td>
                <td className="px-4 py-2.5">{u.status ? '启用' : '停用'}</td>
                <td className="px-4 py-2.5 text-slate-500">{u.created_at?.slice(0, 10) || '-'}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  暂无数据
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
