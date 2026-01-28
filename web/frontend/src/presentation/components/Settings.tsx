import { useState, useRef, useEffect, ChangeEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings2, Upload, Shield, FileText, Save, Plus, ChevronUp, Eye, Trash2, RotateCcw, HardDrive, AlertTriangle } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Badge, ScrollArea, Switch, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/presentation/components/ui'
import api, { PHIType, MaskingType, PHIConfig, RegulationRule } from '@/infrastructure/api'
import { toast } from 'sonner'

export function SettingsPanel() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'phi' | 'regulations' | 'maintenance'>('phi')

  // 取得 PHI 類型
  const { data: phiTypes = [] } = useQuery({
    queryKey: ['phi-types'],
    queryFn: api.getPHITypes,
  })

  // 取得設定
  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: api.getConfig,
  })

  // 取得法規列表
  const { data: regulations = [] } = useQuery({
    queryKey: ['regulations'],
    queryFn: api.listRegulations,
  })

  // 更新設定 mutation
  const updateConfigMutation = useMutation({
    mutationFn: api.updateConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
      toast.success('設定已儲存')
    },
    onError: () => {
      toast.error('儲存設定失敗')
    },
  })

  // 上傳法規 mutation
  const uploadRegulationMutation = useMutation({
    mutationFn: (file: File) => api.uploadRegulation(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['regulations'] })
      toast.success('法規上傳成功')
    },
    onError: () => {
      toast.error('法規上傳失敗')
    },
  })

  // 更新法規啟用狀態 mutation
  const updateRegulationMutation = useMutation({
    mutationFn: ({ ruleId, enabled }: { ruleId: string; enabled: boolean }) =>
      api.updateRegulation(ruleId, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['regulations'] })
      toast.success('法規設定已更新')
    },
    onError: () => {
      toast.error('更新法規設定失敗')
    },
  })

  return (
    <div className="flex flex-col h-full">
      {/* 標籤切換 */}
      <div className="flex border-b">
        <button
          className={`px-6 py-3 text-sm font-medium transition-colors ${
            activeTab === 'phi'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('phi')}
        >
          <Shield className="h-4 w-4 inline mr-2" />
          PHI 設定
        </button>
        <button
          className={`px-6 py-3 text-sm font-medium transition-colors ${
            activeTab === 'regulations'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('regulations')}
        >
          <FileText className="h-4 w-4 inline mr-2" />
          法規管理
        </button>
        <button
          className={`px-6 py-3 text-sm font-medium transition-colors ${
            activeTab === 'maintenance'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => setActiveTab('maintenance')}
        >
          <HardDrive className="h-4 w-4 inline mr-2" />
          系統維護
        </button>
      </div>

      {/* 內容區域 */}
      <div className="flex-1 overflow-auto p-4">
        {activeTab === 'phi' ? (
          <PHISettings
            phiTypes={phiTypes}
            config={config}
            onUpdateConfig={(updates) => updateConfigMutation.mutate(updates)}
            isUpdating={updateConfigMutation.isPending}
          />
        ) : activeTab === 'regulations' ? (
          <RegulationsSettings
            regulations={regulations}
            onUpload={(file) => uploadRegulationMutation.mutate(file)}
            isUploading={uploadRegulationMutation.isPending}
            onToggleEnabled={(ruleId, enabled) =>
              updateRegulationMutation.mutate({ ruleId, enabled })
            }
            isUpdatingRegulation={updateRegulationMutation.isPending}
          />
        ) : (
          <MaintenanceSettings queryClient={queryClient} />
        )}
      </div>
    </div>
  )
}

// PHI 設定子元件
function PHISettings({
  phiTypes,
  config,
  onUpdateConfig,
  isUpdating,
}: {
  phiTypes: PHIType[]
  config?: PHIConfig
  onUpdateConfig: (updates: Partial<PHIConfig>) => void
  isUpdating: boolean
}) {
  const [localConfig, setLocalConfig] = useState<Partial<PHIConfig>>(config || {})

  useEffect(() => {
    if (config) {
      setLocalConfig(config)
    }
  }, [config])

  const handleSave = () => {
    onUpdateConfig(localConfig)
  }

  const maskingTypes: MaskingType[] = ['mask', 'hash', 'replace', 'delete', 'keep']

  return (
    <div className="space-y-6">
      {/* 全域設定 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings2 className="h-5 w-5" />
            全域設定
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">啟用 PHI 偵測</p>
              <p className="text-sm text-muted-foreground">
                自動偵測並標記敏感資料
              </p>
            </div>
            <Switch
              checked={localConfig.enabled ?? true}
              onCheckedChange={(checked: boolean) =>
                setLocalConfig((prev) => ({ ...prev, enabled: checked }))
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">嚴格模式</p>
              <p className="text-sm text-muted-foreground">
                使用更嚴格的偵測規則
              </p>
            </div>
            <Switch
              checked={localConfig.strict_mode ?? false}
              onCheckedChange={(checked: boolean) =>
                setLocalConfig((prev) => ({ ...prev, strict_mode: checked }))
              }
            />
          </div>

          <div className="space-y-2">
            <p className="font-medium">預設遮蔽方式</p>
            <Select
              value={localConfig.default_masking || 'mask'}
              onValueChange={(value: MaskingType) =>
                setLocalConfig((prev) => ({ ...prev, default_masking: value }))
              }
            >
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {maskingTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type === 'mask'
                      ? '遮蔽 (***)'
                      : type === 'hash'
                      ? '雜湊'
                      : type === 'replace'
                      ? '替換'
                      : type === 'delete'
                      ? '刪除'
                      : '保留'}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button onClick={handleSave} disabled={isUpdating}>
            <Save className="h-4 w-4 mr-2" />
            儲存設定
          </Button>
        </CardContent>
      </Card>

      {/* PHI 類型設定 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            PHI 類型設定
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            <div className="space-y-3">
              {phiTypes.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">
                  載入中...
                </p>
              ) : (
                phiTypes.map((phiType: PHIType) => (
                  <div
                    key={phiType.type}
                    className="flex items-center justify-between border rounded-lg p-3"
                  >
                    <div className="flex items-center gap-3">
                      <Switch
                        checked={
                          localConfig.phi_types?.[phiType.type]?.enabled ?? true
                        }
                        onCheckedChange={(checked: boolean) =>
                          setLocalConfig((prev) => ({
                            ...prev,
                            phi_types: {
                              ...prev.phi_types,
                              [phiType.type]: {
                                ...prev.phi_types?.[phiType.type],
                                enabled: checked,
                              },
                            },
                          }))
                        }
                      />
                      <div>
                        <p className="font-medium">{phiType.display_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {phiType.description}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Select
                        value={
                          localConfig.phi_types?.[phiType.type]?.masking ||
                          phiType.default_masking ||
                          'mask'
                        }
                        onValueChange={(value: MaskingType) =>
                          setLocalConfig((prev) => ({
                            ...prev,
                            phi_types: {
                              ...prev.phi_types,
                              [phiType.type]: {
                                ...prev.phi_types?.[phiType.type],
                                masking: value,
                              },
                            },
                          }))
                        }
                      >
                        <SelectTrigger className="w-28">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {maskingTypes.map((type) => (
                            <SelectItem key={type} value={type}>
                              {type === 'mask'
                                ? '遮蔽'
                                : type === 'hash'
                                ? '雜湊'
                                : type === 'replace'
                                ? '替換'
                                : type === 'delete'
                                ? '刪除'
                                : '保留'}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {/* 替換詞輸入框 - 只在選擇「替換」時顯示 */}
                      {(localConfig.phi_types?.[phiType.type]?.masking ||
                        phiType.default_masking) === 'replace' && (
                        <input
                          type="text"
                          placeholder="輸入替換詞"
                          className="w-28 px-2 py-1 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                          value={
                            localConfig.phi_types?.[phiType.type]?.replace_with || ''
                          }
                          onChange={(e) =>
                            setLocalConfig((prev) => ({
                              ...prev,
                              phi_types: {
                                ...prev.phi_types,
                                [phiType.type]: {
                                  ...prev.phi_types?.[phiType.type],
                                  replace_with: e.target.value,
                                },
                              },
                            }))
                          }
                        />
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

// 法規管理子元件
function RegulationsSettings({
  regulations,
  onUpload,
  isUploading,
  onToggleEnabled,
  isUpdatingRegulation,
}: {
  regulations: RegulationRule[]
  onUpload: (file: File) => void
  isUploading: boolean
  onToggleEnabled: (ruleId: string, enabled: boolean) => void
  isUpdatingRegulation: boolean
}) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [expandedRule, setExpandedRule] = useState<string | null>(null)
  const [ruleContent, setRuleContent] = useState<string | null>(null)
  const [loadingContent, setLoadingContent] = useState(false)

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onUpload(file)
      e.target.value = ''
    }
  }

  const handleToggleContent = async (ruleId: string) => {
    if (expandedRule === ruleId) {
      // 收起
      setExpandedRule(null)
      setRuleContent(null)
    } else {
      // 展開並載入內容
      setExpandedRule(ruleId)
      setLoadingContent(true)
      try {
        const content = await api.getRegulationContent(ruleId)
        setRuleContent(content.content)
      } catch (err) {
        setRuleContent('無法載入法規內容')
      } finally {
        setLoadingContent(false)
      }
    }
  }

  return (
    <div className="space-y-6">
      {/* 上傳法規 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            上傳法規文件
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".md,.txt,.pdf"
              onChange={handleFileChange}
              className="hidden"
            />
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              <Plus className="h-4 w-4 mr-2" />
              選擇檔案
            </Button>
            <p className="text-sm text-muted-foreground">
              支援 Markdown, TXT, PDF 格式
            </p>
          </div>
          {isUploading && (
            <p className="text-sm text-muted-foreground mt-2">上傳中...</p>
          )}
        </CardContent>
      </Card>

      {/* 法規列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            已載入法規 ({regulations.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            {regulations.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>尚未載入任何法規</p>
                <p className="text-xs mt-1">上傳法規文件以開始</p>
              </div>
            ) : (
              <div className="space-y-3">
                {regulations.map((reg: RegulationRule) => (
                  <div
                    key={reg.id}
                    className="border rounded-lg p-4 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">{reg.name}</h4>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleContent(reg.id)}
                          className="h-7 px-2"
                        >
                          {expandedRule === reg.id ? (
                            <><ChevronUp className="h-4 w-4 mr-1" />收起</>
                          ) : (
                            <><Eye className="h-4 w-4 mr-1" />查看內容</>
                          )}
                        </Button>
                        <Badge
                          variant={reg.enabled ? 'default' : 'secondary'}
                        >
                          {reg.enabled ? '啟用' : '停用'}
                        </Badge>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {reg.description}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>來源: {reg.source}</span>
                      <span>•</span>
                      <span>{reg.rules_count} 條規則</span>
                    </div>
                    
                    {/* 展開的法規內容 */}
                    {expandedRule === reg.id && (
                      <div className="mt-3 p-3 bg-muted/50 rounded-lg border">
                        {loadingContent ? (
                          <div className="flex items-center justify-center py-4">
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                            <span className="ml-2 text-sm text-muted-foreground">載入中...</span>
                          </div>
                        ) : (
                          <div className="prose prose-sm dark:prose-invert max-w-none">
                            <pre className="whitespace-pre-wrap text-xs font-mono bg-background p-3 rounded overflow-auto max-h-64">
                              {ruleContent || '無內容'}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                    
                    <div className="flex items-center gap-2 mt-2">
                      <Switch
                        checked={reg.enabled}
                        disabled={isUpdatingRegulation}
                        onCheckedChange={(checked) => {
                          onToggleEnabled(reg.id, checked)
                        }}
                      />
                      <span className="text-sm">
                        {reg.enabled ? '啟用中' : '已停用'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

// 格式化檔案大小
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 系統維護子元件
function MaintenanceSettings({
  queryClient,
}: {
  queryClient: ReturnType<typeof useQueryClient>
}) {
  const [confirmAction, setConfirmAction] = useState<string | null>(null)

  // 取得清理統計
  const { data: stats, refetch: refetchStats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['cleanup-stats'],
    queryFn: api.getCleanupStats,
    refetchInterval: false,
  })

  // 清除上傳檔案
  const cleanupUploadsMutation = useMutation({
    mutationFn: api.cleanupUploads,
    onSuccess: (data) => {
      toast.success(`已清除 ${data.files_deleted} 個上傳檔案 (${formatBytes(data.bytes_freed)})`)
      refetchStats()
      queryClient.invalidateQueries({ queryKey: ['files'] })
    },
    onError: () => toast.error('清除上傳檔案失敗'),
  })

  // 清除結果檔案
  const cleanupResultsMutation = useMutation({
    mutationFn: api.cleanupResults,
    onSuccess: (data) => {
      toast.success(`已清除 ${data.files_deleted} 個結果檔案 (${formatBytes(data.bytes_freed)})`)
      refetchStats()
      queryClient.invalidateQueries({ queryKey: ['results'] })
    },
    onError: () => toast.error('清除結果檔案失敗'),
  })

  // 清除報告檔案
  const cleanupReportsMutation = useMutation({
    mutationFn: api.cleanupReports,
    onSuccess: (data) => {
      toast.success(`已清除 ${data.files_deleted} 個報告檔案 (${formatBytes(data.bytes_freed)})`)
      refetchStats()
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: () => toast.error('清除報告檔案失敗'),
  })

  // 清除全部
  const cleanupAllMutation = useMutation({
    mutationFn: api.cleanupAll,
    onSuccess: (data) => {
      toast.success(`已清除所有資料 (${formatBytes(data.total_bytes_freed)})，${data.tasks_cleared} 個任務`)
      refetchStats()
      queryClient.invalidateQueries()
    },
    onError: () => toast.error('清除全部資料失敗'),
  })

  // 重置設定
  const resetConfigMutation = useMutation({
    mutationFn: api.resetConfig,
    onSuccess: () => {
      toast.success('設定已重置為預設值')
      queryClient.invalidateQueries({ queryKey: ['config'] })
    },
    onError: () => toast.error('重置設定失敗'),
  })

  const handleAction = (action: string) => {
    if (confirmAction === action) {
      // 第二次點擊，執行操作
      switch (action) {
        case 'uploads':
          cleanupUploadsMutation.mutate()
          break
        case 'results':
          cleanupResultsMutation.mutate()
          break
        case 'reports':
          cleanupReportsMutation.mutate()
          break
        case 'all':
          cleanupAllMutation.mutate()
          break
        case 'reset':
          resetConfigMutation.mutate()
          break
      }
      setConfirmAction(null)
    } else {
      // 第一次點擊，顯示確認
      setConfirmAction(action)
      // 3 秒後自動取消確認狀態
      setTimeout(() => setConfirmAction(null), 3000)
    }
  }

  const isAnyPending = cleanupUploadsMutation.isPending || 
                       cleanupResultsMutation.isPending || 
                       cleanupReportsMutation.isPending || 
                       cleanupAllMutation.isPending ||
                       resetConfigMutation.isPending

  return (
    <div className="space-y-6">
      {/* 儲存空間統計 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="h-5 w-5" />
            儲存空間統計
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoadingStats ? (
            <div className="flex items-center justify-center py-4">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
              <span className="ml-2 text-sm text-muted-foreground">載入中...</span>
            </div>
          ) : stats ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="border rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-primary">{stats.uploads.files_count}</div>
                <div className="text-sm text-muted-foreground">上傳檔案</div>
                <div className="text-xs text-muted-foreground">{formatBytes(stats.uploads.total_size)}</div>
              </div>
              <div className="border rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-primary">{stats.results.files_count}</div>
                <div className="text-sm text-muted-foreground">結果檔案</div>
                <div className="text-xs text-muted-foreground">{formatBytes(stats.results.total_size)}</div>
              </div>
              <div className="border rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-primary">{stats.reports.files_count}</div>
                <div className="text-sm text-muted-foreground">報告檔案</div>
                <div className="text-xs text-muted-foreground">{formatBytes(stats.reports.total_size)}</div>
              </div>
              <div className="border rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-primary">{stats.tasks.count}</div>
                <div className="text-sm text-muted-foreground">處理任務</div>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-4">無法載入統計資料</p>
          )}
          <div className="mt-4 flex justify-end">
            <Button variant="outline" size="sm" onClick={() => refetchStats()} disabled={isLoadingStats}>
              <RotateCcw className="h-4 w-4 mr-2" />
              重新整理
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 清除資料 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trash2 className="h-5 w-5" />
            清除資料
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between border rounded-lg p-4">
            <div>
              <p className="font-medium">清除上傳檔案</p>
              <p className="text-sm text-muted-foreground">刪除所有已上傳的原始檔案</p>
            </div>
            <Button
              variant={confirmAction === 'uploads' ? 'destructive' : 'outline'}
              onClick={() => handleAction('uploads')}
              disabled={isAnyPending}
            >
              {confirmAction === 'uploads' ? (
                <><AlertTriangle className="h-4 w-4 mr-2" />確認刪除</>
              ) : (
                <><Trash2 className="h-4 w-4 mr-2" />清除</>
              )}
            </Button>
          </div>

          <div className="flex items-center justify-between border rounded-lg p-4">
            <div>
              <p className="font-medium">清除結果檔案</p>
              <p className="text-sm text-muted-foreground">刪除所有處理後的結果檔案</p>
            </div>
            <Button
              variant={confirmAction === 'results' ? 'destructive' : 'outline'}
              onClick={() => handleAction('results')}
              disabled={isAnyPending}
            >
              {confirmAction === 'results' ? (
                <><AlertTriangle className="h-4 w-4 mr-2" />確認刪除</>
              ) : (
                <><Trash2 className="h-4 w-4 mr-2" />清除</>
              )}
            </Button>
          </div>

          <div className="flex items-center justify-between border rounded-lg p-4">
            <div>
              <p className="font-medium">清除報告檔案</p>
              <p className="text-sm text-muted-foreground">刪除所有處理報告</p>
            </div>
            <Button
              variant={confirmAction === 'reports' ? 'destructive' : 'outline'}
              onClick={() => handleAction('reports')}
              disabled={isAnyPending}
            >
              {confirmAction === 'reports' ? (
                <><AlertTriangle className="h-4 w-4 mr-2" />確認刪除</>
              ) : (
                <><Trash2 className="h-4 w-4 mr-2" />清除</>
              )}
            </Button>
          </div>

          <div className="flex items-center justify-between border rounded-lg p-4 bg-destructive/5 border-destructive/30">
            <div>
              <p className="font-medium text-destructive">清除全部資料</p>
              <p className="text-sm text-muted-foreground">刪除所有上傳檔案、結果和報告</p>
            </div>
            <Button
              variant="destructive"
              onClick={() => handleAction('all')}
              disabled={isAnyPending}
            >
              {confirmAction === 'all' ? (
                <><AlertTriangle className="h-4 w-4 mr-2" />確認清除全部</>
              ) : (
                <><Trash2 className="h-4 w-4 mr-2" />全部清除</>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 重置設定 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RotateCcw className="h-5 w-5" />
            重置設定
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between border rounded-lg p-4">
            <div>
              <p className="font-medium">重置 PHI 設定為預設值</p>
              <p className="text-sm text-muted-foreground">將遮蔽設定還原為系統預設值</p>
            </div>
            <Button
              variant={confirmAction === 'reset' ? 'destructive' : 'outline'}
              onClick={() => handleAction('reset')}
              disabled={isAnyPending}
            >
              {confirmAction === 'reset' ? (
                <><AlertTriangle className="h-4 w-4 mr-2" />確認重置</>
              ) : (
                <><RotateCcw className="h-4 w-4 mr-2" />重置</>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
