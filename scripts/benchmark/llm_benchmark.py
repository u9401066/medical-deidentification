#!/usr/bin/env python3
"""
LLM PHI Detection Benchmark | LLM PHI 偵測效能測試

測試不同模型的：
1. 推理速度 (tokens/sec)
2. 正確率 (Precision/Recall/F1)
3. 首次回應延遲 (TTFT)

用法：
    # 設定環境變數
    export OLLAMA_BASE_URL=http://172.18.11.101:30133
    
    # 執行測試（簡單案例）
    python scripts/benchmark/llm_benchmark.py
    
    # 測試特定模型
    python scripts/benchmark/llm_benchmark.py --models "qwen2.5:7b,llama3.1:8b"
    
    # 使用複雜擬真案例（從 Excel 讀取 PHI 標記資料）
    python scripts/benchmark/llm_benchmark.py --realistic
    python scripts/benchmark/llm_benchmark.py --realistic --test-file data/test/test_phi_tagged_cases.xlsx
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

import httpx

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# PHI 標記解析器 (支援複雜擬真案例)
# =============================================================================

def parse_phi_tags(text: str) -> list[dict]:
    """
    從文本中解析所有 PHI 標記
    
    格式: 【PHI:TYPE:ID】content【/PHI】 or 【PHI:TYPE】content【/PHI】
    
    Returns:
        List of dict with keys: type, text, id
    """
    pattern = r'【PHI:(\w+):?(\w*)】([^【]+?)【/PHI】'
    matches = []
    
    for match in re.finditer(pattern, text):
        phi_type = match.group(1)
        phi_id = match.group(2) if match.group(2) else None
        content = match.group(3)
        
        matches.append({
            'type': phi_type,
            'text': content,
            'id': phi_id,
        })
    
    return matches


def remove_phi_tags(text: str) -> str:
    """移除 PHI 標記，只保留內容"""
    # 將 【PHI:TYPE:ID】content【/PHI】 替換為 content
    pattern = r'【PHI:\w+:?\w*】([^【]+?)【/PHI】'
    return re.sub(pattern, r'\1', text)


def load_realistic_test_cases(excel_path: str) -> list[dict]:
    """
    從 PHI 標記的 Excel 檔案載入測試案例
    
    Args:
        excel_path: Excel 檔案路徑 (如 data/test/test_phi_tagged_cases.xlsx)
    
    Returns:
        測試案例列表，格式與 TEST_CASES 相同
    """
    try:
        import openpyxl
    except ImportError:
        print("❌ 需要安裝 openpyxl: pip install openpyxl")
        return []
    
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    
    test_cases = []
    
    # 跳過表頭，從第2行開始
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=1):
        if not row[0]:  # 跳過空行
            continue
        
        case_id = row[0]
        
        # 合併所有文本欄位 (第2-5列)
        text_parts = []
        for col_idx in range(1, 5):
            if col_idx < len(row) and row[col_idx]:
                text_parts.append(str(row[col_idx]))
        
        full_text_with_tags = ' '.join(text_parts)
        
        # 解析 PHI 標記作為 ground truth
        expected_phi = parse_phi_tags(full_text_with_tags)
        
        # 移除標記得到純文本 (這是要送給 LLM 的)
        clean_text = remove_phi_tags(full_text_with_tags)
        
        test_cases.append({
            "id": case_id,
            "text": clean_text,
            "expected_phi": expected_phi,
            "original_with_tags": full_text_with_tags,
        })
    
    return test_cases


# =============================================================================
# 測試資料
# =============================================================================

# 標準測試案例 (含標準答案)
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

# PHI 偵測 Prompt (使用 $text$ 佔位符避免 JSON 大括號衝突)
PHI_DETECTION_PROMPT = """你是一位醫療資料去識別化專家。請識別以下醫療文本中的個人健康資訊(PHI)。

對於每個找到的 PHI，請以 JSON 格式回傳：
```json
{{
  "phi_entities": [
    {{"text": "找到的文字", "type": "PHI類型"}}
  ]
}}
```

PHI 類型包括：NAME, DATE, AGE, AGE_OVER_89, LOCATION, PHONE, EMAIL, ID, 
MEDICAL_RECORD_NUMBER, INSURANCE_NUMBER, HOSPITAL_NAME, RARE_DISEASE 等。

醫療文本：
{text}

請只回傳 JSON，不要其他解釋。"""


@dataclass
class BenchmarkResult:
    """單一模型的測試結果"""
    model: str
    total_cases: int = 0
    passed_cases: int = 0
    
    # 效能指標
    total_time_sec: float = 0.0
    avg_latency_sec: float = 0.0
    avg_tokens_per_sec: float = 0.0
    
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
    
    def calculate_metrics(self):
        """計算 Precision/Recall/F1"""
        if self.true_positives + self.false_positives > 0:
            self.precision = self.true_positives / (self.true_positives + self.false_positives)
        if self.true_positives + self.false_negatives > 0:
            self.recall = self.true_positives / (self.true_positives + self.false_negatives)
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)


class OllamaBenchmark:
    """Ollama 模型效能測試器"""
    
    def __init__(self, base_url: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)
    
    def get_available_models(self) -> list[str]:
        """取得可用模型列表"""
        try:
            resp = self.client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            print(f"❌ 無法取得模型列表: {e}")
            return []
    
    def generate(self, model: str, prompt: str) -> tuple[str, float, dict]:
        """
        呼叫模型生成
        
        Returns:
            (response_text, latency_sec, usage_info)
        """
        start = time.perf_counter()
        
        try:
            resp = self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 1024,
                    }
                }
            )
            resp.raise_for_status()
            data = resp.json()
            
            latency = time.perf_counter() - start
            
            usage = {
                "total_duration_ns": data.get("total_duration", 0),
                "load_duration_ns": data.get("load_duration", 0),
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "eval_count": data.get("eval_count", 0),
                "eval_duration_ns": data.get("eval_duration", 0),
            }
            
            return data.get("response", ""), latency, usage
            
        except Exception as e:
            return f"ERROR: {e}", time.perf_counter() - start, {}
    
    def parse_phi_response(self, response: str) -> list[dict]:
        """解析模型回傳的 PHI JSON"""
        import re
        
        # 清理回應
        response = response.strip()
        
        # 嘗試直接解析
        try:
            data = json.loads(response)
            if isinstance(data, dict):
                return data.get("phi_entities", [])
            return []
        except json.JSONDecodeError:
            pass
        
        # 嘗試找出 JSON 區塊 (包含 code block)
        # 移除 markdown code block
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # 嘗試找到最外層的 { }
        try:
            # 找到第一個 { 和最後一個 }
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = response[start:end+1]
                data = json.loads(json_str)
                if isinstance(data, dict):
                    return data.get("phi_entities", [])
        except json.JSONDecodeError:
            pass
        
        # 嘗試找 phi_entities 陣列
        match = re.search(r'"phi_entities"\s*:\s*\[(.*?)\]', response, re.DOTALL)
        if match:
            try:
                entities_str = '[' + match.group(1) + ']'
                return json.loads(entities_str)
            except:
                pass
        
        return []
    
    def compare_phi(self, expected: list[dict], detected: list[dict]) -> tuple[int, int, int]:
        """
        比較預期和偵測到的 PHI
        
        Returns:
            (true_positives, false_positives, false_negatives)
        """
        expected_texts = {e["text"].lower() for e in expected}
        detected_texts = {d["text"].lower() for d in detected}
        
        tp = len(expected_texts & detected_texts)
        fp = len(detected_texts - expected_texts)
        fn = len(expected_texts - detected_texts)
        
        return tp, fp, fn
    
    def benchmark_model(
        self, 
        model: str, 
        test_cases: list[dict] | None = None
    ) -> BenchmarkResult:
        """測試單一模型"""
        if test_cases is None:
            test_cases = TEST_CASES
        
        result = BenchmarkResult(model=model)
        result.total_cases = len(test_cases)
        
        print(f"\n{'='*60}")
        print(f"🧪 測試模型: {model}")
        print(f"{'='*60}")
        
        for case in test_cases:
            case_id = case["id"]
            text = case["text"]
            expected = case["expected_phi"]
            
            print(f"\n  📝 {case_id}: {text[:50]}...")
            
            # 生成 prompt
            prompt = PHI_DETECTION_PROMPT.format(text=text)
            
            # 呼叫模型
            response, latency, usage = self.generate(model, prompt)
            
            if response.startswith("ERROR:"):
                result.errors.append({"case_id": case_id, "error": response})
                print(f"     ❌ 錯誤: {response}")
                continue
            
            # 解析回應
            detected = self.parse_phi_response(response)
            
            # 計算正確率
            tp, fp, fn = self.compare_phi(expected, detected)
            result.true_positives += tp
            result.false_positives += fp
            result.false_negatives += fn
            
            # 計算效能
            result.total_time_sec += latency
            tokens_per_sec = 0
            if usage.get("eval_duration_ns", 0) > 0:
                tokens_per_sec = usage.get("eval_count", 0) / (usage["eval_duration_ns"] / 1e9)
            
            case_result = {
                "case_id": case_id,
                "latency_sec": latency,
                "tokens_per_sec": tokens_per_sec,
                "expected_count": len(expected),
                "detected_count": len(detected),
                "tp": tp, "fp": fp, "fn": fn,
            }
            result.case_results.append(case_result)
            
            # 顯示結果
            status = "✅" if fn == 0 and fp == 0 else "⚠️" if fn == 0 else "❌"
            print(f"     {status} TP={tp} FP={fp} FN={fn} | {latency:.2f}s | {tokens_per_sec:.1f} tok/s")
            
            if fp > 0 or fn > 0:
                expected_texts = {e["text"] for e in expected}
                detected_texts = {d["text"] for d in detected}
                if fn > 0:
                    print(f"        漏偵: {expected_texts - detected_texts}")
                if fp > 0:
                    print(f"        誤報: {detected_texts - expected_texts}")
        
        # 計算總結指標
        result.calculate_metrics()
        if result.total_cases > 0:
            result.avg_latency_sec = result.total_time_sec / result.total_cases
        
        valid_cases = [c for c in result.case_results if c["tokens_per_sec"] > 0]
        if valid_cases:
            result.avg_tokens_per_sec = sum(c["tokens_per_sec"] for c in valid_cases) / len(valid_cases)
        
        return result
    
    def run_benchmark(
        self, 
        models: list[str] | None = None,
        test_cases: list[dict] | None = None
    ) -> list[BenchmarkResult]:
        """執行完整 benchmark"""
        if models is None:
            models = self.get_available_models()
            if not models:
                print("❌ 沒有可用的模型")
                return []
        
        if test_cases is None:
            test_cases = TEST_CASES
        
        print(f"\n🚀 開始測試 {len(models)} 個模型...")
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
        print("\n")
        print("=" * 80)
        print("📊 測試結果摘要")
        print("=" * 80)
        
        # 表頭
        print(f"\n{'模型':<25} {'F1':>8} {'Prec':>8} {'Recall':>8} {'延遲(s)':>10} {'tok/s':>10}")
        print("-" * 80)
        
        # 按 F1 排序
        sorted_results = sorted(results, key=lambda r: r.f1_score, reverse=True)
        
        for r in sorted_results:
            print(f"{r.model:<25} {r.f1_score:>8.1%} {r.precision:>8.1%} {r.recall:>8.1%} "
                  f"{r.avg_latency_sec:>10.2f} {r.avg_tokens_per_sec:>10.1f}")
        
        print("-" * 80)
        
        # 最佳模型推薦
        if sorted_results:
            best_f1 = sorted_results[0]
            fastest = min(results, key=lambda r: r.avg_latency_sec if r.avg_latency_sec > 0 else float('inf'))
            
            print(f"\n🏆 最高正確率: {best_f1.model} (F1={best_f1.f1_score:.1%})")
            print(f"⚡ 最快速度: {fastest.model} ({fastest.avg_latency_sec:.2f}s, {fastest.avg_tokens_per_sec:.1f} tok/s)")
            
            # 效能/正確率平衡推薦
            balanced = max(results, key=lambda r: r.f1_score * 0.7 + (1 / max(r.avg_latency_sec, 0.1)) * 0.3)
            print(f"⚖️ 最佳平衡: {balanced.model} (F1={balanced.f1_score:.1%}, {balanced.avg_latency_sec:.2f}s)")
    
    def save_results(self, results: list[BenchmarkResult], output_path: str):
        """儲存測試結果"""
        data = []
        for r in results:
            data.append({
                "model": r.model,
                "f1_score": r.f1_score,
                "precision": r.precision,
                "recall": r.recall,
                "avg_latency_sec": r.avg_latency_sec,
                "avg_tokens_per_sec": r.avg_tokens_per_sec,
                "total_cases": r.total_cases,
                "true_positives": r.true_positives,
                "false_positives": r.false_positives,
                "false_negatives": r.false_negatives,
                "case_results": r.case_results,
                "errors": r.errors,
            })
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 結果已儲存至: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="LLM PHI Detection Benchmark")
    parser.add_argument("--base-url", default=os.getenv("OLLAMA_BASE_URL", "http://192.168.1.2:30133"),
                        help="Ollama API URL")
    parser.add_argument("--models", type=str, default=None,
                        help="要測試的模型，逗號分隔 (預設：測試所有可用模型)")
    parser.add_argument("--output", type=str, default="data/output/benchmark_results.json",
                        help="結果輸出路徑")
    parser.add_argument("--timeout", type=float, default=120.0,
                        help="請求超時秒數")
    parser.add_argument("--realistic", action="store_true",
                        help="使用複雜擬真測試案例 (從 Excel 讀取 PHI 標記資料)")
    parser.add_argument("--test-file", type=str, 
                        default="data/test/test_phi_tagged_cases.xlsx",
                        help="PHI 標記測試資料的 Excel 路徑")
    
    args = parser.parse_args()
    
    print(f"🔗 連接 Ollama API: {args.base_url}")
    
    benchmark = OllamaBenchmark(base_url=args.base_url, timeout=args.timeout)
    
    # 解析模型列表
    models = None
    if args.models:
        models = [m.strip() for m in args.models.split(",")]
    
    # 載入測試案例
    test_cases = None
    if args.realistic:
        print(f"📂 載入擬真測試資料: {args.test_file}")
        test_cases = load_realistic_test_cases(args.test_file)
        if test_cases:
            total_phi = sum(len(c["expected_phi"]) for c in test_cases)
            print(f"   ✅ 載入 {len(test_cases)} 個案例，共 {total_phi} 個 PHI 標記")
        else:
            print("   ❌ 載入失敗，使用預設簡單案例")
            test_cases = None
    
    # 執行測試
    results = benchmark.run_benchmark(models, test_cases)
    
    if results:
        # 印出摘要
        benchmark.print_summary(results)
        
        # 儲存結果
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        benchmark.save_results(results, args.output)


if __name__ == "__main__":
    main()
