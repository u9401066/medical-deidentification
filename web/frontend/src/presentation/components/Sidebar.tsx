import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, Trash2, Download, FileSpreadsheet, FileJson, Cpu, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import { Button, ScrollArea, Badge } from '@/presentation/components/ui'
import { useFiles, useUploadFile, useDeleteFile, useHealth } from '@/application/hooks'
import { TASKS_QUERY_KEY } from '@/application/hooks'
import { formatBytes, formatDate } from '@/lib/utils'
import { startProcessing, downloadResult } from '@/infrastructure/api'

interface SidebarProps {
  onFileSelect?: (fileId: string) => void
  selectedFileId?: string | null
}

export function Sidebar({ onFileSelect, selectedFileId }: SidebarProps) {
  const queryClient = useQueryClient()
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)

  // 取得系統健康狀態（含 LLM）
  const { health } = useHealth({ refetchInterval: 10000 })

  // 取得已上傳檔案列表 - 處理中時每 2 秒刷新
  const { files, isLoading } = useFiles()

  // 上傳檔案 mutation
  const uploadMutation = useUploadFile()

  // 刪除檔案 mutation
  const deleteMutation = useDeleteFile()

  // Dropzone 配置
  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      uploadMutation.mutate(file)
    })
  }, [uploadMutation])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'text/plain': ['.txt'],
    },
  })

  // 選取/取消選取檔案（用於批次處理）
  const toggleFileSelection = (fileId: string, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation() // 防止觸發檔案預覽
    }
    setSelectedFiles((prev) =>
      prev.includes(fileId)
        ? prev.filter((id) => id !== fileId)
        : [...prev, fileId]
    )
  }

  // 點擊檔案：預覽 + 切換選取
  const handleFileClick = (fileId: string) => {
    // 切換選取狀態
    setSelectedFiles((prev) =>
      prev.includes(fileId)
        ? prev.filter((id) => id !== fileId)
        : [...prev, fileId]
    )
    // 切換到預覽
    if (onFileSelect) {
      onFileSelect(fileId)
    }
  }

  // 取得檔案圖示
  const getIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    if (ext === 'xlsx' || ext === 'xls' || ext === 'csv') {
      return <FileSpreadsheet className="h-4 w-4" />
    } else if (ext === 'json') {
      return <FileJson className="h-4 w-4" />
    }
    return <FileText className="h-4 w-4" />
  }

  return (
    <div className="w-80 border-r bg-muted/40 flex flex-col h-full">
      {/* 標題 + LLM 狀態 */}
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold">PHI 去識別化工具</h2>
        <p className="text-sm text-muted-foreground">上傳檔案並處理敏感資料</p>
        
        {/* LLM 狀態指示 */}
        <div className="mt-2 flex items-center gap-2 text-xs">
          <Cpu className="h-3 w-3" />
          <span className="text-muted-foreground">LLM:</span>
          {health?.llm?.status === 'online' ? (
            <span className="flex items-center gap-1 text-green-600">
              <CheckCircle className="h-3 w-3" />
              在線 ({health.llm.model || 'ollama'})
            </span>
          ) : (
            <span className="flex items-center gap-1 text-red-500">
              <XCircle className="h-3 w-3" />
              離線
            </span>
          )}
        </div>
        {health && !health.engine_available && (
          <div className="mt-1 text-xs text-yellow-600">
            ⚠️ PHI 引擎未載入（使用模擬處理）
          </div>
        )}
      </div>

      {/* 上傳區域 */}
      <div className="p-4 border-b">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-primary bg-primary/10'
              : 'border-muted-foreground/25 hover:border-primary/50'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
          {isDragActive ? (
            <p className="text-sm text-primary">放開以上傳檔案</p>
          ) : (
            <>
              <p className="text-sm font-medium">拖放檔案至此處</p>
              <p className="text-xs text-muted-foreground mt-1">
                支援 Excel, CSV, JSON, TXT
              </p>
            </>
          )}
        </div>
        {uploadMutation.isPending && (
          <p className="text-sm text-muted-foreground mt-2 text-center">
            上傳中...
          </p>
        )}
      </div>

      {/* 檔案列表 */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="px-4 py-2 border-b flex items-center justify-between">
          <span className="text-sm font-medium">
            已上傳檔案 ({files.length})
          </span>
          {selectedFiles.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                selectedFiles.forEach((id) => deleteMutation.mutate(id))
              }}
            >
              <Trash2 className="h-4 w-4 mr-1" />
              刪除 ({selectedFiles.length})
            </Button>
          )}
        </div>

        <ScrollArea className="flex-1">
          {isLoading ? (
            <div className="p-4 text-center text-muted-foreground">
              載入中...
            </div>
          ) : files.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">
              尚無檔案
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {files.map((file) => (
                <div
                  key={file.id}
                  className={`flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                    selectedFileId === file.id
                      ? 'bg-primary/20 border border-primary/50'
                      : selectedFiles.includes(file.id)
                      ? 'bg-primary/10 border border-primary/30'
                      : 'hover:bg-muted'
                  }`}
                  onClick={() => handleFileClick(file.id)}
                >
                  {/* Checkbox 區域 - 用於選取批次處理 */}
                  <div
                    className="flex items-center justify-center w-5 h-5 rounded border cursor-pointer hover:bg-muted"
                    onClick={(e) => toggleFileSelection(file.id, e)}
                  >
                    {selectedFiles.includes(file.id) && (
                      <CheckCircle className="h-4 w-4 text-primary" />
                    )}
                  </div>
                  {getIcon(file.filename)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {file.filename}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatBytes(file.size)} • {formatDate(file.uploadTime)}
                    </p>
                  </div>
                  <Badge
                    variant={
                      file.status === 'completed'
                        ? 'default'
                        : file.status === 'processing'
                        ? 'secondary'
                        : file.status === 'error'
                        ? 'destructive'
                        : 'outline'
                    }
                  >
                    {file.status === 'completed'
                      ? '已完成'
                      : file.status === 'processing'
                      ? '處理中'
                      : file.status === 'error'
                      ? '錯誤'
                      : '待處理'}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* 操作按鈕 */}
      <div className="p-4 border-t space-y-2">
        <Button
          className="w-full"
          disabled={selectedFiles.length === 0 || isProcessing || health?.llm?.status !== 'online'}
          onClick={async () => {
            if (selectedFiles.length === 0) return
            setIsProcessing(true)
            try {
              await startProcessing({ file_ids: selectedFiles })
              // 立即刷新任務和檔案列表
              await queryClient.invalidateQueries({ queryKey: TASKS_QUERY_KEY })
              await queryClient.invalidateQueries({ queryKey: ['files'] })
              setSelectedFiles([])
              // 延遲一點再關閉 isProcessing，讓 UI 能看到狀態更新
              setTimeout(() => setIsProcessing(false), 1000)
            } catch (err) {
              console.error('處理失敗:', err)
              setIsProcessing(false)
            }
          }}
        >
          {isProcessing ? (
            <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />處理中...</>
          ) : (
            <>開始處理 ({selectedFiles.length})</>
          )}
        </Button>
        <Button
          variant="outline"
          className="w-full"
          disabled={
            selectedFiles.length === 0 ||
            !files.some(
              (f) =>
                selectedFiles.includes(f.id) && f.status === 'completed'
            )
          }
          onClick={async () => {
            for (const fileId of selectedFiles) {
              const file = files.find((f) => f.id === fileId)
              if (file?.status === 'completed') {
                await downloadResult(fileId)
              }
            }
          }}
        >
          <Download className="h-4 w-4 mr-2" />
          下載結果
        </Button>
      </div>
    </div>
  )
}
