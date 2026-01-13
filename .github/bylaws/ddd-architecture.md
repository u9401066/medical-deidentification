# 子法：DDD 架構規範

> 父法：CONSTITUTION.md 第一章

## 第 1 條：目錄結構

```
core/
├── domain/                    # 領域層（核心）
│   ├── entities.py            # 實體
│   ├── value_objects.py       # 值物件
│   ├── aggregates.py          # 聚合根
│   └── phi_types.py           # 領域定義
│
├── application/               # 應用層
│   └── processing/            # 用例處理
│
├── infrastructure/            # 基礎設施層
│   ├── llm/                   # LLM 服務
│   ├── loader/                # 資料載入
│   ├── output/                # 輸出處理
│   ├── rag/                   # RAG 服務
│   └── tools/                 # 工具
│
└── interface/                 # 呈現層（API）
```

## 第 2 條：依賴方向

```
interface → application → domain
                ↓
          infrastructure
```

- domain 不依賴任何外層
- infrastructure 實作 domain 定義的介面

## 第 3 條：命名慣例

| 類型 | 命名規則 | 範例 |
|------|----------|------|
| Entity | 名詞單數 | `MedicalRecord`, `PHIEntity` |
| Value Object | 描述性名詞 | `IdentificationResult`, `MaskingConfig` |
| Use Case | 動詞 + 名詞 | `ProcessDocument`, `IdentifyPHI` |

---

## 第 4 條：模組化規範

> 依據憲法第 7.3 條「主動重構原則」訂定

### 4.1 檔案長度限制

| 類型 | 建議上限 | 硬性上限 | 超過時動作 |
|------|----------|----------|------------|
| 單一檔案 | 200 行 | 400 行 | 必須拆分 |
| 類別 (Class) | 150 行 | 300 行 | 提取子類別或組合 |
| 函數 (Function) | 30 行 | 50 行 | 提取私有方法 |
| 模組 (目錄) | 10 檔案 | 15 檔案 | 建立子模組 |

### 4.2 重構觸發條件

AI 應在以下情況 **主動建議** 重構：

| 觸發條件 | 建議動作 |
|----------|----------|
| 檔案超過 200 行 | 「這個檔案有點長，建議拆分成...」 |
| 函數超過 30 行 | 「這個函數可以提取出...」 |
| 圈複雜度 > 10 | 「這段邏輯較複雜，建議...」 |
| 重複程式碼 | 「發現重複模式，建議抽取為...」 |
| 跨層依賴 | 「這裡違反了 DDD 分層，應該...」 |

---

## 第 5 條：重構安全網

### 5.1 重構前必須

1. ✅ 確保有測試覆蓋（覆蓋率 ≥ 70%）
2. ✅ 執行現有測試確認通過
3. ✅ 記錄重構原因到 `decisionLog.md`

### 5.2 重構後必須

1. ✅ 執行全部測試
2. ✅ 檢查架構是否仍符合 DDD
3. ✅ 更新相關文檔
4. ✅ 更新 `memory-bank/architect.md`

---

*本子法版本：v1.0.0*
