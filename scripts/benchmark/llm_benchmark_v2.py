#!/usr/bin/env python3
"""
LLM PHI Detection Benchmark V2 - 使用專案架構
==============================================

與 v1 的差異：
- ✅ 使用專案的 PHIDetectionResponse 結構化輸出
- ✅ 使用專案的 LLM Factory (LangChain integration)
- ✅ 支援 Ollama structured output
- ✅ 輸出可直接用於後續處理 (PHIEntity)

用法：
    # 簡單案例
    python scripts/benchmark/llm_benchmark_v2.py --models "llama3.1:8b,phi4:14b"
    
    # 複雜擬真案例
    python scripts/benchmark/llm_benchmark_v2.py --realistic --models "llama3.3:70b"
"""

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.domain.phi_identification_models import PHIDetectionResponse
from core.infrastructure.llm.config import LLMConfig
from core.infrastructure.llm.factory import create_structured_output_llm


# =============================================================================
# PHI 標記解析器 (支援複雜擬真案例)
# =============================================================================

def parse_phi_tags(text: str) -> list[dict]:
    """從文本中解析 PHI 標記"""
    pattern = r'【PHI:(\w+):?(\w*)】([^【]+?)【/PHI】'
    matches = []
    for match in re.finditer(pattern, text):
        matches.append({
            'type': match.group(1),
            'text': match.group(3),
            'id': match.group(2) if match.group(2) else None,
        })
    return matches


def remove_phi_tags(text: str) -> str:
    """移除 PHI 標記，只保留內容"""
    pattern = r'【PHI:\w+:?\w*】([^【]+?)【/PHI】'
    return re.sub(pattern, r'\1', text)


def load_realistic_test_cases(excel_path: str) -> list[dict]:
    """從 PHI 標記的 Excel 檔案載入測試案例"""
    try:
        import openpyxl
    except ImportError:
        print("❌ 需要安裝 openpyxl: pip install openpyxl")
        return []
    
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    
    test_cases = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        
        case_id = row[0]
        text_parts = []
        for col_idx in range(1, 5):
            if col_idx < len(row) and row[col_idx]:
                text_parts.append(str(row[col_idx]))
        
        full_text_with_tags = ' '.join(text_parts)
        expected_phi = parse_phi_tags(full_text_with_tags)
        clean_text = remove_phi_tags(full_text_with_tags)
        
        test_cases.append({
            "id": case_id,
            "text": clean_text,
            "expected_phi": expected_phi,
        })
    
    return test_cases


# =============================================================================
# 簡單測試案例
# =============================================================================

TEST_CASES = [
    {
        "id": "case_001",
        "text": "患者張三，男性，45歲，住院號：A123456，於2024年3月15日入院。",
        "expected_phi": [
            {"text": "張三", "type": "NAME"},
            {"text": "45歲", "type": "AGE"},
            {"text": "A123456", "type": "MEDICAL_RECORD_NUMBER"},
            {"text": "2024年3月15日", "type": "DATE"},
        ],
    },
    {
        "id": "case_002",
        "text": "病人李小明(身分證字號：A123456789)，電話0912-345-678，email: test@example.com",
        "expected_phi": [
            {"text": "李小明", "type": "NAME"},
            {"text": "A123456789", "type": "ID"},
            {"text": "0912-345-678", "type": "PHONE"},
            {"text": "test@example.com", "type": "EMAIL"},
        ],
    },
    {
        "id": "case_003",
        "text": "王醫師診斷：患者陳美玲，女，出生日期1965/08/20，住址：台北市信義區松仁路100號5樓",
        "expected_phi": [
            {"text": "王醫師", "type": "NAME"},
            {"text": "陳美玲", "type": "NAME"},
            {"text": "1965/08/20", "type": "DATE"},
            {"text": "台北市信義區松仁路100號5樓", "type": "LOCATION"},
        ],
    },
    {
        "id": "case_004",
        "text": "轉診單：台大醫院神經內科林志明主治醫師，病歷號M2024001234，健保卡號A123456789",
        "expected_phi": [
            {"text": "台大醫院", "type": "HOSPITAL_NAME"},
            {"text": "林志明", "type": "NAME"},
            {"text": "M2024001234", "type": "MEDICAL_RECORD_NUMBER"},
            {"text": "A123456789", "type": "INSURANCE_NUMBER"},
        ],
    },
    {
        "id": "case_005",
        "text": "92歲高齡患者黃老先生，因罕見疾病Hutchinson-Gilford早衰症候群就診",
        "expected_phi": [
            {"text": "92歲", "type": "AGE_OVER_89"},
            {"text": "黃老先生", "type": "NAME"},
            {"text": "Hutchinson-Gilford早衰症候群", "type": "RARE_DISEASE"},
        ],
    },
]


# =============================================================================
# Benchmark 類
# =============================================================================

@dataclass
class BenchmarkResult:
    """單一模型的測試結果"""
    model: str
    total_cases: int = 0
    passed_cases: int = 0
    
    # 效能指標
    total_time_sec: float = 0.0
    avg_latency_sec: float = 0.0
    
    # 正確率指標
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    
    # 詳細結果
    case_results: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    
    # 結構化輸出成功率
    structured_output_success: int = 0
    structured_output_failures: int = 0
    
    def calculate_metrics(self):
        """計算 Precision/Recall/F1"""
        if self.true_positives + self.false_positives > 0:
            self.precision = self.true_positives / (self.true_positives + self.false_positives)
        if self.true_positives + self.false_negatives > 0:
            self.recall = self.true_positives / (self.true_positives + self.false_negatives)
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)


class StructuredBenchmark:
    """使用專案架構的 Benchmark"""
    
    # PHI 偵測 Prompt (與專案一致)
    SYSTEM_PROMPT = """你是一位醫療資料去識別化專家。
請識別文本中所有的個人健康資訊(PHI)，包括但不限於：

- NAME: 姓名、暱稱
- AGE: 年齡 (89歲以下)
- AGE_OVER_89: 高齡 (90歲以上)
- DATE: 日期、時間
- PHONE: 電話號碼
- EMAIL: 電子郵件
- ID: 身分證字號、護照號碼
- MEDICAL_RECORD_NUMBER: 病歷號
- INSURANCE_NUMBER: 健保卡號
- LOCATION: 地址、地點
- HOSPITAL_NAME: 醫院名稱
- RARE_DISEASE: 罕見疾病名稱

請精確擷取 PHI 文字，不要擷取整段句子。"""

    def __init__(self, base_url: str, timeout: float = 120.0):
        self.base_url = base_url
        self.timeout = timeout
        
    def create_llm_config(self, model: str) -> LLMConfig:
        """為指定模型創建 LLM 配置"""
        return LLMConfig(
            provider="ollama",
            model_name=model,
            temperature=0.0,
            api_base=self.base_url,  # 使用 api_base 而非 base_url
            timeout=self.timeout,
        )
    
    def benchmark_model(
        self, 
        model: str, 
        test_cases: list[dict] | None = None
    ) -> BenchmarkResult:
        """測試單一模型 (使用結構化輸出)"""
        if test_cases is None:
            test_cases = TEST_CASES
        
        result = BenchmarkResult(model=model)
        result.total_cases = len(test_cases)
        
        print(f"\n{'='*60}")
        print(f"🧪 測試模型: {model} (Structured Output)")
        print(f"{'='*60}")
        
        # 創建結構化輸出 LLM
        config = self.create_llm_config(model)
        try:
            structured_llm = create_structured_output_llm(
                config=config,
                schema=PHIDetectionResponse
            )
        except Exception as e:
            print(f"❌ 無法創建結構化 LLM: {e}")
            result.errors.append({"error": str(e)})
            return result
        
        for case in test_cases:
            case_id = case["id"]
            text = case["text"]
            expected = case["expected_phi"]
            
            print(f"\n  📝 {case_id}: {text[:50]}...")
            
            # 構建 prompt
            prompt = f"{self.SYSTEM_PROMPT}\n\n醫療文本：\n{text}"
            
            # 呼叫結構化 LLM
            start = time.perf_counter()
            try:
                response: PHIDetectionResponse = structured_llm.invoke(prompt)
                latency = time.perf_counter() - start
                result.structured_output_success += 1
                
                # 從結構化輸出提取 PHI
                detected = [
                    {"text": e.entity_text, "type": e.phi_type.value if e.phi_type else "UNKNOWN"}
                    for e in response.entities
                ]
                
            except Exception as e:
                latency = time.perf_counter() - start
                result.structured_output_failures += 1
                result.errors.append({"case_id": case_id, "error": str(e)})
                print(f"     ❌ 結構化輸出失敗: {e}")
                continue
            
            # 計算 TP/FP/FN
            tp, fp, fn = self.compare_phi(expected, detected)
            result.true_positives += tp
            result.false_positives += fp
            result.false_negatives += fn
            result.total_time_sec += latency
            
            # 記錄結果
            case_result = {
                "case_id": case_id,
                "latency_sec": latency,
                "expected_count": len(expected),
                "detected_count": len(detected),
                "tp": tp, "fp": fp, "fn": fn,
                "detected_entities": detected,  # 保留結構化輸出
            }
            result.case_results.append(case_result)
            
            # 顯示結果
            if fn == 0 and fp == 0:
                print(f"     ✅ TP={tp} FP={fp} FN={fn} | {latency:.2f}s")
            elif fn == 0:
                print(f"     ⚠️ TP={tp} FP={fp} FN={fn} | {latency:.2f}s")
                fp_texts = {d["text"] for d in detected} - {e["text"].lower() for e in expected}
                print(f"        誤報: {fp_texts}")
            else:
                print(f"     ❌ TP={tp} FP={fp} FN={fn} | {latency:.2f}s")
                fn_texts = {e["text"] for e in expected} - {d["text"].lower() for d in detected}
                print(f"        漏偵: {fn_texts}")
                if fp > 0:
                    fp_texts = {d["text"] for d in detected} - {e["text"].lower() for e in expected}
                    print(f"        誤報: {fp_texts}")
        
        # 計算指標
        result.calculate_metrics()
        if result.total_cases > 0:
            result.avg_latency_sec = result.total_time_sec / result.total_cases
        
        return result
    
    def compare_phi(self, expected: list[dict], detected: list[dict]) -> tuple[int, int, int]:
        """比較預期和偵測到的 PHI"""
        expected_texts = {e["text"].lower() for e in expected}
        detected_texts = {d["text"].lower() for d in detected}
        
        tp = len(expected_texts & detected_texts)
        fp = len(detected_texts - expected_texts)
        fn = len(expected_texts - detected_texts)
        
        return tp, fp, fn
    
    def run_benchmark(
        self, 
        models: list[str],
        test_cases: list[dict] | None = None
    ) -> list[BenchmarkResult]:
        """執行完整 benchmark"""
        if test_cases is None:
            test_cases = TEST_CASES
        
        print(f"\n🚀 開始測試 {len(models)} 個模型 (Structured Output Mode)...")
        print(f"📊 測試案例數: {len(test_cases)}")
        
        results = []
        for model in models:
            try:
                result = self.benchmark_model(model, test_cases)
                results.append(result)
            except Exception as e:
                import traceback
                print(f"❌ 測試 {model} 失敗: {e}")
                traceback.print_exc()
        
        return results
    
    def print_summary(self, results: list[BenchmarkResult]):
        """印出測試摘要"""
        print("\n" + "=" * 80)
        print("📊 測試結果摘要 (Structured Output)")
        print("=" * 80)
        
        print(f"\n{'模型':<25} {'F1':>8} {'Prec':>8} {'Recall':>8} {'延遲(s)':>10} {'結構化成功':>12}")
        print("-" * 80)
        
        sorted_results = sorted(results, key=lambda r: r.f1_score, reverse=True)
        
        for r in sorted_results:
            success_rate = r.structured_output_success / max(r.total_cases, 1) * 100
            print(f"{r.model:<25} {r.f1_score:>8.1%} {r.precision:>8.1%} {r.recall:>8.1%} "
                  f"{r.avg_latency_sec:>10.2f} {success_rate:>11.0f}%")
        
        print("-" * 80)
        
        if sorted_results:
            best_f1 = sorted_results[0]
            print(f"\n🏆 最高正確率: {best_f1.model} (F1={best_f1.f1_score:.1%})")
    
    def save_results(self, results: list[BenchmarkResult], output_path: str):
        """儲存測試結果 (包含結構化輸出)"""
        data = []
        for r in results:
            data.append({
                "model": r.model,
                "f1_score": r.f1_score,
                "precision": r.precision,
                "recall": r.recall,
                "avg_latency_sec": r.avg_latency_sec,
                "total_cases": r.total_cases,
                "true_positives": r.true_positives,
                "false_positives": r.false_positives,
                "false_negatives": r.false_negatives,
                "structured_output_success": r.structured_output_success,
                "structured_output_failures": r.structured_output_failures,
                "case_results": r.case_results,
                "errors": r.errors,
            })
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 結果已儲存至: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="LLM PHI Detection Benchmark V2 (Structured Output)")
    parser.add_argument("--base-url", default=os.getenv("OLLAMA_BASE_URL", "http://192.168.1.2:30133"),
                        help="Ollama API URL")
    parser.add_argument("--models", type=str, required=True,
                        help="要測試的模型，逗號分隔")
    parser.add_argument("--output", type=str, default="data/output/benchmark_structured_results.json",
                        help="結果輸出路徑")
    parser.add_argument("--timeout", type=float, default=120.0,
                        help="請求超時秒數")
    parser.add_argument("--realistic", action="store_true",
                        help="使用複雜擬真測試案例")
    parser.add_argument("--test-file", type=str, 
                        default="data/test/test_phi_tagged_cases.xlsx",
                        help="PHI 標記測試資料的 Excel 路徑")
    
    args = parser.parse_args()
    
    print(f"🔗 連接 Ollama API: {args.base_url}")
    print(f"📦 使用專案架構: PHIDetectionResponse (Pydantic)")
    
    benchmark = StructuredBenchmark(base_url=args.base_url, timeout=args.timeout)
    
    # 解析模型列表
    models = [m.strip() for m in args.models.split(",")]
    
    # 載入測試案例
    test_cases = None
    if args.realistic:
        print(f"📂 載入擬真測試資料: {args.test_file}")
        test_cases = load_realistic_test_cases(args.test_file)
        if test_cases:
            total_phi = sum(len(c["expected_phi"]) for c in test_cases)
            print(f"   ✅ 載入 {len(test_cases)} 個案例，共 {total_phi} 個 PHI 標記")
    
    # 執行測試
    results = benchmark.run_benchmark(models, test_cases)
    
    if results:
        benchmark.print_summary(results)
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        benchmark.save_results(results, args.output)


if __name__ == "__main__":
    main()
