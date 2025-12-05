#!/usr/bin/env python
"""Simple test to verify model comparison works"""
import sys
print("Starting test...", flush=True)

sys.path.insert(0, 'd:/workspace251122')
from pathlib import Path

test_file = Path('d:/workspace251122/data/test/test_phi_tagged_cases.xlsx')
print(f"File exists: {test_file.exists()}", flush=True)

if not test_file.exists():
    print("ERROR: Test file not found!")
    sys.exit(1)

import pandas as pd
df = pd.read_excel(test_file)
print(f"Loaded {len(df)} rows", flush=True)
print(f"Columns: {df.columns.tolist()}", flush=True)

# Test Ollama connection
print("\nTesting Ollama connection...", flush=True)
try:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model="qwen2.5:1.5b", temperature=0.1)
    response = llm.invoke("Say 'Hello'")
    print(f"Ollama response: {response.content[:50]}...", flush=True)
except Exception as e:
    print(f"Ollama error: {e}", flush=True)

print("\nTest complete!", flush=True)
