#!/usr/bin/env python3
"""
🚀 Quick Start - 30 秒上手
==========================

最簡單的 PHI 去識別化範例。

Prerequisites:
    1. Install: pip install -e .
    2. Start Ollama: ollama serve
    3. Pull model: ollama pull granite4:1b
    
Usage:
    python examples/quick_start.py
"""

from medical_deidentification.infrastructure.llm import LLMConfig, create_llm
from medical_deidentification.infrastructure.rag import PHIIdentificationChain, PHIIdentificationConfig


def main():
    # 📝 測試文本（含 PHI）
    medical_text = """
    病患姓名：王大明
    身分證字號：A123456789
    出生日期：1985年3月15日
    聯絡電話：0912-345-678
    電子郵件：wang.daming@email.com
    住址：台北市信義區松仁路100號
    
    主訴：患者因持續頭痛三天前來就診。
    診斷：偏頭痛 (Migraine)
    主治醫師：李醫師，台北榮民總醫院
    """
    
    print("=" * 60)
    print("🏥 Medical De-identification - Quick Start")
    print("=" * 60)
    
    # 🔧 配置 LLM（使用本地 Ollama）
    llm_config = LLMConfig(
        provider="ollama",
        model_name="granite4:1b",  # 🏆 Best for PHI (F1=89.4%)
        temperature=0.0,
        timeout=120,
    )
    
    # 🔗 創建 PHI 識別 Chain
    phi_config = PHIIdentificationConfig(
        llm_config=llm_config,
        retrieve_regulation_context=False,  # 不需要 RAG
        use_structured_output=True,
    )
    
    chain = PHIIdentificationChain(config=phi_config)
    
    print("\n📝 Input Text:")
    print("-" * 40)
    print(medical_text.strip())
    print("-" * 40)
    
    # 🔍 識別 PHI
    print("\n🔍 Identifying PHI...")
    entities = chain.identify_phi(medical_text, language="zh-TW")
    
    # 📊 顯示結果
    print(f"\n✅ Found {len(entities)} PHI entities:\n")
    
    for i, entity in enumerate(entities, 1):
        phi_type = entity.get_type_name() if hasattr(entity, 'get_type_name') else entity.phi_type
        print(f"  {i}. [{phi_type:15}] {entity.text}")
    
    print("\n" + "=" * 60)
    print("✨ Done! See examples/ for more advanced usage.")
    print("=" * 60)


if __name__ == "__main__":
    main()
