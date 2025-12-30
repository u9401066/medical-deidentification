# PHI De-identification Benchmark 建立計畫

## 📊 目標

建立一套完整的 PHI 去識別化評估框架，涵蓋：
- 英文黃金標準資料集
- 中文醫療資料集
- 合成資料壓力測試
- 自動化評估 Pipeline

---

## 1️⃣ 黃金標準資料集 (Gold Standards)

### 1.1 i2b2 2006 De-identification Challenge ⭐ 必測

| 項目 | 說明 |
|------|------|
| **規模** | 889 份出院摘要 (Discharge Summaries) |
| **標註** | HIPAA 18 類 PHI (NAME, DATE, LOCATION, PHONE, ID 等) |
| **地位** | 幾乎所有去識別化論文的基準 |
| **取得** | [DBMI Data Portal (n2c2)](https://portal.dbmi.hms.harvard.edu/) |
| **需求** | 簽署 Data Use Agreement (DUA) |

**預期指標 (SOTA 參考)**：
- ClinicalBERT: F1 ≈ 97-98%
- Our Target: F1 ≥ 85%

### 1.2 i2b2 2014 De-identification Challenge

| 項目 | 說明 |
|------|------|
| **規模** | 1,304 份病歷 |
| **特點** | 更多樣的 PHI 格式，更貼近真實情境 |
| **取得** | 同 n2c2 Portal |

### 1.3 申請流程

```bash
# 1. 註冊 n2c2 Portal
https://portal.dbmi.hms.harvard.edu/

# 2. 申請 i2b2 De-identification datasets
# 3. 簽署 DUA (約 1-2 週審核)
# 4. 下載資料集
```

---

## 2️⃣ 中文資料集 (Chinese Datasets)

### 2.1 CBLUE CMeEE (Chinese Medical Entity Extraction)

| 項目 | 說明 |
|------|------|
| **來源** | [GitHub - CBLUE](https://github.com/CBLUEbenchmark/CBLUE) |
| **內容** | 中文醫療實體識別 |
| **可用欄位** | 醫療機構、部位、疾病、藥物 |
| **用途** | 測試中文醫療語境理解能力 |

**測試重點**：
- 避免將「醫療名詞」誤判為「人名」
- 中文分詞準確度
- 機構名稱識別

### 2.2 下載與準備

```bash
# Clone CBLUE
git clone https://github.com/CBLUEbenchmark/CBLUE.git

# CMeEE 資料位置
CBLUE/datasets/CMeEE/
├── CMeEE_train.json
├── CMeEE_dev.json
└── CMeEE_test.json
```

---

## 3️⃣ 合成資料生成 (Synthetic Data)

### 3.1 Synthea - 合成病患生成器

| 項目 | 說明 |
|------|------|
| **來源** | [GitHub - Synthea](https://github.com/synthetichealth/synthea) |
| **語言** | Java |
| **輸出** | HL7 FHIR / C-CDA 標準病歷 |
| **優點** | 完整生命週期病歷，結構化 |

**使用方式**：
```bash
# 安裝 Synthea
git clone https://github.com/synthetichealth/synthea.git
cd synthea
./gradlew build

# 生成 1000 份病患資料
./run_synthea -p 1000

# 輸出位置
output/fhir/*.json
```

**測試計畫**：
- 生成 10,000 份假病歷
- 驗證 PHI Pipeline 100% 抓取率
- 測試處理速度 (throughput)

### 3.2 Microsoft Presidio Evaluator

| 項目 | 說明 |
|------|------|
| **來源** | [GitHub - Presidio Research](https://github.com/microsoft/presidio-research) |
| **功能** | 假資料生成 + 評估框架 |
| **整合** | Faker + 模板 + F1 計算 |

**安裝**：
```bash
pip install presidio-evaluator
```

**使用**：
```python
from presidio_evaluator import InputSample
from presidio_evaluator.evaluation import Evaluator

# 生成測試資料
samples = InputSample.from_faker(size=1000)

# 評估
evaluator = Evaluator(model=your_model)
results = evaluator.evaluate_all(samples)
print(results.to_df())
```

---

## 4️⃣ 台灣在地化資料生成

由於公開的繁體中文醫療 PHI 資料集幾乎不存在，需要自行生成。

### 4.1 台灣 PHI 生成器設計

```python
# scripts/generators/taiwan_phi_generator.py

from faker import Faker
import random

fake_tw = Faker('zh_TW')

class TaiwanPHIGenerator:
    """台灣醫療 PHI 生成器"""
    
    def generate_name(self):
        """生成台灣姓名"""
        surnames = ['王', '李', '張', '陳', '林', '黃', '吳', '劉', '楊', '蔡']
        return random.choice(surnames) + fake_tw.first_name()
    
    def generate_taiwan_id(self):
        """生成符合格式的台灣身分證字號 (假的)"""
        letters = 'ABCDEFGHJKLMNPQRSTUVXYWZIO'
        return random.choice(letters) + str(random.randint(100000000, 299999999))
    
    def generate_phone(self):
        """生成台灣電話"""
        prefixes = ['0912', '0922', '0932', '0952', '0972', '0982']
        return f"{random.choice(prefixes)}-{random.randint(100,999)}-{random.randint(100,999)}"
    
    def generate_address(self):
        """生成台灣地址"""
        cities = ['台北市', '新北市', '桃園市', '台中市', '台南市', '高雄市']
        districts = ['中正區', '大安區', '信義區', '北區', '南區', '東區']
        return f"{random.choice(cities)}{random.choice(districts)}XX路XX號"
    
    def generate_hospital(self):
        """生成醫院名稱"""
        prefixes = ['台大', '榮總', '長庚', '馬偕', '國泰', '新光', '亞東']
        types = ['醫院', '醫學中心', '診所']
        return f"{random.choice(prefixes)}{random.choice(types)}"
    
    def generate_mrn(self):
        """生成病歷號"""
        return f"{random.randint(10000000, 99999999)}"
    
    def generate_medical_record(self):
        """生成完整的假病歷 (含標註)"""
        name = self.generate_name()
        taiwan_id = self.generate_taiwan_id()
        phone = self.generate_phone()
        address = self.generate_address()
        hospital = self.generate_hospital()
        mrn = self.generate_mrn()
        dob = fake_tw.date_of_birth(minimum_age=20, maximum_age=80)
        
        text = f"""
病患姓名：{name}
身分證字號：{taiwan_id}
出生日期：{dob.strftime('%Y年%m月%d日')}
聯絡電話：{phone}
住址：{address}
就診醫院：{hospital}
病歷號：{mrn}

主訴：病患{name}因持續頭痛一週前來{hospital}就診。
"""
        
        annotations = [
            {"text": name, "type": "NAME", "count": 2},
            {"text": taiwan_id, "type": "ID"},
            {"text": dob.strftime('%Y年%m月%d日'), "type": "DATE"},
            {"text": phone, "type": "PHONE"},
            {"text": address, "type": "LOCATION"},
            {"text": hospital, "type": "FACILITY", "count": 2},
            {"text": mrn, "type": "ID"},
        ]
        
        return {
            "text": text,
            "annotations": annotations
        }
```

### 4.2 生成測試資料集

```bash
# 生成 1000 份台灣假病歷
python scripts/generators/generate_taiwan_phi_dataset.py --count 1000 --output data/benchmark/taiwan_phi_1000.json
```

---

## 5️⃣ 評估 Pipeline 設計

### 5.1 評估指標

| 指標 | 計算方式 | 說明 |
|------|----------|------|
| **Precision** | TP / (TP + FP) | 避免過度檢測 |
| **Recall** | TP / (TP + FN) | 避免漏檢 (最重要!) |
| **F1 Score** | 2 * P * R / (P + R) | 綜合指標 |
| **Exact Match** | 完全匹配率 | 嚴格評估 |
| **Partial Match** | 部分匹配率 | 寬鬆評估 |

### 5.2 評估腳本架構

```
scripts/
├── benchmark/
│   ├── __init__.py
│   ├── evaluator.py          # 核心評估器
│   ├── data_loader.py        # 資料載入 (i2b2, CBLUE, 自訂)
│   ├── metrics.py            # 指標計算
│   └── report_generator.py   # 報告生成
├── evaluate_i2b2.py          # i2b2 評估入口
├── evaluate_cblue.py         # CBLUE 評估入口
├── evaluate_synthea.py       # Synthea 評估入口
└── evaluate_taiwan.py        # 台灣資料評估入口
```

### 5.3 自動化評估流程

```bash
# 完整 benchmark 流程
make benchmark

# 或分步執行
python scripts/evaluate_i2b2.py --model granite4:1b --split test
python scripts/evaluate_cblue.py --model granite4:1b --task CMeEE
python scripts/evaluate_taiwan.py --model granite4:1b --dataset taiwan_phi_1000
```

---

## 6️⃣ 實施計畫 (Timeline)

### Phase 1: 基礎建設 (Week 1)
- [ ] 建立 `scripts/benchmark/` 評估框架
- [ ] 實作台灣 PHI 生成器
- [ ] 生成 1000 份台灣假病歷

### Phase 2: 合成資料評估 (Week 2)
- [ ] 整合 Presidio Evaluator
- [ ] 設定 Synthea 生成流程
- [ ] 跑 10,000 份合成資料評估

### Phase 3: 黃金標準評估 (Week 3-4)
- [ ] 申請 i2b2 資料集 (DUA)
- [ ] 下載並準備 CBLUE CMeEE
- [ ] 實作 i2b2 格式解析器

### Phase 4: 報告與優化 (Week 5)
- [ ] 生成完整 Benchmark 報告
- [ ] 分析弱點並優化 Prompt
- [ ] 文件化最佳實踐

---

## 7️⃣ 目標指標

| 資料集 | 目標 F1 | SOTA F1 | 備註 |
|--------|---------|---------|------|
| i2b2 2006 | ≥ 85% | 97-98% | 英文基準 |
| i2b2 2014 | ≥ 85% | 95-97% | 英文進階 |
| CBLUE CMeEE | ≥ 70% | 85%+ | 中文醫療實體 |
| Taiwan Synthetic | ≥ 95% | N/A | 自訂資料 |
| Synthea | ≥ 99% | N/A | 結構化資料 |

---

## 📚 參考資源

- [i2b2/n2c2 Portal](https://portal.dbmi.hms.harvard.edu/)
- [CBLUE Benchmark](https://github.com/CBLUEbenchmark/CBLUE)
- [Synthea](https://github.com/synthetichealth/synthea)
- [Presidio Research](https://github.com/microsoft/presidio-research)
- [Clinical NLP Workshop](https://clinical-nlp.github.io/)
