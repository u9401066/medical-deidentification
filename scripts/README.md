# Scripts | 腳本工具

此目錄包含各種輔助腳本。

## 目錄結構

```
scripts/
├── check_dependencies.py      # 檢查套件依賴
├── phi_evaluator.py           # PHI 識別效能評估工具
└── generators/                # 測試資料生成器
    ├── generate_test_data_complex_phi.py
    ├── generate_test_data_excel.py
    ├── generate_test_data_with_phi_tags.py
    └── phi_tag_parser.py
```

## 使用方式

### 檢查依賴
```bash
python scripts/check_dependencies.py
```

### PHI 評估
```bash
python scripts/phi_evaluator.py
```

### 生成測試資料
```bash
python scripts/generators/generate_test_data_excel.py
```
