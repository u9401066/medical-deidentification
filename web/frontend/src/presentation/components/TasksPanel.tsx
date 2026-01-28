import { useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { Button, ScrollArea } from '@/presentation/components/ui'
import { TaskCard } from './TaskCard'
import api, { TaskStatus } from '@/infrastructure/api'

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
              <TaskCard key={task.task_id} task={task} />
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  )
}
