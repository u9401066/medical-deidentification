"""Files API Router."""

import json
import re
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import REPORTS_DIR, RESULTS_DIR
from models.auth import AuthUser
from models.file import UploadedFile
from security import get_current_user
from services.file_service import get_file_service
from services.result_sanitizer import sanitize_payload
from services.task_service import get_task_service

router = APIRouter()


def _validate_id(value: str, label: str = "ID") -> None:
    if not re.fullmatch(r"[a-zA-Z0-9-]{1,64}", value):
        raise HTTPException(400, f"無效的{label}")


def _result_dataframe(data: dict, only_file_id: str | None = None) -> pd.DataFrame:
    all_masked_data = []
    for file_result in data.get("results", []):
        if only_file_id and file_result.get("file_id") != only_file_id:
            continue
        masked_data = file_result.get("masked_data")
        if masked_data and isinstance(masked_data, list):
            all_masked_data.extend(masked_data)
        elif file_result.get("masked_content"):
            all_masked_data.append(
                {
                    "檔案": file_result.get("filename", ""),
                    "內容": file_result.get("masked_content", ""),
                }
            )

    if all_masked_data:
        return pd.DataFrame(all_masked_data)

    return pd.DataFrame([{"訊息": "沒有可輸出的資料", "任務 ID": data.get("task_id", "")}])


def _report_dataframe(data: dict) -> pd.DataFrame:
    phi_records = []
    for file_detail in data.get("file_details", []):
        filename = file_detail.get("filename", "unknown")
        for phi in file_detail.get("phi_entities", []):
            phi_records.append(
                {
                    "檔案": filename,
                    "PHI 類型": phi.get("type", ""),
                    "原始值": phi.get("value") or "[REDACTED]",
                    "遮罩值": phi.get("masked_value", "[MASKED]"),
                    "信心度": phi.get("confidence", ""),
                }
            )

    if phi_records:
        return pd.DataFrame(phi_records)

    return pd.DataFrame([{"訊息": "沒有發現 PHI", "任務 ID": data.get("task_id", "")}])


def _stream_dataframe(df: pd.DataFrame, filename: str, format: str) -> StreamingResponse:
    output = BytesIO()
    if format == "xlsx":
        df.to_excel(output, index=False, engine="openpyxl")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        df.to_csv(output, index=False, encoding="utf-8-sig")
        media_type = "text/csv"
    output.seek(0)
    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/upload", response_model=UploadedFile)
async def upload_file(
    file: UploadFile = File(...),
    current_user: AuthUser = Depends(get_current_user),
):
    """上傳檔案"""
    file_service = get_file_service()

    if not file.filename:
        raise HTTPException(400, "未提供檔案名稱")

    allowed_extensions = {".xlsx", ".xls", ".csv", ".json", ".txt"}
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if f".{file_ext}" not in allowed_extensions:
        raise HTTPException(400, f"不支援的檔案類型: {file_ext}。支援: xlsx, xls, csv, json, txt")

    content = await file.read()

    try:
        result = await file_service.upload(
            file.filename,
            content,
            owner_user_id=current_user.user_id,
            owner_username=current_user.username,
        )
        return result
    except ValueError as e:
        raise HTTPException(413, str(e))


@router.get("/files", response_model=list[UploadedFile])
async def list_files(current_user: AuthUser = Depends(get_current_user)):
    """列出所有上傳的檔案（含處理狀態）"""
    file_service = get_file_service()
    return file_service.list_files(
        user_id=current_user.user_id,
        is_admin=current_user.role == "admin",
    )


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, current_user: AuthUser = Depends(get_current_user)):
    """刪除檔案"""
    file_service = get_file_service()

    try:
        if file_service.delete(
            file_id,
            user_id=current_user.user_id,
            is_admin=current_user.role == "admin",
        ):
            return {"message": "檔案已刪除"}
        raise HTTPException(404, "檔案不存在")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))


@router.get("/download/{file_id}")
async def download_result(
    file_id: str,
    file_type: str = Query("result", enum=["result", "report"]),
    format: str = Query("xlsx", enum=["xlsx", "csv", "json"]),
    reveal_phi: bool = Query(False),
    current_user: AuthUser = Depends(get_current_user),
):
    """下載處理結果或報告

    Args:
        file_id: 任務 ID
        file_type: result (處理結果) 或 report (報告)
        format: xlsx, csv, json
    """
    _validate_id(file_id, "任務 ID")
    task_service = get_task_service()
    task = task_service.get_task(file_id)
    if not task_service.can_access_task(
        task,
        user_id=current_user.user_id,
        is_admin=current_user.role == "admin",
    ):
        raise HTTPException(404, "檔案不存在")

    if file_type == "result":
        search_dir = RESULTS_DIR
    else:
        search_dir = REPORTS_DIR

    # 找到對應的 JSON 檔案
    artifact_name = f"{file_id}_{file_type}.json"
    matching_files = list(search_dir.rglob(artifact_name))
    if not matching_files:
        raise HTTPException(404, "檔案不存在")

    json_path = matching_files[0]

    # 如果要求 JSON 格式，直接返回
    if format == "json":
        with open(json_path, encoding="utf-8") as f:
            return JSONResponse(
                content=sanitize_payload(json.load(f), reveal_phi=reveal_phi),
                headers={"Content-Disposition": f"attachment; filename={file_id}_{file_type}.json"},
            )

    # 讀取 JSON
    with open(json_path, encoding="utf-8") as f:
        data = sanitize_payload(json.load(f), reveal_phi=reveal_phi)

    if file_type == "result":
        df = _result_dataframe(data)
    else:
        df = _report_dataframe(data)

    # 產生檔案
    if format == "xlsx":
        filename = f"{file_id}_{file_type}.xlsx"
    else:  # csv
        filename = f"{file_id}_{file_type}.csv"

    return _stream_dataframe(df, filename, format)


@router.get("/download/{task_id}/file/{file_id}")
async def download_single_file_result(
    task_id: str,
    file_id: str,
    format: str = Query("xlsx", enum=["xlsx", "csv", "json"]),
    reveal_phi: bool = Query(False),
    current_user: AuthUser = Depends(get_current_user),
):
    """下載任務中單一檔案的去識別化結果。"""
    _validate_id(task_id, "任務 ID")
    _validate_id(file_id, "檔案 ID")
    task_service = get_task_service()
    task = task_service.get_task(task_id)
    if not task_service.can_access_task(
        task,
        user_id=current_user.user_id,
        is_admin=current_user.role == "admin",
    ):
        raise HTTPException(404, "結果不存在")

    matching_result_files = list(RESULTS_DIR.rglob(f"{task_id}_result.json"))
    if not matching_result_files:
        raise HTTPException(404, "結果不存在")

    with open(matching_result_files[0], encoding="utf-8") as f:
        data = json.load(f)

    matching_results = [
        result for result in data.get("results", []) if result.get("file_id") == file_id
    ]
    if not matching_results:
        raise HTTPException(404, "單檔結果不存在")

    if format == "json":
        return sanitize_payload(
            {"task_id": task_id, "results": matching_results},
            reveal_phi=reveal_phi,
        )

    safe_data = sanitize_payload(
        {"task_id": task_id, "results": matching_results},
        reveal_phi=reveal_phi,
    )
    df = _result_dataframe(safe_data, only_file_id=file_id)
    return _stream_dataframe(df, f"{task_id}_{file_id}_result.{format}", format)
