---
name: test-generator
description: Generate test files for new code including unit, integration, and e2e tests. Triggers: test, 產生測試, generate test, 測試, 寫測試.
---

# 測試生成技能

## 描述

為新程式碼自動產生測試檔案。

## 觸發條件

- 「generate tests」「產生測試」「寫測試」
- 新增功能後

## 測試類型

### Unit Tests（單元測試）
- 位置：`tests/unit/`
- 測試單一函數/類別
- Mock 外部依賴

### Integration Tests（整合測試）
- 位置：`tests/integration/`
- 測試模組間互動
- 使用真實依賴（測試資料庫等）

### E2E Tests（端到端測試）
- 位置：`tests/e2e/`
- 測試完整使用者流程

## 命名規範

```
test_{module_name}.py
  └─ test_{function_name}_{scenario}
  └─ test_{function_name}_when_{condition}
```

## 輸出格式

```
🧪 測試生成

目標：core/domain/phi_types.py

產生的測試檔案：
  ✅ tests/unit/test_phi_types.py
    └─ test_phi_type_validation
    └─ test_phi_type_from_string
    └─ test_phi_type_invalid_input

  ✅ tests/integration/test_phi_detection.py
    └─ test_detect_phi_in_text
    └─ test_detect_multiple_phi_types

測試覆蓋率預估：85%

下一步：執行 `pytest tests/unit/test_phi_types.py -v`
```
