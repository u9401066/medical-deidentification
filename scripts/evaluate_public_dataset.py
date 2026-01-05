#!/usr/bin/env python
"""
PHI Evaluation with Public NER Datasets
使用公開 NER 資料集的 PHI 評估

This script uses public datasets from Hugging Face to evaluate PHI detection.
Supported datasets:
  - WikiANN (PAN-X format): PER, ORG, LOC entities
  - XTREME PAN-X: Same as WikiANN but with better availability

此腳本使用 Hugging Face 的公開資料集來評估 PHI 檢測。

Usage:
    python scripts/evaluate_public_dataset.py
    python scripts/evaluate_public_dataset.py --model qwen2.5:3b --dataset wikiann --lang zh
"""

import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from datasets import load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("⚠️  Please install datasets: pip install datasets")

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Our domain models - structured output!
from core.domain.phi_identification_models import (
    PHIDetectionResponse,
)
from core.infrastructure.prompts import (
    get_phi_identification_prompt,
    get_system_message,
)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ConfusionMatrix:
    """Complete Confusion Matrix for evaluation"""
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
    
    def __add__(self, other: "ConfusionMatrix") -> "ConfusionMatrix":
        return ConfusionMatrix(
            true_positives=self.true_positives + other.true_positives,
            false_positives=self.false_positives + other.false_positives,
            false_negatives=self.false_negatives + other.false_negatives,
        )


@dataclass
class NERExample:
    """A single NER example from public dataset"""
    text: str
    entities: List[Dict[str, Any]]  # {"text": "...", "type": "PER|ORG|LOC"}
    source: str = ""


# =============================================================================
# Dataset Loaders
# =============================================================================

# NER tag mapping for BIO format
TAG_MAP = {0: 'O', 1: 'B-PER', 2: 'I-PER', 3: 'B-ORG', 4: 'I-ORG', 5: 'B-LOC', 6: 'I-LOC'}

# Which tags are considered PHI (person and location are PII/PHI related)
PHI_TAGS = {'B-PER', 'I-PER', 'B-LOC', 'I-LOC'}  # ORG is less sensitive


def load_wikiann(lang: str = "en", split: str = "test", max_examples: int = 50) -> List[NERExample]:
    """
    Load WikiANN dataset from Hugging Face
    
    WikiANN contains: PER (person), ORG (organization), LOC (location)
    We treat PER and LOC as PHI since they can identify individuals.
    
    Args:
        lang: Language code (en, zh, de, fr, etc.)
        split: Dataset split (train, validation, test)
        max_examples: Maximum number of examples to load
        
    Returns:
        List of NERExample
    """
    print(f"📂 Loading WikiANN ({lang}) {split}[::{max_examples}]...")
    
    ds = load_dataset("wikiann", lang, split=f"{split}[:{max_examples}]")
    
    examples = []
    for item in ds:
        tokens = item["tokens"]
        tags = item["ner_tags"]
        
        text = " ".join(tokens)
        
        # Extract entities using BIO tags
        entities = []
        current_entity = None
        current_type = None
        
        for token, tag_id in zip(tokens, tags):
            tag = TAG_MAP.get(tag_id, "O")
            
            if tag.startswith("B-"):
                # Save previous entity
                if current_entity:
                    entities.append({
                        "text": current_entity,
                        "type": current_type
                    })
                # Start new entity
                current_type = tag[2:]  # PER, ORG, LOC
                current_entity = token
            elif tag.startswith("I-") and current_entity:
                # Continue entity
                current_entity += " " + token
            else:
                # End entity
                if current_entity:
                    entities.append({
                        "text": current_entity,
                        "type": current_type
                    })
                    current_entity = None
                    current_type = None
        
        # Don't forget last entity
        if current_entity:
            entities.append({
                "text": current_entity,
                "type": current_type
            })
        
        # Filter to PHI-relevant entities (PER and LOC)
        phi_entities = [e for e in entities if e["type"] in {"PER", "LOC"}]
        
        if phi_entities:  # Only include examples with PHI
            examples.append(NERExample(
                text=text,
                entities=phi_entities,
                source=f"wikiann-{lang}"
            ))
    
    print(f"   Loaded {len(examples)} examples with PHI entities")
    return examples


def load_xtreme_panx(lang: str = "en", split: str = "test", max_examples: int = 50) -> List[NERExample]:
    """
    Load XTREME PAN-X dataset from Hugging Face
    
    Same format as WikiANN but may have better availability.
    """
    print(f"📂 Loading XTREME PAN-X ({lang}) {split}[::{max_examples}]...")
    
    config = f"PAN-X.{lang}"
    ds = load_dataset("xtreme", config, split=f"{split}[:{max_examples}]")
    
    examples = []
    for item in ds:
        tokens = item["tokens"]
        tags = item["ner_tags"]
        
        text = " ".join(tokens)
        
        # Extract entities using BIO tags
        entities = []
        current_entity = None
        current_type = None
        
        for token, tag_id in zip(tokens, tags):
            tag = TAG_MAP.get(tag_id, "O")
            
            if tag.startswith("B-"):
                if current_entity:
                    entities.append({"text": current_entity, "type": current_type})
                current_type = tag[2:]
                current_entity = token
            elif tag.startswith("I-") and current_entity:
                current_entity += " " + token
            else:
                if current_entity:
                    entities.append({"text": current_entity, "type": current_type})
                    current_entity = None
                    current_type = None
        
        if current_entity:
            entities.append({"text": current_entity, "type": current_type})
        
        # Filter to PHI-relevant entities
        phi_entities = [e for e in entities if e["type"] in {"PER", "LOC"}]
        
        if phi_entities:
            examples.append(NERExample(
                text=text,
                entities=phi_entities,
                source=f"xtreme-{lang}"
            ))
    
    print(f"   Loaded {len(examples)} examples with PHI entities")
    return examples


# =============================================================================
# PHI Detector
# =============================================================================

class LangChainPHIDetector:
    """PHI Detector using LangChain Structured Output"""
    
    def __init__(self, model_name: str = "qwen2.5:1.5b", language: str = "en"):
        self.model_name = model_name
        
        self.llm = ChatOllama(
            model=model_name,
            temperature=0.1,
            num_predict=4096,  # Increased to handle longer outputs
        )
        
        # Use NER-focused system message
        self.system_message = f"""You are an expert Named Entity Recognition (NER) system.
Your task is to identify all personal identifiable information (PII/PHI) in text.

Focus on:
- Person names (full names, first names, last names)
- Locations (cities, countries, addresses, places)
- Any information that could identify a specific person

Output must be in the requested structured format."""
        
        self.prompt_text = """Identify all Personal Identifiable Information (PII/PHI) in the following text.

Text: {text}

Extract all:
1. Person names (names of people)
2. Locations (cities, countries, addresses, places)

For each entity found, provide:
- entity_text: The exact text of the entity
- entity_type: One of [NAME, LOCATION]
- confidence_score: 0.0 to 1.0

If no PHI is found, return an empty list."""
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("user", self.prompt_text)
        ])
        
        self.chain = self.prompt | self.llm.with_structured_output(PHIDetectionResponse)
        
        print(f"  ✓ Model: {model_name}")
        print(f"  ✓ Using PHIDetectionResponse structured output")
    
    def detect(self, text: str) -> Tuple[List[str], Optional[PHIDetectionResponse]]:
        """
        Detect PHI in text
        
        Returns:
            Tuple of (list of PHI texts, full response or None on error)
        """
        try:
            response: PHIDetectionResponse = self.chain.invoke({"text": text})
            phi_texts = [entity.entity_text for entity in response.entities]
            return phi_texts, response
        except Exception as e:
            print(f"    ⚠️  Error: {e}")
            return [], None


# =============================================================================
# Evaluation
# =============================================================================

def calculate_cm(predicted: List[str], ground_truth: List[str]) -> ConfusionMatrix:
    """Calculate confusion matrix with fuzzy matching"""
    pred_set = {p.lower().strip() for p in predicted if p.strip()}
    gt_set = {g.lower().strip() for g in ground_truth if g.strip()}
    
    matched_gt = set()
    tp = 0
    
    for pred in pred_set:
        for gt in gt_set:
            if gt not in matched_gt:
                # Fuzzy match: substring or exact
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
    print(f"  │ True Positives (TP) │ {cm.true_positives:>10} │  ✓ Correct")
    print(f"  ├─────────────────────┼────────────┤")
    print(f"  │ False Positives(FP) │ {cm.false_positives:>10} │  ⚠ Over-detected")
    print(f"  ├─────────────────────┼────────────┤")
    print(f"  │ False Negatives(FN) │ {cm.false_negatives:>10} │  ❌ Missed")
    print(f"  └─────────────────────┴────────────┘")
    
    print(f"\n📈 Metrics:")
    print(f"  • Precision: {cm.precision:>7.1%}")
    print(f"  • Recall:    {cm.recall:>7.1%}")
    print(f"  • F1 Score:  {cm.f1:>7.1%}")
    print(f"  • Avg Time:  {avg_time:>7.0f} ms")
    
    # Grade
    if cm.f1 >= 0.9:
        grade = "A⭐⭐⭐"
    elif cm.f1 >= 0.8:
        grade = "B⭐⭐"
    elif cm.f1 >= 0.7:
        grade = "C⭐"
    elif cm.f1 >= 0.5:
        grade = "D"
    else:
        grade = "F❌"
    
    print(f"\n🎯 Grade: {grade}")


# =============================================================================
# Main
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate PHI detection with public datasets")
    parser.add_argument("--model", type=str, default="qwen2.5:1.5b", 
                        help="Ollama model name")
    parser.add_argument("--dataset", type=str, default="wikiann",
                        choices=["wikiann", "xtreme"],
                        help="Dataset to use")
    parser.add_argument("--lang", type=str, default="en",
                        help="Language code (en, zh, de, fr, etc.)")
    parser.add_argument("--split", type=str, default="test",
                        help="Dataset split (train, validation, test)")
    parser.add_argument("--max-examples", type=int, default=30,
                        help="Maximum examples to evaluate")
    args = parser.parse_args()
    
    print("=" * 70)
    print("PHI Evaluation with Public NER Dataset")
    print("=" * 70)
    
    if not HF_AVAILABLE:
        print("❌ datasets library not available")
        return
    
    # Load dataset
    print(f"\n📊 Dataset Configuration:")
    print(f"  • Dataset: {args.dataset}")
    print(f"  • Language: {args.lang}")
    print(f"  • Split: {args.split}")
    print(f"  • Max examples: {args.max_examples}")
    
    if args.dataset == "wikiann":
        examples = load_wikiann(args.lang, args.split, args.max_examples)
    else:
        examples = load_xtreme_panx(args.lang, args.split, args.max_examples)
    
    if not examples:
        print("❌ No examples loaded!")
        return
    
    # Show sample
    print(f"\n📝 Sample Example:")
    sample = examples[0]
    print(f"  Text: {sample.text[:100]}...")
    print(f"  Entities: {sample.entities[:3]}...")
    
    # Create detector
    print(f"\n🔧 Creating PHI Detector...")
    detector = LangChainPHIDetector(model_name=args.model, language=args.lang)
    
    # Evaluate
    print(f"\n🔍 Evaluating {len(examples)} examples...")
    total_cm = ConfusionMatrix()
    total_time = 0.0
    errors = 0
    
    for i, ex in enumerate(examples):
        # Get ground truth
        gt = [e["text"] for e in ex.entities]
        
        # Detect
        start = time.time()
        predictions, response = detector.detect(ex.text)
        elapsed = (time.time() - start) * 1000
        
        if response is None:
            errors += 1
            total_cm.false_negatives += len(gt)
            continue
        
        total_time += elapsed
        
        # Calculate CM
        cm = calculate_cm(predictions, gt)
        total_cm = total_cm + cm
        
        # Progress
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  [{i+1:>3}/{len(examples)}] TP={cm.true_positives}, "
                  f"FP={cm.false_positives}, FN={cm.false_negatives}, {elapsed:.0f}ms")
    
    # Results
    avg_time = total_time / (len(examples) - errors) if (len(examples) - errors) > 0 else 0
    
    print_results(
        total_cm, 
        avg_time, 
        f"Results: {args.model} on {args.dataset}-{args.lang}"
    )
    
    if errors > 0:
        print(f"\n⚠️  {errors} examples had errors")
    
    print(f"\n✅ Evaluation complete!")


if __name__ == "__main__":
    main()
