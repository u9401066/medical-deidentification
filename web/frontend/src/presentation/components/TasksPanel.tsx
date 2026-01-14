import { useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, CheckCircle, XCircle, Clock, AlertCircle, Timer } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Progress, Badge, ScrollArea } from '@/presentation/components/ui'
import api, { TaskStatus } from '@/infrastructure/api'

// 格式化時間
function formatTime(seconds?: number): string {
  if (seconds === undefined || seconds === null || seconds < 0) {
    return '計算中...'
  }
  if (seconds < 60) {
    return `${Math.round(seconds)} 秒`
  } else if (seconds < 3600) {
    const mins = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return `${mins} 分 ${secs} 秒`
  } else {
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    return `${hours} 小時 ${mins} 分`
  }
}

export function TasksPanel() {
  const queryClient = useQueryClient()

  // 取得任務列表
  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: api.listTasks,
    refetchInterval: 2000, // 每 2 秒更新
  })

  // 監控任務狀態變化
  useEffect(() => {
    const completed = tasks.filter((t: TaskStatus) => t.status === 'completed')
    if (completed.length > 0) {
      queryClient.invalidateQueries({ queryKey: ['results'] })
      queryClient.invalidateQueries({ queryKey: ['files'] })
    }
  }, [tasks, queryClient])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'processing':
        return <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-500">完成</Badge>
      case 'failed':
        return <Badge variant="destructive">失敗</Badge>
      case 'processing':
        return <Badge className="bg-blue-500">處理中</Badge>
      default:
        return <Badge variant="outline">等待中</Badge>
    }
  }

  const processingTasks = tasks.filter((t: TaskStatus) => t.status === 'processing')
  const completedTasks = tasks.filter((t: TaskStatus) => t.status === 'completed')
  const failedTasks = tasks.filter((t: TaskStatus) => t.status === 'failed')

  return (
    <div className="flex flex-col h-full p-4">
      {/* 標題列 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold">處理任務</h2>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <RefreshCw className="h-3 w-3 text-blue-500" />
              進行中: {processingTasks.length}
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="h-3 w-3 text-green-500" />
              完成: {completedTasks.length}
            </span>
            {failedTasks.length > 0 && (
              <span className="flex items-center gap-1">
                <XCircle className="h-3 w-3 text-red-500" />
                失敗: {failedTasks.length}
              </span>
            )}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['tasks'] })}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          重新整理
        </Button>
      </div>

      {/* 任務列表 */}
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="text-center text-muted-foreground py-8">載入中...</div>
        ) : tasks.length === 0 ? (
          <div className="text-center text-muted-foreground py-16">
            <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>尚無處理任務</p>
            <p className="text-sm mt-2">在左側選擇檔案並點擊「開始處理」</p>
          </div>
        ) : (
          <div className="grid gap-4 grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
            {tasks.map((task: TaskStatus) => (
              <Card key={task.task_id} className={`
                ${task.status === 'processing' ? 'border-blue-500 border-2' : ''}
                ${task.status === 'completed' ? 'border-green-500/50' : ''}
                ${task.status === 'failed' ? 'border-red-500/50' : ''}
              `}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(task.status)}
                      <CardTitle className="text-base">
                        任務 {task.task_id.slice(0, 8)}
                      </CardTitle>
                    </div>
                    {getStatusBadge(task.status)}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* 進度條 */}
                  {task.status === 'processing' && (
                    <>
                      <Progress value={task.progress} className="h-2" />
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Timer className="h-3 w-3" />
                          已用時: {formatTime(task.elapsed_seconds)}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          剩餘: {formatTime(task.estimated_remaining_seconds)}
                        </div>
                      </div>
                      {task.processing_speed && task.processing_speed > 0 && (
                        <div className="text-xs text-muted-foreground">
                          速度: {task.processing_speed.toFixed(1)} 字元/秒
                        </div>
                      )}
                    </>
                  )}

                  {/* 訊息 */}
                  {task.message && (
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {task.message}
                    </p>
                  )}

                  {/* 完成狀態 */}
                  {task.status === 'completed' && task.elapsed_seconds && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-green-600">
                        ✓ 耗時: {formatTime(task.elapsed_seconds)}
                      </span>
                      {task.processing_speed && task.processing_speed > 0 && (
                        <span className="text-muted-foreground">
                          {task.processing_speed.toFixed(0)} 字元/秒
                        </span>
                      )}
                    </div>
                  )}

                  {/* 時間戳記 */}
                  <div className="text-xs text-muted-foreground pt-2 border-t">
                    建立: {new Date(task.created_at).toLocaleString('zh-TW')}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  )
}
