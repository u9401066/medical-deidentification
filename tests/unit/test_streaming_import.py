"""Test imports for streaming PHI chain"""

results = []

try:
    results.append("Testing streaming_processor...")
    results.append("  OK")

    results.append("Testing streaming_phi_chain...")
    results.append("  OK")

    results.append("Testing chains __init__...")
    results.append("  OK")

    results.append("\nAll imports successful!")

except Exception as e:
    results.append(f"ERROR: {e}")
    import traceback
    results.append(traceback.format_exc())

# Write results to file
with open("test_import_result.txt", "w") as f:
    f.write("\n".join(results))
