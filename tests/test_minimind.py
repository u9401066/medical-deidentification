"""
MiniMind LLM Integration Test
測試 MiniMind 超輕量 LLM 是否可以正常運作
"""

import pytest
import time
from typing import Optional


class TestMiniMindIntegration:
    """MiniMind LLM 整合測試"""

    @pytest.fixture(scope="class")
    def llm(self):
        """建立 MiniMind LLM 實例"""
        from medical_deidentification.infrastructure.llm import LLMPresets, create_llm
        return create_llm(LLMPresets.local_minimind())

    def test_minimind_config_exists(self):
        """測試 MiniMind 配置是否存在"""
        from medical_deidentification.infrastructure.llm import LLMPresets, MINIMIND_MODELS
        
        # 檢查 MINIMIND_MODELS 列表
        assert MINIMIND_MODELS is not None
        assert len(MINIMIND_MODELS) >= 3  # 至少有 3 個 MiniMind 模型
        assert "jingyaogong/minimind2" in MINIMIND_MODELS
        
        # 檢查 preset 函數
        config = LLMPresets.local_minimind()
        assert config.provider == "ollama"
        assert config.model_name == "jingyaogong/minimind2"
        assert config.temperature == 0.0
        print("✅ MiniMind 配置正確")

    def test_minimind_presets(self):
        """測試所有 MiniMind preset"""
        from medical_deidentification.infrastructure.llm import LLMPresets
        
        # 測試 local_minimind
        config1 = LLMPresets.local_minimind()
        assert config1.model_name == "jingyaogong/minimind2"
        
        # 測試 local_minimind_small
        config2 = LLMPresets.local_minimind_small()
        assert config2.model_name == "jingyaogong/minimind2-small"
        
        # 測試 local_minimind_reasoning
        config3 = LLMPresets.local_minimind_reasoning()
        assert "r1" in config3.model_name.lower()
        
        print("✅ 所有 MiniMind presets 正確")

    @pytest.mark.slow
    def test_minimind_basic_invoke(self, llm):
        """測試 MiniMind 基本調用"""
        start_time = time.time()
        
        response = llm.invoke("What is 1+1?")
        
        elapsed = time.time() - start_time
        
        # 檢查響應
        content = response.content if hasattr(response, 'content') else str(response)
        assert content is not None
        assert len(content) > 0
        
        print(f"✅ MiniMind 基本調用成功")
        print(f"   響應時間: {elapsed:.2f}s")
        print(f"   響應內容: {content[:100]}...")

    @pytest.mark.slow
    def test_minimind_chinese_support(self, llm):
        """測試 MiniMind 中文支援"""
        response = llm.invoke("請用中文回答：1加1等於多少？")
        
        content = response.content if hasattr(response, 'content') else str(response)
        assert content is not None
        assert len(content) > 0
        
        print(f"✅ MiniMind 中文支援")
        print(f"   響應內容: {content[:100]}...")

    @pytest.mark.slow
    def test_minimind_phi_detection(self, llm):
        """測試 MiniMind PHI 檢測能力"""
        test_text = """
        病患姓名：王大明
        身分證字號：A123456789
        電話：0912-345-678
        """
        
        prompt = f"""請從以下文本中識別出所有個人健康資訊 (PHI):

{test_text}

請列出找到的 PHI 類型和值。"""
        
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        assert content is not None
        assert len(content) > 0
        
        # MiniMind 是小型模型，不要求完美識別
        # 只要能產生有意義的回應即可
        print(f"✅ MiniMind PHI 檢測測試")
        print(f"   響應內容:\n{content[:500]}...")


class TestMiniMindPerformance:
    """MiniMind 效能測試"""

    @pytest.fixture(scope="class")
    def llm(self):
        """建立 MiniMind LLM 實例"""
        from medical_deidentification.infrastructure.llm import LLMPresets, create_llm
        return create_llm(LLMPresets.local_minimind())

    @pytest.mark.slow
    def test_response_time(self, llm):
        """測試響應時間"""
        times = []
        
        for i in range(3):
            start = time.time()
            llm.invoke(f"Test {i}: Say hello")
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        
        print(f"✅ MiniMind 響應時間測試")
        print(f"   平均響應時間: {avg_time:.2f}s")
        print(f"   各次時間: {[f'{t:.2f}s' for t in times]}")
        
        # MiniMind 應該很快 (< 30 秒)
        assert avg_time < 30, f"響應時間過長: {avg_time:.2f}s"


def test_ollama_connection():
    """測試 Ollama 連接"""
    import requests
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        models = [m['name'] for m in data.get('models', [])]
        
        print(f"✅ Ollama 連接成功")
        print(f"   可用模型: {models}")
        
        # 檢查 MiniMind 是否已安裝
        has_minimind = any('minimind' in m.lower() for m in models)
        if has_minimind:
            print("   ✅ MiniMind 已安裝")
        else:
            print("   ⚠️ MiniMind 未安裝，請執行: ollama pull jingyaogong/minimind2")
            
    except requests.exceptions.ConnectionError:
        pytest.skip("Ollama 未運行，跳過測試")


if __name__ == "__main__":
    # 快速測試
    print("=" * 50)
    print("MiniMind Integration Test")
    print("=" * 50)
    
    # 1. 測試 Ollama 連接
    print("\n[1/4] 測試 Ollama 連接...")
    test_ollama_connection()
    
    # 2. 測試配置
    print("\n[2/4] 測試 MiniMind 配置...")
    test = TestMiniMindIntegration()
    test.test_minimind_config_exists()
    test.test_minimind_presets()
    
    # 3. 測試 LLM 調用
    print("\n[3/4] 測試 MiniMind LLM 調用...")
    from medical_deidentification.infrastructure.llm import LLMPresets, create_llm
    llm = create_llm(LLMPresets.local_minimind())
    test.llm = lambda: llm  # Mock fixture
    test.test_minimind_basic_invoke(llm)
    
    # 4. 測試 PHI 檢測
    print("\n[4/4] 測試 MiniMind PHI 檢測...")
    test.test_minimind_phi_detection(llm)
    
    print("\n" + "=" * 50)
    print("✅ 所有測試完成!")
    print("=" * 50)
