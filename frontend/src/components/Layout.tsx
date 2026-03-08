import { Link, useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

const NAV_ITEMS = [
  { path: '/', label: '대시보드', icon: '🏠' },
  { path: '/jobs', label: '작업 목록', icon: '📋' },
  { path: '/jobs/create', label: '작업 등록', icon: '➕' },
  { path: '/chat', label: '채팅', icon: '💬' },
  { path: '/my-apps', label: '내 지원 현황', icon: '📝' },
]

export default function Layout() {
  const location = useLocation()
  const { user, logout } = useAuthStore()

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 사이드바 */}
      <aside className="w-60 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-100">
          <span className="text-xl font-bold text-primary-600">단감</span>
          <p className="text-xs text-gray-400 mt-0.5">농작업 O2O 플랫폼</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV_ITEMS.map(({ path, label, icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                location.pathname === path
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span>{icon}</span>
              <span>{label}</span>
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-100">
          {user && (
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-sm">
                {user.name?.[0] ?? '?'}
              </div>
              <div className="text-sm">
                <p className="font-medium text-gray-800">{user.name ?? '이름 없음'}</p>
                <p className="text-xs text-gray-400">{user.current_role}</p>
              </div>
            </div>
          )}
          <button
            onClick={logout}
            className="w-full text-sm text-gray-500 hover:text-gray-700 text-left"
          >
            로그아웃
          </button>
        </div>
      </aside>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
