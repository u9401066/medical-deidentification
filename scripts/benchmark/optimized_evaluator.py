"""
Optimized PHI Evaluator | 優化版 PHI 評估器

針對 CPU-only 環境優化的評估器：
- 批次處理減少 API 呼叫
- 簡化 prompt 減少 token
- 並行處理 (如支援)
- 結果快取

預期效能: ~1000 tokens / 60s (CPU)
"""

import re
import json
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field


@dataclass
class OptimizedConfig:
    """優化設定"""
    model: str = "granite4:1b"
    num_ctx: int = 512  # 最小 context
    num_predict: int = 150  # 限制輸出
    batch_size: int = 5  # 批次大小
    temperature: float = 0
    max_workers: int = 2  # 並行數


class FastPHI(BaseModel):
    """簡化 PHI 結構"""
    t: str = Field(description="text")  # 短名稱節省 token
    y: str = Field(description="type")  # NAME, DATE, PHONE, EMAIL, ID, LOCATION


class FastPHIList(BaseModel):
    """PHI 列表"""
    p: List[FastPHI] = Field(default_factory=list)


# 簡化的 type mapping
TYPE_MAP = {
    'person': 'NAME', 'name': 'NAME', 'patient': 'NAME',
    'date': 'DATE', 'dob': 'DATE', 'birthday': 'DATE',
    'phone': 'PHONE', 'tel': 'PHONE', 'mobile': 'PHONE',
    'email': 'EMAIL', 'mail': 'EMAIL',
    'id': 'ID', 'ssn': 'ID', 'mrn': 'ID', 'account': 'ID',
    'address': 'LOCATION', 'location': 'LOCATION', 'city': 'LOCATION',
    'org': 'FACILITY', 'hospital': 'FACILITY', 'company': 'FACILITY',
}


def normalize_type(t: str) -> str:
    """快速 type 標準化"""
    t_lower = t.lower().replace(' ', '').replace('_', '')
    for key, val in TYPE_MAP.items():
        if key in t_lower:
            return val
    return t.upper()


class OptimizedPHIDetector:
    """
    優化版 PHI 偵測器
    
    使用簡化 prompt 和批次處理加速
    """
    
    # 極簡 prompt (節省 input tokens)
    PROMPT = "PHI(t=text,y=type NAME/DATE/PHONE/EMAIL/ID/LOCATION):"
    
    def __init__(self, config: Optional[OptimizedConfig] = None):
        self.config = config or OptimizedConfig()
        self.llm = ChatOllama(
            model=self.config.model,
            temperature=self.config.temperature,
            num_ctx=self.config.num_ctx,
            num_predict=self.config.num_predict,
        )
        self.structured_llm = self.llm.with_structured_output(
            FastPHIList, 
            method='json_schema'
        )
        
        # 統計
        self.total_calls = 0
        self.total_time = 0.0
    
    def detect(self, text: str) -> List[Tuple[str, str]]:
        """
        單一文本 PHI 偵測
        
        Returns:
            [(text, type), ...]
        """
        start = time.time()
        try:
            result = self.structured_llm.invoke(f"{self.PROMPT} {text[:500]}")
            self.total_calls += 1
            self.total_time += time.time() - start
            
            if result and result.p:
                return [(p.t, normalize_type(p.y)) for p in result.p]
        except Exception as e:
            pass
        
        return []
    
    def detect_batch(self, texts: List[str]) -> List[List[Tuple[str, str]]]:
        """
        批次 PHI 偵測
        
        將多個文本合併處理，減少 API 呼叫
        """
        if not texts:
            return []
        
        # 合併文本
        combined = "\n".join([
            f"[{i}]{t[:200]}" 
            for i, t in enumerate(texts)
        ])
        
        start = time.time()
        try:
            # 使用非結構化輸出加速
            result = self.llm.invoke(
                f"For each [N], list PHI as JSON {{t:text,y:type}}:\n{combined}"
            )
            self.total_calls += 1
            self.total_time += time.time() - start
            
            # 解析結果
            return self._parse_batch_result(result.content, len(texts))
            
        except Exception as e:
            return [[] for _ in texts]
    
    def _parse_batch_result(
        self, 
        content: str, 
        expected_count: int
    ) -> List[List[Tuple[str, str]]]:
        """解析批次結果"""
        results = [[] for _ in range(expected_count)]
        
        # 嘗試解析 JSON 格式
        try:
            # 找所有 JSON objects
            pattern = r'\{[^}]+\}'
            matches = re.findall(pattern, content)
            
            current_idx = 0
            for match in matches:
                try:
                    obj = json.loads(match)
                    if 't' in obj and 'y' in obj:
                        results[current_idx].append(
                            (obj['t'], normalize_type(obj['y']))
                        )
                except:
                    pass
                    
        except Exception:
            pass
        
        return results
    
    def get_stats(self) -> Dict:
        """取得統計資訊"""
        return {
            "total_calls": self.total_calls,
            "total_time": self.total_time,
            "avg_time": self.total_time / self.total_calls if self.total_calls > 0 else 0,
        }


def run_optimized_benchmark(
    data_path: Path,
    limit: int = 20,
    batch_size: int = 1,
) -> Dict:
    """
    執行優化版 benchmark
    
    Args:
        data_path: 資料路徑
        limit: 樣本數限制
        batch_size: 批次大小
    
    Returns:
        評估結果
    """
    from scripts.benchmark import load_benchmark_data, calculate_metrics
    from scripts.benchmark.metrics import normalize_phi_type
    
    # 載入資料
    samples = list(load_benchmark_data(data_path, format='presidio'))[:limit]
    print(f"📁 載入 {len(samples)} 筆資料")
    
    # 建立偵測器
    detector = OptimizedPHIDetector()
    print(f"🔧 使用 {detector.config.model}, ctx={detector.config.num_ctx}")
    
    # 評估
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    start = time.time()
    
    for i, sample in enumerate(samples):
        if (i + 1) % 5 == 0:
            print(f"⏳ {i+1}/{len(samples)}...")
        
        # 偵測
        predictions = detector.detect(sample.text)
        
        # 標準化 ground truth
        gt = [(ann.text, normalize_phi_type(ann.phi_type)) for ann in sample.annotations]
        pred_normalized = [(t, normalize_phi_type(y)) for t, y in predictions]
        
        # 計算 metrics (簡化版)
        gt_set = set(t.lower() for t, _ in gt)
        pred_set = set(t.lower() for t, _ in pred_normalized)
        
        tp = len(gt_set & pred_set)
        fp = len(pred_set - gt_set)
        fn = len(gt_set - pred_set)
        
        total_tp += tp
        total_fp += fp
        total_fn += fn
    
    elapsed = time.time() - start
    
    # 計算指標
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    stats = detector.get_stats()
    
    return {
        "samples": len(samples),
        "time": elapsed,
        "time_per_sample": elapsed / len(samples),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "api_calls": stats["total_calls"],
        "avg_api_time": stats["avg_time"],
    }


if __name__ == "__main__":
    import sys
    
    data_path = Path("data/benchmark/presidio_synthetic.jsonl")
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    print("=" * 60)
    print("📊 Optimized PHI Benchmark")
    print("=" * 60)
    
    result = run_optimized_benchmark(data_path, limit=limit)
    
    print("\n" + "=" * 60)
    print("📈 Results")
    print("=" * 60)
    print(f"⏱️  Time: {result['time']:.1f}s ({result['time_per_sample']:.2f}s/sample)")
    print(f"📊 Precision: {result['precision']:.3f}")
    print(f"📊 Recall:    {result['recall']:.3f}")
    print(f"📊 F1 Score:  {result['f1']:.3f}")
    print(f"🔢 API Calls: {result['api_calls']} (avg {result['avg_api_time']:.2f}s)")
