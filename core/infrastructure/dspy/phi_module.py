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

NEW in v1.1.0:
- YAML-based prompt configuration support
- Model-specific prompt selection
- Optimization result persistence
"""

import json
import re
from dataclasses import dataclass

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    dspy = None

from loguru import logger

# Import prompt management
try:
    from ..prompts import PromptConfig, load_prompt_config
    PROMPT_MANAGER_AVAILABLE = True
except ImportError:
    PROMPT_MANAGER_AVAILABLE = False
    load_prompt_config = None
    PromptConfig = None


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
        識別醫療文本中的所有個人健康資訊 (PHI) - 必須找出每一個！
        Identify ALL Protected Health Information (PHI) in medical text.
        
        IMPORTANT: You must find EVERY instance of PHI in the text. Missing PHI 
        can lead to privacy violations. Be thorough and comprehensive.
        
        重要：你必須找出文本中的每一個 PHI 實例。遺漏 PHI 可能導致隱私侵犯。
        請徹底且全面地檢查。
        
        PHI Types to identify (找出以下所有類型):
        - NAME: ALL names including patients, doctors, nurses, family members
          (所有姓名，包括病患、醫師、護士、家屬)
        - DATE: ALL dates including birth dates, admission dates, discharge dates,
          surgery dates, appointment dates (所有日期)
        - AGE: ALL ages mentioned (所有年齡，包含 "歲" 結尾的數字)
        - PHONE: ALL phone numbers in any format (所有電話號碼)
        - EMAIL: ALL email addresses (所有電子郵件)
        - ID: ALL ID numbers including medical record numbers, national ID, SSN,
          insurance numbers (所有證號/編號)
        - LOCATION: ALL addresses, cities, districts, streets, room numbers
          (所有地址、城市、區域、街道、房間號)
        - FACILITY: ALL hospital names, clinic names, medical facility names
          (所有醫院/診所名稱)
        
        Output: JSON array with ALL PHI entities found. Include every instance!
        """
        medical_text: str = dspy.InputField(
            desc="Medical text to analyze - find ALL PHI instances"
        )
        phi_entities: str = dspy.OutputField(
            desc='Complete JSON array of ALL PHI entities found. Format: [{"text": "exact text from input", "phi_type": "NAME|DATE|AGE|PHONE|EMAIL|ID|LOCATION|FACILITY", "reason": "brief explanation"}]. Include EVERY PHI instance, do not skip any!'
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
        
        Args:
            use_cot: Use ChainOfThought for better reasoning (slower)
                     使用 ChainOfThought 進行更好的推理（較慢）
        """

        def __init__(self, use_cot: bool = False):
            super().__init__()
            # Use Predict for speed, ChainOfThought for quality
            # 使用 Predict 提高速度，ChainOfThought 提高品質
            if use_cot:
                self.identify = dspy.ChainOfThought(PHIIdentificationSignature)
            else:
                self.identify = dspy.Predict(PHIIdentificationSignature)

        def forward(self, medical_text: str) -> list[PHIEntity]:
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

        def __call__(self, medical_text: str) -> list[PHIEntity]:
            """Convenience method - use module() instead of module.forward()"""
            return self.forward(medical_text)


def parse_phi_entities(
    output: str,
    original_text: str
) -> list[PHIEntity]:
    """
    Parse LLM output to PHI entities (standalone function)
    解析 LLM 輸出為 PHI 實體（獨立函數）
    
    Handles various output formats including:
    - Clean JSON array: [{"text": ...}, ...]
    - Nested structure: {"phi_entities": [...]}
    - Incomplete JSON (attempts repair)
    
    Args:
        output: LLM JSON output string
        original_text: Original medical text for position lookup
        
    Returns:
        List of PHIEntity objects
    """
    entities = []

    # Step 1: Handle nested structure {"phi_entities": [...]}
    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict) and "phi_entities" in parsed:
            if isinstance(parsed["phi_entities"], list):
                return _convert_to_entities(parsed["phi_entities"], original_text)
        elif isinstance(parsed, list):
            return _convert_to_entities(parsed, original_text)
    except json.JSONDecodeError:
        pass  # Continue to try other methods

    # Step 2: Try to extract JSON array from output
    json_match = re.search(r'\[[\s\S]*?\](?=\s*$|\s*\})', output, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return _convert_to_entities(parsed, original_text)
        except json.JSONDecodeError:
            pass

    # Step 3: Try to find individual JSON objects and combine
    object_pattern = r'\{\s*"text"\s*:\s*"[^"]+"\s*,\s*"phi_type"\s*:\s*"[^"]+"\s*(?:,\s*"reason"\s*:\s*"[^"]*")?\s*\}'
    matches = re.findall(object_pattern, output)
    if matches:
        try:
            combined = "[" + ",".join(matches) + "]"
            parsed = json.loads(combined)
            return _convert_to_entities(parsed, original_text)
        except json.JSONDecodeError:
            pass

    # Step 4: Last resort - extract any text/phi_type pairs
    text_matches = re.findall(r'"text"\s*:\s*"([^"]+)"', output)
    type_matches = re.findall(r'"phi_type"\s*:\s*"([^"]+)"', output)

    if text_matches and type_matches:
        for text, phi_type in zip(text_matches, type_matches):
            entity = PHIEntity(text=text, phi_type=phi_type)
            pos = original_text.find(text)
            if pos != -1:
                entity.start_pos = pos
                entity.end_pos = pos + len(text)
            entities.append(entity)
        logger.info(f"Recovered {len(entities)} entities from malformed JSON")
        return entities

    logger.warning(f"Could not parse JSON from output: {output[:300]}")
    return []


def _convert_to_entities(items: list, original_text: str) -> list[PHIEntity]:
    """Convert list of dicts to PHIEntity objects"""
    entities = []
    for item in items:
        if not isinstance(item, dict):
            continue
        entity = PHIEntity.from_dict(item)
        if entity.text and entity.start_pos == -1:
            pos = original_text.find(entity.text)
            if pos != -1:
                entity.start_pos = pos
                entity.end_pos = pos + len(entity.text)
        if entity.text:
            entities.append(entity)
    return entities


# Keep old function for backward compatibility
def _parse_phi_entities_legacy(
    output: str,
    original_text: str
) -> list[PHIEntity]:
    """
    Legacy parser (kept for reference)
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

        def forward(self, medical_text: str) -> list[PHIEntity]:
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
    use_json_mode: bool = True,
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
        use_json_mode: Use Ollama JSON mode for faster response (3-4x speedup)
    """
    if not DSPY_AVAILABLE:
        raise ImportError("DSPy not installed. Install with: pip install dspy-ai")

    # Log model info if it's a known lightweight model
    if model_name in LIGHTWEIGHT_MODELS:
        info = LIGHTWEIGHT_MODELS[model_name]
        logger.info(f"Using lightweight model: {model_name} ({info['size']}) - {info['description']}")

    # DSPy supports Ollama via OpenAI-compatible API
    # JSON mode significantly speeds up response (3-4x faster)
    lm_kwargs = {
        "model": f"ollama_chat/{model_name}",
        "api_base": api_base,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if use_json_mode:
        lm_kwargs["format"] = "json"
        logger.info("JSON mode enabled (3-4x faster)")

    lm = dspy.LM(**lm_kwargs)

    dspy.configure(lm=lm)
    logger.info(f"DSPy configured with Ollama model: {model_name}")


def configure_dspy_openai(
    model_name: str = "gpt-4o-mini",
    api_key: str | None = None,
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


# ============================================================
# NEW: YAML-based Prompt Configuration Integration
# 新增：YAML 格式 Prompt 配置整合
# ============================================================

def create_phi_identifier_from_yaml(
    config_name: str = "phi_identification",
    model_name: str = "granite4:1b",
    config_version: str | None = None,
) -> "PHIIdentifierWithConfig":
    """
    Create PHI identifier with YAML configuration
    使用 YAML 配置創建 PHI 識別器
    
    This function loads prompt configuration from YAML and creates
    a DSPy module that uses the configured prompts and settings.
    
    此函數從 YAML 載入 prompt 配置，並創建使用配置的 prompts 和設定的 DSPy 模組。
    
    Args:
        config_name: Name of YAML config file (without .yaml)
        model_name: Model to use (affects prompt selection)
        config_version: Specific version to load
        
    Returns:
        PHIIdentifierWithConfig instance
        
    Example:
        >>> identifier = create_phi_identifier_from_yaml(
        ...     model_name="granite4:1b"
        ... )
        >>> entities = identifier("病患王大明...")
    """
    if not PROMPT_MANAGER_AVAILABLE:
        raise ImportError("Prompt manager not available. Check prompts module.")

    config = load_prompt_config(config_name, config_version)
    return PHIIdentifierWithConfig(config, model_name)


if DSPY_AVAILABLE:

    class ConfigurablePHISignature(dspy.Signature):
        """
        Configurable PHI Identification Signature
        可配置的 PHI 識別 Signature
        
        This signature's docstring can be dynamically set from YAML config.
        此 signature 的 docstring 可以從 YAML 配置動態設定。
        """
        medical_text: str = dspy.InputField(
            desc="Medical text to analyze for PHI"
        )
        phi_entities: str = dspy.OutputField(
            desc='JSON array of PHI entities with text, phi_type, and reason'
        )


    class PHIIdentifierWithConfig(dspy.Module):
        """
        DSPy PHI Identifier with YAML Configuration Support
        支援 YAML 配置的 DSPy PHI 識別器
        
        This module loads its configuration from YAML files, allowing:
        - Easy prompt customization without code changes
        - Version control of prompts
        - Model-specific prompt selection
        - Optimization result persistence
        
        此模組從 YAML 檔案載入配置，允許：
        - 無需修改程式碼即可自訂 prompts
        - Prompt 版本控制
        - 模型特定的 prompt 選擇
        - 優化結果持久化
        
        Usage:
            >>> # Method 1: Use factory function
            >>> identifier = create_phi_identifier_from_yaml(model_name="granite4:1b")
            >>> 
            >>> # Method 2: Direct instantiation
            >>> from core.infrastructure.prompts import load_prompt_config
            >>> config = load_prompt_config("phi_identification")
            >>> identifier = PHIIdentifierWithConfig(config, "granite4:1b")
            >>> 
            >>> # Identify PHI
            >>> entities = identifier("病患王大明，身分證A123456789...")
        """

        def __init__(
            self,
            config: "PromptConfig",
            model_name: str = "granite4:1b",
        ):
            """
            Initialize with YAML configuration
            
            Args:
                config: PromptConfig loaded from YAML
                model_name: Model name for model-specific settings
            """
            super().__init__()
            self.config = config
            self.model_name = model_name

            # Get model-specific configuration
            self.model_config = config.get_model_config(model_name)

            # Create signature with configured prompt
            self._setup_signature()

            # Use ChainOfThought if configured, else Predict
            if self.model_config.use_cot:
                self.identify = dspy.ChainOfThought(self._signature_class)
            else:
                self.identify = dspy.Predict(self._signature_class)

            logger.info(
                f"PHIIdentifierWithConfig initialized: "
                f"config={config.name} v{config.version}, "
                f"model={model_name}, "
                f"prompt_style={self.model_config.prompt_style}"
            )

        def _setup_signature(self):
            """Setup DSPy signature from config"""
            # Get PHI types from config
            phi_types_str = ", ".join(self.config.get_phi_type_list())

            # Create dynamic signature class with configured docstring
            prompt_template = self.config.get_prompt(
                name=self.model_config.prompt_style,
                medical_text="{medical_text}",  # Placeholder
            )

            # Use the first line of template as description
            description = prompt_template.split("\n")[0][:200]

            class DynamicPHISignature(dspy.Signature):
                __doc__ = f"""
                {description}
                
                PHI Types: {phi_types_str}
                
                Output: JSON array of PHI entities
                """
                medical_text: str = dspy.InputField(
                    desc="Medical text to analyze for PHI"
                )
                phi_entities: str = dspy.OutputField(
                    desc=f'JSON array: [{{"text": "...", "phi_type": "{phi_types_str.split(",")[0]}|...", "reason": "..."}}]'
                )

            self._signature_class = DynamicPHISignature

        def forward(self, medical_text: str) -> list[PHIEntity]:
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

        def __call__(self, medical_text: str) -> list[PHIEntity]:
            """Convenience method to call forward"""
            return self.forward(medical_text)

        def get_few_shot_examples(self) -> list[dict]:
            """Get few-shot examples from config"""
            return [
                {"input": ex.input, "output": ex.output, "note": ex.note}
                for ex in self.config.get_few_shot_examples()
            ]

        def get_optimization_settings(self) -> dict:
            """Get optimization settings from config"""
            opt = self.config.optimization
            return {
                "method": opt.default_method,
                "targets": opt.targets,
                "weights": opt.weights,
            }


# Fallback when DSPy not available
if not DSPY_AVAILABLE:

    class PHIIdentifierWithConfig:
        """Fallback when DSPy not available"""

        def __init__(self, config, model_name: str = "granite4:1b"):
            logger.warning("DSPy not installed. Install with: pip install dspy-ai")
            self.config = config
            self.model_name = model_name

        def forward(self, medical_text: str) -> list[PHIEntity]:
            logger.error("DSPy not available")
            return []

        def __call__(self, medical_text: str) -> list[PHIEntity]:
            return self.forward(medical_text)

