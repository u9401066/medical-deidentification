"""
Quick test of Ollama structured output
"""
import ollama
from medical_deidentification.domain.phi_identification_models import PHIDetectionResponse

# Simple test text
test_text = "Patient John Doe, age 92, visited on 2023-05-15."

# Create prompt
prompt = f"""Based on HIPAA regulations, identify all PHI in the medical text.

Medical Text:
{test_text}

Instructions:
1. Identify ALL PHI entities according to regulations
2. Pay special attention to:
   - Ages ONLY if >90 years (do NOT identify ages 90 and below)
   - Names and identifiers
3. Provide entity_text, phi_type, start_position, end_position, confidence, reason
4. Return structured response with all detected entities
"""

print("Testing Ollama native structured output...")
print(f"Text: {test_text}")
print(f"Schema: {PHIDetectionResponse.model_json_schema()}")

try:
    client = ollama.Client(host='http://localhost:11434', timeout=60.0)
    response = client.chat(
        model='llama3.1:8b',
        messages=[{
            'role': 'user',
            'content': prompt
        }],
        format=PHIDetectionResponse.model_json_schema(),
    )
    
    print(f"\n✅ Response received:")
    print(response['message']['content'])
    
    # Parse it
    detection = PHIDetectionResponse.model_validate_json(response['message']['content'])
    print(f"\n✅ Parsed successfully: {len(detection.entities)} entities")
    for entity in detection.entities:
        print(f"  - {entity.entity_text} ({entity.phi_type})")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
