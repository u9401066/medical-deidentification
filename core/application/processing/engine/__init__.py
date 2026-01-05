"""
De-identification Engine Module
去識別化引擎模組

Modular engine implementation with clear separation of concerns:
- config.py: Configuration classes
- result.py: Result data structures
- masking.py: Masking logic
- handlers.py: Pipeline stage handlers
- core.py: Main engine class

清晰職責分離的模組化引擎實現：
- config.py: 配置類別
- result.py: 結果資料結構
- masking.py: 遮蔽邏輯
- handlers.py: Pipeline 階段處理器
- core.py: 主引擎類別
"""

from .config import (
    ProcessingStatus,
    EngineConfig
)

from .result import (
    ProcessingResult
)

from .masking import (
    MaskingProcessor
)

from .handlers import (
    PipelineHandlers
)

from .core import (
    DeidentificationEngine
)


__all__ = [
    # Config
    "ProcessingStatus",
    "EngineConfig",
    
    # Result
    "ProcessingResult",
    
    # Processing
    "MaskingProcessor",
    "PipelineHandlers",
    
    # Main Engine
    "DeidentificationEngine",
]
