"""
Output Module | 輸出模組 (Infrastructure Layer)
==============================================

Provides output management and report generation capabilities.
提供輸出管理和報告生成功能。

DDD Layer: Infrastructure
DDD 層級：基礎設施層

This module handles all output-related concerns:
- File path management (OutputManager)
- Report generation (ReportGenerator)
- Output formatting and export

此模組處理所有輸出相關的關注點：
- 檔案路徑管理 (OutputManager)
- 報告生成 (ReportGenerator)
- 輸出格式化和匯出
"""

from .output_manager import (
    OutputManager,
    OutputConfig,
    get_default_output_manager,
    set_default_output_manager,
    get_result_path,
    get_report_path,
)

from .report_generator import (
    ReportGenerator,
    generate_batch_report,
    save_batch_report,
)

__all__ = [
    # Output Manager
    "OutputManager",
    "OutputConfig",
    "get_default_output_manager",
    "set_default_output_manager",
    "get_result_path",
    "get_report_path",
    # Report Generator
    "ReportGenerator",
    "generate_batch_report",
    "save_batch_report",
]
