import { useState, useRef, useEffect, ChangeEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings2, Upload, Shield, FileText, Save, Plus } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Badge, ScrollArea, Switch, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui'
import api, { PHIType, MaskingType, PHIConfig, RegulationRule } from '@/api'

export function SettingsPanel() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'phi' | 'regulations'>('phi')

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
        ) : (
          <RegulationsSettings
            regulations={regulations}
            onUpload={(file) => uploadRegulationMutation.mutate(file)}
            isUploading={uploadRegulationMutation.isPending}
          />
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
                      <SelectTrigger className="w-32">
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
}: {
  regulations: RegulationRule[]
  onUpload: (file: File) => void
  isUploading: boolean
}) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onUpload(file)
      e.target.value = ''
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
                      <Badge
                        variant={reg.enabled ? 'default' : 'secondary'}
                      >
                        {reg.enabled ? '啟用' : '停用'}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {reg.description}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>來源: {reg.source}</span>
                      <span>•</span>
                      <span>{reg.rules_count} 條規則</span>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <Switch
                        checked={reg.enabled}
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
