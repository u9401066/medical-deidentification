import { useState, useRef, useEffect, ChangeEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings2, Upload, Shield, FileText, Save, Plus, ChevronUp, Eye, Cpu, RefreshCw, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Badge, ScrollArea, Switch, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, Input } from '@/presentation/components/ui'
import api, { PHIType, PHITypeConfig, MaskingType, PHIConfig, RegulationRule, getLLMStatus, getLLMConfig, updateLLMConfig, setLLMModel, testLLMConnection, getLLMProviders } from '@/infrastructure/api'

interface SettingsPanelProps {
  canEdit?: boolean
  canEditSystem?: boolean
}

type EditablePHIConfig = Omit<PHIConfig, 'phi_types'> & {
  phi_types?: Record<string, PHITypeConfig>
}

function toMaskingType(value?: string): MaskingType {
  if (
    value === 'hash' ||
    value === 'replace' ||
    value === 'delete' ||
    value === 'keep' ||
    value === 'generalize'
  ) {
    return value
  }
  return 'mask'
}

function normalizePHIConfig(
  config: PHIConfig | undefined,
  phiTypes: PHIType[]
): EditablePHIConfig {
  const phiTypeConfig: Record<string, PHITypeConfig> = {}
  const rawPhiTypes = config?.phi_types

  if (Array.isArray(rawPhiTypes)) {
    rawPhiTypes.forEach((type) => {
      phiTypeConfig[type] = {
        enabled: true,
      }
    })
  } else if (rawPhiTypes && typeof rawPhiTypes === 'object') {
    Object.entries(rawPhiTypes).forEach(([type, typeConfig]) => {
      if (/^\d+$/.test(type)) return
      phiTypeConfig[type] = {
        enabled: typeConfig.enabled ?? true,
        masking: toMaskingType(typeConfig.masking || config?.default_masking),
        replace_with: typeConfig.replace_with,
      }
    })
  }

  phiTypes.forEach((phiType) => {
    phiTypeConfig[phiType.type] = {
      enabled: phiTypeConfig[phiType.type]?.enabled ?? true,
      masking: toMaskingType(
        phiTypeConfig[phiType.type]?.masking ||
        phiType.default_masking ||
        config?.default_masking
      ),
      replace_with: phiTypeConfig[phiType.type]?.replace_with,
    }
  })

  return {
    ...config,
    enabled: config?.enabled ?? true,
    strict_mode: config?.strict_mode ?? false,
    default_masking: toMaskingType(config?.default_masking),
    phi_types: phiTypeConfig,
  }
}

export function SettingsPanel({ canEdit = true, canEditSystem = true }: SettingsPanelProps) {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'phi' | 'regulations' | 'llm'>('phi')

  useEffect(() => {
    if (!canEditSystem && activeTab !== 'phi') {
      setActiveTab('phi')
    }
  }, [activeTab, canEditSystem])

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
    enabled: canEditSystem,
  })

  // 更新設定 mutation
  const updateConfigMutation = useMutation({
    mutationFn: api.updateConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
    },
  })

  // 上傳法規 mutation
  const uploadRegulationMutation = useMutation({
    mutationFn: (file: File) => api.uploadRegulation(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['regulations'] })
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
        {canEditSystem && (
          <>
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
                activeTab === 'llm'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setActiveTab('llm')}
            >
              <Cpu className="h-4 w-4 inline mr-2" />
              LLM 設定
            </button>
          </>
        )}
      </div>

      {/* 內容區域 */}
      <div className="flex-1 overflow-auto p-4">
        {!canEdit && (
          <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-100">
            目前為一般使用者模式，可在開始處理前檢視 PHI 設定；若需調整偵測類型、遮蔽方式或 LLM 設定，請由管理員修改。
          </div>
        )}
        {canEdit && !canEditSystem && (
          <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-100">
            你可以自行調整本帳號的 PHI 偵測類型與遮蔽方式；法規與 LLM 連線設定仍由管理員維護。
          </div>
        )}
        {activeTab === 'phi' ? (
          <PHISettings
            phiTypes={phiTypes}
            config={config}
            canEdit={canEdit}
            onUpdateConfig={(updates) => {
              if (canEdit) {
                updateConfigMutation.mutate(updates)
              }
            }}
            isUpdating={updateConfigMutation.isPending}
          />
        ) : activeTab === 'regulations' ? (
          <RegulationsSettings
            regulations={regulations}
            canEdit={canEditSystem}
            onUpload={(file) => uploadRegulationMutation.mutate(file)}
            isUploading={uploadRegulationMutation.isPending}
          />
        ) : (
          <LLMSettings canEdit={canEditSystem} />
        )}
      </div>
    </div>
  )
}

// PHI 設定子元件
function PHISettings({
  phiTypes,
  config,
  canEdit,
  onUpdateConfig,
  isUpdating,
}: {
  phiTypes: PHIType[]
  config?: PHIConfig
  canEdit: boolean
  onUpdateConfig: (updates: Partial<PHIConfig>) => void
  isUpdating: boolean
}) {
  const [localConfig, setLocalConfig] = useState<EditablePHIConfig>(() =>
    normalizePHIConfig(config, phiTypes)
  )

  useEffect(() => {
    setLocalConfig(normalizePHIConfig(config, phiTypes))
  }, [config, phiTypes])

  const handleSave = () => {
    if (!canEdit) return
    onUpdateConfig(localConfig)
  }

  const maskingTypes: MaskingType[] = ['mask', 'hash', 'replace', 'delete', 'keep', 'generalize']

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
              disabled={!canEdit}
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
              disabled={!canEdit}
              onCheckedChange={(checked: boolean) =>
                setLocalConfig((prev) => ({ ...prev, strict_mode: checked }))
              }
            />
          </div>

          <div className="space-y-2">
            <p className="font-medium">預設遮蔽方式</p>
            <Select
              value={localConfig.default_masking || 'mask'}
              disabled={!canEdit}
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
                      : type === 'generalize'
                      ? '泛化'
                      : '保留'}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button onClick={handleSave} disabled={!canEdit || isUpdating}>
            <Save className="h-4 w-4 mr-2" />
            {canEdit ? '儲存設定' : '僅可檢視'}
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
                        disabled={!canEdit}
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
                          toMaskingType(phiType.default_masking) ||
                          'mask'
                        }
                        disabled={!canEdit}
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
                              : type === 'generalize'
                              ? '泛化'
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
                          disabled={!canEdit}
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
  canEdit,
  onUpload,
  isUploading,
}: {
  regulations: RegulationRule[]
  canEdit: boolean
  onUpload: (file: File) => void
  isUploading: boolean
}) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [expandedRule, setExpandedRule] = useState<string | null>(null)
  const [ruleContent, setRuleContent] = useState<string | null>(null)
  const [loadingContent, setLoadingContent] = useState(false)

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && canEdit) {
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
              disabled={!canEdit}
              className="hidden"
            />
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              disabled={!canEdit || isUploading}
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
                        disabled={!canEdit}
                        onCheckedChange={() => {
                          // TODO: 更新法規啟用狀態
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

// LLM 設定子元件
function LLMSettings({ canEdit = true }: { canEdit?: boolean }) {
  const queryClient = useQueryClient()
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)

  // 取得 LLM 狀態
  const { data: llmStatus, isLoading: statusLoading, isFetching: statusFetching, refetch: refetchStatus } = useQuery({
    queryKey: ['llm-status'],
    queryFn: getLLMStatus,
    refetchInterval: 30000, // 每 30 秒更新一次
    staleTime: 10000, // 10 秒內視為新鮮資料
    retry: 2,
  })

  // 取得 LLM 設定
  const { data: llmConfig } = useQuery({
    queryKey: ['llm-config'],
    queryFn: getLLMConfig,
    staleTime: 10000,
  })
  const [llmDraft, setLlmDraft] = useState({
    base_url: '',
    api_key: '',
    temperature: '0.1',
    max_tokens: '4096',
    timeout: '120',
  })

  useEffect(() => {
    if (!llmConfig) return
    setLlmDraft({
      base_url: llmConfig.base_url || '',
      api_key: '',
      temperature: String(llmConfig.temperature ?? 0.1),
      max_tokens: String(llmConfig.max_tokens ?? 4096),
      timeout: String(llmConfig.timeout ?? 120),
    })
  }, [llmConfig])

  // 取得支援的提供者
  const { data: providers = [] } = useQuery({
    queryKey: ['llm-providers'],
    queryFn: getLLMProviders,
  })

  // 更新設定
  const updateMutation = useMutation({
    mutationFn: updateLLMConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-config'] })
      queryClient.invalidateQueries({ queryKey: ['llm-status'] })
    },
  })

  // 切換模型
  const setModelMutation = useMutation({
    mutationFn: setLLMModel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-config'] })
      queryClient.invalidateQueries({ queryKey: ['llm-status'] })
    },
  })

  // 測試連線
  const handleTestConnection = async () => {
    if (!canEdit) return
    setIsTesting(true)
    setTestResult(null)
    try {
      const result = await testLLMConnection()
      setTestResult({
        success: result.success,
        message: result.success
          ? `連線成功！模型: ${result.model}`
          : result.error || '連線失敗',
      })
    } catch (error) {
      setTestResult({
        success: false,
        message: '測試連線時發生錯誤',
      })
    } finally {
      setIsTesting(false)
    }
  }

  const currentProvider = providers.find(p => p.id === llmConfig?.provider)

  return (
    <div className="space-y-6">
      {/* 連線狀態 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            LLM 連線狀態
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {statusLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              ) : llmStatus?.online ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500" />
              )}
              <span className="font-medium">
                {statusLoading ? '檢查中...' : llmStatus?.online ? '線上' : '離線'}
              </span>
              {statusFetching && !statusLoading && (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              )}
            </div>
            {llmStatus?.current_model && (
              <Badge variant="outline">{llmStatus.current_model}</Badge>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchStatus()}
              className="ml-auto"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              重新檢查
            </Button>
          </div>

          {llmStatus?.error && (
            <div className="text-sm text-red-500 bg-red-50 dark:bg-red-950 p-3 rounded-lg">
              錯誤: {llmStatus.error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">提供者:</span>{' '}
              <span className="font-medium">{currentProvider?.name || llmConfig?.provider}</span>
            </div>
            <div>
              <span className="text-muted-foreground">端點:</span>{' '}
              <span className="font-medium">{llmStatus?.endpoint || llmConfig?.base_url}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={handleTestConnection}
              disabled={!canEdit || isTesting}
            >
              {isTesting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  測試中...
                </>
              ) : (
                '測試連線'
              )}
            </Button>
            {testResult && (
              <span className={`text-sm ${testResult.success ? 'text-green-600' : 'text-red-600'}`}>
                {testResult.message}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 模型選擇 */}
      <Card>
        <CardHeader>
          <CardTitle>模型選擇</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {llmStatus?.available_models && llmStatus.available_models.length > 0 ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">目前模型:</span>
                <Select
                  value={llmConfig?.model || ''}
                  onValueChange={(model) => setModelMutation.mutate(model)}
                  disabled={!canEdit || setModelMutation.isPending}
                >
                  <SelectTrigger className="w-64">
                    <SelectValue placeholder="選擇模型" />
                  </SelectTrigger>
                  <SelectContent>
                    {llmStatus.available_models.map((model) => (
                      <SelectItem key={model.name} value={model.name}>
                        <div className="flex items-center gap-2">
                          <span>{model.name}</span>
                          {model.size && (
                            <span className="text-xs text-muted-foreground">({model.size})</span>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <p className="text-xs text-muted-foreground">
                共 {llmStatus.available_models.length} 個可用模型
              </p>
            </div>
          ) : (
            <div className="text-center py-4 text-muted-foreground">
              <p>無可用模型</p>
              <p className="text-xs mt-1">請確認 LLM 服務已啟動並下載模型</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 連線設定 */}
      <Card>
        <CardHeader>
          <CardTitle>連線設定</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">服務提供者</label>
              <Select
                value={llmConfig?.provider || 'ollama'}
                disabled={!canEdit}
                onValueChange={(provider) => {
                  if (!canEdit) return
                  const selectedProvider = providers.find(p => p.id === provider)
                  updateMutation.mutate({
                    provider,
                    base_url: selectedProvider?.default_url || llmConfig?.base_url,
                  })
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {providers.map((provider) => (
                    <SelectItem key={provider.id} value={provider.id}>
                      {provider.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">API 端點</label>
              <Input
                value={llmDraft.base_url}
                disabled={!canEdit}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setLlmDraft((draft) => ({ ...draft, base_url: e.target.value }))
                }
                onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                  if (!canEdit) return
                  if (e.target.value !== llmConfig?.base_url) {
                    updateMutation.mutate({ base_url: e.target.value })
                  }
                }}
                placeholder="http://localhost:11434"
              />
            </div>
          </div>

          {currentProvider?.requires_api_key && (
            <div className="space-y-2">
              <label className="text-sm font-medium">API Key</label>
              <Input
                type="password"
                value={llmDraft.api_key}
                disabled={!canEdit}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setLlmDraft((draft) => ({ ...draft, api_key: e.target.value }))
                }
                onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                  if (!canEdit) return
                  if (e.target.value) {
                    updateMutation.mutate({ api_key: e.target.value })
                    setLlmDraft((draft) => ({ ...draft, api_key: '' }))
                  }
                }}
                placeholder={llmConfig?.api_key ? '已設定 API Key，輸入新值可覆蓋' : '輸入 API Key'}
              />
            </div>
          )}

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Temperature</label>
              <Input
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={llmDraft.temperature}
                disabled={!canEdit}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setLlmDraft((draft) => ({ ...draft, temperature: e.target.value }))
                }
                onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                  if (!canEdit) return
                  const value = parseFloat(e.target.value)
                  if (!isNaN(value) && value !== llmConfig?.temperature) {
                    updateMutation.mutate({ temperature: value })
                  }
                }}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Max Tokens</label>
              <Input
                type="number"
                min="1"
                max="32000"
                value={llmDraft.max_tokens}
                disabled={!canEdit}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setLlmDraft((draft) => ({ ...draft, max_tokens: e.target.value }))
                }
                onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                  if (!canEdit) return
                  const value = parseInt(e.target.value)
                  if (!isNaN(value) && value !== llmConfig?.max_tokens) {
                    updateMutation.mutate({ max_tokens: value })
                  }
                }}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Timeout (秒)</label>
              <Input
                type="number"
                min="10"
                max="600"
                value={llmDraft.timeout}
                disabled={!canEdit}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setLlmDraft((draft) => ({ ...draft, timeout: e.target.value }))
                }
                onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                  if (!canEdit) return
                  const value = parseInt(e.target.value)
                  if (!isNaN(value) && value !== llmConfig?.timeout) {
                    updateMutation.mutate({ timeout: value })
                  }
                }}
              />
            </div>
          </div>

          {updateMutation.isPending && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              儲存中...
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
