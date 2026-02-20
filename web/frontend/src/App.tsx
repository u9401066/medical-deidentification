import { useState } from 'react'
import { FileSearch, Database, FileBarChart, Settings, ListTodo } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/presentation/components/ui'
import { Sidebar, DataPreview, TasksPanel, ResultsPanel, Reports, SettingsPanel } from '@/presentation/components'

function App() {
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('preview')

  // 當 sidebar 選擇檔案時，切換到資料預覽
  const handleFileSelect = (fileId: string) => {
    setSelectedFileId(fileId)
    setActiveTab('preview')
  }

  return (
    <div className="flex h-screen bg-background">
      {/* 側邊欄 */}
      <Sidebar onFileSelect={handleFileSelect} selectedFileId={selectedFileId} />

      {/* 主內容區 */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
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
            <DataPreview selectedFileId={selectedFileId} onFileSelect={setSelectedFileId} />
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
