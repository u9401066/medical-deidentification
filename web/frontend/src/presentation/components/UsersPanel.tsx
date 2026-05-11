import { FormEvent, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Shield, UserPlus } from 'lucide-react'
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/presentation/components/ui'
import api, { AuthUser } from '@/infrastructure/api'
import { toast } from 'sonner'

interface UsersPanelProps {
  currentUser: AuthUser
}

export function UsersPanel({ currentUser }: UsersPanelProps) {
  const queryClient = useQueryClient()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<'admin' | 'user'>('user')

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['auth-users'],
    queryFn: api.listUsers,
    enabled: currentUser.role === 'admin',
  })

  const createMutation = useMutation({
    mutationFn: () => api.createUser(username, password, role),
    onSuccess: () => {
      toast.success('使用者已建立')
      setUsername('')
      setPassword('')
      setRole('user')
      queryClient.invalidateQueries({ queryKey: ['auth-users'] })
    },
    onError: () => toast.error('建立使用者失敗'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ userId, updates }: { userId: string; updates: { role?: 'admin' | 'user'; is_active?: boolean } }) =>
      api.updateUser(userId, updates),
    onSuccess: () => {
      toast.success('使用者已更新')
      queryClient.invalidateQueries({ queryKey: ['auth-users'] })
    },
    onError: () => toast.error('更新使用者失敗'),
  })

  const handleCreate = (event: FormEvent) => {
    event.preventDefault()
    createMutation.mutate()
  }

  if (currentUser.role !== 'admin') {
    return (
      <div className="p-6 text-muted-foreground">
        此頁面僅限 admin 管理使用者。
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            新增使用者
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="grid gap-3 md:grid-cols-[1fr_1fr_160px_auto]">
            <Input placeholder="帳號" value={username} onChange={(event) => setUsername(event.target.value)} required />
            <Input placeholder="密碼" type="password" minLength={1} value={password} onChange={(event) => setPassword(event.target.value)} required />
            <Select value={role} onValueChange={(value) => setRole(value as 'admin' | 'user')}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="user">user</SelectItem>
                <SelectItem value="admin">admin</SelectItem>
              </SelectContent>
            </Select>
            <Button type="submit" disabled={createMutation.isPending}>建立</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            使用者與角色
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-muted-foreground">載入中...</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>帳號</TableHead>
                  <TableHead>角色</TableHead>
                  <TableHead>狀態</TableHead>
                  <TableHead>最後登入</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.user_id}>
                    <TableCell>{user.username}</TableCell>
                    <TableCell>
                      <Badge variant={user.role === 'admin' ? 'default' : 'outline'}>{user.role}</Badge>
                    </TableCell>
                    <TableCell>{user.is_active ? '啟用' : '停用'}</TableCell>
                    <TableCell>{user.last_login_at ? new Date(user.last_login_at).toLocaleString('zh-TW') : '尚無'}</TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={user.user_id === currentUser.user_id}
                        onClick={() => updateMutation.mutate({
                          userId: user.user_id,
                          updates: { role: user.role === 'admin' ? 'user' : 'admin' },
                        })}
                      >
                        切換角色
                      </Button>
                      <Button
                        size="sm"
                        variant={user.is_active ? 'destructive' : 'outline'}
                        disabled={user.user_id === currentUser.user_id}
                        onClick={() => updateMutation.mutate({
                          userId: user.user_id,
                          updates: { is_active: !user.is_active },
                        })}
                      >
                        {user.is_active ? '停用' : '啟用'}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
