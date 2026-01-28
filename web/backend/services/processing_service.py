"""
Processing Service
PHI 處理服務
"""

import json
import re
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

# 建立專用 logger
log = logger.bind(component="processing_service")


class ProcessingService:
    """PHI 處理服務 - 封裝去識別化引擎"""

    def __init__(self) -> None:
        self.results_dir = RESULTS_DIR
        self.reports_dir = REPORTS_DIR
        self._engine_available = False
        self._check_engine()

    def _check_engine(self) -> None:
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

    def process_file(
        self,
        file_path: Path,
        config: dict[str, Any],
        original_filename: str | None = None,
    ) -> dict[str, Any]:
        """處理單一檔案

        Args:
            file_path: 檔案路徑
            config: 處理配置
            original_filename: 原始檔名 (用於報告顯示)
        """
        if not self._engine_available:
            return self._simulate_processing(file_path, original_filename)

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

            masking_type = config.get("masking_type", "redact")
            return self._convert_engine_result(result, file_path, original_filename, masking_type)

        except Exception as e:
            logger.error(f"Processing error: {e}")
            raise

    def _convert_engine_result(
        self,
        result: Any,
        file_path: Path,
        original_filename: str | None = None,
        masking_type: str = "redact",
    ) -> dict[str, Any]:
        """轉換引擎結果為標準格式

        Args:
            result: 引擎處理結果
            file_path: 檔案路徑 (含 file_id)
            original_filename: 原始檔名 (用於報告顯示)
            masking_type: 遮罩類型 (redact/hash/generalize)
        """
        # 從 ProcessingResult 提取資料
        phi_entities = []
        original_content = ""
        masked_content = ""

        # ProcessingResult 使用 documents 屬性 (不是 document_results)
        documents = getattr(result, "documents", [])
        log.debug(
            "Engine result received",
            documents_count=len(documents),
            has_summary=hasattr(result, "summary"),
        )

        if documents:
            for doc_idx, doc in enumerate(documents):
                # doc 是 dict，包含 phi_entities, masked_content, original_content
                if isinstance(doc, dict):
                    raw_entities = doc.get("phi_entities", [])
                    log.info(
                        "Document PHI entities from engine",
                        doc_idx=doc_idx,
                        entities_count=len(raw_entities),
                        entities_preview=[
                            {"type": e.get("type"), "text": e.get("text", "")[:30]}
                            for e in raw_entities[:10]
                        ],
                    )

                    for entity in raw_entities:
                        original_text = entity.get("text", "")
                        # 計算 masked_value 基於遮罩類型
                        masked_value = self._compute_masked_value(
                            original_text,
                            entity.get("type", "UNKNOWN"),
                            masking_type,
                        )
                        phi_entities.append(
                            {
                                "type": entity.get("type", "UNKNOWN"),
                                "value": original_text,
                                "masked_value": masked_value,
                                "confidence": entity.get("confidence", 0.0),
                                "start_pos": entity.get("start_pos"),
                                "end_pos": entity.get("end_pos"),
                                "reason": entity.get("reason", "Identified as PHI"),
                            }
                        )
                    original_content = doc.get("original_content", "") or ""
                    masked_content = doc.get("masked_content", "") or ""

                    # 檢查 masked_content 和 original_content 的差異
                    log.debug(
                        "Content comparison",
                        original_len=len(original_content),
                        masked_len=len(masked_content),
                        original_preview=original_content[:200] if original_content else None,
                        masked_preview=masked_content[:200] if masked_content else None,
                    )

        # 若 documents 為空，嘗試從 summary.phi_entities 取得
        if not phi_entities and hasattr(result, "summary"):
            summary = result.summary
            if isinstance(summary, dict):
                for entity in summary.get("phi_entities", []):
                    original_text = entity.get("text", "")
                    masked_value = self._compute_masked_value(
                        original_text,
                        entity.get("type", "UNKNOWN"),
                        masking_type,
                    )
                    phi_entities.append(
                        {
                            "type": entity.get("type", "UNKNOWN"),
                            "value": original_text,
                            "masked_value": masked_value,
                            "confidence": entity.get("confidence", 0.0),
                            "start_pos": entity.get("start_pos"),
                            "end_pos": entity.get("end_pos"),
                            "reason": entity.get("reason", ""),
                        }
                    )

        # 使用原始檔名 (若提供) 或檔案路徑名稱
        display_filename = original_filename or file_path.name
        file_id = file_path.stem.split("_")[0] if "_" in file_path.stem else file_path.stem[:8]

        # 記錄 hard rules 前的 entities
        entities_before_rules = len(phi_entities)
        log.debug(
            "Before hard rules",
            entities_count=entities_before_rules,
            entities_types=[e.get("type") for e in phi_entities],
        )

        # 套用 hard rules 後處理 (修正 LLM 常見錯誤)
        phi_entities, corrections = self._apply_hard_rules(phi_entities)
        if corrections:
            log.warning(
                "Hard rules applied",
                corrections=corrections,
                removed_count=entities_before_rules - len(phi_entities),
            )

            # 如果有 entities 被移除，需要重新生成 masked_content
            # 因為 Engine 返回的 masked_content 是用所有 entities 生成的
            if entities_before_rules != len(phi_entities) and original_content:
                log.info("Regenerating masked_content after hard rules filtering")
                masked_content = self._regenerate_masked_content(
                    original_content, phi_entities, masking_type
                )

        log.info(
            "Final engine result",
            file_id=file_id,
            filename=display_filename,
            phi_found=len(phi_entities),
            phi_types=[e.get("type") for e in phi_entities],
        )

        return {
            "file_id": file_id,
            "filename": display_filename,
            "phi_found": len(phi_entities),
            "phi_entities": phi_entities,
            "original_content": original_content[:5000] if original_content else None,
            "masked_content": masked_content[:5000] if masked_content else None,
            "status": "completed",
        }

    def _compute_masked_value(self, original_text: str, phi_type: str, masking_type: str) -> str:
        """計算遮罩後的值"""
        if not original_text:
            return "[REDACTED]"

        if masking_type == "hash":
            import hashlib

            hash_val = hashlib.sha256(original_text.encode()).hexdigest()[:8]
            return f"[{phi_type}_{hash_val}]"
        elif masking_type == "generalize":
            # 泛化: 保留類型標籤
            return f"[{phi_type}]"
        else:  # redact (預設)
            return "[REDACTED]"

    def _apply_hard_rules(
        self, phi_entities: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        套用 hard rules 後處理，修正 LLM 常見錯誤

        Returns:
            (filtered_entities, corrections): 過濾後的實體列表和修正記錄
        """
        corrections: list[str] = []
        filtered: list[dict[str, Any]] = []

        for entity in phi_entities:
            phi_type = entity.get("type", "")
            value = entity.get("value", "")

            # Rule 1: AGE_OVER_89 和 AGE 類型必須 >= 89 才保留
            # LLM 有時會把任意數字誤判為年齡
            if phi_type in ("AGE_OVER_89", "AGE_OVER_90", "AGE"):
                age = self._extract_age_number(value)
                if age is not None and age < 89:
                    corrections.append(f"Removed {phi_type} '{value}' (age={age} < 89)")
                    continue  # 跳過這條記錄
                elif age is not None and age >= 89:
                    # 年齡正確，保留
                    filtered.append(entity)
                else:
                    # 無法解析數字，移除（保守策略：不確定就不要遮罩）
                    corrections.append(f"Removed {phi_type} '{value}' (unable to parse age)")
                    continue
            else:
                # 其他類型直接保留
                filtered.append(entity)

        return filtered, corrections

    def _extract_age_number(self, text: str) -> int | None:
        """
        從文字中提取年齡數值

        支援格式: "72歲", "92 歲", "85", "age 72", "年齡: 90"
        """
        if not text:
            return None

        # 移除常見單位和標籤
        clean_text = text.strip()

        # 嘗試直接匹配數字
        # Pattern 1: 純數字或數字+歲
        match = re.search(r"(\d+)\s*歲?", clean_text)
        if match:
            return int(match.group(1))

        # Pattern 2: age/年齡 + 數字
        match = re.search(r"(?:age|年齡|歲數)[\s:：]*(\d+)", clean_text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        return None

    def _regenerate_masked_content(
        self,
        original_content: str,
        phi_entities: list[dict[str, Any]],
        masking_type: str,
    ) -> str:
        """
        根據過濾後的 phi_entities 重新生成 masked_content

        這用於在 _apply_hard_rules 移除了某些 entities 後，
        確保 masked_content 和 phi_entities 保持同步。

        Args:
            original_content: 原始文本內容
            phi_entities: 過濾後的 PHI 實體列表
            masking_type: 遮罩類型 (redact/hash/generalize)

        Returns:
            重新生成的 masked_content
        """
        if not phi_entities:
            return original_content

        # 按位置排序（從後往前替換以避免位置偏移問題）
        sorted_entities = sorted(phi_entities, key=lambda e: e.get("start_pos", 0), reverse=True)

        masked_text = original_content

        for entity in sorted_entities:
            start_pos = entity.get("start_pos")
            end_pos = entity.get("end_pos")
            value = entity.get("value", "")
            phi_type = entity.get("type", "UNKNOWN")

            if start_pos is None or end_pos is None:
                # 沒有位置信息，嘗試搜索替換
                masked_value = self._compute_masked_value(value, phi_type, masking_type)
                masked_text = masked_text.replace(value, masked_value, 1)
                log.debug(
                    "Replaced entity by search",
                    value=value[:30],
                    phi_type=phi_type,
                )
            else:
                # 使用位置替換
                masked_value = self._compute_masked_value(value, phi_type, masking_type)

                # 驗證位置是否匹配
                if start_pos < len(masked_text) and masked_text[start_pos:end_pos] == value:
                    masked_text = masked_text[:start_pos] + masked_value + masked_text[end_pos:]
                    log.debug(
                        "Replaced entity by position",
                        value=value[:30],
                        phi_type=phi_type,
                        pos=f"{start_pos}-{end_pos}",
                    )
                # 位置不匹配，嘗試搜索替換
                elif value in masked_text:
                    masked_text = masked_text.replace(value, masked_value, 1)
                    log.warning(
                        "Position mismatch, replaced by search",
                        value=value[:30],
                        expected_pos=f"{start_pos}-{end_pos}",
                    )
                else:
                    log.error(
                        "Could not replace entity",
                        value=value[:30],
                        phi_type=phi_type,
                    )

        return masked_text

    def _simulate_processing(
        self, file_path: Path, original_filename: str | None = None
    ) -> dict[str, Any]:
        """模擬處理（當引擎不可用時）"""
        import time

        time.sleep(1)  # 模擬處理時間

        display_filename = original_filename or file_path.name

        return {
            "file_id": file_path.stem[:8],
            "filename": display_filename,
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
        total_chars = sum(len(r.get("original_content") or "") for r in file_results)

        # 建立檔案名稱清單 (用於顯示)
        filenames = [r.get("filename", "") for r in file_results if r.get("filename")]
        files_display = ", ".join(filenames[:3])  # 最多顯示 3 個
        if len(filenames) > 3:
            files_display += f" ... 等 {len(filenames)} 個檔案"

        # 聚合 PHI 類型統計
        phi_by_type: dict[str, int] = {}
        for result in file_results:
            for entity in result.get("phi_entities", []):
                phi_type = entity.get("type", "UNKNOWN")
                phi_by_type[phi_type] = phi_by_type.get(phi_type, 0) + 1

        report = {
            "task_id": task_id,
            "job_name": job_name,
            "files_display": files_display,  # 新增：檔案名稱顯示
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "files_processed": len(file_results),
                "total_phi_found": total_phi,
                "total_chars": total_chars,
                "processing_time_seconds": processing_time,
                "processing_speed_chars_per_sec": total_chars / processing_time
                if processing_time > 0
                else 0,
                "filenames": filenames,  # 新增：完整檔案名稱列表
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
