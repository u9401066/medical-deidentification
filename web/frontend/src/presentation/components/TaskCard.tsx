import { RefreshCw, CheckCircle, XCircle, Clock, Timer } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, Progress, Badge } from '@/presentation/components/ui'
import { TaskStatus } from '@/infrastructure/api'

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

interface TaskCardProps {
  task: TaskStatus
}

export function TaskCard({ task }: TaskCardProps) {
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

  return (
    <Card className={`
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
        {/* 處理的文件 */}
        {task.file_results && Object.keys(task.file_results).length > 0 ? (
          <div className="text-sm space-y-1">
            {Object.values(task.file_results).map((fr) => (
              <div key={fr.file_id} className="flex items-center justify-between">
                <span className="font-medium truncate max-w-[200px]">
                  {fr.filename || fr.file_id}
                </span>
                <Badge variant={
                  fr.status === 'completed' ? 'default' :
                  fr.status === 'processing' ? 'secondary' :
                  fr.status === 'error' ? 'destructive' : 'outline'
                } className="text-xs">
                  {fr.status === 'completed' ? `✓ ${fr.phi_found} PHI` :
                   fr.status === 'processing' ? '處理中' :
                   fr.status === 'error' ? '錯誤' : '等待'}
                </Badge>
              </div>
            ))}
          </div>
        ) : task.current_file ? (
          <div className="text-sm">
            <span className="text-muted-foreground">文件: </span>
            <span className="font-medium">{task.current_file}</span>
          </div>
        ) : null}

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
  )
}
