#!/usr/bin/env python3
"""
Quick test: Single file PHI identification (non-streaming)
快速測試：單一檔案 PHI 識別（非串流）
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_direct_llm_call():
    """Test 1: Direct LLM call without any chain"""
    print("\n" + "="*60)
    print("TEST 1: Direct LLM Call (No Chain)")
    print("="*60)

    from core.infrastructure.llm.config import LLMConfig
    from core.infrastructure.llm.factory import create_llm

    llm_config = LLMConfig(
        provider="ollama",
        model_name="qwen2.5:1.5b",
        temperature=0.0,
        timeout=60.0,
    )
    llm = create_llm(llm_config)

    test_text = "Patient 陳老先生, 94-year-old male. Phone: 02-2758-9999. ID: A123456789."

    start = time.time()
    response = llm.invoke(f"Extract PHI from: {test_text}")
    elapsed = time.time() - start

    print(f"Response: {response.content[:300]}...")
    print(f"⏱️  Time: {elapsed:.2f}s")
    return elapsed


def test_prompt_chain():
    """Test 2: LangChain prompt | llm chain with simple JSON output"""
    print("\n" + "="*60)
    print("TEST 2: Prompt | LLM | StrOutputParser")
    print("="*60)

    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    from core.infrastructure.llm.config import LLMConfig
    from core.infrastructure.llm.factory import create_llm

    llm_config = LLMConfig(
        provider="ollama",
        model_name="qwen2.5:1.5b",
        temperature=0.0,
        timeout=60.0,
    )
    llm = create_llm(llm_config)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a PHI identification expert. Return JSON array."),
        ("user", """Extract PHI entities from this medical text.

Return JSON array like:
[{{"entity_text": "...", "phi_type": "NAME|PHONE|ID|AGE_OVER_89", "confidence": 0.9}}]

Text: {text}""")
    ])

    chain = prompt | llm | StrOutputParser()

    test_text = "Patient 陳老先生, 94-year-old male. Phone: 02-2758-9999. ID: A123456789."

    start = time.time()
    response = chain.invoke({"text": test_text})
    elapsed = time.time() - start

    print(f"Response:\n{response[:500]}")
    print(f"⏱️  Time: {elapsed:.2f}s")
    return elapsed


def test_json_fallback():
    """Test 3: processors.identify_phi_json_fallback"""
    print("\n" + "="*60)
    print("TEST 3: identify_phi_json_fallback (Existing Module)")
    print("="*60)

    from core.infrastructure.llm.config import LLMConfig
    from core.infrastructure.llm.factory import create_llm
    from core.infrastructure.rag.chains.processors import (
        identify_phi_with_parser as identify_phi_json_fallback,
    )

    llm_config = LLMConfig(
        provider="ollama",
        model_name="qwen2.5:1.5b",
        temperature=0.0,
        timeout=60.0,
    )
    llm = create_llm(llm_config)

    test_text = "Patient 陳老先生, 94-year-old male. Phone: 02-2758-9999. ID: A123456789."
    context = """PHI types to identify:
- NAME: Patient names
- AGE_OVER_89: Ages over 89 years
- PHONE: Phone numbers
- ID: ID numbers"""

    start = time.time()
    try:
        entities, raw = identify_phi_json_fallback(
            text=test_text,
            context=context,
            llm=llm,
            language="zh-TW"
        )
        elapsed = time.time() - start

        print(f"Entities found: {len(entities)}")
        for e in entities[:5]:
            print(f"  - {e.type.value}: '{e.text}'")
        print(f"⏱️  Time: {elapsed:.2f}s")
        return elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Error after {elapsed:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return elapsed


def main():
    print("="*60)
    print("PHI IDENTIFICATION PERFORMANCE TEST")
    print("Model: qwen2.5:1.5b via Ollama")
    print("="*60)

    results = {}

    # Test 1: Direct
    results['direct_llm'] = test_direct_llm_call()

    # Test 2: Simple chain
    results['prompt_chain'] = test_prompt_chain()

    # Test 3: JSON fallback (what streaming should use)
    results['json_fallback'] = test_json_fallback()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, time_sec in results.items():
        status = "✅" if 0 < time_sec < 10 else "⚠️" if 0 < time_sec < 30 else "❌"
        print(f"{status} {name}: {time_sec:.2f}s")

    avg = sum(results.values()) / len(results)
    print(f"\n📊 Average: {avg:.2f}s per call")
    print("💡 If streaming is much slower, the issue is in streaming chain overhead")


if __name__ == "__main__":
    main()
