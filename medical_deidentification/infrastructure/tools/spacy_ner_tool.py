"""
SpaCy NER Tool for PHI Detection | SpaCy NER PHI 檢測工具

Uses SpaCy's Named Entity Recognition for detecting names, locations, and organizations.
使用 SpaCy 的命名實體識別來檢測姓名、地點和組織。

Supported models:
- zh_core_web_sm / zh_core_web_md / zh_core_web_lg (Chinese)
- en_core_web_sm / en_core_web_md / en_core_web_lg (English)
"""

import logging
from typing import List, Dict, Optional, Any

from medical_deidentification.domain.phi_types import PHIType
from medical_deidentification.infrastructure.tools.base_tool import BasePHITool, ToolResult

logger = logging.getLogger(__name__)


class SpaCyNERTool(BasePHITool):
    """
    SpaCy-based Named Entity Recognition tool
    基於 SpaCy 的命名實體識別工具
    
    Features:
    - Detects PERSON, ORG, GPE, LOC entities
    - Maps SpaCy entities to PHI types
    - Supports Chinese and English models
    - Lazy loading of SpaCy model
    
    Usage:
        tool = SpaCyNERTool(model_name="zh_core_web_sm")
        results = tool.scan("患者王小明住在台北市")
    
    Note:
        SpaCy model must be installed separately:
        python -m spacy download zh_core_web_sm
    """
    
    # Mapping from SpaCy entity types to PHI types
    # SpaCy 實體類型到 PHI 類型的對應
    ENTITY_TYPE_MAP: Dict[str, PHIType] = {
        # Person names
        "PERSON": PHIType.NAME,
        "PER": PHIType.NAME,  # Some models use PER
        
        # Locations
        "GPE": PHIType.LOCATION,  # Geopolitical entity (country, city, state)
        "LOC": PHIType.LOCATION,  # Non-GPE locations
        "FAC": PHIType.LOCATION,  # Facilities (buildings, airports)
        
        # Organizations (could be hospitals, departments)
        "ORG": PHIType.HOSPITAL_NAME,
        
        # Dates
        "DATE": PHIType.DATE,
        "TIME": PHIType.DATE,
        
        # Other
        "CARDINAL": PHIType.OTHER,  # Numerals
        "ORDINAL": PHIType.OTHER,  # Ordinals
    }
    
    # Confidence scores for different entity types
    CONFIDENCE_MAP: Dict[str, float] = {
        "PERSON": 0.85,
        "PER": 0.85,
        "GPE": 0.80,
        "LOC": 0.75,
        "FAC": 0.70,
        "ORG": 0.75,
        "DATE": 0.80,
        "TIME": 0.75,
        "CARDINAL": 0.50,
        "ORDINAL": 0.50,
    }
    
    def __init__(
        self, 
        model_name: str = "zh_core_web_sm",
        entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.5
    ):
        """
        Initialize SpaCy NER tool
        初始化 SpaCy NER 工具
        
        Args:
            model_name: SpaCy model to use (default: zh_core_web_sm for Chinese)
            entity_types: List of SpaCy entity types to detect (default: all mapped types)
            min_confidence: Minimum confidence threshold for results
        """
        self._model_name = model_name
        self._nlp = None  # Lazy load
        self._entity_types = entity_types or list(self.ENTITY_TYPE_MAP.keys())
        self._min_confidence = min_confidence
        self._load_error: Optional[str] = None
    
    @property
    def name(self) -> str:
        return f"spacy_ner_tool:{self._model_name}"
    
    @property
    def supported_types(self) -> List[PHIType]:
        return [
            PHIType.NAME,
            PHIType.LOCATION,
            PHIType.HOSPITAL_NAME,
            PHIType.DATE,
        ]
    
    def _ensure_model_loaded(self) -> bool:
        """
        Ensure SpaCy model is loaded (lazy loading)
        確保 SpaCy 模型已載入（延遲載入）
        
        Returns:
            True if model is loaded successfully
        """
        if self._nlp is not None:
            return True
        
        if self._load_error is not None:
            return False
        
        try:
            import spacy
            self._nlp = spacy.load(self._model_name)
            logger.info(f"SpaCy model '{self._model_name}' loaded successfully")
            return True
        except ImportError:
            self._load_error = "SpaCy is not installed. Install with: pip install spacy"
            logger.warning(self._load_error)
            return False
        except OSError:
            self._load_error = f"SpaCy model '{self._model_name}' not found. Install with: python -m spacy download {self._model_name}"
            logger.warning(self._load_error)
            return False
    
    def scan(self, text: str) -> List[ToolResult]:
        """
        Scan text using SpaCy NER
        使用 SpaCy NER 掃描文本
        
        Args:
            text: Text to scan
            
        Returns:
            List of detected entities as PHI
        """
        if not self._ensure_model_loaded():
            logger.debug(f"SpaCy model not available: {self._load_error}")
            return []
        
        results = []
        
        try:
            doc = self._nlp(text)
            
            for ent in doc.ents:
                # Skip if not in our tracked entity types
                if ent.label_ not in self._entity_types:
                    continue
                
                # Get PHI type mapping
                phi_type = self.ENTITY_TYPE_MAP.get(ent.label_, PHIType.OTHER)
                confidence = self.CONFIDENCE_MAP.get(ent.label_, 0.5)
                
                # Skip if below minimum confidence
                if confidence < self._min_confidence:
                    continue
                
                results.append(ToolResult(
                    text=ent.text,
                    phi_type=phi_type,
                    start_pos=ent.start_char,
                    end_pos=ent.end_char,
                    confidence=confidence,
                    tool_name=self.name,
                    metadata={
                        "spacy_label": ent.label_,
                        "spacy_label_desc": ent.label_ if hasattr(ent, 'label_') else "",
                    }
                ))
                
        except Exception as e:
            logger.error(f"SpaCy NER error: {e}")
        
        return results
    
    def is_available(self) -> bool:
        """
        Check if SpaCy model is available
        檢查 SpaCy 模型是否可用
        """
        return self._ensure_model_loaded()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model
        獲取載入模型的資訊
        """
        if not self._ensure_model_loaded():
            return {"error": self._load_error}
        
        return {
            "model_name": self._model_name,
            "pipeline": self._nlp.pipe_names if self._nlp else [],
            "entity_types": self._entity_types,
        }


class OptionalSpaCyNERTool(BasePHITool):
    """
    SpaCy NER tool that gracefully handles missing SpaCy installation
    當 SpaCy 未安裝時優雅降級的 NER 工具
    
    This wrapper ensures the tool doesn't break the pipeline if SpaCy is not available.
    此封裝確保即使 SpaCy 不可用，也不會中斷處理流程。
    """
    
    def __init__(self, model_name: str = "zh_core_web_sm"):
        self._inner_tool: Optional[SpaCyNERTool] = None
        self._model_name = model_name
        self._tried_loading = False
    
    @property
    def name(self) -> str:
        return f"optional_spacy_ner:{self._model_name}"
    
    @property
    def supported_types(self) -> List[PHIType]:
        return [PHIType.NAME, PHIType.LOCATION, PHIType.HOSPITAL_NAME, PHIType.DATE]
    
    def scan(self, text: str) -> List[ToolResult]:
        """Scan text, returning empty list if SpaCy unavailable"""
        if not self._tried_loading:
            self._tried_loading = True
            try:
                self._inner_tool = SpaCyNERTool(self._model_name)
                if not self._inner_tool.is_available():
                    self._inner_tool = None
            except Exception:
                self._inner_tool = None
        
        if self._inner_tool:
            return self._inner_tool.scan(text)
        
        return []
