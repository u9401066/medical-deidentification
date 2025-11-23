"""
System Messages and Contexts
系統訊息和上下文

System messages for different agent roles and default regulation contexts.
"""

# ============================================================================
# System Messages
# ============================================================================

SYSTEM_MESSAGE_PHI_EXPERT = "You are a medical de-identification expert specializing in identifying Protected Health Information (PHI) according to HIPAA, GDPR, and other privacy regulations."

SYSTEM_MESSAGE_PHI_EXPERT_ZH_TW = "您是一位醫療去識別化專家，專門根據 HIPAA、GDPR 和其他隱私法規識別個人健康資訊（PHI）。"

SYSTEM_MESSAGE_REGULATION_ANALYST = "You are a healthcare regulation analyst specializing in data privacy and de-identification requirements."

SYSTEM_MESSAGE_REGULATION_ANALYST_ZH_TW = "您是一位醫療法規分析師，專門研究數據隱私和去識別化要求。"


# ============================================================================
# Default Regulation Contexts
# ============================================================================

DEFAULT_HIPAA_SAFE_HARBOR_RULES = """Standard HIPAA Safe Harbor PHI Identifiers:

1. Names: All names (patients, relatives, employers, etc.)
2. Geographic Subdivisions: All smaller than state level (cities, counties, street addresses, ZIP codes - first 3 digits OK if population >20,000)
3. Dates: All dates directly related to individual (birth, admission, discharge, death)
   - Exception: Year may be retained
   - Ages over 89 must be aggregated to single category
4. Telephone numbers
5. Fax numbers
6. Email addresses
7. Social Security numbers
8. Medical record numbers
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers and serial numbers (license plates, VINs)
13. Device identifiers and serial numbers
14. Web URLs
15. IP addresses
16. Biometric identifiers (fingerprints, voiceprints)
17. Full-face photographs and comparable images
18. Any other unique identifying number, characteristic, or code

Note: The list excludes elements that are not individually identifiable health information, such as:
- Gender
- Race/Ethnicity
- Common diseases (diabetes, hypertension, etc.)
- Ages 89 and below (except birth dates)"""
