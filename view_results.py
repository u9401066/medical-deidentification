import pandas as pd
import sys

file_path = "phi_identification_results.xlsx"

try:
    df = pd.read_excel(file_path)
    print(f"\n{'='*80}")
    print(f"PHI Identification Results ({len(df)} entities found)")
    print(f"{'='*80}\n")
    print(df.to_string())
except FileNotFoundError:
    print(f"File not found: {file_path}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
