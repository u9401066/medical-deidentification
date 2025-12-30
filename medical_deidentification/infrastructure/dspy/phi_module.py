"""
DSPy PHI Identification Module
DSPy PHI 識別模組

Defines the DSPy module for PHI identification with structured output.
定義用於 PHI 識別的 DSPy 模組，具有結構化輸出。

DSPy vs LangChain:
- LangChain: Manual prompt engineering
- DSPy: Automatic prompt optimization based on metrics

DSPy 與 LangChain 的區別：
- LangChain: 手動 prompt 工程
- DSPy: 基於指標的自動 prompt 優化
"""

from typing import List, Optional
from dataclasses import dataclass
import json
import re

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    dspy = None

from loguru import logger


@dataclass
class PHIEntity:
    """
    Simple PHI entity for DSPy
    DSPy 用的簡單 PHI 實體
    """
    text: str
    phi_type: str
    start_pos: int = -1
    end_pos: int = -1
    confidence: float = 0.9
    reason: str = ""
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "phi_type": self.phi_type,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "confidence": self.confidence,
            "reason": self.reason,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "PHIEntity":
        return cls(
            text=d.get("text", d.get("entity_text", "")),
            phi_type=d.get("phi_type", "UNKNOWN"),
            start_pos=d.get("start_pos", d.get("start_position", -1)),
            end_pos=d.get("end_pos", d.get("end_position", -1)),
            confidence=d.get("confidence", 0.9),
            reason=d.get("reason", ""),
        )


# DSPy Signature for PHI Identification
if DSPY_AVAILABLE:
    
    class PHIIdentificationSignature(dspy.Signature):
        """
        識別醫療文本中的個人健康資訊 (PHI)
        Identify Protected Health Information (PHI) in medical text.
        
        PHI Types:
        - NAME: Patient names, doctor names, family member names
        - DATE: Birth dates, admission dates, discharge dates
        - AGE: Ages over 89 years only
        - PHONE: Phone numbers
        - EMAIL: Email addresses
        - ID: Medical record numbers, SSN, account numbers
        - LOCATION: Addresses, cities (smaller than state)
        - FACILITY: Hospital names, clinic names
        
        Output Format: JSON array of PHI entities
        """
        medical_text: str = dspy.InputField(
            desc="Medical text to analyze for PHI"
        )
        phi_entities: str = dspy.OutputField(
            desc='JSON array of PHI entities: [{"text": "...", "phi_type": "NAME|DATE|AGE|PHONE|EMAIL|ID|LOCATION|FACILITY", "reason": "..."}]'
        )
    
    
    class PHIIdentifier(dspy.Module):
        """
        DSPy Module for PHI Identification
        PHI 識別的 DSPy 模組
        
        This module can be optimized using DSPy optimizers like:
        - BootstrapFewShot: Add few-shot examples
        - BootstrapFewShotWithRandomSearch: Search for optimal examples
        - MIPRO: Multi-stage instruction optimization
        
        這個模組可以使用 DSPy 優化器進行優化，例如：
        - BootstrapFewShot: 添加少量樣本示例
        - BootstrapFewShotWithRandomSearch: 搜索最佳示例
        - MIPRO: 多階段指令優化
        """
        
        def __init__(self):
            super().__init__()
            # Use ChainOfThought for better reasoning
            self.identify = dspy.ChainOfThought(PHIIdentificationSignature)
        
        def forward(self, medical_text: str) -> List[PHIEntity]:
            """
            Identify PHI entities in medical text
            識別醫療文本中的 PHI 實體
            
            Args:
                medical_text: Medical text to analyze
                
            Returns:
                List of PHIEntity objects
            """
            try:
                # Call DSPy predictor
                result = self.identify(medical_text=medical_text)
                
                # Parse JSON output
                entities = parse_phi_entities(result.phi_entities, medical_text)
                
                return entities
                
            except Exception as e:
                logger.error(f"PHI identification failed: {e}")
                return []


def parse_phi_entities(
    output: str, 
    original_text: str
) -> List[PHIEntity]:
    """
    Parse LLM output to PHI entities (standalone function)
    解析 LLM 輸出為 PHI 實體（獨立函數）
    
    Args:
        output: LLM JSON output string
        original_text: Original medical text for position lookup
        
    Returns:
        List of PHIEntity objects
    """
    entities = []
    
    # Try to extract JSON from output
    json_match = re.search(r'\[.*\]', output, re.DOTALL)
    if not json_match:
        # Try to find individual JSON objects
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        if json_match:
            output = f"[{json_match.group()}]"
        else:
            logger.warning(f"No JSON found in output: {output[:200]}")
            return []
    else:
        output = json_match.group()
    
    try:
        parsed = json.loads(output)
        if not isinstance(parsed, list):
            parsed = [parsed]
            
        for item in parsed:
            if not isinstance(item, dict):
                continue
                
            entity = PHIEntity.from_dict(item)
            
            # Find position in original text
            if entity.text and entity.start_pos == -1:
                pos = original_text.find(entity.text)
                if pos != -1:
                    entity.start_pos = pos
                    entity.end_pos = pos + len(entity.text)
            
            if entity.text:
                entities.append(entity)
                
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}, output: {output[:200]}")
    
    return entities


if not DSPY_AVAILABLE:
    # Fallback when DSPy is not installed
    class PHIIdentificationSignature:
        pass
    
    class PHIIdentifier:
        def __init__(self):
            logger.warning("DSPy not installed. Install with: pip install dspy-ai")
        
        def forward(self, medical_text: str) -> List[PHIEntity]:
            logger.error("DSPy not available")
            return []


# Recommended lightweight models for CPU inference
# Benchmarked on 2024-12-30 with PHI extraction task
LIGHTWEIGHT_MODELS = {
    "granite4:1b": {
        "size": "3.3GB", 
        "json_capable": True,
        "f1_score": 0.894,
        "avg_time": 15.77,
        "recommended": True,
        "description": "🏆 Best quality - IBM model, excellent JSON/tool support, F1=89.4%",
    },
    "qwen2.5:1.5b": {
        "size": "986MB",
        "json_capable": True,
        "f1_score": 0.667,
        "avg_time": 4.21,
        "recommended": True,
        "description": "⭐ Best balance - Fast (4s), good quality, F1=66.7%",
    },
    "llama3.2:1b": {
        "size": "1.3GB",
        "json_capable": True,
        "f1_score": 0.550,
        "avg_time": 8.30,
        "recommended": False,
        "description": "Meta model, high recall (79%) but lower precision",
    },
    "smollm2:360m": {
        "size": "725MB",
        "json_capable": False,
        "f1_score": 0.0,
        "avg_time": 3.78,
        "recommended": False,
        "description": "❌ Too small - Cannot understand PHI extraction task",
    },
    "qwen2.5:0.5b": {
        "size": "395MB",
        "json_capable": True,
        "f1_score": None,  # Not benchmarked
        "avg_time": None,
        "recommended": False,
        "description": "Smallest Qwen, may have similar issues as smollm2",
    },
}


def configure_dspy_ollama(
    model_name: str = "granite4:1b",
    api_base: str = "http://localhost:11434",
    temperature: float = 0.1,
    max_tokens: int = 1024,
) -> None:
    """
    Configure DSPy to use Ollama
    配置 DSPy 使用 Ollama
    
    Recommended lightweight models for CPU (Benchmarked 2024-12-30):
    - granite4:1b (3.3GB) - 🏆 Best quality, F1=89.4%
    - qwen2.5:1.5b (986MB) - ⭐ Best balance, F1=66.7%, ~4s
    - llama3.2:1b (1.3GB) - Good recall but lower precision
    - smollm2:360m (725MB) - ❌ Too small, cannot do PHI extraction
    
    Args:
        model_name: Ollama model name
        api_base: Ollama API base URL
        temperature: Generation temperature (lower = more deterministic)
        max_tokens: Maximum output tokens
    """
    if not DSPY_AVAILABLE:
        raise ImportError("DSPy not installed. Install with: pip install dspy-ai")
    
    # Log model info if it's a known lightweight model
    if model_name in LIGHTWEIGHT_MODELS:
        info = LIGHTWEIGHT_MODELS[model_name]
        logger.info(f"Using lightweight model: {model_name} ({info['size']}) - {info['description']}")
    
    # DSPy supports Ollama via OpenAI-compatible API
    lm = dspy.LM(
        model=f"ollama_chat/{model_name}",
        api_base=api_base,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    dspy.configure(lm=lm)
    logger.info(f"DSPy configured with Ollama model: {model_name}")


def configure_dspy_openai(
    model_name: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 1024,
) -> None:
    """
    Configure DSPy to use OpenAI
    配置 DSPy 使用 OpenAI
    
    Args:
        model_name: OpenAI model name
        api_key: OpenAI API key (or use OPENAI_API_KEY env var)
        temperature: Generation temperature
        max_tokens: Maximum output tokens
    """
    if not DSPY_AVAILABLE:
        raise ImportError("DSPy not installed. Install with: pip install dspy-ai")
    
    import os
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    
    lm = dspy.LM(
        model=f"openai/{model_name}",
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    dspy.configure(lm=lm)
    logger.info(f"DSPy configured with OpenAI model: {model_name}")
