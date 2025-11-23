"""
測試實際批次處理中的 Ollama 調用
模擬真實場景的 prompt 和文本長度
"""

import ollama
import time
from medical_deidentification.domain.phi_identification_models import PHIDetectionResponse
from medical_deidentification.infrastructure.prompts import (
    get_phi_identification_prompt,
    DEFAULT_HIPAA_SAFE_HARBOR_RULES
)

def test_actual_batch_scenario():
    """測試實際批次處理場景"""
    print("="*80)
    print("測試實際批次處理場景（模擬 simple_batch_test.py 的調用）")
    print("="*80)
    
    # 使用實際的測試文本（從 test_complex_phi_cases.xlsx 第一行）
    text = """case_id: 1
name: 張三
age: 45
diagnosis: 糖尿病
notes: 病患於2024年1月15日入院，主訴多飲多尿症狀持續3個月。過去病史：高血壓5年，規則服藥控制中。家族史：父親有糖尿病病史。理學檢查：血壓 140/90 mmHg，體溫 36.5°C，心跳 80 次/分。實驗室檢查：空腹血糖 180 mg/dL，糖化血色素 8.5%。診斷：第2型糖尿病。治療計畫：開立 Metformin 500mg 每日兩次，衛教飲食控制及規律運動。"""
    
    # 使用實際的 prompt 模板
    prompt_template = get_phi_identification_prompt(
        language="zh-TW",
        structured=True
    )
    
    # 使用默認的 HIPAA 規則作為 context
    context = DEFAULT_HIPAA_SAFE_HARBOR_RULES
    
    # 組合完整的 prompt
    prompt = prompt_template.format(context=context, text=text)
    
    print(f"\n📊 Prompt 資訊:")
    print(f"  - Context 長度: {len(context)} 字元")
    print(f"  - Text 長度: {len(text)} 字元")
    print(f"  - 完整 Prompt 長度: {len(prompt)} 字元")
    print(f"  - 預估 tokens: ~{len(prompt) * 0.75:.0f}")
    
    print(f"\n完整 Prompt（前 500 字元）:")
    print(prompt[:500])
    print("...\n")
    
    try:
        print("開始調用 Ollama（使用實際 PHI schema）...")
        print("超時設定: 120 秒")
        
        start_time = time.time()
        
        client = ollama.Client(host='http://localhost:11434', timeout=120.0)
        response = client.chat(
            model='llama3.1:8b',
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            format=PHIDetectionResponse.model_json_schema(),
            options={
                'temperature': 0.0,
            }
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n✅ 成功！耗時: {elapsed:.2f} 秒")
        
        # 解析結果
        import json
        data = json.loads(response['message']['content'])
        print(f"\n識別結果:")
        print(f"  - has_phi: {data.get('has_phi', False)}")
        print(f"  - 識別到 {len(data.get('entities', []))} 個 PHI 實體")
        
        if data.get('entities'):
            print(f"\n前 3 個實體:")
            for i, entity in enumerate(data['entities'][:3], 1):
                print(f"  {i}. {entity.get('entity_text')} - {entity.get('phi_type')}")
        
        return True, elapsed
        
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n❌ 被中斷（耗時 {elapsed:.2f} 秒）")
        return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ 失敗（耗時 {elapsed:.2f} 秒）: {e}")
        import traceback
        traceback.print_exc()
        return False, elapsed

def test_with_minimal_context():
    """測試使用最小 context（模擬空 context）"""
    print("\n" + "="*80)
    print("測試最小 Context（空規則）")
    print("="*80)
    
    text = """病患姓名：陳建國，出生日期：1955年3月15日，病歷號：MRN-2024-001"""
    
    prompt_template = get_phi_identification_prompt(
        language="zh-TW",
        structured=True
    )
    
    # 使用空的 context
    context = "根據 HIPAA Safe Harbor 規則識別 PHI。"
    prompt = prompt_template.format(context=context, text=text)
    
    print(f"\n📊 Prompt 資訊:")
    print(f"  - Context 長度: {len(context)} 字元（極簡）")
    print(f"  - Text 長度: {len(text)} 字元")
    print(f"  - 完整 Prompt 長度: {len(prompt)} 字元")
    
    try:
        print("\n開始調用 Ollama...")
        
        start_time = time.time()
        
        client = ollama.Client(host='http://localhost:11434', timeout=60.0)
        response = client.chat(
            model='llama3.1:8b',
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            format=PHIDetectionResponse.model_json_schema(),
            options={
                'temperature': 0.0,
            }
        )
        
        elapsed = time.time() - start_time
        
        print(f"✅ 成功！耗時: {elapsed:.2f} 秒")
        return True, elapsed
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 失敗（耗時 {elapsed:.2f} 秒）: {e}")
        return False, elapsed

if __name__ == "__main__":
    print("測試實際批次處理場景")
    print(f"時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 測試 1: 實際場景
    success1, time1 = test_actual_batch_scenario()
    
    # 測試 2: 最小 context
    success2, time2 = test_with_minimal_context()
    
    # 總結
    print("\n" + "="*80)
    print("測試總結")
    print("="*80)
    print(f"測試 1 (實際批次處理場景): {'✅ 通過' if success1 else '❌ 失敗'} - {time1:.2f} 秒")
    print(f"測試 2 (最小 context): {'✅ 通過' if success2 else '❌ 失敗'} - {time2:.2f} 秒")
    
    if success1:
        print("\n✅ 實際批次處理場景能正常運作！")
        print(f"   平均處理時間: {time1:.2f} 秒/請求")
        if time1 > 10:
            print(f"   ⚠️ 處理較慢，可能需要優化或使用更快的模型")
    else:
        print("\n❌ 實際批次處理場景失敗，可能是:")
        print("   1. Prompt 過長")
        print("   2. Schema 過於複雜")
        print("   3. Ollama 服務問題")
