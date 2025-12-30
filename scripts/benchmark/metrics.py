"""
Evaluation Metrics | 評估指標

計算 PHI 識別的各項指標：
- Precision (精確率)
- Recall (召回率)  
- F1 Score (綜合指標)
- Confusion Matrix (混淆矩陣)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


@dataclass
class ConfusionMatrix:
    """
    混淆矩陣
    
    Attributes:
        true_positives: 正確識別的 PHI
        false_positives: 誤報 (非 PHI 被標為 PHI)
        false_negatives: 漏檢 (PHI 未被識別)
    """
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    @property
    def precision(self) -> float:
        """精確率 = TP / (TP + FP)"""
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 0.0
    
    @property
    def recall(self) -> float:
        """召回率 = TP / (TP + FN)"""
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0
    
    @property
    def f1(self) -> float:
        """F1 Score = 2 * P * R / (P + R)"""
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    
    def __add__(self, other: "ConfusionMatrix") -> "ConfusionMatrix":
        """合併兩個混淆矩陣"""
        return ConfusionMatrix(
            true_positives=self.true_positives + other.true_positives,
            false_positives=self.false_positives + other.false_positives,
            false_negatives=self.false_negatives + other.false_negatives,
        )
    
    def to_dict(self) -> Dict:
        return {
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
        }


@dataclass
class EvaluationMetrics:
    """
    完整評估指標
    
    包含整體指標和按 PHI 類型分類的指標
    """
    overall: ConfusionMatrix = field(default_factory=ConfusionMatrix)
    by_type: Dict[str, ConfusionMatrix] = field(default_factory=dict)
    
    # 額外統計
    total_samples: int = 0
    total_time: float = 0.0
    
    @property
    def avg_time_per_sample(self) -> float:
        return self.total_time / self.total_samples if self.total_samples > 0 else 0.0
    
    def add_type_result(self, phi_type: str, cm: ConfusionMatrix):
        """新增特定類型的結果"""
        if phi_type not in self.by_type:
            self.by_type[phi_type] = ConfusionMatrix()
        self.by_type[phi_type] = self.by_type[phi_type] + cm
    
    def to_dict(self) -> Dict:
        return {
            "overall": self.overall.to_dict(),
            "by_type": {k: v.to_dict() for k, v in self.by_type.items()},
            "total_samples": self.total_samples,
            "total_time": self.total_time,
            "avg_time_per_sample": self.avg_time_per_sample,
        }


def calculate_precision(tp: int, fp: int) -> float:
    """計算精確率"""
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0


def calculate_recall(tp: int, fn: int) -> float:
    """計算召回率"""
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0


def calculate_f1(precision: float, recall: float) -> float:
    """計算 F1 Score"""
    return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0


def normalize_phi_type(phi_type: str) -> str:
    """
    標準化 PHI 類型名稱
    
    將不同格式的 PHI 類型名稱統一
    """
    mapping = {
        # Name variations
        'NAME': 'NAME',
        'PATIENT': 'NAME',
        'PATIENT_NAME': 'NAME',
        'DOCTOR': 'NAME',
        'DOCTOR_NAME': 'NAME',
        'PERSON': 'NAME',
        'PERSON_NAME': 'NAME',
        'FULL_NAME': 'NAME',
        'PERSON/NAME': 'NAME',
        
        # Date variations
        'DATE': 'DATE',
        'DOB': 'DATE',
        'BIRTHDATE': 'DATE',
        'DATE_OF_BIRTH': 'DATE',
        'DATE_TIME': 'DATE',
        'DATETIME': 'DATE',
        
        # Age variations
        'AGE': 'AGE',
        'AGE_OVER_89': 'AGE',
        
        # ID variations
        'ID': 'ID',
        'ID_NUMBER': 'ID',
        'MRN': 'ID',
        'SSN': 'ID',
        'MEDICALRECORD': 'ID',
        'IDNUM': 'ID',
        'CREDIT_CARD': 'ID',
        'CREDIT_CARD_NUMBER': 'ID',
        'ID/SSN': 'ID',
        
        # Phone variations
        'PHONE': 'PHONE',
        'TELEPHONE': 'PHONE',
        'MOBILE': 'PHONE',
        'FAX': 'PHONE',
        'PHONE_NUMBER': 'PHONE',
        
        # Email
        'EMAIL': 'EMAIL',
        'EMAIL_ADDRESS': 'EMAIL',
        
        # Location variations
        'LOCATION': 'LOCATION',
        'ADDRESS': 'LOCATION',
        'STREET': 'LOCATION',
        'CITY': 'LOCATION',
        'STATE': 'LOCATION',
        'ZIP': 'LOCATION',
        'COUNTRY': 'LOCATION',
        'STREET_ADDRESS': 'LOCATION',
        'GPE': 'LOCATION',
        'LOCATION/GPE': 'LOCATION',
        
        # Facility variations
        'FACILITY': 'FACILITY',
        'HOSPITAL': 'FACILITY',
        'ORGANIZATION': 'FACILITY',
        
        # NRP (Nationality/Religion/Political)
        'NRP': 'OTHER',
        'TITLE': 'OTHER',
    }
    
    upper = phi_type.upper().replace(' ', '_').replace('-', '_')
    return mapping.get(upper, upper)


def match_entities(
    ground_truth: List[Tuple[str, str]],  # [(text, type), ...]
    predictions: List[Tuple[str, str]],
    match_type: str = "exact",  # "exact", "partial", "overlap"
) -> Tuple[List[Tuple], List[Tuple], List[Tuple]]:
    """
    匹配 ground truth 和 predictions
    
    Args:
        ground_truth: 標準答案 [(text, type), ...]
        predictions: 預測結果 [(text, type), ...]
        match_type: 匹配方式
            - "exact": 完全匹配 (text 和 type 都要一樣)
            - "partial": 部分匹配 (text 包含或被包含)
            - "overlap": 只看 text 是否匹配
    
    Returns:
        (true_positives, false_positives, false_negatives)
    """
    # 標準化
    gt_normalized = [(text.strip().lower(), normalize_phi_type(t)) for text, t in ground_truth]
    pred_normalized = [(text.strip().lower(), normalize_phi_type(t)) for text, t in predictions]
    
    true_positives = []
    false_positives = []
    false_negatives = []
    
    matched_gt = set()
    
    for pred_text, pred_type in pred_normalized:
        found = False
        
        for i, (gt_text, gt_type) in enumerate(gt_normalized):
            if i in matched_gt:
                continue
            
            text_match = False
            type_match = (pred_type == gt_type) if match_type == "exact" else True
            
            if match_type == "exact":
                text_match = (pred_text == gt_text)
            elif match_type == "partial":
                text_match = (pred_text in gt_text) or (gt_text in pred_text)
            elif match_type == "overlap":
                # 任何重疊都算
                text_match = (pred_text in gt_text) or (gt_text in pred_text) or (pred_text == gt_text)
            
            if text_match and type_match:
                true_positives.append((pred_text, pred_type, gt_text, gt_type))
                matched_gt.add(i)
                found = True
                break
        
        if not found:
            false_positives.append((pred_text, pred_type))
    
    # 未匹配的 ground truth 是 false negatives
    for i, (gt_text, gt_type) in enumerate(gt_normalized):
        if i not in matched_gt:
            false_negatives.append((gt_text, gt_type))
    
    return true_positives, false_positives, false_negatives


def calculate_metrics(
    ground_truth: List[Tuple[str, str]],
    predictions: List[Tuple[str, str]],
    match_type: str = "partial",
) -> ConfusionMatrix:
    """
    計算單個樣本的混淆矩陣
    
    Args:
        ground_truth: 標準答案
        predictions: 預測結果
        match_type: 匹配方式
    
    Returns:
        ConfusionMatrix
    """
    tp, fp, fn = match_entities(ground_truth, predictions, match_type)
    
    return ConfusionMatrix(
        true_positives=len(tp),
        false_positives=len(fp),
        false_negatives=len(fn),
    )


def calculate_metrics_by_type(
    ground_truth: List[Tuple[str, str]],
    predictions: List[Tuple[str, str]],
    match_type: str = "partial",
) -> Dict[str, ConfusionMatrix]:
    """
    按 PHI 類型計算混淆矩陣
    
    Returns:
        Dict[type -> ConfusionMatrix]
    """
    # 分類
    gt_by_type = defaultdict(list)
    pred_by_type = defaultdict(list)
    
    for text, t in ground_truth:
        gt_by_type[normalize_phi_type(t)].append((text, t))
    
    for text, t in predictions:
        pred_by_type[normalize_phi_type(t)].append((text, t))
    
    # 計算每個類型
    all_types = set(gt_by_type.keys()) | set(pred_by_type.keys())
    results = {}
    
    for phi_type in all_types:
        gt_list = gt_by_type.get(phi_type, [])
        pred_list = pred_by_type.get(phi_type, [])
        results[phi_type] = calculate_metrics(gt_list, pred_list, match_type)
    
    return results
