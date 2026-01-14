"""
Processing Service
PHI 處理服務
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, REPORTS_DIR, RESULTS_DIR


class ProcessingService:
    """PHI 處理服務 - 封裝去識別化引擎"""

    def __init__(self):
        self.results_dir = RESULTS_DIR
        self.reports_dir = REPORTS_DIR
        self._engine_available = False
        self._check_engine()

    def _check_engine(self):
        """檢查引擎是否可用"""
        try:
            # 確保可以 import 主專案模組
            project_root = Path(__file__).parent.parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from core.application.processing.engine import DeidentificationEngine

            self._engine_available = True
        except ImportError as e:
            logger.warning(f"PHI Engine not available: {e}")
            self._engine_available = False

    @property
    def engine_available(self) -> bool:
        return self._engine_available

    def process_file(self, file_path: Path, config: dict[str, Any]) -> dict[str, Any]:
        """處理單一檔案"""
        if not self._engine_available:
            return self._simulate_processing(file_path)

        try:
            from core.application.processing.engine import (
                DeidentificationEngine,
                EngineConfig,
            )

            engine_config = EngineConfig(
                llm_provider="ollama",
                llm_model=OLLAMA_MODEL,
                llm_base_url=OLLAMA_BASE_URL,
                use_rag=False,
            )
            engine = DeidentificationEngine(engine_config)
            result = engine.process_file(file_path)

            return self._convert_engine_result(result, file_path)

        except Exception as e:
            logger.error(f"Processing error: {e}")
            raise

    def _convert_engine_result(self, result: Any, file_path: Path) -> dict[str, Any]:
        """轉換引擎結果為標準格式"""
        # 從 ProcessingResult 提取資料
        phi_entities = []
        original_content = ""
        masked_content = ""

        if hasattr(result, "document_results"):
            for doc_result in result.document_results:
                if hasattr(doc_result, "phi_entities"):
                    for entity in doc_result.phi_entities:
                        phi_entities.append(
                            {
                                "type": entity.phi_type.value
                                if hasattr(entity.phi_type, "value")
                                else str(entity.phi_type),
                                "value": entity.original_text,
                                "masked_value": entity.masked_text,
                                "confidence": entity.confidence,
                                "start_pos": entity.start_pos,
                                "end_pos": entity.end_pos,
                                "reason": "Identified as PHI",
                            }
                        )

                if hasattr(doc_result, "original_content"):
                    original_content = doc_result.original_content
                if hasattr(doc_result, "masked_content"):
                    masked_content = doc_result.masked_content

        return {
            "file_id": file_path.stem.split("_")[0]
            if "_" in file_path.stem
            else file_path.stem[:8],
            "filename": file_path.name,
            "phi_found": len(phi_entities),
            "phi_entities": phi_entities,
            "original_content": original_content[:5000] if original_content else None,
            "masked_content": masked_content[:5000] if masked_content else None,
            "status": "completed",
        }

    def _simulate_processing(self, file_path: Path) -> dict[str, Any]:
        """模擬處理（當引擎不可用時）"""
        import time

        time.sleep(1)  # 模擬處理時間

        return {
            "file_id": file_path.stem[:8],
            "filename": file_path.name,
            "phi_found": 0,
            "phi_entities": [],
            "original_content": "[Simulated - Engine not available]",
            "masked_content": "[Simulated - Engine not available]",
            "status": "completed",
            "warning": "PHI 引擎未載入，使用模擬處理",
        }

    def save_result(self, task_id: str, result: dict[str, Any]) -> Path:
        """儲存處理結果"""
        result_path = self.results_dir / f"{task_id}_result.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        return result_path

    def save_report(
        self,
        task_id: str,
        job_name: str,
        file_results: list[dict[str, Any]],
        processing_time: float,
    ) -> Path:
        """生成並儲存報告"""
        total_phi = sum(r.get("phi_found", 0) for r in file_results)
        total_chars = sum(len(r.get("original_content", "")) for r in file_results)

        # 聚合 PHI 類型統計
        phi_by_type: dict[str, int] = {}
        for result in file_results:
            for entity in result.get("phi_entities", []):
                phi_type = entity.get("type", "UNKNOWN")
                phi_by_type[phi_type] = phi_by_type.get(phi_type, 0) + 1

        report = {
            "task_id": task_id,
            "job_name": job_name,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "files_processed": len(file_results),
                "total_phi_found": total_phi,
                "total_chars": total_chars,
                "processing_time_seconds": processing_time,
                "processing_speed_chars_per_sec": total_chars / processing_time
                if processing_time > 0
                else 0,
            },
            "file_details": [
                {
                    "file_id": r.get("file_id"),
                    "filename": r.get("filename"),
                    "phi_found": r.get("phi_found", 0),
                    "phi_by_type": self._count_phi_types(r.get("phi_entities", [])),
                    "status": r.get("status", "completed"),
                    "phi_entities": r.get("phi_entities", [])[:100],  # 限制數量
                }
                for r in file_results
            ],
        }

        report_path = self.reports_dir / f"{task_id}_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        return report_path

    def _count_phi_types(self, entities: list[dict]) -> dict[str, int]:
        """統計 PHI 類型數量"""
        counts: dict[str, int] = {}
        for entity in entities:
            phi_type = entity.get("type", "UNKNOWN")
            counts[phi_type] = counts.get(phi_type, 0) + 1
        return counts


# 單例模式
_processing_service: ProcessingService | None = None


def get_processing_service() -> ProcessingService:
    """取得 ProcessingService 單例"""
    global _processing_service
    if _processing_service is None:
        _processing_service = ProcessingService()
    return _processing_service


__all__ = ["ProcessingService", "get_processing_service"]
