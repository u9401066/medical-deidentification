import { FileSearch, Database, FileBarChart, Settings, ListTodo } from 'lucide-react'
import { Toaster } from 'sonner'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/presentation/components/ui'
import { Sidebar, DataPreview, TasksPanel, ResultsPanel, Reports, SettingsPanel } from '@/presentation/components'
import { useUIStore } from '@/infrastructure/store'

function App() {
  const activeTab = useUIStore((state) => state.activeTab)
  const setActiveTab = useUIStore((state) => state.setActiveTab)

  return (
    <div className="flex h-screen bg-background">
      {/* Toast 通知 */}
      <Toaster position="top-right" richColors closeButton />

      {/* 側邊欄 */}
      <Sidebar />

      {/* 主內容區 */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)} className="flex-1 flex flex-col">
          {/* 標籤列 */}
          <div className="border-b px-4">
            <TabsList className="h-12">
              <TabsTrigger value="preview" className="gap-2">
                <FileSearch className="h-4 w-4" />
                資料預覽
              </TabsTrigger>
              <TabsTrigger value="tasks" className="gap-2">
                <ListTodo className="h-4 w-4" />
                處理任務
              </TabsTrigger>
              <TabsTrigger value="results" className="gap-2">
                <Database className="h-4 w-4" />
                處理結果
              </TabsTrigger>
              <TabsTrigger value="reports" className="gap-2">
                <FileBarChart className="h-4 w-4" />
                報告
              </TabsTrigger>
              <TabsTrigger value="settings" className="gap-2">
                <Settings className="h-4 w-4" />
                設定
              </TabsTrigger>
            </TabsList>
          </div>

          {/* 標籤內容 */}
          <TabsContent value="preview" className="flex-1 m-0">
            <DataPreview />
          </TabsContent>
          <TabsContent value="tasks" className="flex-1 m-0">
            <TasksPanel />
          </TabsContent>
          <TabsContent value="results" className="flex-1 m-0">
            <ResultsPanel />
          </TabsContent>
          <TabsContent value="reports" className="flex-1 m-0">
            <Reports />
          </TabsContent>
          <TabsContent value="settings" className="flex-1 m-0">
            <SettingsPanel />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

export default App
