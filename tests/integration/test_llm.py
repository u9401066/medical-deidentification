"""
Integration Tests for LLM Module | LLM 模組整合測試
"""

import pytest
import time
from typing import Optional


class TestLLMConfig:
    """測試 LLM 配置"""

    def test_all_presets_exist(self):
        """測試所有預設配置存在"""
        from medical_deidentification.infrastructure.llm import LLMPresets
        
        # Cloud presets
        assert hasattr(LLMPresets, 'gpt_4o')
        assert hasattr(LLMPresets, 'gpt_4o_mini')
        assert hasattr(LLMPresets, 'claude_3_opus')
        assert hasattr(LLMPresets, 'claude_3_sonnet')
        
        # Local presets
        assert hasattr(LLMPresets, 'local_qwen')
        assert hasattr(LLMPresets, 'local_llama')
        assert hasattr(LLMPresets, 'local_mistral')
        
        # MiniMind presets
        assert hasattr(LLMPresets, 'local_minimind')
        assert hasattr(LLMPresets, 'local_minimind_small')
        assert hasattr(LLMPresets, 'local_minimind_reasoning')

    def test_model_lists_exist(self):
        """測試模型列表存在"""
        from medical_deidentification.infrastructure.llm import (
            OPENAI_MODELS,
            ANTHROPIC_MODELS,
            OLLAMA_MODELS,
            MINIMIND_MODELS,
        )
        
        assert len(OPENAI_MODELS) >= 3
        assert len(ANTHROPIC_MODELS) >= 3
        assert len(OLLAMA_MODELS) >= 3
        assert len(MINIMIND_MODELS) >= 3

    def test_llm_config_validation(self):
        """測試 LLM 配置驗證"""
        from medical_deidentification.infrastructure.llm import LLMConfig
        
        # Valid config
        config = LLMConfig(
            provider="ollama",
            model_name="qwen2.5:7b",
            temperature=0.0,
            max_tokens=2048
        )
        assert config.provider == "ollama"
        
        # Invalid provider should raise
        with pytest.raises(ValueError):
            LLMConfig(provider="invalid_provider", model_name="test")

    def test_minimind_config_values(self):
        """測試 MiniMind 配置值"""
        from medical_deidentification.infrastructure.llm import LLMPresets
        
        config = LLMPresets.local_minimind()
        assert config.provider == "ollama"
        assert config.model_name == "jingyaogong/minimind2"
        assert config.temperature == 0.0
        
        config_small = LLMPresets.local_minimind_small()
        assert "small" in config_small.model_name


class TestLLMFactory:
    """測試 LLM 工廠"""

    def test_create_llm_function_exists(self):
        """測試 create_llm 函數存在"""
        from medical_deidentification.infrastructure.llm import create_llm
        assert callable(create_llm)

    @pytest.mark.slow
    def test_create_ollama_llm(self):
        """測試建立 Ollama LLM"""
        from medical_deidentification.infrastructure.llm import create_llm, LLMPresets
        
        try:
            llm = create_llm(LLMPresets.local_minimind())
            assert llm is not None
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")


class TestOllamaConnection:
    """測試 Ollama 連接"""

    def test_ollama_server_running(self):
        """測試 Ollama 伺服器運行中"""
        import requests
        
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Ollama server not running")

    def test_minimind_model_available(self):
        """測試 MiniMind 模型可用"""
        import requests
        
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m['name'] for m in response.json().get('models', [])]
                has_minimind = any('minimind' in m.lower() for m in models)
                if not has_minimind:
                    pytest.skip("MiniMind not installed. Run: ollama pull jingyaogong/minimind2")
            else:
                pytest.skip("Could not get model list")
        except requests.exceptions.ConnectionError:
            pytest.skip("Ollama server not running")


@pytest.mark.slow
class TestMiniMindFunctional:
    """MiniMind 功能測試 (需要 Ollama)"""

    @pytest.fixture(scope="class")
    def minimind_llm(self):
        """建立 MiniMind LLM"""
        from medical_deidentification.infrastructure.llm import create_llm, LLMPresets
        try:
            return create_llm(LLMPresets.local_minimind())
        except Exception as e:
            pytest.skip(f"Cannot create MiniMind LLM: {e}")

    def test_basic_invoke(self, minimind_llm):
        """測試基本調用"""
        response = minimind_llm.invoke("Say hello")
        content = response.content if hasattr(response, 'content') else str(response)
        assert content is not None
        assert len(content) > 0

    def test_chinese_text(self, minimind_llm):
        """測試中文文本"""
        response = minimind_llm.invoke("你好，請回覆這條訊息")
        content = response.content if hasattr(response, 'content') else str(response)
        assert content is not None
        assert len(content) > 0

    def test_response_time(self, minimind_llm):
        """測試響應時間"""
        start = time.time()
        minimind_llm.invoke("Test")
        elapsed = time.time() - start
        
        # MiniMind 應該在 30 秒內響應
        assert elapsed < 30, f"Response too slow: {elapsed:.2f}s"
