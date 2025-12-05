#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHI Tag Parser - Extract Ground Truth PHI
解析 PHI 標記，提取標準答案
"""

import re
import pandas as pd
from typing import List, Dict, Tuple

def parse_phi_tags(text: str) -> List[Dict]:
    """
    從文本中解析所有 PHI 標記
    
    Returns:
        List of dict with keys: type, id, content, start, end
    """
    pattern = r'【PHI:(\w+):?(\w*)】([^【]+?)【/PHI】'
    matches = []
    
    for match in re.finditer(pattern, text):
        phi_type = match.group(1)
        phi_id = match.group(2) if match.group(2) else None
        content = match.group(3)
        
        matches.append({
            'type': phi_type,
            'id': phi_id,
            'content': content,
            'start': match.start(),
            'end': match.end(),
            'full_match': match.group(0)
        })
    
    return matches

def calculate_metrics(ground_truth: List[Dict], detected: List[Dict]) -> Dict:
    """
    計算檢出率指標
    
    Args:
        ground_truth: 標記的 PHI 列表
        detected: 系統檢出的 PHI 列表
    
    Returns:
        Dict with TP, FP, FN, Precision, Recall, F1
    """
    # 轉換為集合方便比較 (使用 content 作為鍵)
    gt_set = {(phi['type'], phi['content']) for phi in ground_truth}
    det_set = {(phi['type'], phi['content']) for phi in detected}
    
    tp = len(gt_set & det_set)  # True Positives
    fp = len(det_set - gt_set)  # False Positives
    fn = len(gt_set - det_set)  # False Negatives
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'TP': tp,
        'FP': fp,
        'FN': fn,
        'Precision': precision,
        'Recall': recall,
        'F1': f1
    }

if __name__ == "__main__":
    # 範例使用
    test_text = "Patient 【PHI:NAME:P001】陳老先生【/PHI】, age 【PHI:AGE_OVER_89:A001】94【/PHI】"
    
    phi_list = parse_phi_tags(test_text)
    print("Parsed PHI:")
    for phi in phi_list:
        print(f"  - Type: {phi['type']}, Content: {phi['content']}, ID: {phi['id']}")
    
    # 載入測試文件
    df = pd.read_excel("data/test/test_phi_tagged_cases.xlsx")
    print(f"\nLoaded {len(df)} test cases")
    
    total_phi = 0
    for idx, row in df.iterrows():
        case_id = row['Case ID']
        # 合併所有文本列
        full_text = ' '.join([str(row[col]) for col in df.columns[1:5] if pd.notna(row[col])])
        phi_list = parse_phi_tags(full_text)
        total_phi += len(phi_list)
        print(f"{case_id}: {len(phi_list)} PHI instances")
    
    print(f"\nTotal PHI across all cases: {total_phi}")
