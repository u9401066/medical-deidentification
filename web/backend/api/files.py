"""
Files API Router
檔案上傳/下載 API
"""

import json
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from starlette.responses import StreamingResponse

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import REPORTS_DIR, RESULTS_DIR
from models.file import UploadedFile
from services.file_service import get_file_service

router = APIRouter()


@router.post("/upload", response_model=UploadedFile)
async def upload_file(file: UploadFile = File(...)):
    """上傳檔案"""
    file_service = get_file_service()

    # 支援的檔案類型
    allowed_extensions = {
        # 表格
        ".xlsx", ".xls", ".csv",
        # 結構化
        ".json",
        # 文字
        ".txt", ".md", ".markdown",
        # 文件
        ".docx", ".doc", ".pdf",
    }
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if f".{file_ext}" not in allowed_extensions:
        supported = ", ".join(ext.lstrip(".") for ext in sorted(allowed_extensions))
        raise HTTPException(400, f"不支援的檔案類型: {file_ext}。支援: {supported}")

    content = await file.read()

    try:
        result = await file_service.upload(file.filename, content)
        return result
    except ValueError as e:
        raise HTTPException(413, str(e))


@router.get("/files", response_model=list[UploadedFile])
async def list_files():
    """列出所有上傳的檔案（含處理狀態）"""
    file_service = get_file_service()
    return file_service.list_files()


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """刪除檔案"""
    file_service = get_file_service()

    try:
        if file_service.delete(file_id):
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
):
    """下載處理結果或報告

    Args:
        file_id: 任務 ID
        file_type: result (處理結果) 或 report (報告)
        format: xlsx, csv, json
    """
    if file_type == "result":
        search_dir = RESULTS_DIR
    else:
        search_dir = REPORTS_DIR

    # 找到對應的 JSON 檔案
    matching_files = list(search_dir.glob(f"{file_id}*"))
    if not matching_files:
        raise HTTPException(404, "檔案不存在")

    json_path = matching_files[0]

    # 如果要求 JSON 格式，直接返回
    if format == "json":
        return FileResponse(
            json_path, filename=f"{file_id}_{file_type}.json", media_type="application/json"
        )

    # 讀取 JSON
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    # 輸出 mask 後的完整資料
    output = BytesIO()

    if file_type == "result":
        # 優先使用 masked_data (表格資料)
        all_masked_data = []
        for file_result in data.get("results", []):
            masked_data = file_result.get("masked_data")
            if masked_data and isinstance(masked_data, list):
                all_masked_data.extend(masked_data)
            elif file_result.get("masked_content"):
                # 純文字內容，包裝成表格
                all_masked_data.append(
                    {
                        "檔案": file_result.get("filename", ""),
                        "內容": file_result.get("masked_content", ""),
                    }
                )

        if all_masked_data:
            df = pd.DataFrame(all_masked_data)
        else:
            # fallback: 輸出 PHI 摘要
            df = pd.DataFrame(
                [
                    {
                        "訊息": "沒有可輸出的資料",
                        "任務 ID": file_id,
                    }
                ]
            )
    else:
        # 報告格式：輸出 PHI 列表
        phi_records = []
        for file_detail in data.get("file_details", []):
            filename = file_detail.get("filename", "unknown")
            for phi in file_detail.get("phi_entities", []):
                phi_records.append(
                    {
                        "檔案": filename,
                        "PHI 類型": phi.get("type", ""),
                        "原始值": phi.get("value", ""),
                        "遮罩值": phi.get("masked_value", "[MASKED]"),
                        "信心度": phi.get("confidence", ""),
                    }
                )

        if phi_records:
            df = pd.DataFrame(phi_records)
        else:
            df = pd.DataFrame(
                [
                    {
                        "訊息": "沒有發現 PHI",
                        "任務 ID": file_id,
                    }
                ]
            )

    # 產生檔案
    if format == "xlsx":
        df.to_excel(output, index=False, engine="openpyxl")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{file_id}_{file_type}.xlsx"
    else:  # csv
        df.to_csv(output, index=False, encoding="utf-8-sig")  # BOM for Excel
        media_type = "text/csv"
        filename = f"{file_id}_{file_type}.csv"

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
