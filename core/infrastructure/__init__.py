"""
Infrastructure Layer | 基礎設施層

Contains implementations for external integrations and technical concerns.
包含外部整合與技術關注點的實作。

Modules:
- loader: Document loading implementations
- rag: RAG engine for regulation retrieval
- llm: LLM provider integrations
- output: Output management and report generation
- utils: Utility functions and helpers
"""

from .output import (
    OutputConfig,
    OutputManager,
    ReportGenerator,
    generate_batch_report,
    get_default_output_manager,
    get_report_path,
    get_result_path,
    save_batch_report,
    set_default_output_manager,
)

__all__ = [
    # Output Management
    "OutputManager",
    "OutputConfig",
    "get_default_output_manager",
    "set_default_output_manager",
    "get_result_path",
    "get_report_path",
    # Report Generation
    "ReportGenerator",
    "generate_batch_report",
    "save_batch_report",
]
