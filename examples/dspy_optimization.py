#!/usr/bin/env python3
"""
🧠 DSPy Prompt Optimization Example
===================================

使用 DSPy 自動優化 PHI 識別的 prompt。
這是本專案的核心差異化功能。

What is DSPy?
- 自動化 prompt engineering
- 基於訓練資料優化 prompt
- 無需手動調整 prompt 模板

Prerequisites:
    1. pip install -e .
    2. ollama pull granite4:1b
    
Usage:
    python examples/dspy_optimization.py
    python examples/dspy_optimization.py --optimize  # Run optimization
"""

import argparse

# DSPy integration
from medical_deidentification.infrastructure.dspy import (
    PHIIdentifier,
    PHIPromptOptimizer,
    configure_dspy_ollama,
    LIGHTWEIGHT_MODELS,
)


def show_available_models():
    """顯示可用的輕量模型"""
    print("\n📋 Available Lightweight Models (CPU-friendly):")
    print("-" * 60)
    for name, info in LIGHTWEIGHT_MODELS.items():
        recommended = "✅" if info.get("recommended") else "  "
        f1 = info.get("f1_score")
        f1_str = f"F1={f1*100:.1f}%" if f1 else "N/A"
        print(f"  {recommended} {name:20s} {info['size']:>8s}  {f1_str:>10s}")
        print(f"      {info['description']}")
    print("-" * 60)


def basic_usage():
    """基本用法：直接使用 PHIIdentifier"""
    print("\n" + "=" * 60)
    print("🔍 Basic Usage: PHIIdentifier")
    print("=" * 60)
    
    # Configure DSPy with Ollama
    configure_dspy_ollama(model_name="granite4:1b")
    
    # Create identifier
    identifier = PHIIdentifier()
    
    # Test text
    test_text = """
    Patient John Smith (DOB: 1990-05-15) visited Dr. Mary Johnson 
    at Taipei General Hospital on 2024-01-20. 
    Contact: 0912-345-678, email: john.smith@email.com
    Address: 100 Xinyi Road, Taipei City
    """
    
    print(f"\n📝 Input:\n{test_text.strip()}")
    
    # Identify PHI
    print("\n🔍 Identifying PHI...")
    entities = identifier.forward(medical_text=test_text)
    
    print(f"\n✅ Found {len(entities)} PHI entities:")
    for entity in entities:
        print(f"   [{entity.phi_type:15}] {entity.text}")


def optimization_demo():
    """進階用法：使用 DSPy 優化"""
    print("\n" + "=" * 60)
    print("🧠 Advanced Usage: DSPy Optimization")
    print("=" * 60)
    
    print("""
    DSPy Optimization Workflow:
    
    1. Prepare training data (labeled examples)
    2. Configure optimizer (BootstrapFewShot or MIPRO)
    3. Run optimization
    4. Evaluate and save optimized module
    
    Benefits:
    - Automatic prompt improvement
    - No manual prompt engineering
    - Adapts to your specific data
    """)
    
    # Example training data format
    print("\n📚 Training Data Format:")
    print("-" * 40)
    
    example_data = [
        {
            "medical_text": "病患王大明，身分證 A123456789，電話 0912-345-678",
            "expected_phi": [
                {"text": "王大明", "type": "NAME"},
                {"text": "A123456789", "type": "ID"},
                {"text": "0912-345-678", "type": "PHONE"},
            ]
        },
        {
            "medical_text": "Dr. Smith treated patient at Taipei Hospital on 2024-01-15",
            "expected_phi": [
                {"text": "Smith", "type": "NAME"},
                {"text": "Taipei Hospital", "type": "FACILITY"},
                {"text": "2024-01-15", "type": "DATE"},
            ]
        },
    ]
    
    import json
    print(json.dumps(example_data[0], indent=2, ensure_ascii=False))
    
    print("""
    
    📖 To run actual optimization:
    
    ```python
    from medical_deidentification.infrastructure.dspy import PHIPromptOptimizer
    
    optimizer = PHIPromptOptimizer()
    result = optimizer.optimize(
        trainset=training_examples,
        method="bootstrap",  # or "mipro"
        max_iterations=10
    )
    
    # Use optimized module
    optimized_identifier = result.best_module
    print(f"F1 improved: {result.baseline_score:.2%} → {result.optimized_score:.2%}")
    ```
    
    See scripts/dspy_phi_optimizer.py for full implementation.
    """)


def main():
    parser = argparse.ArgumentParser(description="DSPy PHI Optimization Demo")
    parser.add_argument("--optimize", action="store_true", help="Show optimization demo")
    parser.add_argument("--models", action="store_true", help="Show available models")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧠 DSPy Prompt Optimization for PHI Detection")
    print("=" * 60)
    
    if args.models:
        show_available_models()
        return
    
    if args.optimize:
        optimization_demo()
    else:
        basic_usage()
    
    print("\n" + "=" * 60)
    print("✨ Done!")
    print("=" * 60)
    print("\nNext steps:")
    print("  --models    Show available lightweight models")
    print("  --optimize  Show optimization workflow")


if __name__ == "__main__":
    main()
