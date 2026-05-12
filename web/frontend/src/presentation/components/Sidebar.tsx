import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, Trash2, Download, FileSpreadsheet, FileJson, Cpu, CheckCircle, XCircle, RefreshCw, Shield, Settings2, AlertTriangle } from 'lucide-react'
import { Button, ScrollArea, Badge } from '@/presentation/components/ui'
import { useFiles, useUploadFile, useDeleteFile, useHealth } from '@/application/hooks'
import { TASKS_QUERY_KEY } from '@/application/hooks'
import { deidentifiedFilename, formatBytes, formatDate, saveBlob } from '@/lib/utils'
import api, { startProcessing, downloadSingleFileResult } from '@/infrastructure/api'
import { toast } from 'sonner'

interface SidebarProps {
  onFileSelect?: (fileId: string) => void
  onOpenSettings?: () => void
  selectedFileId?: string | null
}

export function Sidebar({ onFileSelect, onOpenSettings, selectedFileId }: SidebarProps) {
  const queryClient = useQueryClient()
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [showProcessConfirm, setShowProcessConfirm] = useState(false)

  const errorMessage = (error: unknown) => {
    const apiError = error as { response?: { data?: { detail?: string } }; message?: string }
    return apiError.response?.data?.detail || apiError.message || '未知錯誤'
  }

  // 取得系統健康狀態（含 LLM）
  const { health } = useHealth({ refetchInterval: 10000 })

  // 取得已上傳檔案列表 - 處理中時每 2 秒刷新
  const { files, isLoading } = useFiles()

  const { data: phiTypes = [] } = useQuery({
    queryKey: ['phi-types'],
    queryFn: api.getPHITypes,
  })

  const { data: phiConfig } = useQuery({
    queryKey: ['config'],
    queryFn: api.getConfig,
  })

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

  const maskingTypeLabel = (type?: string) => {
    switch (type) {
      case 'hash':
        return '雜湊'
      case 'replace':
        return '替換'
      case 'delete':
        return '刪除'
      case 'keep':
        return '保留'
      case 'mask':
      default:
        return '遮蔽'
    }
  }

  const selectedFileDetails = selectedFiles
    .map((fileId) => files.find((file) => file.id === fileId))
    .filter((file): file is NonNullable<typeof file> => Boolean(file))

  const enabledPhiTypeLabels = phiTypes
    .filter((phiType) => phiConfig?.phi_types?.[phiType.type]?.enabled ?? true)
    .map((phiType) => phiType.display_name || phiType.type)

  const phiDetectionEnabled = phiConfig?.enabled ?? true
  const llmOnline = health?.llm?.status === 'online'

  const handleConfirmStartProcessing = async () => {
    if (selectedFiles.length === 0) return

    const fileIdsToProcess = [...selectedFiles]
    setIsProcessing(true)
    setShowProcessConfirm(false)
    try {
      await startProcessing({ file_ids: fileIdsToProcess })
      // 立即刷新任務和檔案列表
      await queryClient.invalidateQueries({ queryKey: TASKS_QUERY_KEY })
      await queryClient.invalidateQueries({ queryKey: ['files'] })
      setSelectedFiles([])
      toast.success(`已建立 ${fileIdsToProcess.length} 個檔案的去識別化任務`)
      // 延遲一點再關閉 isProcessing，讓 UI 能看到狀態更新
      setTimeout(() => setIsProcessing(false), 1000)
    } catch (err) {
      console.error('處理失敗:', err)
      toast.error(`開始處理失敗：${errorMessage(err)}`)
      setIsProcessing(false)
    }
  }

  return (
    <>
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
                      {file.ownerUsername ? ` • owner: ${file.ownerUsername}` : ''}
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
          disabled={selectedFiles.length === 0 || isProcessing}
          onClick={() => setShowProcessConfirm(true)}
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
                const taskId = file.taskId
                if (!taskId) {
                  toast.error(`${file.filename} 找不到任務 ID，無法下載`)
                  continue
                }
                try {
                  const blob = await downloadSingleFileResult(taskId, fileId)
                  saveBlob(blob, deidentifiedFilename(file.filename, fileId))
                } catch {
                  toast.error(`${file.filename} 下載失敗`)
                }
              }
            }
          }}
        >
          <Download className="h-4 w-4 mr-2" />
          下載結果
        </Button>
      </div>
    </div>

    {showProcessConfirm && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="process-confirm-title"
          className="w-full max-w-xl rounded-xl border bg-background shadow-2xl"
        >
          <div className="border-b p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 id="process-confirm-title" className="text-lg font-semibold">
                  開始前確認 PHI 設定
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  請確認檔案與目前設定符合預期後，再送出去識別化任務。
                </p>
              </div>
              <Shield className="h-6 w-6 text-primary" />
            </div>
          </div>

          <div className="space-y-4 p-5">
            <div className="rounded-lg border p-3">
              <p className="text-sm font-medium">
                即將處理 {selectedFileDetails.length || selectedFiles.length} 個檔案
              </p>
              <div className="mt-2 max-h-28 space-y-1 overflow-auto text-sm text-muted-foreground">
                {selectedFileDetails.length > 0 ? (
                  selectedFileDetails.map((file) => (
                    <div key={file.id} className="flex items-center gap-2">
                      {getIcon(file.filename)}
                      <span className="truncate">{file.filename}</span>
                    </div>
                  ))
                ) : (
                  <p>已選取的檔案仍在載入中。</p>
                )}
              </div>
            </div>

            <div className="rounded-lg border p-3">
              <div className="mb-2 flex items-center gap-2">
                <Settings2 className="h-4 w-4" />
                <p className="text-sm font-medium">目前 PHI 設定摘要</p>
              </div>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <div>
                  <span className="text-muted-foreground">PHI 偵測：</span>
                  <span className={phiDetectionEnabled ? 'text-green-600' : 'text-red-600'}>
                    {phiDetectionEnabled ? '啟用' : '停用'}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">嚴格模式：</span>
                  <span>{phiConfig?.strict_mode ? '啟用' : '停用'}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">預設遮蔽：</span>
                  <span>{maskingTypeLabel(phiConfig?.default_masking || phiConfig?.masking_type)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">格式保留：</span>
                  <span>{phiConfig?.preserve_format === false ? '停用' : '啟用'}</span>
                </div>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                啟用類型：{enabledPhiTypeLabels.length > 0
                  ? `${enabledPhiTypeLabels.slice(0, 6).join('、')}${enabledPhiTypeLabels.length > 6 ? ` 等 ${enabledPhiTypeLabels.length} 類` : ''}`
                  : '尚未取得設定'}
              </p>
            </div>

            <div
              className={`rounded-lg border p-3 text-sm ${
                llmOnline
                  ? 'border-green-200 bg-green-50 text-green-900 dark:border-green-900 dark:bg-green-950 dark:text-green-100'
                  : 'border-yellow-200 bg-yellow-50 text-yellow-900 dark:border-yellow-900 dark:bg-yellow-950 dark:text-yellow-100'
              }`}
            >
              <div className="flex items-start gap-2">
                {llmOnline ? (
                  <CheckCircle className="mt-0.5 h-4 w-4" />
                ) : (
                  <AlertTriangle className="mt-0.5 h-4 w-4" />
                )}
                <div>
                  <p className="font-medium">
                    LLM 狀態：{llmOnline ? `在線 (${health?.llm?.model || 'ollama'})` : '離線或尚未確認'}
                  </p>
                  {!llmOnline && (
                    <p className="mt-1">
                      正式處理建議先排除 LLM 連線問題；若繼續，後端可能改用 fallback，結果不適合作為正式交付。
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="flex flex-col-reverse gap-2 border-t p-5 sm:flex-row sm:justify-end">
            <Button
              variant="ghost"
              onClick={() => setShowProcessConfirm(false)}
            >
              取消
            </Button>
            {onOpenSettings && (
              <Button
                variant="outline"
                onClick={() => {
                  setShowProcessConfirm(false)
                  onOpenSettings()
                }}
              >
                返回 PHI 設定
              </Button>
            )}
            <Button
              onClick={handleConfirmStartProcessing}
              disabled={isProcessing || selectedFiles.length === 0}
            >
              確認開始
            </Button>
          </div>
        </div>
      </div>
    )}
    </>
  )
}
