"""
Output Manager Module | 輸出管理模組 (Compatibility Layer)
==========================================================

This module re-exports from infrastructure.output for backward compatibility.
此模組從 infrastructure.output 重新導出以保持向後相容性。

DEPRECATED: Please import directly from infrastructure.output instead.
已棄用：請改為直接從 infrastructure.output 導入。

Example:
    # Old (deprecated):
    from medical_deidentification.application.processing.output_manager import OutputManager
    
    # New (recommended):
    from medical_deidentification.infrastructure.output import OutputManager
"""

# Re-export from infrastructure layer for backward compatibility
from ...infrastructure.output.output_manager import (
    OutputManager,
    OutputConfig,
    get_default_output_manager,
    set_default_output_manager,
    get_result_path,
    get_report_path,
)

__all__ = [
    "OutputManager",
    "OutputConfig",
    "get_default_output_manager",
    "set_default_output_manager",
    "get_result_path",
    "get_report_path",
]
