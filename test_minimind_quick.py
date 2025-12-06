"""Quick test for minimind via Ollama"""
import sys
sys.path.insert(0, ".")

try:
    from langchain_ollama import ChatOllama
    print("ChatOllama imported OK")
    
    llm = ChatOllama(
        model="jingyaogong/minimind2",
        temperature=0,
        base_url="http://localhost:11434"
    )
    print("LLM created OK")
    
    response = llm.invoke("What is 1+1?")
    print(f"Response type: {type(response)}")
    print(f"Response content: {response.content[:200] if response.content else 'empty'}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
