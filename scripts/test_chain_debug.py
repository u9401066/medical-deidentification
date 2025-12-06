#!/usr/bin/env python3
"""
Debug: Test exact chain used by streaming PHI chain
"""
import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from medical_deidentification.infrastructure.llm.factory import create_llm
from medical_deidentification.infrastructure.llm.config import LLMConfig
from medical_deidentification.infrastructure.prompts import get_phi_identification_prompt, get_system_message
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


def test_exact_streaming_chain():
    """Test exact chain used by streaming_phi_chain"""
    print("="*60)
    print("Testing EXACT chain from streaming_phi_chain")
    print("="*60)
    
    # Create LLM
    llm_config = LLMConfig(
        provider="ollama",
        model_name="qwen2.5:1.5b",
        temperature=0.0,
        timeout=60.0,
    )
    llm = create_llm(llm_config)
    
    # Get prompts - EXACTLY as streaming chain does
    prompt_template_text = get_phi_identification_prompt(
        language="en",  # or zh-TW
        structured=False
    )
    system_message = get_system_message("phi_expert", "en")
    
    print(f"\nSystem message length: {len(system_message)} chars")
    print(f"Prompt template length: {len(prompt_template_text)} chars")
    
    # Build chain - Method 1: from_template (current implementation)
    print("\n--- Method 1: from_template ---")
    prompt1 = ChatPromptTemplate.from_template(prompt_template_text)
    chain1 = prompt1 | llm | StrOutputParser()
    
    context = "PHI types: NAME, AGE_OVER_89, PHONE, ID"
    test_text = "Patient 陳老先生, 94-year-old male. Phone: 02-2758-9999."
    
    print(f"Invoking with context={context[:50]}..., question={test_text[:30]}...")
    
    start = time.time()
    try:
        response = chain1.invoke({"context": context, "question": test_text})
        elapsed = time.time() - start
        print(f"✅ Response: {response[:300]}...")
        print(f"⏱️  Time: {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Error after {elapsed:.2f}s: {e}")
    
    # Build chain - Method 2: from_messages (simpler)
    print("\n--- Method 2: from_messages ---")
    prompt2 = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", prompt_template_text)
    ])
    chain2 = prompt2 | llm | StrOutputParser()
    
    start = time.time()
    try:
        response = chain2.invoke({"context": context, "question": test_text})
        elapsed = time.time() - start
        print(f"✅ Response: {response[:300]}...")
        print(f"⏱️  Time: {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Error after {elapsed:.2f}s: {e}")
    
    # Build chain - Method 3: Simple inline prompt
    print("\n--- Method 3: Simple inline prompt ---")
    simple_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a PHI identification expert."),
        ("user", """Identify PHI in this text. Return JSON array.

Context: {context}

Text: {question}

Return format: [{{"entity_text": "...", "phi_type": "NAME|PHONE|ID", "confidence": 0.9}}]
""")
    ])
    chain3 = simple_prompt | llm | StrOutputParser()
    
    start = time.time()
    try:
        response = chain3.invoke({"context": context, "question": test_text})
        elapsed = time.time() - start
        print(f"✅ Response: {response[:300]}...")
        print(f"⏱️  Time: {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Error after {elapsed:.2f}s: {e}")


if __name__ == "__main__":
    test_exact_streaming_chain()
