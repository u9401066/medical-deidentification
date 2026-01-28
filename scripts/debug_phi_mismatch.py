#!/usr/bin/env python3
"""
Debug script to reproduce the PHI/masked_content mismatch issue
用於重現 PHI 和 masked_content 不匹配問題的調試腳本
"""

import json
import re
from pathlib import Path

# 分析現有結果
result_file = Path("web/backend/data/results/36bfc264_result.json")
if not result_file.exists():
    print(f"Error: {result_file} not found")
    exit(1)

data = json.load(open(result_file))
result = data["results"][0]

original = result["original_content"]
masked = result["masked_content"]
entities = result["phi_entities"]

print("=" * 60)
print("ANALYSIS: PHI vs Masked Content Mismatch")
print("=" * 60)

# 1. 計算 [REDACTED] 數量
redacted_count = masked.count("[REDACTED]")
print(f"\n1. [REDACTED] count in masked_content: {redacted_count}")
print(f"   phi_entities count: {len(entities)}")
print(f"   Difference: {redacted_count - len(entities)}")

# 2. 找出所有 [REDACTED] 的位置和上下文
print("\n2. [REDACTED] positions in masked_content:")
for i, m in enumerate(re.finditer(r"\[REDACTED\]", masked)):
    start = m.start()
    context_before = masked[max(0, start - 20) : start]
    context_after = masked[m.end() : m.end() + 20]
    print(f"   [{i}] pos {start}: ...{context_before}[REDACTED]{context_after}...")

# 3. 列出所有 phi_entities
print("\n3. phi_entities list:")
for i, e in enumerate(entities):
    print(f'   [{i}] {e["type"]}: "{e["value"]}" @ {e.get("start_pos")}-{e.get("end_pos")}')

# 4. 找出 original 中 "72" 的位置
print("\n4. Looking for '72' in original_content:")
pos = 0
while True:
    pos = original.find("72", pos)
    if pos == -1:
        break
    context = original[max(0, pos - 20) : pos + 20]
    print(f"   Found at pos {pos}: ...{context}...")
    pos += 1

# 5. 檢查是否有任何 entity 包含 "72"
print("\n5. Checking if any entity contains '72':")
found = False
for e in entities:
    if "72" in e["value"]:
        print(f'   Found: {e["type"]}: "{e["value"]}"')
        found = True
if not found:
    print("   No entity contains '72'")

# 6. 理論上的替換位置
print("\n6. Mapping [REDACTED] to original positions:")
# 需要逐個追蹤位置偏移
offset = 0
masked_idx = 0
for m in re.finditer(r"\[REDACTED\]", masked):
    start = m.start()
    redacted_len = len("[REDACTED]")

    # 找到對應的 entity
    matched_entity = None
    for e in entities:
        # 檢查這個 entity 是否對應這個 [REDACTED]
        # 由於替換會改變位置，需要計算偏移
        if e.get("start_pos") is not None:
            expected_masked_pos = e["start_pos"] - offset
            entity_len = len(e["value"])
            if abs(expected_masked_pos - start) < 10:  # 允許小誤差
                matched_entity = e
                offset += entity_len - redacted_len
                break

    if matched_entity:
        print(
            f'   [{masked_idx}] @ {start} -> entity: {matched_entity["type"]}: "{matched_entity["value"]}"'
        )
    else:
        # 沒有匹配的 entity，這是問題所在
        # 嘗試推斷原始位置
        print(f"   [{masked_idx}] @ {start} -> NO MATCHING ENTITY (this is the problem!)")

    masked_idx += 1

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
if redacted_count != len(entities):
    print(f"MISMATCH DETECTED: {redacted_count} [REDACTED] but {len(entities)} entities")
    print("This means MaskingProcessor received more entities than what's in the final result.")
    print("Possible causes:")
    print("  1. _apply_hard_rules() removed some entities but masked_content was not updated")
    print("  2. Engine returned different phi_entities than what MaskingProcessor used")
    print("  3. Serialization issue when converting PHIEntity to dict")
else:
    print("No mismatch detected.")
