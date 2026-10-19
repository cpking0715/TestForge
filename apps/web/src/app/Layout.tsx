/** 主布局：侧边菜单（来自后端 /auth/menus）+ 顶栏 + 内容区。 */

import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { authApi, type MenuItem, type MeInfo } from '../features/auth/api'
import { getToken } from '../shared/api/client'

export default function Layout() {
  const navigate = useNavigate()
  const [me, setMe] = useState<MeInfo | null>(null)
  const [menus, setMenus] = useState<MenuItem[]>([])

  useEffect(() => {
    if (!getToken()) {
      navigate('/login', { replace: true })
      return
    }
    authApi.me().then(setMe).catch(() => {})
    authApi.menus().then(setMenus).catch(() => {})
  }, [navigate])

  function logout() {
    authApi.logout()
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="flex w-56 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-5 py-4 text-lg font-semibold text-slate-800">
          TestForge
        </div>
        <nav className="flex-1 overflow-y-auto py-2" aria-label="主导航">
          <MenuTree items={menus} />
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
          <span className="text-sm text-slate-500">工作台</span>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <span>{me?.nickname || me?.username || '…'}</span>
            <button
              onClick={logout}
              className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-100"
            >
              退出
            </button>
          </div>
        </header>
        <main className="min-w-0 flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function MenuTree({ items }: { items: MenuItem[] }) {
  return (
    <ul className="px-2">
      {items
        .filter((m) => m.type !== 'button' && m.visible)
        .map((m) => (
          <li key={m.id}>
            {m.type === 'page' ? (
              <NavLink
                to={m.path}
                end
                className={({ isActive }) =>
                  `block rounded-md px-3 py-2 text-sm ${
                    isActive
                      ? 'bg-slate-100 font-medium text-slate-900'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`
                }
              >
                {m.name}
              </NavLink>
            ) : (
              <div className="px-3 py-2 text-sm text-slate-400">{m.name}</div>
            )}
            {m.children.length > 0 && <MenuTree items={m.children} />}
          </li>
        ))}
    </ul>
  )
}
