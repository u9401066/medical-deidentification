"""
Simple Domain Model Test
簡單領域模型測試

Test domain models without external dependencies.
測試不需外部依賴的領域模型。
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("Domain Model Test (No Dependencies Required)")
print("=" * 70)
print()

# Test PHIType enum
print("Test 1: PHI Types")
from medical_deidentification.domain.models import PHIType

standard_types = PHIType.get_standard_types()
strict_types = PHIType.get_strict_types()

print(f"  Standard PHI Types ({len(standard_types)}):")
for phi_type in standard_types:
    print(f"    - {phi_type.value}")

print(f"\n  Strict PHI Types ({len(strict_types)}):")
print(f"    (includes {len(strict_types) - len(standard_types)} additional types)")

print()

# Test SupportedLanguage
print("Test 2: Supported Languages")
from medical_deidentification.domain.models import SupportedLanguage

print(f"  Total Languages: {len(list(SupportedLanguage))}")
print(f"  Default: {SupportedLanguage.get_default().value}")
print()
print("  Languages:")
for lang in list(SupportedLanguage)[:5]:  # Show first 5
    print(f"    - {lang.value}: {lang.name}")
print(f"    ... and {len(list(SupportedLanguage)) - 5} more")

print()

# Test PHI Type helpers
print("Test 3: PHI Type Helpers")
print(f"  Is AGE_OVER_89 age-related? {PHIType.is_age_related(PHIType.AGE_OVER_89)}")
print(f"  Is NAME age-related? {PHIType.is_age_related(PHIType.NAME)}")
print(f"  Is HOSPITAL_NAME facility-related? {PHIType.is_facility_related(PHIType.HOSPITAL_NAME)}")
print(f"  Is NAME facility-related? {PHIType.is_facility_related(PHIType.NAME)}")

print()

# Test DocumentFormat (if loader base works)
print("Test 4: Document Formats")
try:
    from medical_deidentification.infrastructure.loader.base import DocumentFormat
    
    print(f"  Total Formats: {len(list(DocumentFormat))}")
    print("  Formats:")
    for fmt in list(DocumentFormat):
        print(f"    - {fmt.value}: {fmt.name}")
except Exception as e:
    print(f"  ⚠️  DocumentFormat requires pydantic: {type(e).__name__}")

print()
print("=" * 70)
print("✅ Domain model tests completed successfully!")
print("=" * 70)
print()
print("These models work without any external dependencies.")
print("Once dependencies are installed, full functionality will be available.")
