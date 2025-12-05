"""
Report Generator Module | 報告生成模組 (Compatibility Layer)
============================================================

This module re-exports from infrastructure.output for backward compatibility.
此模組從 infrastructure.output 重新導出以保持向後相容性。

DEPRECATED: Please import directly from infrastructure.output instead.
已棄用：請改為直接從 infrastructure.output 導入。

Example:
    # Old (deprecated):
    from medical_deidentification.application.processing.report_generator import ReportGenerator
    
    # New (recommended):
    from medical_deidentification.infrastructure.output import ReportGenerator
"""

# Re-export from infrastructure layer for backward compatibility
from ...infrastructure.output.report_generator import (
    ReportGenerator,
    generate_batch_report,
    save_batch_report,
)

__all__ = [
    "ReportGenerator",
    "generate_batch_report",
    "save_batch_report",
]
