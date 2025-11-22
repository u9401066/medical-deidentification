"""
Simple Ollama Test - Direct API Call
直接調用Ollama API測試
"""
import requests
import json
from loguru import logger

def test_ollama_direct():
    """直接測試Ollama API"""
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "llama3.1:8b",
        "prompt": """Identify PHI in this medical text:
Patient: Ms. Lee, age 95
Location: Taipei City
Disease: Huntington's Disease

Return JSON array format:
[{"entity_text": "...", "phi_type": "...", "confidence": 0.95}]""",
        "stream": False
    }
    
    logger.info("Sending request to Ollama...")
    try:
        response = requests.post(url, json=payload, timeout=30)
        logger.success(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Response text:\n{result.get('response', '')[:500]}")
            return result
        else:
            logger.error(f"Error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Request timeout after 30s")
        return None
    except Exception as e:
        logger.error(f"Error: {e}")
        return None


def test_langchain_ollama():
    """測試LangChain ChatOllama"""
    from langchain_community.chat_models import ChatOllama
    
    logger.info("Testing LangChain ChatOllama...")
    
    try:
        llm = ChatOllama(
            model="llama3.1:8b",
            base_url="http://localhost:11434",
            temperature=0.0
        )
        
        prompt = "List 3 PHI types. Be brief."
        logger.info(f"Invoking LLM with prompt: {prompt}")
        
        response = llm.invoke(prompt)
        logger.success(f"LangChain response: {response.content[:200]}")
        return response
        
    except Exception as e:
        logger.error(f"LangChain error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    logger.info("=== Test 1: Direct Ollama API ===")
    test_ollama_direct()
    
    print("\n")
    
    logger.info("=== Test 2: LangChain ChatOllama ===")
    test_langchain_ollama()
