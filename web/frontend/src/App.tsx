import { useState } from 'react'
import { FileSearch, Database, FileBarChart, Settings, ListTodo, BookOpen, Users, LogOut } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/presentation/components/ui'
import { AuthGate, Guide, Sidebar, DataPreview, TasksPanel, ResultsPanel, Reports, SettingsPanel, UsersPanel } from '@/presentation/components'
import type { AuthUser } from '@/infrastructure/api'

function WorkspaceApp({ user, onLogout }: { user: AuthUser, onLogout: () => void }) {
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('guide')

  // 當 sidebar 選擇檔案時，切換到資料預覽
  const handleFileSelect = (fileId: string) => {
    setSelectedFileId(fileId)
    setActiveTab('preview')
  }

  const handleOpenSettings = () => {
    setActiveTab('settings')
  }

  return (
    <div className="flex h-screen bg-background">
      {/* 側邊欄 */}
      <Sidebar
        onFileSelect={handleFileSelect}
        onOpenSettings={handleOpenSettings}
        selectedFileId={selectedFileId}
      />

      {/* 主內容區 */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          {/* 標籤列 */}
          <div className="border-b px-4">
            <div className="flex items-center justify-between">
            <TabsList className="h-12">
              <TabsTrigger value="guide" className="gap-2">
                <BookOpen className="h-4 w-4" />
                使用說明
              </TabsTrigger>
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
              {user.role === 'admin' && (
                <TabsTrigger value="users" className="gap-2">
                  <Users className="h-4 w-4" />
                  使用者
                </TabsTrigger>
              )}
            </TabsList>
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <span>{user.username} ({user.role})</span>
              <button className="inline-flex items-center gap-1 hover:text-foreground" onClick={onLogout}>
                <LogOut className="h-4 w-4" />
                登出
              </button>
            </div>
            </div>
          </div>

          {/* 標籤內容 */}
          <TabsContent value="guide" className="flex-1 m-0">
            <Guide />
          </TabsContent>
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
            <SettingsPanel canEdit canEditSystem={user.role === 'admin'} />
          </TabsContent>
          {user.role === 'admin' && (
            <TabsContent value="users" className="flex-1 m-0">
              <UsersPanel currentUser={user} />
            </TabsContent>
          )}
        </Tabs>
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthGate>
      {(user, onLogout) => <WorkspaceApp user={user} onLogout={onLogout} />}
    </AuthGate>
  )
}

export default App
