#!/usr/bin/env python
"""
PHI Evaluation with LangChain Structured Output
使用 LangChain 結構化輸出的 PHI 評估

This script uses the existing LangChain structured output (PHIDetectionResponse)
to evaluate PHI detection performance with full confusion matrix metrics.

此腳本使用現有的 LangChain 結構化輸出 (PHIDetectionResponse)
來評估 PHI 檢測性能，包含完整的混淆矩陣指標。

Usage:
    python scripts/evaluate_langchain_phi.py
    python scripts/evaluate_langchain_phi.py --model qwen2.5:3b
"""

import sys
import time
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from loguru import logger

# LangChain
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Our domain models - the structured output schema!
from medical_deidentification.domain.phi_identification_models import (
    PHIDetectionResponse,
)
from medical_deidentification.infrastructure.prompts import (
    get_phi_identification_prompt,
    get_system_message,
    DEFAULT_HIPAA_SAFE_HARBOR_RULES,
)

print("=" * 70)
print("PHI Evaluation - LangChain Structured Output")
print("=" * 70)


# =============================================================================
# Confusion Matrix
# =============================================================================

@dataclass
class ConfusionMatrix:
    """Complete Confusion Matrix"""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    @property
    def precision(self) -> float:
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 0.0
    
    @property
    def recall(self) -> float:
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0
    
    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


# =============================================================================
# LangChain PHI Detector
# =============================================================================

class LangChainPHIDetector:
    """
    PHI Detector using LangChain Structured Output
    
    Uses PHIDetectionResponse Pydantic model for structured output.
    This ensures consistent schema and validation.
    """
    
    def __init__(self, model_name: str = "qwen2.5:1.5b", language: str = "en"):
        self.model_name = model_name
        
        # Initialize LLM
        self.llm = ChatOllama(
            model=model_name,
            temperature=0.1,
            num_predict=2048,
        )
        
        # Get prompts from our centralized module
        self.prompt_text = get_phi_identification_prompt(language=language, structured=True)
        self.system_message = get_system_message("phi_expert", language=language)
        
        # Build LangChain prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("user", self.prompt_text)
        ])
        
        # Build chain with structured output!
        self.chain = self.prompt | self.llm.with_structured_output(PHIDetectionResponse)
        
        print(f"  ✓ Model: {model_name}")
        print(f"  ✓ Using PHIDetectionResponse structured output")
        print(f"  ✓ Prompt length: {len(self.prompt_text)} chars")
    
    def detect(self, text: str, context: str = "") -> Tuple[List[str], PHIDetectionResponse]:
        """
        Detect PHI using LangChain structured output
        
        Args:
            text: Medical text to analyze
            context: Regulation context (uses default if empty)
            
        Returns:
            Tuple of (list of PHI texts, full PHIDetectionResponse)
        """
        if not context:
            context = DEFAULT_HIPAA_SAFE_HARBOR_RULES
        
        # Invoke chain
        response: PHIDetectionResponse = self.chain.invoke({
            "context": context,
            "text": text
        })
        
        # Extract PHI texts
        phi_texts = [entity.entity_text for entity in response.entities]
        
        return phi_texts, response


# =============================================================================
# Data Loading & Metrics
# =============================================================================

def load_tagged_data(file_path: str) -> List[Dict[str, Any]]:
    """Load test data with PHI tags"""
    df = pd.read_excel(file_path)
    
    tag_pattern = r'【PHI:(\w+):[\w-]+】([^【]+)【/PHI】'
    
    text_columns = [col for col in df.columns 
                    if any(x in col.replace('\n', ' ') 
                           for x in ['Summary', 'Contact', 'History', 'Treatment', 'Notes'])]
    
    examples = []
    for _, row in df.iterrows():
        for col in text_columns:
            if col in row and pd.notna(row[col]):
                text = str(row[col])
                matches = re.findall(tag_pattern, text)
                ground_truth = [content.strip() for _, content in matches]
                
                if ground_truth:
                    clean_text = re.sub(r'【PHI:\w+:[\w-]+】', '', text)
                    clean_text = re.sub(r'【/PHI】', '', clean_text)
                    examples.append({
                        'text': clean_text.strip(),
                        'ground_truth': ground_truth,
                    })
    
    return examples


def calculate_cm(predicted: List[str], ground_truth: List[str]) -> ConfusionMatrix:
    """Calculate confusion matrix with fuzzy matching"""
    pred_set = {p.lower().strip() for p in predicted if p.strip()}
    gt_set = {g.lower().strip() for g in ground_truth if g.strip()}
    
    matched_gt = set()
    tp = 0
    
    for pred in pred_set:
        for gt in gt_set:
            if gt not in matched_gt:
                if pred in gt or gt in pred or pred == gt:
                    tp += 1
                    matched_gt.add(gt)
                    break
    
    return ConfusionMatrix(
        true_positives=tp,
        false_positives=len(pred_set) - tp,
        false_negatives=len(gt_set) - len(matched_gt),
    )


def print_results(cm: ConfusionMatrix, avg_time: float, title: str):
    """Print evaluation results"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    print(f"\n📊 Confusion Matrix:")
    print(f"  ┌─────────────────────┬────────────┐")
    print(f"  │ True Positives (TP) │ {cm.true_positives:>10} │  ✓ 正確檢測")
    print(f"  ├─────────────────────┼────────────┤")
    print(f"  │ False Positives(FP) │ {cm.false_positives:>10} │  ⚠ 誤報")
    print(f"  ├─────────────────────┼────────────┤")
    print(f"  │ False Negatives(FN) │ {cm.false_negatives:>10} │  ❌ 漏檢")
    print(f"  └─────────────────────┴────────────┘")
    
    print(f"\n📈 Metrics:")
    print(f"  • Precision: {cm.precision:>7.1%}")
    print(f"  • Recall:    {cm.recall:>7.1%}")
    print(f"  • F1 Score:  {cm.f1:>7.1%}")
    print(f"  • Avg Time:  {avg_time:>7.0f} ms")
    
    grade = "A⭐⭐⭐" if cm.f1 >= 0.9 else "B⭐⭐" if cm.f1 >= 0.8 else "C⭐" if cm.f1 >= 0.7 else "D" if cm.f1 >= 0.5 else "F❌"
    print(f"\n🎯 Grade: {grade}")


# =============================================================================
# Main
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="qwen2.5:1.5b")
    parser.add_argument("--test-file", type=str, default="data/test/test_phi_tagged_cases.xlsx")
    parser.add_argument("--max-examples", type=int, default=3)
    args = parser.parse_args()
    
    # Load data
    test_file = project_root / args.test_file
    print(f"\n📂 Loading: {test_file}")
    examples = load_tagged_data(str(test_file))[:args.max_examples]
    print(f"   Loaded {len(examples)} examples")
    
    # Create detector
    print(f"\n🔧 Creating LangChain PHI Detector")
    detector = LangChainPHIDetector(model_name=args.model)
    
    # Evaluate
    print(f"\n🔍 Evaluating...")
    total_cm = ConfusionMatrix()
    total_time = 0.0
    
    for i, ex in enumerate(examples):
        start = time.time()
        
        try:
            predictions, response = detector.detect(ex['text'])
            elapsed = (time.time() - start) * 1000
            total_time += elapsed
            
            cm = calculate_cm(predictions, ex['ground_truth'])
            total_cm.true_positives += cm.true_positives
            total_cm.false_positives += cm.false_positives
            total_cm.false_negatives += cm.false_negatives
            
            print(f"  Ex {i+1}: TP={cm.true_positives}, FP={cm.false_positives}, FN={cm.false_negatives}, {elapsed:.0f}ms")
            print(f"    GT:   {ex['ground_truth'][:3]}...")
            print(f"    Pred: {predictions[:3]}...")
            
        except Exception as e:
            print(f"  Ex {i+1}: ERROR - {e}")
            total_cm.false_negatives += len(ex['ground_truth'])
    
    # Results
    avg_time = total_time / len(examples) if examples else 0
    print_results(total_cm, avg_time, f"Results ({args.model})")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
