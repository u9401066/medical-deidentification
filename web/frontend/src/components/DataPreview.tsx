import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, FileText } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Badge } from '@/components/ui'
import api, { UploadedFile } from '@/api'

export function DataPreview() {
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const pageSize = 50

  // 取得檔案列表
  const { data: files = [] } = useQuery({
    queryKey: ['files'],
    queryFn: api.listFiles,
  })

  // 取得預覽資料
  const { data: preview, isLoading: previewLoading } = useQuery({
    queryKey: ['preview', selectedFileId, page, pageSize],
    queryFn: () =>
      selectedFileId
        ? api.previewFile(selectedFileId, page, pageSize)
        : Promise.resolve(null),
    enabled: !!selectedFileId,
  })

  // 當檔案列表變化時，自動選擇第一個檔案
  useEffect(() => {
    if (files.length > 0 && !selectedFileId) {
      setSelectedFileId(files[0].id)
    }
  }, [files, selectedFileId])

  const totalPages = preview ? Math.ceil(preview.total_rows / pageSize) : 0

  return (
    <div className="flex flex-col h-full">
      {/* 工具列 */}
      <div className="flex items-center gap-4 p-4 border-b">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">選擇檔案:</span>
          <Select
            value={selectedFileId || ''}
            onValueChange={(value: string) => {
              setSelectedFileId(value)
              setPage(1)
            }}
          >
            <SelectTrigger className="w-64">
              <SelectValue placeholder="選擇檔案" />
            </SelectTrigger>
            <SelectContent>
              {files.map((file: UploadedFile) => (
                <SelectItem key={file.id} value={file.id}>
                  {file.filename}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {preview && (
          <div className="flex items-center gap-2 ml-auto">
            <Badge variant="outline">
              {preview.total_rows} 筆資料
            </Badge>
            {preview.columns && (
              <Badge variant="secondary">
                {preview.columns.length} 欄位
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* 內容區域 */}
      <div className="flex-1 overflow-auto p-4">
        {!selectedFileId ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <FileText className="h-16 w-16 mb-4" />
            <p>請選擇檔案以預覽內容</p>
          </div>
        ) : previewLoading ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">載入中...</p>
          </div>
        ) : preview ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                {files.find((f: UploadedFile) => f.id === selectedFileId)?.filename}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {preview.type === 'tabular' && preview.columns && preview.data ? (
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="p-2 text-left font-medium w-12">#</th>
                        {preview.columns.map((col, idx) => (
                          <th
                            key={idx}
                            className="p-2 text-left font-medium min-w-[120px]"
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {preview.data.map((row, rowIdx) => (
                        <tr
                          key={rowIdx}
                          className="border-b hover:bg-muted/30 transition-colors"
                        >
                          <td className="p-2 text-muted-foreground">
                            {(page - 1) * pageSize + rowIdx + 1}
                          </td>
                          {preview.columns!.map((col, colIdx) => (
                            <td key={colIdx} className="p-2 max-w-xs truncate">
                              {String(row[col] ?? '')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : preview.type === 'text' ? (
                <pre className="whitespace-pre-wrap font-mono text-sm bg-muted p-4 rounded-lg overflow-auto max-h-[600px]">
                  {preview.content}
                </pre>
              ) : preview.type === 'json' ? (
                <pre className="whitespace-pre-wrap font-mono text-sm bg-muted p-4 rounded-lg overflow-auto max-h-[600px]">
                  {JSON.stringify(preview.data, null, 2)}
                </pre>
              ) : (
                <p className="text-muted-foreground">不支援的檔案類型</p>
              )}
            </CardContent>
          </Card>
        ) : null}
      </div>

      {/* 分頁控制 */}
      {preview && totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 p-4 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            <ChevronLeft className="h-4 w-4" />
            上一頁
          </Button>
          <span className="text-sm">
            第 {page} / {totalPages} 頁
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            下一頁
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
