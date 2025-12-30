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

NEW: YAML-based Prompt Configuration
- Prompt 配置存儲在 YAML 檔案中
- 支援版本控制
- 優化結果可保存到新版本 YAML

Prerequisites:
    1. pip install -e .
    2. ollama pull granite4:1b
    
Usage:
    python examples/dspy_optimization.py
    python examples/dspy_optimization.py --optimize  # Run optimization
    python examples/dspy_optimization.py --yaml      # Use YAML config
"""

import argparse

# DSPy integration
from medical_deidentification.infrastructure.dspy import (
    PHIIdentifier,
    PHIPromptOptimizer,
    configure_dspy_ollama,
    LIGHTWEIGHT_MODELS,
    # NEW: YAML integration
    PHIIdentifierWithConfig,
    create_phi_identifier_from_yaml,
    optimize_and_save_to_yaml,
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


def yaml_config_demo():
    """NEW: 使用 YAML 配置的 PHI 識別"""
    print("\n" + "=" * 60)
    print("📄 NEW: YAML-based Prompt Configuration")
    print("=" * 60)
    
    print("""
    YAML Prompt Configuration provides:
    
    ✅ Version control for prompts
    ✅ Easy customization without code changes
    ✅ Model-specific prompt selection
    ✅ Optimization result persistence
    """)
    
    # Configure DSPy
    configure_dspy_ollama(model_name="granite4:1b")
    
    # Method 1: Use factory function
    print("\n📌 Method 1: Factory Function")
    print("-" * 40)
    print("""
    identifier = create_phi_identifier_from_yaml(
        config_name="phi_identification",
        model_name="granite4:1b",
    )
    entities = identifier("病患王大明...")
    """)
    
    try:
        identifier = create_phi_identifier_from_yaml(
            config_name="phi_identification",
            model_name="granite4:1b",
        )
        
        # Test
        test_text = "病患王大明，身分證 A123456789，電話 0912-345-678"
        print(f"\n📝 Test: {test_text}")
        
        entities = identifier(test_text)
        print(f"✅ Found {len(entities)} PHI:")
        for e in entities:
            print(f"   [{e.phi_type}] {e.text}")
            
    except Exception as e:
        print(f"⚠️ Demo skipped: {e}")
        print("   (Run `ollama serve` and `ollama pull granite4:1b` first)")
    
    # Method 2: Load prompt config directly
    print("\n📌 Method 2: Direct Config Access")
    print("-" * 40)
    
    try:
        from medical_deidentification.infrastructure.prompts import load_prompt_config
        
        config = load_prompt_config("phi_identification")
        
        print(f"Config: {config.name} v{config.version}")
        print(f"PHI Types: {config.get_phi_type_list()[:5]}...")
        print(f"Few-shot Examples: {len(config.few_shot_examples)}")
        
        # Get prompt for specific model
        prompt = config.get_prompt(
            name="simplified",
            medical_text="[示例文本]",
        )
        print(f"\nPrompt preview (first 200 chars):")
        print(f"   {prompt[:200]}...")
        
    except Exception as e:
        print(f"⚠️ Config not available: {e}")


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
    4. Save optimized config to new YAML version
    
    Benefits:
    - Automatic prompt improvement
    - No manual prompt engineering
    - Results persisted to YAML
    """)
    
    # Example training data format
    print("\n📚 Training Data Format (Tagged Text):")
    print("-" * 40)
    
    tagged_examples = [
        "病患【PHI:NAME:1】王大明【/PHI】，身分證【PHI:ID:2】A123456789【/PHI】",
        "主治醫師【PHI:NAME:3】張明華【/PHI】，入院日【PHI:DATE:4】2024-05-15【/PHI】",
        "【PHI:AGE_OVER_89:5】92歲【/PHI】女性，於【PHI:FACILITY:6】台北榮總【/PHI】就醫",
    ]
    
    for ex in tagged_examples[:2]:
        print(f"  {ex}")
    
    print("""
    
    📖 To run optimization and save to YAML:
    
    ```python
    from medical_deidentification.infrastructure.dspy import (
        optimize_and_save_to_yaml,
        load_optimized_identifier,
    )
    
    # Optimize and save to new YAML version
    result, yaml_path = optimize_and_save_to_yaml(
        tagged_texts=tagged_examples,
        model_name="granite4:1b",
        config_name="phi_identification",
        method="bootstrap",
    )
    
    print(f"F1: {result.original_score:.2%} → {result.optimized_score:.2%}")
    print(f"Saved to: {yaml_path}")
    
    # Load optimized identifier
    identifier = load_optimized_identifier(
        config_name="phi_identification",
        version="1.1.0",  # Or None for latest
    )
    ```
    
    📁 YAML files saved to:
       medical_deidentification/infrastructure/prompts/phi_identification.v*.yaml
    """)


def main():
    parser = argparse.ArgumentParser(description="DSPy PHI Optimization Demo")
    parser.add_argument("--optimize", action="store_true", help="Show optimization demo")
    parser.add_argument("--yaml", action="store_true", help="Show YAML config demo")
    parser.add_argument("--models", action="store_true", help="Show available models")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧠 DSPy Prompt Optimization for PHI Detection")
    print("=" * 60)
    
    if args.models:
        show_available_models()
        return
    
    if args.yaml:
        yaml_config_demo()
    elif args.optimize:
        optimization_demo()
    else:
        basic_usage()
    
    print("\n" + "=" * 60)
    print("✨ Done!")
    print("=" * 60)
    print("\nOptions:")
    print("  --models    Show available lightweight models")
    print("  --yaml      Show YAML prompt configuration (NEW)")
    print("  --optimize  Show optimization workflow")


if __name__ == "__main__":
    main()
