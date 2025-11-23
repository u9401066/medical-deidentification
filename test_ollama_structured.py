"""
測試 Ollama Structured Output 是否正常運作
Test if Ollama structured output works correctly
"""

import ollama
import json
from pydantic import BaseModel, Field
from typing import List
import time

# 定義簡單的結構
class Person(BaseModel):
    name: str = Field(description="Person's name")
    age: int = Field(description="Person's age")
    city: str = Field(description="City where person lives")

class PeopleList(BaseModel):
    people: List[Person] = Field(description="List of people")

def test_simple_structured_output():
    """測試簡單的 structured output"""
    print("="*80)
    print("測試 1: 簡單的 Structured Output")
    print("="*80)
    
    prompt = """
    請從以下文字中提取人物資訊：
    
    "張三今年35歲，住在台北。李四28歲，住在高雄。"
    
    請以JSON格式返回人物列表。
    """
    
    try:
        print(f"\n提示詞長度: {len(prompt)} 字元")
        print("開始調用 Ollama...")
        
        start_time = time.time()
        
        client = ollama.Client(host='http://localhost:11434', timeout=60.0)
        response = client.chat(
            model='llama3.1:8b',
            messages=[{'role': 'user', 'content': prompt}],
            format=PeopleList.model_json_schema(),
            options={
                'temperature': 0.0,
            }
        )
        
        elapsed = time.time() - start_time
        
        print(f"✅ 成功！耗時: {elapsed:.2f} 秒")
        print(f"\n回應內容:")
        print(response['message']['content'])
        
        # 解析 JSON
        data = json.loads(response['message']['content'])
        print(f"\n解析後的資料:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ 失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_without_structured_output():
    """測試不使用 structured output 的普通對話"""
    print("\n" + "="*80)
    print("測試 2: 不使用 Structured Output（普通對話）")
    print("="*80)
    
    prompt = "請用一句話介紹台灣。"
    
    try:
        print(f"\n提示詞: {prompt}")
        print("開始調用 Ollama...")
        
        start_time = time.time()
        
        client = ollama.Client(host='http://localhost:11434', timeout=30.0)
        response = client.chat(
            model='llama3.1:8b',
            messages=[{'role': 'user', 'content': prompt}],
            options={
                'temperature': 0.0,
            }
        )
        
        elapsed = time.time() - start_time
        
        print(f"✅ 成功！耗時: {elapsed:.2f} 秒")
        print(f"\n回應內容: {response['message']['content']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complex_structured_output():
    """測試複雜的 PHI 識別 structured output（模擬實際使用場景）"""
    print("\n" + "="*80)
    print("測試 3: 複雜的 PHI 識別 Structured Output（實際場景）")
    print("="*80)
    
    # 使用實際的 PHI detection schema
    from medical_deidentification.domain.phi_identification_models import PHIDetectionResponse
    
    prompt = """
你是一個醫療文件去識別化專家。請識別以下文本中的所有個人健康資訊(PHI)。

文本:
病患姓名：陳建國，出生日期：1955年3月15日，病歷號：MRN-2024-001

請以JSON格式返回識別結果。對每個PHI實體，提供：
- entity_text: PHI文字
- phi_type: PHI類型（如：姓名、日期、病歷號等）
- start_position: 開始位置
- end_position: 結束位置  
- confidence: 信心度(0-1)
- reason: 識別理由
"""
    
    try:
        print(f"\n提示詞長度: {len(prompt)} 字元")
        print("開始調用 Ollama (使用實際 PHI schema)...")
        
        start_time = time.time()
        
        client = ollama.Client(host='http://localhost:11434', timeout=120.0)
        response = client.chat(
            model='llama3.1:8b',
            messages=[{'role': 'user', 'content': prompt}],
            format=PHIDetectionResponse.model_json_schema(),
            options={
                'temperature': 0.0,
            }
        )
        
        elapsed = time.time() - start_time
        
        print(f"✅ 成功！耗時: {elapsed:.2f} 秒")
        print(f"\n回應內容 (前 500 字元):")
        content = response['message']['content']
        print(content[:500] if len(content) > 500 else content)
        
        # 嘗試解析
        try:
            data = json.loads(content)
            print(f"\n✅ JSON 解析成功")
            print(f"識別到 {len(data.get('entities', []))} 個 PHI 實體")
        except json.JSONDecodeError as je:
            print(f"\n❌ JSON 解析失敗: {je}")
        
        return True
        
    except Exception as e:
        try:
            elapsed = time.time() - start_time
            print(f"❌ 失敗（耗時 {elapsed:.2f} 秒）: {e}")
        except:
            print(f"❌ 失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("開始測試 Ollama Structured Output...")
    print(f"時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 測試 1: 簡單 structured output
    result1 = test_simple_structured_output()
    
    # 測試 2: 普通對話（基準測試）
    result2 = test_without_structured_output()
    
    # 測試 3: 複雜 PHI schema（實際場景）
    result3 = test_complex_structured_output()
    
    # 總結
    print("\n" + "="*80)
    print("測試總結")
    print("="*80)
    print(f"測試 1 (簡單 structured output): {'✅ 通過' if result1 else '❌ 失敗'}")
    print(f"測試 2 (普通對話): {'✅ 通過' if result2 else '❌ 失敗'}")
    print(f"測試 3 (PHI schema): {'✅ 通過' if result3 else '❌ 失敗'}")
    
    if all([result1, result2, result3]):
        print("\n✅ 所有測試通過！Ollama structured output 正常運作。")
    else:
        print("\n⚠️ 部分測試失敗，請檢查失敗原因。")
