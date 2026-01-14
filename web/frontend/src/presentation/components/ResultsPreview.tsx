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

export function ResultsPreview() {
  const queryClient = useQueryClient()

  // 取得任務列表
  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks'],
    queryFn: api.listTasks,
    refetchInterval: 2000, // 每 2 秒更新
  })

  // 取得處理結果
  const { data: results = [] } = useQuery<unknown[]>({
    queryKey: ['results'],
    queryFn: api.getResults,
  })

  // 監控任務狀態
  useEffect(() => {
    // 有任務完成時刷新結果
    const completed = tasks.filter((t: TaskStatus) => t.status === 'completed')
    if (completed.length > 0) {
      queryClient.invalidateQueries({ queryKey: ['results'] })
      queryClient.invalidateQueries({ queryKey: ['files'] })
    }
  }, [tasks, queryClient])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'processing':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default">完成</Badge>
      case 'failed':
        return <Badge variant="destructive">失敗</Badge>
      case 'processing':
        return <Badge variant="secondary">處理中</Badge>
      default:
        return <Badge variant="outline">等待中</Badge>
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* 標題列 */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-lg font-semibold">處理狀態與結果</h2>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] })
            queryClient.invalidateQueries({ queryKey: ['results'] })
          }}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          重新整理
        </Button>
      </div>

      {/* 內容區域 */}
      <div className="flex-1 overflow-hidden grid grid-cols-2 gap-4 p-4">
        {/* 任務狀態 */}
        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              處理任務
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              {tasks.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  尚無任務
                </div>
              ) : (
                <div className="space-y-3">
                  {tasks.map((task: TaskStatus) => (
                    <div
                      key={task.task_id}
                      className="border rounded-lg p-3 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(task.status)}
                          <span className="text-sm font-medium">
                            任務 {task.task_id.slice(0, 8)}
                          </span>
                        </div>
                        {getStatusBadge(task.status)}
                      </div>
                      {task.status === 'processing' && (
                        <>
                          <Progress value={task.progress} />
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Timer className="h-3 w-3" />
                              <span>已用時: {formatTime(task.elapsed_seconds)}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              <span>預計剩餘: {formatTime(task.estimated_remaining_seconds)}</span>
                            </div>
                          </div>
                          {task.processing_speed && task.processing_speed > 0 && (
                            <div className="text-xs text-muted-foreground">
                              處理速度: {task.processing_speed.toFixed(1)} 字元/秒
                            </div>
                          )}
                        </>
                      )}
                      {task.message && (
                        <p className="text-xs text-muted-foreground">
                          {task.message}
                        </p>
                      )}
                      {task.status === 'completed' && task.elapsed_seconds && (
                        <div className="text-xs text-green-600">
                          ✓ 總耗時: {formatTime(task.elapsed_seconds)}
                          {task.processing_speed && task.processing_speed > 0 && 
                            ` (${task.processing_speed.toFixed(1)} 字元/秒)`
                          }
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* 處理結果 */}
        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              處理結果
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              {results.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  尚無處理結果
                </div>
              ) : (
                <div className="space-y-3">
                  {results.map((result: any, idx: number) => (
                    <div
                      key={idx}
                      className="border rounded-lg p-3 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">
                          {result.filename}
                        </span>
                        <Badge variant="outline">
                          {result.phi_count} PHI 項目
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>總筆數: {result.total_records}</span>
                        <span>處理時間: {result.processing_time}s</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
