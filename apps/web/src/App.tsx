/** 根路由：登录页独立，业务页挂在 Layout 下。 */

import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './app/Layout'
import LoginPage from './features/auth/LoginPage'
import Dashboard from './pages/Dashboard'
import UsersPage from './pages/system/Users'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/system/user" element={<UsersPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
