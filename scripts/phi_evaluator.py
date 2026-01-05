#!/usr/bin/env python3
"""
PHI Detection Evaluation Tool
PHI 檢出率評估工具

評估 PHI 檢測系統的效能，計算 Precision、Recall、F1 Score
"""

import re
from collections import Counter, defaultdict

import pandas as pd


class PHIEvaluator:
    """PHI 檢測效能評估器"""

    def __init__(self):
        self.tag_pattern = r'【PHI:(\w+):?(\w*)】([^【]+?)【/PHI】'

    def parse_ground_truth(self, text: str) -> list[dict]:
        """
        從帶標記的文本中提取標準答案 PHI
        
        Returns:
            List of dict: [{'type': 'NAME', 'id': 'P001', 'content': '陳老先生', 'start': 0, 'end': 10}, ...]
        """
        phi_list = []

        for match in re.finditer(self.tag_pattern, text):
            phi_type = match.group(1)
            phi_id = match.group(2) if match.group(2) else None
            content = match.group(3)

            # 計算在原始文本（移除標記後）中的位置
            # 這裡簡化處理，實際使用時需要更精確的位置計算
            phi_list.append({
                'type': phi_type,
                'id': phi_id,
                'content': content.strip(),
                'start': match.start(),
                'end': match.end()
            })

        return phi_list

    def remove_tags(self, text: str) -> str:
        """移除 PHI 標記，返回原始文本"""
        return re.sub(self.tag_pattern, r'\3', text)

    def calculate_metrics(
        self,
        ground_truth: list[dict],
        detected: list[dict],
        match_mode: str = 'exact'  # 'exact', 'partial', 'type_only'
    ) -> dict:
        """
        計算檢測指標
        
        Args:
            ground_truth: 標準答案 PHI 列表
            detected: 系統檢測的 PHI 列表
            match_mode: 匹配模式
                - 'exact': 內容和類型都要完全匹配
                - 'partial': 內容部分匹配即可
                - 'type_only': 只要類型正確即可
        
        Returns:
            指標字典: {TP, FP, FN, Precision, Recall, F1, detailed_results}
        """
        if match_mode == 'exact':
            gt_set = {(phi['type'], phi['content'].lower()) for phi in ground_truth}
            det_set = {(phi['type'], phi['content'].lower()) for phi in detected}

            tp_items = gt_set & det_set
            tp = len(tp_items)
            fp = len(det_set - gt_set)
            fn = len(gt_set - det_set)

        elif match_mode == 'partial':
            # 部分匹配：檢測的內容包含在標準答案中，或標準答案包含在檢測中
            tp = 0
            matched_gt = set()
            matched_det = set()

            for i, det_phi in enumerate(detected):
                for j, gt_phi in enumerate(ground_truth):
                    if det_phi['type'] == gt_phi['type']:
                        det_content = det_phi['content'].lower().strip()
                        gt_content = gt_phi['content'].lower().strip()

                        if det_content in gt_content or gt_content in det_content:
                            tp += 1
                            matched_gt.add(j)
                            matched_det.add(i)
                            break

            fp = len(detected) - len(matched_det)
            fn = len(ground_truth) - len(matched_gt)

        else:  # type_only
            gt_types = Counter(phi['type'] for phi in ground_truth)
            det_types = Counter(phi['type'] for phi in detected)

            tp = sum((gt_types & det_types).values())
            fp = sum((det_types - gt_types).values())
            fn = sum((gt_types - det_types).values())

        # 計算指標
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        # 計算各類型的指標
        type_metrics = self._calculate_type_metrics(ground_truth, detected, match_mode)

        return {
            'TP': tp,
            'FP': fp,
            'FN': fn,
            'Precision': precision,
            'Recall': recall,
            'F1': f1,
            'Accuracy': tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0,
            'by_type': type_metrics
        }

    def _calculate_type_metrics(self, ground_truth: list[dict], detected: list[dict], match_mode: str) -> dict:
        """計算各 PHI 類型的指標"""
        # 按類型分組
        gt_by_type = defaultdict(list)
        det_by_type = defaultdict(list)

        for phi in ground_truth:
            gt_by_type[phi['type']].append(phi)

        for phi in detected:
            det_by_type[phi['type']].append(phi)

        # 計算各類型指標
        type_metrics = {}
        all_types = set(gt_by_type.keys()) | set(det_by_type.keys())

        for phi_type in all_types:
            gt_list = gt_by_type[phi_type]
            det_list = det_by_type[phi_type]

            if match_mode == 'exact':
                gt_set = {phi['content'].lower() for phi in gt_list}
                det_set = {phi['content'].lower() for phi in det_list}
                tp = len(gt_set & det_set)
                fp = len(det_set - gt_set)
                fn = len(gt_set - det_set)
            else:
                # 簡化計算
                tp = min(len(gt_list), len(det_list))
                fp = max(0, len(det_list) - len(gt_list))
                fn = max(0, len(gt_list) - len(det_list))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            type_metrics[phi_type] = {
                'TP': tp,
                'FP': fp,
                'FN': fn,
                'Precision': precision,
                'Recall': recall,
                'F1': f1,
                'Ground_Truth_Count': len(gt_list),
                'Detected_Count': len(det_list)
            }

        return type_metrics

    def evaluate_from_excel(self, excel_path: str, detected_phi_dict: dict[str, list[dict]]) -> dict:
        """
        從 Excel 文件評估檢測結果
        
        Args:
            excel_path: 帶 PHI 標記的測試文件路徑
            detected_phi_dict: 系統檢測結果，格式：{case_id: [phi_list]}
        
        Returns:
            評估結果
        """
        df = pd.read_excel(excel_path)

        overall_metrics = {
            'TP': 0, 'FP': 0, 'FN': 0,
            'by_case': {}
        }

        for idx, row in df.iterrows():
            case_id = row['Case ID']

            # 合併所有文本列
            text_columns = [col for col in df.columns[1:5]]  # 排除 Case ID 和 PHI Count
            full_text = ' '.join([str(row[col]) for col in text_columns if pd.notna(row[col])])

            # 提取標準答案
            ground_truth = self.parse_ground_truth(full_text)

            # 獲取系統檢測結果
            detected = detected_phi_dict.get(case_id, [])

            # 計算指標
            metrics = self.calculate_metrics(ground_truth, detected, match_mode='partial')

            overall_metrics['TP'] += metrics['TP']
            overall_metrics['FP'] += metrics['FP']
            overall_metrics['FN'] += metrics['FN']
            overall_metrics['by_case'][case_id] = metrics

        # 計算總體指標
        tp = overall_metrics['TP']
        fp = overall_metrics['FP']
        fn = overall_metrics['FN']

        overall_metrics['Precision'] = tp / (tp + fp) if (tp + fp) > 0 else 0
        overall_metrics['Recall'] = tp / (tp + fn) if (tp + fn) > 0 else 0
        overall_metrics['F1'] = (
            2 * overall_metrics['Precision'] * overall_metrics['Recall'] /
            (overall_metrics['Precision'] + overall_metrics['Recall'])
            if (overall_metrics['Precision'] + overall_metrics['Recall']) > 0 else 0
        )

        return overall_metrics

    def print_evaluation_report(self, metrics: dict, title: str = "PHI Detection Evaluation Report"):
        """打印評估報告"""
        print("\n" + "="*70)
        print(title)
        print("="*70)

        print("\n📊 Overall Metrics:")
        print(f"  True Positives (TP):  {metrics['TP']:4d}")
        print(f"  False Positives (FP): {metrics['FP']:4d}")
        print(f"  False Negatives (FN): {metrics['FN']:4d}")
        print(f"\n  Precision: {metrics['Precision']:.2%}")
        print(f"  Recall:    {metrics['Recall']:.2%}")
        print(f"  F1 Score:  {metrics['F1']:.2%}")

        if 'by_case' in metrics:
            print("\n📋 By Case:")
            for case_id, case_metrics in metrics['by_case'].items():
                print(f"\n  {case_id}:")
                print(f"    TP={case_metrics['TP']}, FP={case_metrics['FP']}, FN={case_metrics['FN']}")
                print(f"    Precision={case_metrics['Precision']:.2%}, "
                      f"Recall={case_metrics['Recall']:.2%}, "
                      f"F1={case_metrics['F1']:.2%}")

        if 'by_type' in metrics:
            print("\n📌 By PHI Type:")
            for phi_type, type_metrics in sorted(metrics['by_type'].items()):
                print(f"\n  {phi_type}:")
                print(f"    Ground Truth: {type_metrics['Ground_Truth_Count']}, "
                      f"Detected: {type_metrics['Detected_Count']}")
                print(f"    TP={type_metrics['TP']}, FP={type_metrics['FP']}, FN={type_metrics['FN']}")
                print(f"    Precision={type_metrics['Precision']:.2%}, "
                      f"Recall={type_metrics['Recall']:.2%}, "
                      f"F1={type_metrics['F1']:.2%}")


if __name__ == "__main__":
    # 使用範例
    evaluator = PHIEvaluator()

    # 測試標記解析
    test_text = """
    Patient 【PHI:NAME:P001】陳老先生【/PHI】, age 【PHI:AGE_OVER_89:A001】94【/PHI】, 
    contact 【PHI:PHONE:T001】02-2758-9999【/PHI】
    """

    ground_truth = evaluator.parse_ground_truth(test_text)
    print("✅ Parsed Ground Truth PHI:")
    for phi in ground_truth:
        print(f"  - {phi['type']}: {phi['content']} (ID: {phi['id']})")

    # 模擬系統檢測結果
    detected = [
        {'type': 'NAME', 'content': '陳老先生'},
        {'type': 'AGE_OVER_89', 'content': '94'},
        # 缺少 PHONE (False Negative)
        {'type': 'DATE', 'content': '2024'},  # 多檢測了一個 (False Positive)
    ]

    # 計算指標
    metrics = evaluator.calculate_metrics(ground_truth, detected, match_mode='exact')

    evaluator.print_evaluation_report(metrics, "Demo Evaluation")

    print("\n\n" + "="*70)
    print("💡 使用說明:")
    print("="*70)
    print("\n1. 載入帶標記的測試文件:")
    print("   df = pd.read_excel('data/test/test_phi_tagged_cases.xlsx')")
    print("\n2. 執行 PHI 檢測系統，獲得檢測結果:")
    print("   detected_phi_dict = {")
    print("       'CASE-001': [{'type': 'NAME', 'content': '陳老先生'}, ...],")
    print("       'CASE-002': [...],")
    print("       ...")
    print("   }")
    print("\n3. 評估檢測效能:")
    print("   evaluator = PHIEvaluator()")
    print("   results = evaluator.evaluate_from_excel(")
    print("       'data/test/test_phi_tagged_cases.xlsx',")
    print("       detected_phi_dict")
    print("   )")
    print("   evaluator.print_evaluation_report(results)")
