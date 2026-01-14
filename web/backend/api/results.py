"""
Results API Router
結果與報告 API
"""

import json
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from loguru import logger

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import REPORTS_DIR, RESULTS_DIR

router = APIRouter()


@router.get("/results")
async def list_results():
    """列出所有處理結果"""
    results = []

    for result_file in RESULTS_DIR.glob("*_result.json"):
        try:
            with open(result_file, encoding="utf-8") as f:
                data = json.load(f)

            # 聚合 PHI 類型
            phi_by_type: dict[str, int] = {}
            for file_result in data.get("results", []):
                for entity in file_result.get("phi_entities", []):
                    phi_type = entity.get("type", "UNKNOWN")
                    phi_by_type[phi_type] = phi_by_type.get(phi_type, 0) + 1

            results.append(
                {
                    "task_id": data["task_id"],
                    "job_name": data.get("job_name", ""),
                    "files_count": len(data.get("results", [])),
                    "total_phi_found": sum(r.get("phi_found", 0) for r in data.get("results", [])),
                    "phi_by_type": phi_by_type,
                    "processed_at": data.get("processed_at", ""),
                }
            )
        except Exception as e:
            logger.warning(f"Error reading result file {result_file}: {e}")

    return sorted(results, key=lambda x: x["processed_at"], reverse=True)


@router.get("/results/{task_id}")
async def get_result(task_id: str):
    """取得處理結果詳情"""
    result_file = RESULTS_DIR / f"{task_id}_result.json"

    if not result_file.exists():
        raise HTTPException(404, "結果不存在")

    with open(result_file, encoding="utf-8") as f:
        return json.load(f)


@router.get("/reports")
async def list_reports():
    """列出所有報告"""
    reports = []

    for report_file in REPORTS_DIR.glob("*_report.json"):
        try:
            with open(report_file, encoding="utf-8") as f:
                report = json.load(f)

            task_id = report["task_id"]
            reports.append(
                {
                    "id": task_id,  # 前端需要 id 欄位
                    "task_id": task_id,
                    "filename": report.get("job_name", report_file.name),
                    "job_name": report.get("job_name", ""),
                    "files_processed": report["summary"]["files_processed"],
                    "total_phi_found": report["summary"]["total_phi_found"],
                    "created_at": report["generated_at"],  # 前端需要 created_at
                    "generated_at": report["generated_at"],
                }
            )
        except Exception as e:
            logger.warning(f"Error reading report file {report_file}: {e}")

    return sorted(reports, key=lambda x: x["generated_at"], reverse=True)


@router.get("/reports/{task_id}")
async def get_report(task_id: str):
    """取得報告詳情"""
    report_file = REPORTS_DIR / f"{task_id}_report.json"

    if not report_file.exists():
        raise HTTPException(404, "報告不存在")

    with open(report_file, encoding="utf-8") as f:
        return json.load(f)
