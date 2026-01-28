import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FileText, Download, Eye, Calendar, BarChart3 } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Badge, ScrollArea, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/presentation/components/ui'
import api, { Report } from '@/infrastructure/api'
import { formatDate } from '@/lib/utils'
import { toast } from 'sonner'

export function Reports() {
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)

  // 取得報告列表
  const { data: reports = [], isLoading: reportsLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: api.listReports,
  })

  // 取得報告詳情
  const { data: reportDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['report', selectedReportId],
    queryFn: () =>
      selectedReportId ? api.getReport(selectedReportId) : Promise.resolve(null),
    enabled: !!selectedReportId,
  })

  // 匯出報告
  const handleExportReport = async () => {
    if (!selectedReportId || !reportDetail) return
    setIsExporting(true)
    try {
      // 建立 JSON 格式的報告資料
      const exportData = {
        task_id: reportDetail.task_id,
        job_name: reportDetail.job_name,
        generated_at: reportDetail.generated_at,
        summary: reportDetail.summary,
        file_details: reportDetail.file_details,
      }
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report_${reportDetail.task_id || 'export'}.json`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('報告匯出成功')
    } catch (error) {
      console.error('匯出失敗:', error)
      toast.error('報告匯出失敗')
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
            onValueChange={setSelectedReportId}
          >
            <SelectTrigger className="w-80">
              <SelectValue placeholder="選擇報告" />
            </SelectTrigger>
            <SelectContent>
              {reports.map((report: Report) => (
                <SelectItem key={report.id} value={report.id}>
                  {report.filename} - {formatDate(report.created_at)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedReportId && (
          <Button
            variant="outline"
            className="ml-auto"
            disabled={isExporting || !reportDetail}
            onClick={handleExportReport}
          >
            <Download className="h-4 w-4 mr-2" />
            {isExporting ? '匯出中...' : '匯出報告'}
          </Button>
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
        ) : reportDetail ? (
          <div className="space-y-6">
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
                                    <td className="p-2 font-mono text-xs text-red-600">
                                      {item.value}
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
