import { FormEvent, useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ShieldCheck } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Badge } from '@/presentation/components/ui'
import api, { AuthUser } from '@/infrastructure/api'
import { API_BASE } from '@/infrastructure/api/base'
import { toast } from 'sonner'
import type { ReactNode } from 'react'

interface AuthGateProps {
  children: (user: AuthUser, onLogout: () => void) => ReactNode
}

export function AuthGate({ children }: AuthGateProps) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [setupRequired, setSetupRequired] = useState(false)
  const [loading, setLoading] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [authError, setAuthError] = useState<string | null>(null)
  const inputClassName = 'border-slate-700 bg-slate-950 text-slate-100 placeholder:text-slate-500'

  useEffect(() => {
    let cancelled = false
    async function loadAuthState() {
      setAuthError(null)
      try {
        const me = await api.getCurrentUser()
        if (!cancelled) setUser(me.user)
      } catch (meError) {
        try {
          const required = await api.getSetupRequired()
          if (!cancelled) {
            setSetupRequired(required)
            setAuthError(null)
          }
        } catch (setupError) {
          if (!cancelled) {
            setSetupRequired(false)
            setAuthError(
              `無法連線到後端 API (${API_BASE})。請確認前端部署設定與 CORS。`
            )
          }
          console.error('Auth state load failed', { meError, setupError })
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadAuthState()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    async function handleAuthError(event: Event) {
      const status = (event as CustomEvent<{ status?: number }>).detail?.status
      if (status === 401) {
        if (user) toast.error('登入已過期，請重新登入')
        queryClient.clear()
        setUser(null)
        setPassword('')
        return
      }
      if (status === 403 && user) {
        try {
          const me = await api.getCurrentUser()
          queryClient.clear()
          setUser(me.user)
          toast.error('權限不足，已重新同步使用者角色')
        } catch {
          queryClient.clear()
          setUser(null)
        }
      }
    }

    window.addEventListener('medical-deid-auth-error', handleAuthError)
    return () => window.removeEventListener('medical-deid-auth-error', handleAuthError)
  }, [queryClient, user])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    try {
      const response = setupRequired
        ? await api.bootstrapAdmin(username, password)
        : await api.login(username, password)
      queryClient.clear()
      setUser(response.user)
      toast.success(setupRequired ? '管理員已建立' : '登入成功')
    } catch {
      toast.error(setupRequired ? '建立管理員失敗' : '登入失敗')
    } finally {
      setSubmitting(false)
    }
  }

  const handleLogout = async () => {
    const loggedOut = await api.logout().then(() => true).catch(() => false)
    if (!loggedOut) {
      toast.error('本機已登出，但伺服器 session 未確認清除')
    }
    queryClient.clear()
    setUser(null)
    setPassword('')
  }

  if (loading) {
    return <div className="grid h-screen place-items-center text-muted-foreground">載入驗證狀態...</div>
  }

  if (user) {
    return children(user, handleLogout)
  }

  if (authError) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 grid place-items-center p-6">
        <Card className="w-full max-w-md border-slate-800 bg-slate-900/90 text-slate-100 shadow-2xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-amber-400" />
              無法連線到後端
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="rounded bg-amber-500/10 p-3 text-sm text-amber-100">
              {authError}
            </p>
            <p className="text-xs text-slate-400">
              目前前端 API endpoint: {API_BASE}
            </p>
            <Button className="w-full" type="button" onClick={() => window.location.reload()}>
              重新載入
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 grid place-items-center p-6">
      <Card className="w-full max-w-md border-slate-800 bg-slate-900/90 text-slate-100 shadow-2xl">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-400" />
              醫療去識別化登入
            </CardTitle>
            <Badge variant="outline">{setupRequired ? '首次設定' : '安全入口'}</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {setupRequired && (
              <p className="rounded bg-amber-500/10 p-3 text-sm text-amber-200">
                尚未建立任何使用者。請先建立第一個 admin 帳號。
              </p>
            )}
            <Input
              autoComplete="username"
              className={inputClassName}
              placeholder="帳號"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
            <Input
              autoComplete={setupRequired ? 'new-password' : 'current-password'}
              className={inputClassName}
              minLength={1}
              placeholder="密碼"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <Button className="w-full" type="submit" disabled={submitting}>
              {submitting ? '處理中...' : setupRequired ? '建立 admin' : '登入'}
            </Button>
            <p className="text-xs text-slate-400">
              多人正式上線請透過 HTTPS reverse proxy 存取；session cookie 會由後端以 HttpOnly 方式發放。
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
