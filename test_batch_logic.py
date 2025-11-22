"""
快速測試 - 驗證批次處理邏輯
使用簡化的測試資料
"""

import pandas as pd
from loguru import logger
import time

# Simple test data
test_data = {
    'Case ID': ['CASE-001', 'CASE-002', 'CASE-003'],
    'Name': ['陳大明 (Chen Ta-Ming)', '王小華 (Wang Xiao-Hua)', '李美麗 (Li Mei-Li)'],
    'Age': [45, 32, 67],
    'Phone': ['02-2345-6789', '0912-345-678', '04-2234-5678'],
    'Address': ['台北市信義區', '新北市板橋區', '台中市西屯區']
}

df = pd.DataFrame(test_data)

logger.info(f"Test data: {len(df)} rows, {len(df.columns)} columns\n")

# Test row combination
for idx, row in df.iterrows():
    parts = []
    for col in df.columns:
        value = row[col]
        if pd.notna(value):
            parts.append(f"[{col}] {value}")
    
    combined = "\n".join(parts)
    logger.info(f"Row {idx + 1}:")
    logger.info(f"Length: {len(combined)} chars")
    logger.info(f"Content preview:\n{combined[:200]}...\n")

logger.success(f"Test complete! Demonstrated combining {len(df)} rows into single texts.")
logger.info(f"This reduces API calls from {len(df) * len(df.columns)} to {len(df)}!")
logger.info(f"Reduction: {len(df) * len(df.columns)} → {len(df)} calls ({len(df) * len(df.columns) - len(df)} fewer calls)")
