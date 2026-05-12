import { useState } from 'react'
import { 
  BookOpen, 
  Upload, 
  Eye, 
  Settings2, 
  Play, 
  FileBarChart, 
  Download, 
  CheckCircle, 
  ChevronDown, 
  ChevronRight,
  Cpu,
  Shield,
  FileText,
  AlertTriangle,
  Info,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, Badge, ScrollArea, Button } from '@/presentation/components/ui'

// ─── 資料 ───────────────────────────────────────────────────────────────────

const WORKFLOW_STEPS = [
  {
    step: 1,
    icon: <Cpu className="h-5 w-5 text-blue-500" />,
    title: '確認 LLM 連線',
    badge: '前置作業',
    badgeColor: 'bg-blue-100 text-blue-800',
    description: '確認側邊欄左上角的 LLM 狀態為「在線」（綠色），才能使用 AI 去識別化功能。',
    details: [
      '側邊欄標題下方可見 LLM 狀態指示器',
      '顯示綠色 ✓「在線」表示 Ollama 服務正常',
      '如顯示紅色 ✗「離線」，請按照 docs/OLLAMA_CONNECTION_GUIDE.md 排查',
      '⚠️ 若 LLM 離線，系統仍可執行（使用模擬處理），但 PHI 偵測結果不可靠',
    ],
  },
  {
    step: 2,
    icon: <Upload className="h-5 w-5 text-green-500" />,
    title: '上傳檔案',
    badge: '步驟一',
    badgeColor: 'bg-green-100 text-green-800',
    description: '將含有病患資料的檔案拖放到左側上傳區，或點擊選擇檔案。',
    details: [
      '支援格式：Excel (.xlsx, .xls)、CSV、JSON、純文字(.txt)',
      '可一次上傳多個檔案',
      '最大檔案大小：10MB（每個）',
      '上傳後可在側邊欄檔案列表中看到，並顯示檔案大小',
    ],
  },
  {
    step: 3,
    icon: <Eye className="h-5 w-5 text-purple-500" />,
    title: '預覽資料',
    badge: '步驟二',
    badgeColor: 'bg-purple-100 text-purple-800',
    description: '點擊「資料預覽」標籤，選擇已上傳的檔案，確認內容正確後再執行去識別化。',
    details: [
      '「資料預覽」Tab 可查看原始資料內容（最多 50 筆/頁）',
      '支援分頁瀏覽大型資料集',
      '欄位名稱和資料類型一目了然',
      '確認包含 PHI 欄位（姓名、日期、電話等）再繼續',
    ],
  },
  {
    step: 4,
    icon: <Settings2 className="h-5 w-5 text-orange-500" />,
    title: 'PHI 設定（可選）',
    badge: '步驟三',
    badgeColor: 'bg-orange-100 text-orange-800',
    description: '正式開始前請確認 PHI 偵測範圍與遮蔽方式；一般使用者可檢視，管理員可調整。',
    details: [
      '可啟用/停用特定 PHI 類型（姓名、日期、電話、Email、地址、ID、病歷號）',
      '支援遮蔽方式：遮蔽(***) / 雜湊(Hash) / 替換 / 刪除 / 保留',
      '「嚴格模式」會提高偵測靈敏度（可能增加誤判）',
      '點擊「開始處理」後會先跳出確認視窗，可返回「設定」再次確認',
      '設定儲存後立即生效，適用於後續所有處理任務',
    ],
  },
  {
    step: 5,
    icon: <Play className="h-5 w-5 text-red-500" />,
    title: '執行去識別化',
    badge: '步驟四',
    badgeColor: 'bg-red-100 text-red-800',
    description: '在側邊欄勾選要處理的檔案，點擊「開始處理」按鈕啟動去識別化任務。',
    details: [
      '在側邊欄檔案列表中，點擊檔案會同時選取並切換預覽',
      '可多選檔案，一次批次處理',
      '勾選後點擊「開始處理 (N 個檔案)」按鈕，先確認檔案、PHI 設定與 LLM 狀態',
      '切換到「處理任務」Tab 可查看進度',
      '藍色旋轉圖示表示處理中，完成後顯示綠色勾勾',
    ],
  },
  {
    step: 6,
    icon: <FileText className="h-5 w-5 text-teal-500" />,
    title: '查看結果',
    badge: '步驟五',
    badgeColor: 'bg-teal-100 text-teal-800',
    description: '處理完成後，切換到「處理結果」標籤，查看 PHI 偵測詳情和去識別化內容。',
    details: [
      '結果列表顯示每筆任務的 PHI 偵測數量',
      '點擊任一結果可進入詳情頁',
      '「PHI 列表」模式：以表格顯示每個欄位原始值 vs 遮蔽值',
      '「差異檢視」模式：在文字中高亮顯示所有被遮蔽的 PHI',
      '可一鍵下載結果為 Excel 格式',
    ],
  },
  {
    step: 7,
    icon: <FileBarChart className="h-5 w-5 text-indigo-500" />,
    title: '查看報告',
    badge: '步驟六',
    badgeColor: 'bg-indigo-100 text-indigo-800',
    description: '「報告」標籤提供詳細的 PHI 分析統計，可匯出為 JSON/CSV/Markdown 格式。',
    details: [
      '顯示各 PHI 類型的數量統計（圓餅圖）',
      '每個檔案的去識別化概要',
      '支援匯出為 JSON / CSV / Markdown 三種格式',
      '報告保留完整的 PHI 分布資訊，適合法規稽核',
    ],
  },
  {
    step: 8,
    icon: <Download className="h-5 w-5 text-cyan-500" />,
    title: '下載去識別化資料',
    badge: '步驟七',
    badgeColor: 'bg-cyan-100 text-cyan-800',
    description: '在結果頁面或側邊欄，點擊下載按鈕取得去識別化後的資料。',
    details: [
      '在「處理結果」列表，每筆結果右側有下載按鈕',
      '也可在側邊欄檔案列表旁找到下載圖示',
      '下載格式為 Excel (.xlsx)，欄位結構與原始檔相同',
      '去識別化欄位中，PHI 已被替換為遮蔽值',
    ],
  },
]

const PHI_TYPES = [
  { type: 'NAME', label: '姓名', color: 'bg-red-100 text-red-800', example: '王小明 → [NAME_1]' },
  { type: 'DATE', label: '日期', color: 'bg-blue-100 text-blue-800', example: '2024/01/15 → [DATE_1]' },
  { type: 'PHONE', label: '電話', color: 'bg-green-100 text-green-800', example: '0912-345-678 → [PHONE_1]' },
  { type: 'EMAIL', label: 'Email', color: 'bg-purple-100 text-purple-800', example: 'user@example.com → [EMAIL_1]' },
  { type: 'ADDRESS', label: '地址', color: 'bg-orange-100 text-orange-800', example: '台北市信義區 → [ADDRESS_1]' },
  { type: 'ID_NUMBER', label: '身分證號', color: 'bg-yellow-100 text-yellow-800', example: 'A123456789 → [ID_NUMBER_1]' },
  { type: 'MEDICAL_RECORD', label: '病歷號', color: 'bg-pink-100 text-pink-800', example: 'MR001234 → [MEDICAL_RECORD_1]' },
  { type: 'AGE_OVER_89', label: '年齡 ≥ 89', color: 'bg-cyan-100 text-cyan-800', example: '92歲 → [AGE_OVER_89_1]' },
]

const FAQS = [
  {
    q: 'LLM 離線時還可以使用嗎？',
    a: '可以，系統會改用「模擬處理」模式，但 PHI 偵測能力大幅下降，僅能透過正則表達式偵測部分固定格式（如電話、Email）。建議連線 Ollama 後再進行正式處理。',
  },
  {
    q: '處理時間多長？',
    a: '依資料量而異。單個檔案通常 30 秒至 3 分鐘。每列文字較長時會更久。進度可在「處理任務」頁面即時查看。',
  },
  {
    q: '支援的最大資料量？',
    a: '目前沒有硬性限制，但建議單個任務不超過 500 列，超過可能造成超時。可分批上傳處理。',
  },
  {
    q: '結果儲存在哪裡？',
    a: '結果儲存在後端 web/backend/results/ 目錄，報告在 web/backend/reports/。重新整理頁面後仍可在「處理結果」和「報告」標籤看到歷史資料。',
  },
  {
    q: '如何清除資料？',
    a: '可呼叫 DELETE /api/cleanup/all API 清除全部資料，或分別呼叫 /api/cleanup/uploads、/api/cleanup/results 等。前端尚無 UI 按鈕，可使用 curl 或 API Docs (http://localhost:8000/docs)。',
  },
]

// ─── 組件 ───────────────────────────────────────────────────────────────────

function StepCard({ step: s, expanded, onToggle }: { 
  step: typeof WORKFLOW_STEPS[0]
  expanded: boolean
  onToggle: () => void 
}) {
  return (
    <Card 
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={onToggle}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* 步驟編號 */}
          <div className="shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">
            {s.step}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {s.icon}
              <span className="font-semibold">{s.title}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${s.badgeColor}`}>
                {s.badge}
              </span>
              <div className="ml-auto shrink-0">
                {expanded
                  ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  : <ChevronRight className="h-4 w-4 text-muted-foreground" />
                }
              </div>
            </div>
            <p className="text-sm text-muted-foreground mt-1">{s.description}</p>

            {expanded && (
              <ul className="mt-3 space-y-1.5">
                {s.details.map((d, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <CheckCircle className="h-3.5 w-3.5 text-green-500 shrink-0 mt-0.5" />
                    <span>{d}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function FAQItem({ faq, expanded, onToggle }: { 
  faq: typeof FAQS[0]
  expanded: boolean
  onToggle: () => void
}) {
  return (
    <div 
      className="border rounded-lg cursor-pointer hover:bg-muted/40 transition-colors"
      onClick={onToggle}
    >
      <div className="flex items-center gap-2 p-3">
        <Info className="h-4 w-4 text-muted-foreground shrink-0" />
        <span className="font-medium text-sm flex-1">{faq.q}</span>
        {expanded 
          ? <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
          : <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
        }
      </div>
      {expanded && (
        <div className="px-3 pb-3">
          <p className="text-sm text-muted-foreground pl-6">{faq.a}</p>
        </div>
      )}
    </div>
  )
}

// ─── 主頁面 ─────────────────────────────────────────────────────────────────

export function Guide() {
  const [expandedStep, setExpandedStep] = useState<number | null>(1)
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null)
  const [activeSection, setActiveSection] = useState<'workflow' | 'phi' | 'faq'>('workflow')

  const toggleStep = (step: number) => {
    setExpandedStep(expandedStep === step ? null : step)
  }

  const toggleFaq = (idx: number) => {
    setExpandedFaq(expandedFaq === idx ? null : idx)
  }

  return (
    <div className="flex flex-col h-full">
      {/* 頁面標題 */}
      <div className="p-4 border-b bg-gradient-to-r from-primary/5 to-primary/10">
        <div className="flex items-center gap-3">
          <BookOpen className="h-6 w-6 text-primary" />
          <div>
            <h1 className="text-xl font-bold">使用說明</h1>
            <p className="text-sm text-muted-foreground">PHI 醫療資料去識別化工具 — 完整操作指南</p>
          </div>
        </div>

        {/* 快速概覽 */}
        <div className="mt-3 flex items-center gap-2 flex-wrap">
          <Badge variant="outline" className="gap-1">
            <Upload className="h-3 w-3" />
            上傳檔案
          </Badge>
          <span className="text-muted-foreground text-xs">→</span>
          <Badge variant="outline" className="gap-1">
            <Play className="h-3 w-3" />
            執行處理
          </Badge>
          <span className="text-muted-foreground text-xs">→</span>
          <Badge variant="outline" className="gap-1">
            <Eye className="h-3 w-3" />
            查看結果
          </Badge>
          <span className="text-muted-foreground text-xs">→</span>
          <Badge variant="outline" className="gap-1">
            <Download className="h-3 w-3" />
            下載資料
          </Badge>
        </div>
      </div>

      {/* 🔔 警告提示 */}
      <div className="mx-4 mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-2">
        <AlertTriangle className="h-4 w-4 text-yellow-600 shrink-0 mt-0.5" />
        <p className="text-sm text-yellow-800">
          <strong>注意：</strong>本工具處理的是敏感醫療資料，請確保在安全環境中使用，並遵守相關法規（個資法、HIPAA 等）。
          去識別化結果僅供參考，請由專業人員進行最終審查。
        </p>
      </div>

      {/* 區段切換 */}
      <div className="flex gap-1 mx-4 mt-4">
        <Button
          variant={activeSection === 'workflow' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveSection('workflow')}
        >
          操作流程
        </Button>
        <Button
          variant={activeSection === 'phi' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveSection('phi')}
        >
          PHI 類型說明
        </Button>
        <Button
          variant={activeSection === 'faq' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveSection('faq')}
        >
          常見問題
        </Button>
      </div>

      {/* 內容 */}
      <ScrollArea className="flex-1 mt-4">
        <div className="px-4 pb-8 space-y-3">

          {/* 操作流程 */}
          {activeSection === 'workflow' && (
            <>
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  共 {WORKFLOW_STEPS.length} 個步驟，點擊展開詳細說明
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs"
                  onClick={() => setExpandedStep(expandedStep ? null : 1)}
                >
                  {expandedStep ? '全部收合' : '全部展開'}
                </Button>
              </div>
              {WORKFLOW_STEPS.map((s) => (
                <StepCard
                  key={s.step}
                  step={s}
                  expanded={expandedStep === s.step}
                  onToggle={() => toggleStep(s.step)}
                />
              ))}
            </>
          )}

          {/* PHI 類型說明 */}
          {activeSection === 'phi' && (
            <>
              <p className="text-sm text-muted-foreground mb-2">
                系統支援偵測以下 8 種 PHI（個人健康資訊）類型：
              </p>
              <div className="grid grid-cols-1 gap-2">
                {PHI_TYPES.map((p) => (
                  <div key={p.type} className="flex items-center gap-3 border rounded-lg p-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-mono font-medium shrink-0 ${p.color}`}>
                      {p.type}
                    </span>
                    <div>
                      <span className="font-medium text-sm">{p.label}</span>
                      <p className="text-xs text-muted-foreground font-mono">{p.example}</p>
                    </div>
                  </div>
                ))}
              </div>
              <Card className="mt-2">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    遮蔽格式說明
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p>預設遮蔽格式為 <code className="bg-muted px-1 rounded">[TYPE_序號]</code>，例如同一文件第二個姓名為 <code className="bg-muted px-1 rounded">[NAME_2]</code>。</p>
                  <p>可在「設定」頁面更改遮蔽方式為雜湊值、固定替換文字、或直接刪除。</p>
                </CardContent>
              </Card>
            </>
          )}

          {/* 常見問題 */}
          {activeSection === 'faq' && (
            <>
              {FAQS.map((faq, idx) => (
                <FAQItem
                  key={idx}
                  faq={faq}
                  expanded={expandedFaq === idx}
                  onToggle={() => toggleFaq(idx)}
                />
              ))}
            </>
          )}

        </div>
      </ScrollArea>
    </div>
  )
}
