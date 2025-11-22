"""
Basic Import Test
基本導入測試

Test if core modules can be imported without dependencies.
測試核心模組是否可以在沒有依賴的情況下導入。
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("Basic Import Test")
print("=" * 70)
print()

# Test 1: Domain Models
print("Test 1: Domain Models")
try:
    from medical_deidentification.domain.models import (
        PHIType,
        PHIEntity,
        SupportedLanguage,
        CustomPHIType
    )
    print("  ✅ Domain models imported successfully")
    print(f"     - PHIType enum: {len(list(PHIType))} types")
    print(f"     - SupportedLanguage: {len(list(SupportedLanguage))} languages")
except Exception as e:
    print(f"  ❌ Failed to import domain models: {e}")

print()

# Test 2: Document Loader Base Classes
print("Test 2: Document Loader Base Classes")
try:
    from medical_deidentification.infrastructure.loader.base import (
        DocumentLoader,
        DocumentFormat,
        DocumentMetadata,
        LoadedDocument
    )
    print("  ✅ Loader base classes imported successfully")
    print(f"     - DocumentFormat: {len(list(DocumentFormat))} formats")
except Exception as e:
    print(f"  ❌ Failed to import loader base: {e}")

print()

# Test 3: Processing Strategies (without pydantic)
print("Test 3: Processing Strategies")
try:
    # These require pydantic, so we expect this to fail
    from medical_deidentification.application.processing.strategies import (
        StrategyType
    )
    print("  ✅ Strategy types imported")
    print(f"     - StrategyType enum: {len(list(StrategyType))} strategies")
except Exception as e:
    print(f"  ⚠️  Strategies require pydantic: {type(e).__name__}")
    print(f"     This is expected until dependencies are installed")

print()

# Test 4: Module Structure
print("Test 4: Module Structure")
modules_to_test = [
    "medical_deidentification",
    "medical_deidentification.domain",
    "medical_deidentification.infrastructure",
    "medical_deidentification.infrastructure.loader",
    "medical_deidentification.infrastructure.rag",
    "medical_deidentification.application",
    "medical_deidentification.application.processing",
]

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"  ✅ {module_name}")
    except Exception as e:
        print(f"  ⚠️  {module_name}: {type(e).__name__}")

print()
print("=" * 70)
print("Import test completed")
print("=" * 70)
print()
print("Note: Some imports may fail without dependencies installed.")
print("Run 'scripts/install_dependencies.py' to install all dependencies.")
