import { useState } from 'react'
import { 
  ChevronLeft, 
  FileText, 
  Eye, 
  Download,
  CheckCircle,
  ArrowLeftRight,
  AlertTriangle,
} from 'lucide-react'
import { 
  Button, 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  Badge, 
  ScrollArea,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Switch,
} from '@/presentation/components/ui'
import { useResults, useResultDetail, useDownloadResult } from '@/application/hooks'
import type { ResultItem, PHIEntity } from '@/infrastructure/api'
import { deidentifiedDownloadFilename, saveBlob } from '@/lib/utils'
import { toast } from 'sonner'

// PHI 類型顏色映射
const PHI_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  NAME: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300' },
  DATE: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300' },
  PHONE: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300' },
  EMAIL: { bg: 'bg-purple-100', text: 'text-purple-800', border: 'border-purple-300' },
  ADDRESS: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-300' },
  ID_NUMBER: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300' },
  MEDICAL_RECORD: { bg: 'bg-pink-100', text: 'text-pink-800', border: 'border-pink-300' },
  SSN: { bg: 'bg-indigo-100', text: 'text-indigo-800', border: 'border-indigo-300' },
  AGE_OVER_89: { bg: 'bg-cyan-100', text: 'text-cyan-800', border: 'border-cyan-300' },
  DEFAULT: { bg: 'bg-gray-100', text: 'text-gray-800', border: 'border-gray-300' },
}

function getPhiColor(type: string) {
  return PHI_COLORS[type] || PHI_COLORS.DEFAULT
}

function hasVisiblePhiValue(value?: string | null) {
  return Boolean(value && value !== '[REDACTED]' && value !== '[已隱藏]')
}

function PhiValueCell({ value }: { value?: string | null }) {
  if (!hasVisiblePhiValue(value)) {
    return <span className="text-muted-foreground">[已隱藏]</span>
  }

  return <span>{value}</span>
}

// Diff 高亮組件 - 加強 masked 內容的視覺效果
function DiffCell({ original, masked, phiType }: { original?: string; masked: string; phiType?: string }) {
  const colors = phiType ? getPhiColor(phiType) : PHI_COLORS.DEFAULT
  const originalValue = hasVisiblePhiValue(original) ? original : '[已隱藏]'

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="text-xs text-red-500 font-medium shrink-0">原始:</span>
        <span className={`px-1.5 py-0.5 rounded ${colors.bg} ${colors.text} line-through opacity-70`}>
          {originalValue}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-green-500 font-medium shrink-0">遮罩:</span>
        <span className="px-1.5 py-0.5 rounded bg-yellow-200 text-yellow-900 font-mono font-semibold border border-yellow-400 shadow-sm">
          {String(masked)}
        </span>
      </div>
    </div>
  )
}

// 高亮文字中的 masked 部分
function HighlightedContent({ masked, phiEntities }: { 
  original?: string; 
  masked: string; 
  phiEntities?: PHIEntity[];
}) {
  if (!phiEntities || phiEntities.length === 0) {
    return <span>{masked}</span>
  }

  // 收集所有 mask 標記
  const maskPattern = /\[([A-Z_]+)_\d+\]|\[MASKED\]|\[REDACTED\]|\*{3,}/g
  const parts: Array<{ text: string; isMasked: boolean }> = []
  let lastIndex = 0
  let match

  while ((match = maskPattern.exec(masked)) !== null) {
    // 添加前面的普通文字
    if (match.index > lastIndex) {
      parts.push({ text: masked.slice(lastIndex, match.index), isMasked: false })
    }
    // 添加 masked 部分
    parts.push({ text: match[0], isMasked: true })
    lastIndex = match.index + match[0].length
  }
  
  // 添加剩餘文字
  if (lastIndex < masked.length) {
    parts.push({ text: masked.slice(lastIndex), isMasked: false })
  }

  if (parts.length === 0) {
    return <span>{masked}</span>
  }

  return (
    <span>
      {parts.map((part, idx) => 
        part.isMasked ? (
          <mark key={idx} className="bg-yellow-300 text-yellow-900 px-1 rounded font-mono font-semibold border border-yellow-500">
            {part.text}
          </mark>
        ) : (
          <span key={idx}>{part.text}</span>
        )
      )}
    </span>
  )
}

export function ResultsPanel() {
  const [selectedResult, setSelectedResult] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'list' | 'diff'>('list')
  const [revealPhi, setRevealPhi] = useState(false)

  // 取得結果列表
  const { results, isLoading } = useResults()

  // 取得選中結果的詳情
  const {
    data: resultDetail,
    isLoading: isDetailLoading,
    isError: isDetailError,
    error: resultDetailError,
    refetch: refetchResultDetail,
  } = useResultDetail(selectedResult, revealPhi)

  const downloadResult = useDownloadResult()

  // 返回列表
  const handleBack = () => {
    setSelectedResult(null)
    setViewMode('list')
    setRevealPhi(false)
  }

  // 下載結果
  const handleDownload = async (taskId: string) => {
    try {
      const blob = await downloadResult.mutateAsync({ taskId, fileType: 'result', revealPhi })
      const filenames = resultDetail?.task_id === taskId
        ? resultDetail.results?.map((result) => result.filename)
        : undefined
      saveBlob(blob, deidentifiedDownloadFilename(taskId, filenames))
      toast.success('結果已下載')
    } catch (error) {
      console.error('下載失敗:', error)
      toast.error('下載失敗，請確認結果尚未過期且您有權限存取')
    }
  }

  // 渲染列表視圖
  const renderListView = () => (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">處理結果</h2>
        <Badge variant="secondary">{results.length} 筆結果</Badge>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : results.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>尚無處理結果</p>
            <p className="text-sm">請先上傳檔案並執行處理</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {results.map((result: ResultItem) => (
            <Card 
              key={result.task_id} 
              className="cursor-pointer hover:bg-muted/50 transition-colors"
              onClick={() => {
                setRevealPhi(false)
                setSelectedResult(result.task_id)
              }}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="font-medium">
                        {result.filenames?.length > 0 
                          ? result.filenames.join(', ') 
                          : result.job_name || result.task_id}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {result.files_count} 個檔案 • {result.processed_at ? new Date(result.processed_at).toLocaleString('zh-TW') : '未知時間'}
                        {result.owner_username ? ` • owner: ${result.owner_username}` : ''}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge variant={result.total_phi_found > 0 ? 'destructive' : 'secondary'}>
                      {result.total_phi_found} PHI
                    </Badge>
                    <Button 
                      variant="ghost" 
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDownload(result.task_id)
                      }}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )

  // 渲染詳情視圖
  const renderDetailView = () => {
    if (isDetailError) {
      const message = resultDetailError instanceof Error ? resultDetailError.message : '結果載入失敗'
      return (
        <div className="p-4 space-y-4">
          <Button variant="ghost" onClick={handleBack} className="gap-2">
            <ChevronLeft className="h-4 w-4" />
            返回列表
          </Button>
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="font-medium text-foreground">無法載入結果詳情</p>
              <p className="text-sm mt-2">{message}</p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => refetchResultDetail()}
              >
                重新嘗試
              </Button>
            </CardContent>
          </Card>
        </div>
      )
    }

    if (!resultDetail) {
      return (
        <div className="flex items-center justify-center py-12">
          {isDetailLoading ? (
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          ) : (
            <p className="text-sm text-muted-foreground">找不到結果詳情</p>
          )}
        </div>
      )
    }

    return (
      <div className="p-4 space-y-4">
        {/* 頂部操作列 */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={handleBack} className="gap-2">
            <ChevronLeft className="h-4 w-4" />
            返回列表
          </Button>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 rounded-md border px-3 py-2">
              <Switch
                checked={revealPhi}
                onCheckedChange={setRevealPhi}
                aria-label="切換 PHI 校對模式"
              />
              <div className="leading-tight">
                <p className="text-xs font-medium">校對模式</p>
                <p className="text-[11px] text-muted-foreground">顯示原始命中值</p>
              </div>
            </div>
            <Button
              variant={viewMode === 'list' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('list')}
              className="gap-2"
            >
              <Eye className="h-4 w-4" />
              PHI 列表
            </Button>
            <Button
              variant={viewMode === 'diff' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('diff')}
              className="gap-2"
            >
              <ArrowLeftRight className="h-4 w-4" />
              差異比較
            </Button>
          </div>
        </div>

        {/* 摘要卡片 */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">{resultDetail.job_name || resultDetail.task_id}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">處理時間</span>
                <p className="font-medium">{resultDetail.processed_at ? new Date(resultDetail.processed_at).toLocaleString() : '-'}</p>
              </div>
              <div>
                <span className="text-muted-foreground">檔案數</span>
                <p className="font-medium">{resultDetail.results?.length || 0}</p>
              </div>
              <div>
                <span className="text-muted-foreground">總 PHI 數</span>
                <p className="font-medium text-red-600">
                  {resultDetail.results?.reduce((acc: number, r) => acc + (r.phi_found || 0), 0) || 0}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">遮罩策略</span>
                <p className="font-medium">{resultDetail.config?.masking_type || 'default'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {(resultDetail.raw_phi_notice || revealPhi) && (
          <Card className={resultDetail.raw_phi_revealed ? 'border-amber-300 bg-amber-50' : ''}>
            <CardContent className="flex gap-3 py-3 text-sm">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
              <div>
                <p className="font-medium">
                  {resultDetail.raw_phi_revealed ? 'PHI 校對模式已啟用' : 'PHI 原始值目前隱藏'}
                </p>
                <p className="text-muted-foreground">
                  {resultDetail.raw_phi_notice ||
                    '若要比對正確性，請開啟校對模式；正式多人環境建議關閉。'}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* PHI 列表視圖 */}
        {viewMode === 'list' && (
          <ScrollArea className="h-[calc(100vh-320px)]">
            <div className="space-y-4">
              {resultDetail.results?.map((fileResult, idx: number) => (
                <Card key={fileResult.file_id || idx}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center justify-between">
                      <span>{fileResult.filename}</span>
                      <Badge variant="destructive">{fileResult.phi_found} PHI</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {fileResult.phi_entities && fileResult.phi_entities.length > 0 ? (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-24">類型</TableHead>
                            <TableHead>原始值</TableHead>
                            <TableHead>遮罩值</TableHead>
                            <TableHead className="w-20">信心度</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {fileResult.phi_entities.map((phi: PHIEntity, phiIdx: number) => {
                            const colors = getPhiColor(phi.type)
                            return (
                              <TableRow key={phiIdx}>
                                <TableCell>
                                  <Badge className={`${colors.bg} ${colors.text} border ${colors.border}`}>
                                    {phi.type}
                                  </Badge>
                                </TableCell>
                                <TableCell className="font-mono text-sm line-through text-red-600">
                                  <PhiValueCell value={phi.value} />
                                </TableCell>
                                <TableCell className="font-mono text-sm text-green-600">
                                  {phi.masked_value}
                                </TableCell>
                                <TableCell>
                                  {phi.confidence ? `${(phi.confidence * 100).toFixed(0)}%` : '-'}
                                </TableCell>
                              </TableRow>
                            )
                          })}
                        </TableBody>
                      </Table>
                    ) : (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        未偵測到 PHI
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        )}

        {/* 差異比較視圖 */}
        {viewMode === 'diff' && (
          <ScrollArea className="h-[calc(100vh-320px)]">
            <div className="space-y-4">
              {resultDetail.results?.map((fileResult, idx: number) => (
                <Card key={fileResult.file_id || idx}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">{fileResult.filename}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {fileResult.masked_data ? (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-12">#</TableHead>
                            {Object.keys(fileResult.masked_data[0] || {}).map((col) => (
                              <TableHead key={col}>{col}</TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {fileResult.masked_data.slice(0, 20).map((maskedRow: Record<string, unknown>, rowIdx: number) => {
                            return (
                              <TableRow key={rowIdx}>
                                <TableCell className="text-muted-foreground">{rowIdx + 1}</TableCell>
                                {Object.keys(maskedRow).map((col) => {
                                  const maskedVal = String(maskedRow[col] ?? '')
                                  const originalRow = fileResult.original_data?.[rowIdx]
                                  const originalVal = originalRow ? String(originalRow[col] ?? '') : undefined
                                  const phi = fileResult.phi_entities?.find(
                                    (p: PHIEntity) => p.field === col
                                  )
                                  return (
                                    <TableCell key={col}>
                                      <DiffCell 
                                        original={originalVal}
                                        masked={maskedVal} 
                                        phiType={phi?.type}
                                      />
                                    </TableCell>
                                  )
                                })}
                              </TableRow>
                            )
                          })}
                        </TableBody>
                      </Table>
                    ) : fileResult.masked_content ? (
                      <div className="grid gap-4">
                        {fileResult.original_content && (
                          <div>
                            <h4 className="text-sm font-medium mb-2 text-red-600">原始內容 <span className="text-muted-foreground">(校對模式)</span></h4>
                            <pre className="bg-red-50 p-3 rounded text-xs whitespace-pre-wrap overflow-auto max-h-64 border border-red-200">
                              {fileResult.original_content}
                            </pre>
                          </div>
                        )}
                        <div>
                          <h4 className="text-sm font-medium mb-2 text-green-600">🔒 遮罩後 <span className="text-yellow-600">(黃色標記 = PHI)</span></h4>
                          <pre className="bg-green-50 p-3 rounded text-xs whitespace-pre-wrap overflow-auto max-h-64 border border-green-200">
                            <HighlightedContent 
                              masked={fileResult.masked_content}
                              phiEntities={fileResult.phi_entities}
                            />
                          </pre>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        無差異資料可顯示
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        )}
      </div>
    )
  }

  return (
    <div className="h-full">
      {selectedResult ? renderDetailView() : renderListView()}
    </div>
  )
}
