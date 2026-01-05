import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  ChevronLeft, 
  FileText, 
  Eye, 
  Download,
  CheckCircle,
  AlertTriangle,
  ArrowLeftRight
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
} from '@/components/ui'
import api, { ResultItem, ResultDetail, PHIEntity } from '@/api'

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

// Diff 高亮組件
function DiffCell({ original, masked, phiType }: { original: string; masked: string; phiType?: string }) {
  if (original === masked) {
    return <span>{String(original)}</span>
  }

  const colors = phiType ? getPhiColor(phiType) : PHI_COLORS.DEFAULT

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="text-xs text-red-500 font-medium">原始:</span>
        <span className={`px-1 rounded ${colors.bg} ${colors.text} line-through`}>
          {String(original)}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-green-500 font-medium">處理:</span>
        <span className="px-1 rounded bg-green-100 text-green-800 font-mono">
          {String(masked)}
        </span>
      </div>
    </div>
  )
}

export function ResultsPanel() {
  const [selectedResult, setSelectedResult] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'list' | 'diff'>('list')

  // 取得結果列表
  const { data: results = [], isLoading } = useQuery<ResultItem[]>({
    queryKey: ['results'],
    queryFn: api.getResults,
  })

  // 取得選中結果的詳情
  const { data: resultDetail } = useQuery<ResultDetail>({
    queryKey: ['result-detail', selectedResult],
    queryFn: () => api.getResultDetail(selectedResult!),
    enabled: !!selectedResult,
  })

  // 返回列表
  const handleBack = () => {
    setSelectedResult(null)
    setViewMode('list')
  }

  // 下載結果
  const handleDownload = async (taskId: string) => {
    try {
      const blob = await api.downloadResult(taskId, 'result')
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `result_${taskId}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('下載失敗:', error)
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
              onClick={() => setSelectedResult(result.task_id)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {result.status === 'completed' ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-yellow-500" />
                    )}
                    <div>
                      <p className="font-medium">{result.filename || result.task_id}</p>
                      <p className="text-sm text-muted-foreground">
                        {new Date(result.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge variant={result.phi_count > 0 ? 'destructive' : 'secondary'}>
                      {result.phi_count} PHI
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
    if (!resultDetail) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
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
                                  {phi.value}
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
                    {fileResult.original_data && fileResult.masked_data ? (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-12">#</TableHead>
                            {Object.keys(fileResult.original_data[0] || {}).map((col) => (
                              <TableHead key={col}>{col}</TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {fileResult.original_data.slice(0, 20).map((origRow: Record<string, unknown>, rowIdx: number) => {
                            const maskedRow = fileResult.masked_data?.[rowIdx] || {}
                            return (
                              <TableRow key={rowIdx}>
                                <TableCell className="text-muted-foreground">{rowIdx + 1}</TableCell>
                                {Object.keys(origRow).map((col) => {
                                  const origVal = String(origRow[col] ?? '')
                                  const maskedVal = String(maskedRow[col] ?? '')
                                  const phi = fileResult.phi_entities?.find(
                                    (p: PHIEntity) => p.value === origVal || p.field === col
                                  )
                                  return (
                                    <TableCell key={col}>
                                      <DiffCell 
                                        original={origVal} 
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
                    ) : fileResult.original_content && fileResult.masked_content ? (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h4 className="text-sm font-medium mb-2 text-red-600">原始內容</h4>
                          <pre className="bg-red-50 p-3 rounded text-xs whitespace-pre-wrap overflow-auto max-h-64">
                            {fileResult.original_content}
                          </pre>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium mb-2 text-green-600">處理後</h4>
                          <pre className="bg-green-50 p-3 rounded text-xs whitespace-pre-wrap overflow-auto max-h-64">
                            {fileResult.masked_content}
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
