#!/usr/bin/env python3
"""
Quick test: Single file PHI identification (non-streaming)
快速測試：單一檔案 PHI 識別（非串流）

Compare with streaming chain to identify performance bottleneck
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="DEBUG", format="{time:HH:mm:ss} | {level} | {message}")


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

    print(f"Response: {response.content[:200]}...")
    print(f"⏱️  Time: {elapsed:.2f}s")
    return elapsed


def test_prompt_chain():
    """Test 2: LangChain prompt | llm chain"""
    print("\n" + "="*60)
    print("TEST 2: Prompt | LLM Chain")
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
        ("system", "You are a PHI identification expert."),
        ("user", "Extract PHI entities from this medical text as JSON array:\n{text}")
    ])

    chain = prompt | llm | StrOutputParser()

    test_text = "Patient 陳老先生, 94-year-old male. Phone: 02-2758-9999. ID: A123456789."

    start = time.time()
    response = chain.invoke({"text": test_text})
    elapsed = time.time() - start

    print(f"Response: {response[:300]}...")
    print(f"⏱️  Time: {elapsed:.2f}s")
    return elapsed


def test_structured_output():
    """Test 3: LangChain with_structured_output"""
    print("\n" + "="*60)
    print("TEST 3: with_structured_output (Pydantic)")
    print("="*60)

    from langchain_core.prompts import ChatPromptTemplate

    from core.domain.phi_identification_models import PHIDetectionResponse
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
        ("system", "You are a PHI identification expert. Extract PHI entities."),
        ("user", "Context: HIPAA requires identifying names, dates, IDs, phones.\n\nText: {text}")
    ])

    try:
        structured_llm = llm.with_structured_output(PHIDetectionResponse)
        chain = prompt | structured_llm

        test_text = "Patient 陳老先生, 94-year-old male. Phone: 02-2758-9999. ID: A123456789."

        start = time.time()
        response = chain.invoke({"text": test_text})
        elapsed = time.time() - start

        print(f"Response type: {type(response)}")
        if hasattr(response, 'entities'):
            print(f"Entities found: {len(response.entities)}")
            for e in response.entities[:3]:
                print(f"  - {e.phi_type}: {e.entity_text}")
        print(f"⏱️  Time: {elapsed:.2f}s")
        return elapsed
    except Exception as e:
        print(f"❌ Error: {e}")
        return -1


def test_processors_function():
    """Test 4: Using processors.py functions"""
    print("\n" + "="*60)
    print("TEST 4: processors.identify_phi_json_fallback")
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
- AGE_OVER_89: Ages over 89
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
            print(f"  - {e.type.value}: {e.text}")
        print(f"⏱️  Time: {elapsed:.2f}s")
        return elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Error after {elapsed:.2f}s: {e}")
        return elapsed


def test_full_prompt():
    """Test 5: Full PHI identification prompt (same as streaming uses)"""
    print("\n" + "="*60)
    print("TEST 5: Full PHI Prompt (Same as Streaming)")
    print("="*60)

    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    from core.infrastructure.llm.config import LLMConfig
    from core.infrastructure.llm.factory import create_llm
    from core.infrastructure.prompts import get_phi_identification_prompt, get_system_message

    llm_config = LLMConfig(
        provider="ollama",
        model_name="qwen2.5:1.5b",
        temperature=0.0,
        timeout=60.0,
    )
    llm = create_llm(llm_config)

    # Use the actual prompts
    system_msg = get_system_message("phi_expert", "en")
    prompt_text = get_phi_identification_prompt(language="en", structured=False)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("user", prompt_text)
    ])

    chain = prompt | llm | StrOutputParser()

    test_text = "Patient 陳老先生, 94-year-old male. Phone: 02-2758-9999. ID: A123456789."
    context = """PHI types: NAME, AGE_OVER_89, PHONE, ID"""

    print(f"Prompt length: ~{len(prompt_text)} chars")

    start = time.time()
    try:
        response = chain.invoke({"context": context, "question": test_text})
        elapsed = time.time() - start

        print(f"Response: {response[:400]}...")
        print(f"⏱️  Time: {elapsed:.2f}s")
        return elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Error after {elapsed:.2f}s: {e}")
        return elapsed


def main():
    print("="*60)
    print("PHI IDENTIFICATION PERFORMANCE TEST")
    print("Model: qwen2.5:1.5b via Ollama")
    print("="*60)

    results = {}

    # Test 1: Direct
    results['direct'] = test_direct_llm_call()

    # Test 2: Simple chain
    results['simple_chain'] = test_prompt_chain()

    # Test 3: Structured output
    results['structured'] = test_structured_output()

    # Test 4: processors function
    results['processors'] = test_processors_function()

    # Test 5: Full prompt
    results['full_prompt'] = test_full_prompt()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, time_sec in results.items():
        status = "✅" if time_sec > 0 and time_sec < 30 else "⚠️" if time_sec > 0 else "❌"
        print(f"{status} {name}: {time_sec:.2f}s")

    print("\nConclusion:")
    if results.get('structured', -1) > 30:
        print("⚠️  Structured output is slow - consider using JSON fallback")
    if results.get('full_prompt', -1) > 30:
        print("⚠️  Full prompt is slow - prompt may be too long")


if __name__ == "__main__":
    main()
