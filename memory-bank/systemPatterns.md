# System Patterns (Updated: 2026-02-20)

## Development Guidelines

- **Language**: 繁體中文 for docs/comments, English for code
- **Methodology**: MVP + DDD
- **GIT + MEM**: All code changes must sync with Git + Memory Bank

## Architecture Patterns

### 1. DDD 四層架構

**Backend (Python)**
```text
core/domain/         → 實體、值物件、PHI 類型
core/application/    → 批次處理、Pipeline
core/infrastructure/ → RAG、LLM、Loaders、Tools
core/interface/      → CLI
```

**Frontend (TypeScript/React)**
```text
src/domain/         → Task/File/Report entities, PHI value objects
src/application/    → React Query hooks (useTasks, useFiles, etc.)
src/infrastructure/ → API client, Zustand stores, Logger
src/presentation/   → UI Components (不得直接引用 infrastructure/api)
```

### 2. RAG-Enhanced De-identification

- RAG 檢索「需要遮蔽的內容」而非「需要保留的內容」
- Privacy-first: in-memory vector store for medical docs, persistent for regulations
- Hybrid PHI Detection: Regex → SpaCy NER → LLM

### 3. LLM 統一管理

- Config Layer: `LLMConfig` + `LLMPresets`
- Factory Layer: `create_llm()` 工廠函數
- Manager Layer: `LLMManager` 懶載入 + 統計追蹤
- Prompt 模板集中管理: `infrastructure/prompts/`

### 4. Frontend DDD Hooks Pattern

```text
Presentation → Application Hooks → Infrastructure API
(Components)    (useXxx hooks)     (API functions)
```

**Hooks**: useTasks, useFiles, useUploadFile, useDeleteFile, useFilePreview, useResults, useResultDetail, useReports, useReportDetail, useExportReport, useHealth, useDownloadResult, useDownloadSingleFile

**State**: Zustand (uiStore, selectionStore) for client state, TanStack Query for server state

### 5. Structured Output Pattern

LangChain `llm.with_structured_output(PydanticModel)` 確保 LLM 返回類型安全的結構化資料。

### 6. FIFO Streaming Pattern

Process data in chunks with immediate output and memory release. Enables unlimited input size with constant memory usage. Checkpoint saves for resume capability.

## Testing Strategy

| Level | Tool | Scope |
|-------|------|-------|
| Python Unit | pytest | `tests/` (exclude integration/) |
| Python Integration | pytest | `tests/integration/` (requires Ollama) |
| Frontend Unit | Vitest + RTL | `src/**/*.test.tsx` |
| Frontend E2E | Playwright | `e2e/*.spec.ts` |

## Environment

- Python 3.12, uv (no pip)
- Venv: `.venv/` (shared for web/backend too)
- Ollama: `http://192.168.1.2:30133`, model: `gemma3:27b`
- Frontend: npm, Vite, TypeScript strict
