# Active Context

## Current Goals

- 準備增加 Ollama 本地 LLM 支援。因 OpenAI API 極度緩慢（>5分鐘/請求），需要本地替代方案提升效率和隱私性。將修改 LLMProvider 加入 "ollama"，新增 OLLAMA_MODELS list，實現 _create_ollama_llm() 函數。

## Current Blockers

- None yet