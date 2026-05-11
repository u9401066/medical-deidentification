import { useState } from 'react'
import { FileText, Download, Eye, Calendar, BarChart3, AlertTriangle } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Badge, ScrollArea, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Switch } from '@/presentation/components/ui'
import { useReports, useReportDetail, useExportReport } from '@/application/hooks'
import type { Report, ReportExportFormat } from '@/infrastructure/api'
import { formatDate, saveBlob } from '@/lib/utils'
import { toast } from 'sonner'

export function Reports() {
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const [exportFormat, setExportFormat] = useState<ReportExportFormat>('json')
  const [revealPhi, setRevealPhi] = useState(false)

  // 取得報告列表
  const { reports, isLoading: reportsLoading } = useReports()

  // 取得報告詳情
  const {
    data: reportDetail,
    isLoading: detailLoading,
    isError: detailError,
  } = useReportDetail(selectedReportId, revealPhi)

  // 匯出報告功能
  const exportMutation = useExportReport()
  const handleExportReport = async () => {
    if (!selectedReportId) return
    
    setIsExporting(true)
    try {
      const blob = await exportMutation.mutateAsync({
        taskId: selectedReportId,
        format: exportFormat,
        revealPhi,
      })
      
      // 根據格式設定檔名
      const extensions: Record<ReportExportFormat, string> = {
        json: 'json',
        csv: 'csv',
        markdown: 'md',
      }
      const filename = `report_${selectedReportId}.${extensions[exportFormat]}`
      
      saveBlob(blob, filename)
      toast.success('報告已匯出')
    } catch (error) {
      console.error('匯出報告失敗:', error)
      toast.error('匯出報告失敗，請確認報告尚未過期且您有權限存取')
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* 工具列 */}
      <div className="flex items-center gap-4 p-4 border-b">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">選擇報告:</span>
          <Select
            value={selectedReportId || ''}
            onValueChange={(value) => {
              setRevealPhi(false)
              setSelectedReportId(value)
            }}
          >
            <SelectTrigger className="w-80">
              <SelectValue placeholder="選擇報告" />
            </SelectTrigger>
            <SelectContent>
              {reports.map((report: Report) => (
                <SelectItem key={report.id} value={report.task_id}>
                  {report.filename} - {formatDate(report.created_at)}
                  {report.owner_username ? ` - owner: ${report.owner_username}` : ''}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedReportId && (
          <div className="flex items-center gap-2 ml-auto">
            <div className="flex items-center gap-2 rounded-md border px-3 py-2">
              <Switch
                checked={revealPhi}
                onCheckedChange={setRevealPhi}
                aria-label="切換 PHI 校對模式"
              />
              <div className="leading-tight">
                <p className="text-xs font-medium">校對模式</p>
                <p className="text-[11px] text-muted-foreground">匯出也會包含原始值</p>
              </div>
            </div>
            <Select value={exportFormat} onValueChange={(v) => setExportFormat(v as ReportExportFormat)}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="markdown">Markdown</SelectItem>
              </SelectContent>
            </Select>
            <Button 
              variant="outline" 
              onClick={handleExportReport}
              disabled={isExporting}
            >
              <Download className="h-4 w-4 mr-2" />
              {isExporting ? '匯出中...' : '匯出報告'}
            </Button>
          </div>
        )}
      </div>

      {/* 內容區域 */}
      <div className="flex-1 overflow-auto p-4">
        {reportsLoading ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">載入中...</p>
          </div>
        ) : !selectedReportId ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <FileText className="h-16 w-16 mb-4" />
            <p>請選擇報告以查看詳情</p>
            {reports.length === 0 && (
              <p className="text-sm mt-2">尚無任何報告</p>
            )}
          </div>
        ) : detailLoading ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">載入報告中...</p>
          </div>
        ) : detailError ? (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="font-medium text-foreground">無法載入報告</p>
              <p className="text-sm mt-2">報告可能已過期、被清理，或目前 session 無權限存取。</p>
            </CardContent>
          </Card>
        ) : reportDetail ? (
          <div className="space-y-6">
            {(reportDetail.raw_phi_notice || revealPhi) && (
              <Card className={reportDetail.raw_phi_revealed ? 'border-amber-300 bg-amber-50' : ''}>
                <CardContent className="flex gap-3 py-3 text-sm">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                  <div>
                    <p className="font-medium">
                      {reportDetail.raw_phi_revealed ? 'PHI 校對模式已啟用' : 'PHI 原始值目前隱藏'}
                    </p>
                    <p className="text-muted-foreground">
                      {reportDetail.raw_phi_notice ||
                        '若要比對正確性，請開啟校對模式；正式多人環境建議關閉。'}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 報告概要 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  報告概要
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-muted rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-primary">
                      {reportDetail.summary?.files_processed || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">處理檔案數</p>
                  </div>
                  <div className="bg-muted rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-orange-500">
                      {reportDetail.summary?.total_phi_found || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">發現 PHI</p>
                  </div>
                  <div className="bg-muted rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-green-500">
                      {reportDetail.summary?.total_chars?.toLocaleString() || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">處理字數</p>
                  </div>
                  <div className="bg-muted rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-blue-500">
                      {reportDetail.summary?.processing_time_seconds?.toFixed(1) || 0}s
                    </p>
                    <p className="text-sm text-muted-foreground">處理時間</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* PHI 類型統計 - 從 file_details 聚合 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  PHI 類型分布
                </CardTitle>
              </CardHeader>
              <CardContent>
                {(() => {
                  // 聚合所有檔案的 PHI 類型統計
                  const aggregatedTypes: Record<string, number> = {};
                  reportDetail.file_details?.forEach((file: any) => {
                    if (file.phi_by_type) {
                      Object.entries(file.phi_by_type).forEach(([type, count]) => {
                        aggregatedTypes[type] = (aggregatedTypes[type] || 0) + (count as number);
                      });
                    }
                  });
                  
                  return Object.keys(aggregatedTypes).length > 0 ? (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                      {Object.entries(aggregatedTypes).map(([type, count]) => (
                        <div
                          key={type}
                          className="flex items-center justify-between border rounded-lg p-3"
                        >
                          <span className="text-sm font-medium">{type}</span>
                          <Badge variant="secondary">{count}</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-4">
                      無 PHI 類型資料
                    </p>
                  );
                })()}
              </CardContent>
            </Card>

            {/* 詳細記錄 - 顯示 PHI 實體列表 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  PHI 詳細列表
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  {reportDetail.file_details && reportDetail.file_details.length > 0 ? (
                    <div className="space-y-4">
                      {reportDetail.file_details.map((fileDetail: any, fileIdx: number) => (
                        <div key={fileIdx} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-medium">{fileDetail.filename}</h4>
                            <Badge variant="destructive">{fileDetail.phi_found} PHI</Badge>
                          </div>
                          {fileDetail.phi_entities && fileDetail.phi_entities.length > 0 ? (
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="border-b">
                                  <th className="p-2 text-left">類型</th>
                                  <th className="p-2 text-left">原始值</th>
                                  <th className="p-2 text-left">遮罩值</th>
                                  <th className="p-2 text-left">信心度</th>
                                </tr>
                              </thead>
                              <tbody>
                                {fileDetail.phi_entities.slice(0, 50).map((item: any, idx: number) => (
                                  <tr key={idx} className="border-b hover:bg-muted/30">
                                    <td className="p-2">
                                      <Badge variant="outline">{item.type}</Badge>
                                    </td>
                                    <td className="p-2 font-mono text-xs text-red-600 line-through">
                                      {item.value && item.value !== '[REDACTED]' ? item.value : '[已隱藏]'}
                                    </td>
                                    <td className="p-2 font-mono text-xs text-green-600">
                                      {item.masked_value}
                                    </td>
                                    <td className="p-2 text-muted-foreground">
                                      {item.confidence ? `${(item.confidence * 100).toFixed(0)}%` : '-'}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          ) : (
                            <p className="text-muted-foreground text-center py-2">
                              此檔案未發現 PHI
                            </p>
                          )}
                          {fileDetail.phi_entities?.length > 50 && (
                            <p className="text-sm text-muted-foreground text-center mt-2">
                              顯示前 50 筆，共 {fileDetail.phi_entities.length} 筆
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-4">
                      無詳細記錄
                    </p>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>

            {/* 報告資訊 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  報告資訊
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">任務名稱:</span>
                    <span className="ml-2 font-medium">{reportDetail.job_name}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">產生時間:</span>
                    <span className="ml-2 font-medium">
                      {formatDate(reportDetail.generated_at || '')}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">任務 ID:</span>
                    <span className="ml-2 font-mono text-xs">{reportDetail.task_id}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">處理速度:</span>
                    <span className="ml-2 font-medium">
                      {reportDetail.summary?.processing_speed_chars_per_sec?.toFixed(1) || 0} 字/秒
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null}
      </div>
    </div>
  )
}
