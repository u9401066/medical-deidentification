"""
測試 OpenAI API 連接
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_basic_connection():
    """測試基本的 OpenAI API 連接"""
    print("Testing OpenAI API connection...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print(f"✓ API key found (starts with: {api_key[:10]}...)")
    
    try:
        client = OpenAI(api_key=api_key, timeout=10.0)
        
        print("\nSending test request to gpt-4o-mini...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'Hello, I am working!' in one sentence."}
            ],
            max_tokens=50,
            timeout=10.0
        )
        
        print(f"✓ Response received: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_structured_output():
    """測試 structured output"""
    print("\n" + "="*60)
    print("Testing structured output...")
    
    from pydantic import BaseModel
    
    class TestResponse(BaseModel):
        message: str
        count: int
    
    try:
        client = OpenAI(timeout=10.0)
        
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say hello and count to 3"}
            ],
            response_format=TestResponse,
            timeout=10.0
        )
        
        parsed = response.choices[0].message.parsed
        print(f"✓ Structured response: message='{parsed.message}', count={parsed.count}")
        return True
        
    except Exception as e:
        print(f"❌ Structured output error: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("OpenAI API Connection Test")
    print("="*60 + "\n")
    
    basic_ok = test_basic_connection()
    
    if basic_ok:
        structured_ok = test_structured_output()
    else:
        print("\n⚠ Skipping structured output test due to basic connection failure")
    
    print("\n" + "="*60)
    print("Test complete")
    print("="*60)
