import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { RefreshCw, CheckCircle, XCircle, Clock, AlertCircle, Timer, FileText } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Progress, Badge, ScrollArea } from '@/presentation/components/ui'
import { useTasks } from '@/application/hooks'

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
  const { tasks, isLoading, processingTasks, completedTasks, failedTasks, refresh } = useTasks({ refetchInterval: 2000 })

  // 監控任務狀態變化 - 當有任務完成時刷新結果和報告
  useEffect(() => {
    if (completedTasks.length > 0) {
      queryClient.invalidateQueries({ queryKey: ['results'] })
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['files'] })
    }
  }, [completedTasks.length, queryClient])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'completed_with_errors':
        return <AlertCircle className="h-5 w-5 text-amber-500" />
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
      case 'completed_with_errors':
        return <Badge className="bg-amber-500">部分失敗</Badge>
      case 'failed':
        return <Badge variant="destructive">失敗</Badge>
      case 'processing':
        return <Badge className="bg-blue-500">處理中</Badge>
      default:
        return <Badge variant="outline">等待中</Badge>
    }
  }

  const progressValue = (progress: number) => (progress <= 1 ? progress * 100 : progress)
  const progressText = (progress: number) => `${Math.round(progressValue(progress))}%`
  const fileProgressText = (progress?: number | null) => {
    if (progress === undefined || progress === null) return null
    const value = progress <= 1 ? progress * 100 : progress
    return `${Math.round(value)}%`
  }

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
          onClick={refresh}
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
            {tasks.map((task) => {
              const fileResults = Object.values(task.fileResults)
              const fileCount = task.totalFiles || task.fileIds.length || fileResults.length
              const primaryFileLabel = fileResults.length > 0
                ? fileResults.map((file) => file.filename || file.fileId).join(', ')
                : task.currentFile || `${fileCount} 個檔案`

              return (
              <Card key={task.id} className={`
                ${task.status === 'processing' ? 'border-blue-500 border-2' : ''}
                ${task.status === 'completed' ? 'border-green-500/50' : ''}
                ${task.status === 'completed_with_errors' ? 'border-amber-500/70' : ''}
                ${task.status === 'failed' ? 'border-red-500/50' : ''}
              `}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(task.status)}
                      <CardTitle className="text-base">
                        任務 {task.id.slice(0, 8)}
                      </CardTitle>
                    </div>
                    {getStatusBadge(task.status)}
                  </div>
                  <div className="mt-2 space-y-1">
                    <p className="text-sm font-medium truncate" title={primaryFileLabel}>
                      <FileText className="inline h-3.5 w-3.5 mr-1 text-muted-foreground" />
                      {primaryFileLabel}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {fileCount} 個檔案
                      {task.filesCompleted !== undefined && task.totalFiles
                        ? ` • 已完成 ${task.filesCompleted}/${task.totalFiles}`
                        : ''}
                      {task.ownerUsername ? ` • owner: ${task.ownerUsername}` : ''}
                    </p>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {fileResults.length > 0 && (
                    <div className="space-y-1">
                      {fileResults.map((file) => (
                        <div key={file.fileId} className="rounded bg-muted/50 px-2 py-1 text-xs">
                          <div className="flex items-center justify-between gap-2">
                            <span className="truncate" title={file.filename || file.fileId}>
                              {file.filename || file.fileId}
                            </span>
                            <Badge
                              variant={file.status === 'error' ? 'destructive' : 'outline'}
                              className="shrink-0"
                            >
                              {file.status === 'completed'
                                ? `${file.phiFound} PHI`
                                : file.status === 'processing'
                                ? '處理中'
                                : file.status === 'error'
                                ? '錯誤'
                                : '等待'}
                            </Badge>
                          </div>
                          {file.status === 'error' && file.error && (
                            <p className="mt-1 text-[11px] text-red-600 line-clamp-2">
                              {file.error}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* 進度條 */}
                  {task.status === 'processing' && (
                    <>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-medium text-blue-600">
                            {task.phaseLabel || '處理中'}
                          </span>
                          <span className="text-muted-foreground">
                            {progressText(task.progress)}
                          </span>
                        </div>
                        <Progress value={progressValue(task.progress)} className="h-2" />
                        {fileProgressText(task.currentFileProgress) && (
                          <div className="text-xs text-muted-foreground">
                            目前檔案進度: {fileProgressText(task.currentFileProgress)}
                            {task.phase === 'model_scanning' ? '（模型掃描中，為估算值）' : ''}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Timer className="h-3 w-3" />
                          已用時: {task.elapsedTimeFormatted || formatTime(task.elapsedSeconds)}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          剩餘: {task.estimatedRemainingFormatted || formatTime(task.estimatedRemainingSeconds)}
                        </div>
                      </div>
                      {task.processingSpeed && task.processingSpeed > 0 && (
                        <div className="text-xs text-muted-foreground">
                          速度: {task.processingSpeed.toFixed(1)} 字元/秒
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
                  {(task.status === 'completed' || task.status === 'completed_with_errors') && task.elapsedSeconds && (
                    <div className="flex items-center justify-between text-sm">
                      <span className={task.status === 'completed_with_errors' ? 'text-amber-600' : 'text-green-600'}>
                        {task.status === 'completed_with_errors' ? '⚠ 部分完成' : '✓ 耗時'}: {task.elapsedTimeFormatted || formatTime(task.elapsedSeconds)}
                      </span>
                      {task.processingSpeed && task.processingSpeed > 0 && (
                        <span className="text-muted-foreground">
                          {task.processingSpeed.toFixed(0)} 字元/秒
                        </span>
                      )}
                    </div>
                  )}

                  {/* 時間戳記 */}
                  <div className="text-xs text-muted-foreground pt-2 border-t">
                    建立: {task.createdAt.toLocaleString('zh-TW')}
                  </div>
                </CardContent>
              </Card>
              )
            })}
          </div>
        )}
      </ScrollArea>
    </div>
  )
}
