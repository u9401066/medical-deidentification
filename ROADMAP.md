# 🗺️ Development Roadmap | 開發路線圖

> **設計原則**: 每個 Phase 都是可獨立發布的完整功能

## 🎯 Performance Target | 效能目標

```
目標：處理 1GB 文檔 在 10 分鐘內完成
Target: Process 1GB documents within 10 minutes
Required throughput: ~1.7 MB/s
```

---

## 📊 Current Status | 現況分析

### Bottleneck Analysis | 瓶頸分析

| Component | Current Speed | Target | Gap |
|-----------|---------------|--------|-----|
| Pure LLM (Qwen 7B) | 15-25s/row | 0.1s/row | 150-250x |
| Pure LLM (Qwen 0.5B) | 0.5-1s/row | 0.1s/row | 5-10x |
| SpaCy NER | 0.01-0.05s/row | 0.01s/row | ✅ |
| Regex | 0.001s/row | 0.001s/row | ✅ |

### Why NOT Multi-threading? | 為何不用多線程？

```
❌ Python 3.10 GIL (Global Interpreter Lock) 限制
   - Multi-threading 無法真正並行 CPU 密集型任務
   - LLM inference 是 CPU/GPU bound，不是 I/O bound
   - asyncio 只對 I/O 操作有效
```

### Ollama Concurrency | Ollama 並發限制

```
⚠️ Ollama 單一實例限制 (8GB VRAM):
   - 可同時載入多個模型，但 VRAM 共用
   - 8GB 只夠載入一個 3B 模型 + context
   - 方案：使用 LiteLLM 作為統一 API Gateway
   - 替代：多 Ollama 實例 (需多 GPU 或 CPU offload)
```

---

## 🚀 Solution: Phased Multi-Agent System | 解決方案：分階段多 Agent 系統

### Hardware Constraint | 硬體限制

```text
┌─────────────────────────────────────────┐
│  VRAM: 8GB (單 GPU)                     │
│  ├── Option A: 單模型載入               │
│  │   └── Qwen-1.5B (~3GB) + context    │
│  │                                      │
│  ├── Option B: 使用 LiteLLM Gateway     │
│  │   └── 統一 API，自動負載均衡         │
│  │                                      │
│  └── Option C: MiniMind + Qwen 輪替     │
│      └── 批次處理，減少切換成本         │
└─────────────────────────────────────────┘
```

### Architecture | 架構

```text
┌─────────────────────────────────────────────────────────────────────┐
│              Phased Multi-Agent PHI Detection System                │
│                    with Safety Net (安全網機制)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ⚠️ 核心原則: 所有路徑最終都經過 Verification!                       │
│                                                                     │
│  Phase 1: Tool Workers ──► Phase 2: Single Agent ──►               │
│                                                                     │
│  Phase 3: Multi-Agent + Router ──► Phase 4: DSPy Optimization      │
│                                                                     │
│  每個 Phase 都可獨立發布使用！                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### ⚠️ Safety Net Design | 安全網設計

**問題**: 如果任何節點漏檢 PHI，沒有後續核對就會漏掉！

**解決方案**: **Parallel Detection + Union Merge (並行檢測 + 聯集合併)**

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    Safety Net Architecture                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Input Text ────┬────────────────────────────────────┐             │
│                 │                                     │             │
│                 ▼                                     ▼             │
│  ┌──────────────────────────┐     ┌──────────────────────────┐    │
│  │   Path A: Tool Workers   │     │   Path B: LLM Agent      │    │
│  │   (Regex, SpaCy, Rules)  │     │   (Always runs!)         │    │
│  │                          │     │                          │    │
│  │   Output: tool_phi[]     │     │   Output: llm_phi[]      │    │
│  └────────────┬─────────────┘     └────────────┬─────────────┘    │
│               │                                 │                   │
│               └─────────────┬───────────────────┘                   │
│                             ▼                                       │
│              ┌──────────────────────────────┐                       │
│              │     UNION MERGE (聯集)       │                       │
│              │  all_candidates = A ∪ B      │                       │
│              │  寧可誤報，不可漏報！          │                       │
│              └──────────────┬───────────────┘                       │
│                             ▼                                       │
│              ┌──────────────────────────────┐                       │
│              │   Verification Agent         │                       │
│              │   (Qwen-1.5B)                │                       │
│              │   • Confirm real PHI         │                       │
│              │   • Remove false positives   │                       │
│              │   • ALWAYS runs on ALL       │                       │
│              └──────────────┬───────────────┘                       │
│                             ▼                                       │
│                      Final PHI Output                               │
└─────────────────────────────────────────────────────────────────────┘

Key Insight:
- Tools 快但可能漏：用 Regex/SpaCy 快速找結構化 PHI
- LLM 慢但更全面：Agent 會找到 Tools 漏掉的語義 PHI  
- 聯集合併：兩邊結果合併，確保不漏
- Verification 必過：所有候選都經過最終確認
```

### Fallback Strategy | 容錯策略

```text
┌─────────────────────────────────────────────────────────────────────┐
│  Fallback Chains (容錯鏈)                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Level 1: Tool Pre-scan                                            │
│     │                                                               │
│     ├── Success → Continue with results                            │
│     └── Failure → Flag chunk, still send to LLM                    │
│                                                                     │
│  Level 2: Fast Agent (Qwen-0.5B)                                   │
│     │                                                               │
│     ├── Success → Merge with tool results                          │
│     ├── Timeout → Retry once, then escalate to Precise             │
│     └── Error → Escalate to Precise Agent                          │
│                                                                     │
│  Level 3: Precise Agent (Qwen-1.5B)                                │
│     │                                                               │
│     ├── Success → Final verification                               │
│     ├── Timeout → Use conservative mode (keep all candidates)      │
│     └── Error → Flag for human review                              │
│                                                                     │
│  Level 4: Human Review Queue                                       │
│     └── Chunks that failed all automated paths                     │
│                                                                     │
│  Principle: 失敗時寧可保守 (keep candidates) 也不要丟棄！             │
└─────────────────────────────────────────────────────────────────────┘
```

### Confidence-based Routing (改良版) | 基於信心的路由

```text
Previous (有漏洞):                    New (安全網版):
                                     
┌─────────┐                          ┌─────────┐
│ Router  │                          │  Text   │
└────┬────┘                          └────┬────┘
     │                                    │
     ├── tools_only ─► Done (危險!)       ├─► Tools (parallel)
     ├── fast ─► Fast Agent               │        │
     └── precise ─► Precise Agent         ├─► LLM Agent (parallel)
                                          │        │
                                          └─► UNION ─► Verification ─► Done
                                          
差異:
- 舊: tools_only 路徑沒有 LLM 核對 (危險！)
- 新: 所有路徑都有 LLM 參與 + 最終 Verification
```

---

## 📅 Implementation Phases | 實施階段

> **原則**: 
> - 每個 Phase 都可獨立發布使用
> - 基於現有 Chain 架構擴展，不重寫！
> - 速度太慢 = 沒人用的工具！

### 🔧 現有架構分析 | Existing Architecture

```text
現有 Chain 架構：
┌─────────────────────────────────────────────────────────────────────┐
│  PHIIdentificationChain (infrastructure/rag/phi_identification_chain.py)
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ├── _identify_phi_direct()  ──► chains/processors.py              │
│  │   └── identify_phi_structured()                                  │
│  │   └── identify_phi_json_fallback()                               │
│  │                                                                  │
│  └── _identify_phi_chunked() ──► chains/map_reduce.py              │
│      └── build_map_chain()                                          │
│      └── merge_phi_results()                                        │
│      └── identify_phi_with_map_reduce()                             │
│                                                                     │
│  Dependencies:                                                      │
│  ├── RegulationRetrievalChain (regulation context)                 │
│  ├── MedicalTextSplitter (chunking)                                │
│  ├── create_llm() from llm/factory.py                              │
│  └── PHIDetectionResponse (structured output model)                │
└─────────────────────────────────────────────────────────────────────┘

擴展策略：在現有 Chain 基礎上加入 Tool Workers！
```

---

### 🟢 Phase 1: Single Agent + Tools Foundation (Week 1-2)

**🎯 目標**: 在現有 Chain 架構上加入 Tool Workers，提升速度

**✅ 發布狀態**: 可獨立發布運作

**擴展點**: `chains/processors.py` → 加入 Tool Pre-scan

```text
┌────────────────────────────────────────────────────────────────────┐
│  Phase 1: Enhanced PHIIdentificationChain                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  BEFORE (現有):                                                    │
│  Text ──► LLM (identify_phi_structured) ──► PHI Entities          │
│                    ~1-2s/chunk                                     │
│                                                                    │
│  AFTER (Phase 1):                                                  │
│  Text ──┬──► Tool Workers (parallel) ──► tool_results             │
│         │         ~0.01s                       │                   │
│         └──────────────────────────────────────┤                   │
│                                                ▼                   │
│                    identify_phi_structured(text, tool_results)     │
│                              ~0.3s (有 context!)                   │
│                                                │                   │
│                                                ▼                   │
│                                         PHI Entities               │
│                                                                    │
│  Speed: 1.5s → 0.31s (5x faster!)                                 │
└────────────────────────────────────────────────────────────────────┘
```

**實作計劃 - 擴展現有程式碼**:

```python
# 1. 新增: infrastructure/tools/base_tool.py
class BasePHITool(ABC):
    """Base class for PHI detection tools."""
    
    @abstractmethod
    def scan(self, text: str) -> List[PHIEntity]:
        """Scan text and return PHI entities."""
        pass

# 2. 新增: infrastructure/tools/tool_runner.py  
class ToolRunner:
    """Runs multiple tools in parallel using multiprocessing."""
    
    def __init__(self, tools: List[BasePHITool], num_workers: int = 4):
        self.tools = tools
        self.pool = Pool(num_workers)
    
    def run_all(self, text: str) -> List[PHIEntity]:
        """Run all tools on text and merge results."""
        results = self.pool.map(lambda t: t.scan(text), self.tools)
        return self._merge_results(results)

# 3. 修改: chains/processors.py - 加入 tool_results 參數
def identify_phi_structured(
    text: str,
    context: str,
    llm,
    language: Optional[str] = None,
    tool_results: Optional[List[PHIEntity]] = None  # 新增！
) -> Tuple[List[PHIEntity], List[PHIIdentificationResult]]:
    """Enhanced with tool pre-scan results."""
    
    # Format tool results for prompt
    if tool_results:
        tool_context = format_tool_results(tool_results)
        context = f"{context}\n\n已由工具識別的 PHI:\n{tool_context}"
    
    # 繼續現有邏輯...

# 4. 修改: phi_identification_chain.py - 加入 ToolRunner
class PHIIdentificationChain:
    def __init__(self, ..., tool_runner: Optional[ToolRunner] = None):
        self.tool_runner = tool_runner or ToolRunner([
            RegexPHITool(),
            IDValidatorTool(),
            PhoneTool(),
            SpaCyNERTool()
        ])
    
    def identify_phi(self, text: str, ...) -> Dict[str, Any]:
        # Step 1: Tool pre-scan (parallel, fast)
        tool_results = self.tool_runner.run_all(text)
        
        # Step 2: LLM identification (with tool context)
        return self._identify_phi_direct(
            text, ..., 
            tool_results=tool_results  # 傳遞 tool 結果
        )
```

**Deliverables (擴展現有架構)**:

| File | Action | Description |
|------|--------|-------------|
| `infrastructure/tools/__init__.py` | **新增** | Tool 模組入口 |
| `infrastructure/tools/base_tool.py` | **新增** | Tool 基礎類別 |
| `infrastructure/tools/tool_runner.py` | **新增** | 並行 Tool Runner |
| `infrastructure/tools/regex_phi_tool.py` | **新增** | Regex patterns |
| `infrastructure/tools/id_validator_tool.py` | **新增** | Taiwan ID validation |
| `infrastructure/tools/phone_tool.py` | **新增** | Phone detection |
| `infrastructure/tools/spacy_ner_tool.py` | **新增** | SpaCy NER |
| `chains/processors.py` | **修改** | 加入 tool_results 參數 |
| `phi_identification_chain.py` | **修改** | 整合 ToolRunner |

**Prompt 調整** (修改 `prompts/` 模組):

```python
# prompts/phi_identification.py - 新增支援 tool_results
def get_phi_identification_prompt_with_tools(
    language: str = "en",
    structured: bool = True
) -> str:
    """Prompt that includes tool pre-scan results."""
    
    return """你是 PHI 識別專家。

## 工具預掃描結果
以下是自動工具已識別的 PHI (請確認是否正確):
{tool_results}

## 待分析文本
{text}

## 任務
1. 確認工具結果 (confirmed/rejected)
2. 找出工具漏掉的 PHI (姓名、地址、罕見疾病等)

輸出 JSON 格式的 PHI 清單。
"""
```

**Expected Performance (Phase 1)**:

| Component | Time/Chunk | Notes |
|-----------|------------|-------|
| Tool Workers (parallel) | ~0.01s | 8 workers |
| PHI Agent (Qwen-0.5B) | ~0.3s | With tool context |
| **Total** | **~0.31s** | |

| Metric | Value | vs Pure LLM |
|--------|-------|-------------|
| 1GB Processing | ~8.6 hours | 20x faster |
| PHI Coverage | ~90% | Acceptable |
| F1 Score | ~0.85 | Good start |

**測試指令**:

```bash
# 安裝依賴
pip install spacy dspy-ai
python -m spacy download zh_core_web_sm

# 下載模型
ollama pull qwen2.5:0.5b

# 執行測試
pytest tests/unit/test_agents.py -v
pytest tests/integration/test_agent_pipeline.py -v

# Benchmark
python scripts/benchmark_phase1.py --input data/test/sample_1mb.jsonl
```

---

### 🟡 Phase 2: DSPy Optimization (Week 3-4)

**🎯 目標**: 用 DSPy 優化 Phase 1 的 Prompt，提升準確度和速度

**✅ 發布狀態**: Phase 1 的升級版

**擴展點**: `infrastructure/dspy/` + `prompts/` 模組

```text
┌────────────────────────────────────────────────────────────────────┐
│  Phase 2: DSPy-Optimized Chains                                   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  擴展現有架構，加入 DSPy 優化層：                                    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  DSPy Optimizer Pipeline                                     │ │
│  │                                                              │ │
│  │  1. Load training data (PHI examples)                        │ │
│  │  2. Define PHISignature (input/output schema)                │ │
│  │  3. Run optimization (BootstrapFewShot)                      │ │
│  │  4. Export optimized prompts → prompts/optimized/            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              │                                     │
│                              ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  chains/processors.py (修改)                                 │ │
│  │                                                              │ │
│  │  - 載入 optimized prompts (if exists)                        │ │
│  │  - 使用 few-shot examples                                    │ │
│  │  - 更短的 prompt → 更快的 response                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

**實作計劃 - 擴展現有 DSPy 模組**:

```python
# infrastructure/dspy/phi_signatures.py (新增)
import dspy

class PHISignature(dspy.Signature):
    """Signature for PHI identification with tool context."""
    
    text: str = dspy.InputField(desc="Medical text to analyze")
    tool_results: str = dspy.InputField(desc="Pre-scanned PHI candidates")
    regulation_context: str = dspy.InputField(desc="Regulation requirements")
    
    confirmed_phi: str = dspy.OutputField(desc="Confirmed PHI entities")
    additional_phi: str = dspy.OutputField(desc="PHI missed by tools")

# infrastructure/dspy/phi_optimizer.py (修改現有)
class PHIOptimizer:
    """Optimizes PHI prompts using DSPy."""
    
    def optimize(self, train_data: List[dict]) -> dict:
        """Run optimization and return optimized prompts."""
        
        # Define module
        module = dspy.ChainOfThought(PHISignature)
        
        # Setup optimizer
        optimizer = BootstrapFewShot(
            metric=self.phi_f1_metric,
            max_bootstrapped_demos=3
        )
        
        # Run optimization
        optimized = optimizer.compile(module, trainset=train_data)
        
        # Export prompts
        return self._export_prompts(optimized)
    
    def _export_prompts(self, module) -> dict:
        """Export optimized prompts for use in chains."""
        return {
            "few_shot_examples": module.demos,
            "system_prompt": self._extract_system_prompt(module)
        }

# prompts/phi_identification.py (修改現有)
def get_optimized_phi_prompt(
    language: str = "zh-tw"
) -> str:
    """Load DSPy-optimized prompt if available."""
    
    optimized_path = Path("data/optimized_prompts/phi_prompt.json")
    
    if optimized_path.exists():
        optimized = json.load(optimized_path.open())
        return _format_optimized_prompt(optimized)
    
    # Fallback to manual prompt
    return get_phi_identification_prompt_with_tools(language)
```

**Deliverables (擴展現有模組)**:

| File | Action | Description |
|------|--------|-------------|
| `infrastructure/dspy/phi_signatures.py` | **新增** | DSPy Signatures |
| `infrastructure/dspy/optimizer.py` | **修改** | 加入 export 功能 |
| `infrastructure/dspy/metrics.py` | **修改** | 加入 tool-aware metrics |
| `prompts/phi_identification.py` | **修改** | 載入 optimized prompts |
| `scripts/dspy_optimize.py` | **新增** | CLI 優化腳本 |
| `data/optimized_prompts/` | **新增** | 儲存優化結果 |

**Expected Performance (Phase 2)**:

| Metric | Phase 1 | Phase 2 | Improvement |
|--------|---------|---------|-------------|
| 1GB Processing | ~8.6 hours | ~7 hours | 20% faster |
| F1 Score | 0.85 | 0.90 | +5% |
| Token Usage | 100% | ~70% | 30% less |

---

### 🟠 Phase 3: Multi-Agent with Safety Net (Week 5-6)

**🎯 目標**: 雙 Agent (快 + 精確) + Safety Net，速度與安全兼顧

**✅ 發布狀態**: Phase 2 的升級版，更高準確度

**擴展點**: `infrastructure/agents/` + `chains/map_reduce.py`

```text
┌────────────────────────────────────────────────────────────────────┐
│  Phase 3: Dual Agent with Routing                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  擴展現有架構，加入多模型支援：                                      │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Stage 1: Tool Workers (same as Phase 1) ⚡ ~0.01s           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              │                                     │
│                              ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Stage 2: Smart Router (rule-based) ⚡ ~0.001s               │ │
│  │                                                              │ │
│  │  擴展 llm/factory.py，根據 complexity 選擇模型               │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              │                                     │
│              ┌───────────────┴───────────────┐                    │
│              ▼                               ▼                    │
│  ┌─────────────────────────┐   ┌─────────────────────────┐       │
│  │  Fast Path (85%)        │   │  Precise Path (15%)     │       │
│  │  Qwen-0.5B ⚡ ~0.3s     │   │  Qwen-1.5B ⚡ ~0.8s     │       │
│  │  使用現有 processors.py │   │  使用現有 processors.py │       │
│  └───────────┬─────────────┘   └───────────┬─────────────┘       │
│              │                               │                    │
│              └───────────────┬───────────────┘                    │
│                              ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Result Merger (修改 chains/map_reduce.py)                   │ │
│  │  merge_phi_results() - 已有，加入 confidence weighting       │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

**實作計劃 - 擴展現有程式碼**:

```python
# 1. 修改: llm/factory.py - 支援多模型
def create_llm(
    provider: str = "ollama",
    model_name: Optional[str] = None,
    complexity: str = "normal"  # 新增：fast/normal/precise
) -> BaseChatModel:
    """Create LLM based on complexity requirement."""
    
    if model_name is None:
        model_name = _get_model_for_complexity(complexity)
    
    # ... existing logic ...

def _get_model_for_complexity(complexity: str) -> str:
    """Select model based on complexity."""
    models = {
        "fast": "qwen2.5:0.5b",
        "normal": "qwen2.5:0.5b",
        "precise": "qwen2.5:1.5b"
    }
    return models.get(complexity, "qwen2.5:0.5b")

# 2. 新增: chains/router.py
class ChunkRouter:
    """Routes chunks to appropriate processing path."""
    
    def route(self, text: str, tool_results: List[PHIEntity]) -> str:
        """Determine complexity level for chunk."""
        
        if self._is_complex(text, tool_results):
            return "precise"
        return "fast"
    
    def _is_complex(self, text: str, tool_results: List[PHIEntity]) -> bool:
        # 複雜指標
        indicators = ["罕見", "遺傳", "家族史", "職業病"]
        if any(ind in text for ind in indicators):
            return True
        
        # 低信心結果
        if tool_results and any(e.confidence < 0.7 for e in tool_results):
            return True
        
        return False

# 3. 修改: phi_identification_chain.py
class PHIIdentificationChain:
    def __init__(self, ..., use_routing: bool = False):  # 新增
        self.use_routing = use_routing
        self.router = ChunkRouter() if use_routing else None
    
    def _identify_phi_direct(self, text: str, tool_results: List[PHIEntity], ...):
        # Phase 3: 根據 routing 選擇模型
        if self.use_routing and self.router:
            complexity = self.router.route(text, tool_results)
            llm = create_llm(complexity=complexity)
        else:
            llm = self.llm
        
        # 繼續現有 identify_phi_structured 邏輯
        return identify_phi_structured(text, context, llm, tool_results=tool_results)

# 4. 修改: chains/map_reduce.py - 加入 confidence weighting
def merge_phi_results_weighted(
    results: List[PHIDetectionResponse],
    complexity_levels: List[str]  # 新增
) -> PHIDetectionResponse:
    """Merge results with confidence weighting based on model used."""
    
    all_entities = []
    for result, complexity in zip(results, complexity_levels):
        weight = 1.2 if complexity == "precise" else 1.0
        for entity in result.entities:
            entity.confidence *= weight
            all_entities.append(entity)
    
    # Deduplicate with highest confidence
    return _deduplicate_entities(all_entities)
```

**Deliverables (擴展現有模組)**:

| File | Action | Description |
|------|--------|-------------|
| `infrastructure/llm/factory.py` | **修改** | 加入 complexity 參數 |
| `infrastructure/llm/model_manager.py` | **新增** | VRAM-aware 模型管理 |
| `chains/router.py` | **新增** | Chunk 路由邏輯 |
| `chains/map_reduce.py` | **修改** | 加入 weighted merge |
| `phi_identification_chain.py` | **修改** | 整合 routing |

**Smart Router** (rule-based, 無需 LLM):

```python
class ChunkRouter:
    """Rule-based router - fast and predictable."""

    def route(self, text: str, tool_results: List[PHIEntity]) -> str:
        # Complex content → precise
        if self._has_complex_indicators(text):
            return "precise"

        # Low confidence → precise
        if tool_results and any(e.confidence < 0.7 for e in tool_results):
            return "precise"

        # Many candidates → precise (might have conflicts)
        if len(tool_results) > 10:
            return "precise"

        # Default → fast
        return "fast"

    def _has_complex_indicators(self, text: str) -> bool:
        indicators = ["罕見", "遺傳", "家族史", "職業病", "高齡", "未成年"]
        return any(ind in text for ind in indicators)
```

**Expected Performance (Phase 3)**:

| Route | % | Time/Chunk |
|-------|---|------------|
| Fast Path | 85% | 0.31s |
| Precise Path | 15% | 0.81s |
| **Weighted Avg** | 100% | **~0.39s** |

| Metric | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| 1GB Processing | ~8.6h | ~7h | ~10.8h* |
| F1 Score | 0.85 | 0.90 | 0.93 |
| Coverage | 90% | 92% | 96% |

*Phase 3 slower due to Precise Path, but higher accuracy

---

### 🔵 Phase 4: Batch Optimization + Human Review (Week 7-8)

**🎯 目標**: 批次處理優化 + 人工審核佇列，達到生產品質

**✅ 發布狀態**: 完整生產版本

**擴展點**: `application/processing/batch_processor.py` + 新增 `interface/review_api.py`

```text
┌────────────────────────────────────────────────────────────────────┐
│  Phase 4: Production-Ready Pipeline                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  擴展現有 batch_processor.py：                                     │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Optimized BatchProcessor (修改現有)                         │ │
│  │  • 單次模型載入處理整批 (減少 VRAM swap)                      │ │
│  │  • Async I/O for file operations                             │ │
│  │  • Progress tracking with ETA                                │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              │                                     │
│                              ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Result Classification (新增)                                │ │
│  │                                                              │ │
│  │  High Confidence (>0.9) ────► Direct Output (90%)            │ │
│  │  Medium Confidence ─────────► Secondary Check (8%)           │ │
│  │  Low Confidence (<0.6) ─────► Human Review Queue (2%)        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                              │                                     │
│                              ▼                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Human Review Interface (新增)                               │ │
│  │  • Simple REST API for review UI                             │ │
│  │  • Bulk approve/reject                                       │ │
│  │  • Feedback loop for model improvement                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

**實作計劃 - 擴展現有程式碼**:

```python
# 1. 修改: application/processing/batch_processor.py
class BatchProcessor:
    """Enhanced batch processor with optimization."""
    
    def __init__(self, phi_chain: PHIIdentificationChain, ...):
        self.phi_chain = phi_chain
        self.review_queue = HumanReviewQueue()  # 新增
    
    async def process_batch_optimized(
        self,
        chunks: List[str],
        progress_callback: Optional[Callable] = None
    ) -> BatchResult:
        """Optimized batch processing."""
        
        results = []
        for i, chunk in enumerate(chunks):
            result = await self.phi_chain.identify_phi(chunk)
            
            # Classify result
            classification = self._classify_result(result)
            
            if classification == "low_confidence":
                self.review_queue.add(chunk, result)
            
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, len(chunks))
        
        return BatchResult(results=results, review_queue=self.review_queue)
    
    def _classify_result(self, result: PHIDetectionResponse) -> str:
        avg_confidence = sum(e.confidence for e in result.entities) / len(result.entities)
        
        if avg_confidence > 0.9:
            return "high_confidence"
        elif avg_confidence > 0.6:
            return "medium_confidence"
        else:
            return "low_confidence"

# 2. 新增: application/processing/review_queue.py
class HumanReviewQueue:
    """Queue for chunks requiring human review."""
    
    def __init__(self, storage_path: Path = Path("data/review_queue")):
        self.storage_path = storage_path
        self.items: List[ReviewItem] = []
    
    def add(self, chunk: str, result: PHIDetectionResponse, reason: str = ""):
        item = ReviewItem(
            id=str(uuid.uuid4()),
            chunk=chunk,
            result=result,
            reason=reason,
            created_at=datetime.now()
        )
        self.items.append(item)
        self._persist(item)
    
    def get_pending(self, limit: int = 50) -> List[ReviewItem]:
        return [i for i in self.items if i.status == "pending"][:limit]
    
    def approve(self, item_id: str, corrections: Optional[dict] = None):
        # Update item and optionally log corrections for training
        pass

# 3. 新增: interface/review_api.py
from fastapi import FastAPI, HTTPException
from application.processing.review_queue import HumanReviewQueue

app = FastAPI(title="PHI Review API")
review_queue = HumanReviewQueue()

@app.get("/api/review/pending")
async def get_pending_reviews(limit: int = 50):
    """Get pending review items."""
    return review_queue.get_pending(limit)

@app.post("/api/review/{item_id}/approve")
async def approve_review(item_id: str, corrections: dict = None):
    """Approve a review item with optional corrections."""
    review_queue.approve(item_id, corrections)
    return {"status": "approved"}

@app.post("/api/review/{item_id}/reject")
async def reject_review(item_id: str, reason: str = ""):
    """Reject a review item."""
    review_queue.reject(item_id, reason)
    return {"status": "rejected"}
```

**Deliverables (擴展現有模組)**:

| File | Action | Description |
|------|--------|-------------|
| `application/processing/batch_processor.py` | **修改** | 加入 classification + queue |
| `application/processing/review_queue.py` | **新增** | Human review queue |
| `interface/review_api.py` | **新增** | REST API for review |
| `scripts/benchmark.py` | **新增** | Performance benchmark suite |
| `docs/review-api.md` | **新增** | API documentation |

**Expected Performance (Phase 4 - Final)**:

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|---------|---------|---------|---------|
| 1GB Processing | ~8.6h | ~7h | ~10.8h | ~6h |
| F1 Score | 0.85 | 0.90 | 0.93 | 0.96 |
| Coverage | 90% | 92% | 96% | 99% |
| Human Review | 0% | 0% | 0% | 2% |

---

## 📊 Phase Comparison Summary | 各 Phase 比較

```text
┌────────────────────────────────────────────────────────────────────┐
│  Phase Progression                                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Phase 1: Single Agent + Tools                                     │
│  ├── Speed: ★★★★☆ (8.6h/1GB)                                      │
│  ├── Accuracy: ★★★☆☆ (F1=0.85)                                    │
│  └── Complexity: ★☆☆☆☆                                            │
│                                                                    │
│  Phase 2: + DSPy Optimization                                      │
│  ├── Speed: ★★★★★ (7h/1GB)                                        │
│  ├── Accuracy: ★★★★☆ (F1=0.90)                                    │
│  └── Complexity: ★★☆☆☆                                            │
│                                                                    │
│  Phase 3: + Multi-Agent Router                                     │
│  ├── Speed: ★★★★☆ (10.8h/1GB)                                     │
│  ├── Accuracy: ★★★★★ (F1=0.93)                                    │
│  └── Complexity: ★★★☆☆                                            │
│                                                                    │
│  Phase 4: + Batch Optimization + Human Review                      │
│  ├── Speed: ★★★★★ (6h/1GB)                                        │
│  ├── Accuracy: ★★★★★ (F1=0.96)                                    │
│  └── Complexity: ★★★★☆                                            │
│                                                                    │
│  選擇建議:                                                         │
│  • 快速啟動 → Phase 1                                              │
│  • 平衡選擇 → Phase 2                                              │
│  • 高準確度 → Phase 3                                              │
│  • 生產環境 → Phase 4                                              │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Tool Worker Architecture | 工具 Worker 架構

### Why Multiprocessing? | 為何用多進程？

```text
Problem: Python GIL prevents true parallelism for CPU-bound tasks
Solution: multiprocessing creates separate processes, each with own GIL

┌─────────────────────────────────────────────────────────────┐
│  Tool Worker Pool (multiprocessing)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Main Process                                               │
│       │                                                     │
│       ├──► Worker Process 1 (has own GIL)                  │
│       │    └── SpaCy NER + Regex                           │
│       │                                                     │
│       ├──► Worker Process 2 (has own GIL)                  │
│       │    └── SpaCy NER + Regex                           │
│       │                                                     │
│       ├──► Worker Process 3 (has own GIL)                  │
│       │    └── SpaCy NER + Regex                           │
│       │                                                     │
│       └──► Worker Process N (has own GIL)                  │
│            └── SpaCy NER + Regex                           │
│                                                             │
│  Each worker: ~200MB memory for SpaCy model                │
│  Recommended: 4-8 workers for typical machine              │
└─────────────────────────────────────────────────────────────┘
```

### Worker Implementation | Worker 實作

```python
# infrastructure/tools/tool_worker.py
import multiprocessing as mp
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class WorkerTask:
    text: str
    chunk_id: str
    tools: List[str]

@dataclass  
class WorkerResult:
    chunk_id: str
    entities: List[Dict[str, Any]]
    processing_time: float

class ToolWorkerPool:
    """Multiprocessing worker pool for CPU-bound tool execution."""
    
    def __init__(self, num_workers: int = None, preload_models: bool = True):
        self.num_workers = num_workers or max(1, mp.cpu_count() - 1)
        self.preload = preload_models
        self._pool = None
        self._initialized = False
    
    def start(self):
        """Initialize worker pool with preloaded models."""
        if self._initialized:
            return
        
        # Use spawn to ensure clean processes on Windows
        ctx = mp.get_context('spawn')
        self._pool = ctx.Pool(
            self.num_workers,
            initializer=_worker_init if self.preload else None
        )
        self._initialized = True
    
    def process_batch(self, tasks: List[WorkerTask]) -> List[WorkerResult]:
        """Process batch of tasks in parallel."""
        if not self._initialized:
            self.start()
        
        results = self._pool.map(_worker_process, tasks)
        return results
    
    def shutdown(self):
        """Gracefully shutdown worker pool."""
        if self._pool:
            self._pool.close()
            self._pool.join()
            self._initialized = False

# Worker functions (must be at module level for pickling)
_worker_nlp = None
_worker_tools = None

def _worker_init():
    """Initialize models in worker process."""
    global _worker_nlp, _worker_tools
    import spacy
    _worker_nlp = spacy.load("zh_core_web_sm")
    _worker_tools = _load_all_tools()

def _worker_process(task: WorkerTask) -> WorkerResult:
    """Process single task in worker."""
    import time
    start = time.time()
    
    entities = []
    for tool_name in task.tools:
        tool = _worker_tools[tool_name]
        result = tool.run(task.text, nlp=_worker_nlp)
        entities.extend(result)
    
    return WorkerResult(
        chunk_id=task.chunk_id,
        entities=entities,
        processing_time=time.time() - start
    )
```

---

## 🔧 Technical Details | 技術細節

### Model Selection | 模型選擇

| Model | Params | Chinese | Speed | Memory | Recommendation |
|-------|--------|---------|-------|--------|----------------|
| **Qwen2.5-0.5B** | 500M | ★★★★★ | ⚡⚡⚡⚡⚡ | 1GB | 🏆 Best for screening |
| **Qwen2.5-1.5B** | 1.5B | ★★★★★ | ⚡⚡⚡⚡ | 2GB | ✅ Balanced choice |
| Phi-3-mini | 3.8B | ★★★☆☆ | ⚡⚡⚡ | 3GB | English-focused |
| TinyLlama | 1.1B | ★★☆☆☆ | ⚡⚡⚡⚡ | 1GB | English only |
| Gemma-2B | 2B | ★★★☆☆ | ⚡⚡⚡ | 2GB | Multilingual |
| MiniMind2 | 104M | ★★☆☆☆ | ⚡⚡⚡⚡⚡ | <1GB | Ultra-fast, low accuracy |

### SpaCy Model Selection | SpaCy 模型選擇

| Model | Language | Size | Speed | Accuracy |
|-------|----------|------|-------|----------|
| `zh_core_web_sm` | Chinese | 46MB | ⚡⚡⚡⚡⚡ | ★★★☆☆ |
| `zh_core_web_md` | Chinese | 75MB | ⚡⚡⚡⚡ | ★★★★☆ |
| `zh_core_web_lg` | Chinese | 575MB | ⚡⚡⚡ | ★★★★★ |
| `en_core_web_sm` | English | 12MB | ⚡⚡⚡⚡⚡ | ★★★☆☆ |

**Recommendation**: Use `zh_core_web_sm` for speed, fall back to LLM for accuracy

### PHI Coverage by Method | 各方法 PHI 覆蓋率

| PHI Type | Regex | SpaCy | LLM Needed? |
|----------|-------|-------|-------------|
| Taiwan ID | ✅ 99% | ❌ | Rarely |
| Phone | ✅ 95% | ❌ | Rarely |
| Email | ✅ 99% | ❌ | No |
| Date | ✅ 80% | ✅ 95% | Rarely |
| Name | ❌ | ✅ 85% | Sometimes |
| Address | ❌ | 🟡 60% | Often |
| Organization | ❌ | ✅ 80% | Sometimes |
| Medical Terms | ❌ | ❌ | Always |
| Rare Diseases | ❌ | ❌ | Always |
| Age >90 | ✅ 90% | ❌ | Rarely |

---

## 📈 Success Metrics | 成功指標

### Performance Targets | 效能目標

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Throughput | 0.04 row/s | 10 row/s | ❌ 250x gap |
| 1GB Processing | ~170 days | 10 min | ❌ |
| Memory Usage | 4GB | <8GB | ✅ |
| Accuracy (F1) | 95% | >90% | ✅ |

### Accuracy Targets | 準確度目標

| PHI Type | Target Precision | Target Recall |
|----------|------------------|---------------|
| ID Numbers | >99% | >98% |
| Phone/Email | >99% | >95% |
| Names | >95% | >90% |
| Dates | >98% | >95% |
| Addresses | >90% | >85% |
| Medical Terms | >90% | >85% |

---

## 🔄 Dependencies | 相依性

### New Dependencies to Add | 新增相依套件

```toml
# pyproject.toml additions
spacy = "^3.8"
# Download model: python -m spacy download zh_core_web_sm
```

### Ollama Models to Pull | 需要的 Ollama 模型

```bash
# Fast screening model
ollama pull qwen2.5:0.5b

# Balanced model (recommended)
ollama pull qwen2.5:1.5b

# Existing models (keep)
ollama pull qwen2.5:7b
ollama pull jingyaogong/minimind2
```

---

## 📚 References | 參考資料

- [SpaCy Chinese Models](https://spacy.io/models/zh)
- [Qwen2.5 Model Card](https://huggingface.co/Qwen/Qwen2.5-0.5B)
- [LangChain Tools](https://python.langchain.com/docs/modules/tools/)
- [HIPAA Safe Harbor PHI Types](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html)

---

## 📋 Extension Summary | 擴展總覽

> **核心原則**：基於現有 Chain 架構擴展，不重寫！

### 現有檔案擴展點

| 現有檔案 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|---------|---------|---------|---------|---------|
| `chains/processors.py` | 加入 `tool_results` 參數 | 載入 optimized prompts | - | - |
| `chains/map_reduce.py` | - | - | 加入 weighted merge | - |
| `phi_identification_chain.py` | 整合 `ToolRunner` | - | 整合 routing | - |
| `llm/factory.py` | - | - | 加入 `complexity` 參數 | - |
| `dspy/optimizer.py` | - | 加入 export 功能 | - | - |
| `dspy/metrics.py` | - | 加入 tool-aware metrics | - | - |
| `prompts/phi_identification.py` | 加入 tool prompt | 載入 DSPy prompts | - | - |
| `batch_processor.py` | - | - | - | 加入 classification |

### 新增檔案

| Phase | 新增檔案 | 用途 |
|-------|---------|------|
| **Phase 1** | `infrastructure/tools/__init__.py` | Tool 模組入口 |
| | `infrastructure/tools/base_tool.py` | Tool 基礎類別 |
| | `infrastructure/tools/tool_runner.py` | 並行 Tool Runner |
| | `infrastructure/tools/regex_phi_tool.py` | Regex patterns |
| | `infrastructure/tools/id_validator_tool.py` | Taiwan ID validation |
| | `infrastructure/tools/phone_tool.py` | Phone detection |
| | `infrastructure/tools/spacy_ner_tool.py` | SpaCy NER |
| **Phase 2** | `infrastructure/dspy/phi_signatures.py` | DSPy Signatures |
| | `scripts/dspy_optimize.py` | CLI 優化腳本 |
| | `data/optimized_prompts/` | 儲存優化結果 |
| **Phase 3** | `chains/router.py` | Chunk 路由邏輯 |
| | `infrastructure/llm/model_manager.py` | VRAM-aware 模型管理 |
| **Phase 4** | `application/processing/review_queue.py` | Human review queue |
| | `interface/review_api.py` | REST API for review |
| | `scripts/benchmark.py` | Performance benchmark |
| | `docs/review-api.md` | API documentation |

### Phase 1 快速開始

```bash
# 1. 安裝依賴
pip install spacy
python -m spacy download zh_core_web_sm

# 2. 下載模型
ollama pull qwen2.5:0.5b

# 3. 開始開發 (依序)
# Step 1: 建立 Tool 基礎
touch core/infrastructure/tools/__init__.py
touch core/infrastructure/tools/base_tool.py
touch core/infrastructure/tools/tool_runner.py

# Step 2: 實作各 Tool
touch core/infrastructure/tools/regex_phi_tool.py
touch core/infrastructure/tools/id_validator_tool.py

# Step 3: 修改現有 Chain
# 編輯 chains/processors.py - 加入 tool_results 參數
# 編輯 phi_identification_chain.py - 整合 ToolRunner

# Step 4: 測試
pytest tests/unit/test_tools.py -v
pytest tests/integration/test_tool_chain.py -v
```

---

**Last Updated**: 2026-02-20
**Status**: 📋 Planning Phase (Core) | ✅ Web UI Complete
**Owner**: Medical Deidentification Team

---

## ✅ Completed Milestones | 已完成里程碑

### Web 應用平台 (2026-01 ~ 2026-02)

- ✅ Frontend DDD 架構 (React + Vite + TanStack Query)
- ✅ Backend 模組化 (FastAPI + DDD services)
- ✅ PHI 設定獨立服務 (導入/導出/預設範本)
- ✅ LLM 設定管理 (Ollama/OpenAI/Azure provider)
- ✅ 完整 Web 功能 (Settings/Reports/Results/DataPreview/Tasks)
- ✅ 單元測試 68 個 (Vitest + RTL)
- ✅ E2E 測試 58 個 (Playwright)
- ✅ Systemd 部署腳本
