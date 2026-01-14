"""
Preview API Router
資料預覽 API
"""
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from services.file_service import get_file_service

router = APIRouter()


@router.get("/preview/{file_id}")
async def preview_file(
    file_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """預覽檔案內容
    
    Args:
        file_id: 檔案 ID
        page: 頁碼
        page_size: 每頁筆數
    """
    file_service = get_file_service()
    file_path = file_service.get_file_path(file_id)
    
    if not file_path or not file_path.exists():
        raise HTTPException(404, "檔案不存在")
    
    file_type = file_path.suffix.lower().lstrip(".")
    
    try:
        if file_type in ["xlsx", "xls", "csv"]:
            return await _preview_tabular(file_path, file_type, page, page_size)
        elif file_type == "txt":
            return await _preview_text(file_path, page, page_size)
        elif file_type == "json":
            return await _preview_json(file_path, page, page_size)
        else:
            raise HTTPException(400, f"不支援預覽的檔案類型: {file_type}")
    except Exception as e:
        raise HTTPException(500, f"預覽失敗: {str(e)}")


async def _preview_tabular(
    file_path: Path,
    file_type: str,
    page: int,
    page_size: int
) -> dict[str, Any]:
    """預覽表格資料"""
    if file_type == "csv":
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    
    total_rows = len(df)
    total_pages = (total_rows + page_size - 1) // page_size
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)
    
    page_data = df.iloc[start_idx:end_idx]
    
    return {
        "type": "table",
        "columns": list(df.columns),
        "data": page_data.fillna("").to_dict(orient="records"),
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_rows": total_rows,
            "total_pages": total_pages,
        }
    }


async def _preview_text(
    file_path: Path,
    page: int,
    page_size: int
) -> dict[str, Any]:
    """預覽純文字檔案"""
    with open(file_path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    lines = content.split("\n")
    total_lines = len(lines)
    total_pages = (total_lines + page_size - 1) // page_size
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_lines)
    
    return {
        "type": "text",
        "content": "\n".join(lines[start_idx:end_idx]),
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_rows": total_lines,
            "total_pages": total_pages,
        }
    }


async def _preview_json(
    file_path: Path,
    page: int,
    page_size: int
) -> dict[str, Any]:
    """預覽 JSON 檔案"""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    
    if isinstance(data, list):
        total_rows = len(data)
        total_pages = (total_rows + page_size - 1) // page_size
        
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        return {
            "type": "json",
            "data": data[start_idx:end_idx],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_rows": total_rows,
                "total_pages": total_pages,
            }
        }
    else:
        # 單一物件，直接返回
        return {
            "type": "json",
            "data": data,
            "pagination": {
                "page": 1,
                "page_size": 1,
                "total_rows": 1,
                "total_pages": 1,
            }
        }
