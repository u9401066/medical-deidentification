"""
Regulation Models
法規相關資料模型
"""
from pydantic import BaseModel


class RegulationRule(BaseModel):
    """法規規則"""
    id: str
    name: str
    description: str
    enabled: bool = True
    source: str  # built-in, custom
    rules_count: int


class RegulationContent(BaseModel):
    """法規完整內容"""
    id: str
    name: str
    content: str
    source_file: str | None = None


__all__ = ["RegulationRule", "RegulationContent"]
