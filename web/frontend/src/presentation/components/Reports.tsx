import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FileText, Download, Eye, Calendar, BarChart3 } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Badge, ScrollArea, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/presentation/components/ui'
import api, { Report } from '@/infrastructure/api'
import { formatDate } from '@/lib/utils'

export function Reports() {
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null)

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
          <Button variant="outline" className="ml-auto">
            <Download className="h-4 w-4 mr-2" />
            匯出報告
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
                      {reportDetail.summary?.total_records || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">總記錄數</p>
                  </div>
                  <div className="bg-muted rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-orange-500">
                      {reportDetail.summary?.phi_found || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">發現 PHI</p>
                  </div>
                  <div className="bg-muted rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-green-500">
                      {reportDetail.summary?.phi_masked || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">已遮蔽</p>
                  </div>
                  <div className="bg-muted rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-blue-500">
                      {reportDetail.summary?.processing_time?.toFixed(2) || 0}s
                    </p>
                    <p className="text-sm text-muted-foreground">處理時間</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* PHI 類型統計 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  PHI 類型分布
                </CardTitle>
              </CardHeader>
              <CardContent>
                {reportDetail.phi_types && Object.keys(reportDetail.phi_types).length > 0 ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {Object.entries(reportDetail.phi_types).map(([type, count]) => (
                      <div
                        key={type}
                        className="flex items-center justify-between border rounded-lg p-3"
                      >
                        <span className="text-sm font-medium">{type}</span>
                        <Badge variant="secondary">{count as number}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-4">
                    無 PHI 類型資料
                  </p>
                )}
              </CardContent>
            </Card>

            {/* 詳細記錄 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  處理詳情
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[300px]">
                  {reportDetail.details && reportDetail.details.length > 0 ? (
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="p-2 text-left">欄位</th>
                          <th className="p-2 text-left">原始值</th>
                          <th className="p-2 text-left">遮蔽值</th>
                          <th className="p-2 text-left">類型</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reportDetail.details.map((item: any, idx: number) => (
                          <tr key={idx} className="border-b hover:bg-muted/30">
                            <td className="p-2">{item.field}</td>
                            <td className="p-2 font-mono text-xs text-red-600">
                              {item.original}
                            </td>
                            <td className="p-2 font-mono text-xs text-green-600">
                              {item.masked}
                            </td>
                            <td className="p-2">
                              <Badge variant="outline">{item.phi_type}</Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
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
                    <span className="text-muted-foreground">檔案名稱:</span>
                    <span className="ml-2 font-medium">{reportDetail.filename}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">建立時間:</span>
                    <span className="ml-2 font-medium">
                      {formatDate(reportDetail.created_at)}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">報告 ID:</span>
                    <span className="ml-2 font-mono text-xs">{reportDetail.id}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">來源檔案:</span>
                    <span className="ml-2 font-mono text-xs">
                      {reportDetail.source_file_id}
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
