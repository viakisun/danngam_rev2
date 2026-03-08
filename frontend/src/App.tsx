import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from '@/components/Layout'
import { useAuthStore } from '@/stores/authStore'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import JobList from '@/pages/JobList'
import JobDetail from '@/pages/JobDetail'
import JobCreate from '@/pages/JobCreate'
import JobMap from '@/pages/JobMap'
import ChatRoom from '@/pages/ChatRoom'
import MyApps from '@/pages/MyApps'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const { initFromStorage } = useAuthStore()

  useEffect(() => {
    initFromStorage()
  }, [initFromStorage])

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <RequireAuth>
                <Layout />
              </RequireAuth>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="jobs" element={<JobList />} />
            <Route path="jobs/create" element={<JobCreate />} />
            <Route path="jobs/:id" element={<JobDetail />} />
            <Route path="jobs/map" element={<JobMap />} />
            <Route path="chat" element={<ChatRoom />} />
            <Route path="chat/:roomId" element={<ChatRoom />} />
            <Route path="my-apps" element={<MyApps />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
