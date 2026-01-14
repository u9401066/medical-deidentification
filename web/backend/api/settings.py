"""
Settings API Router
設定與法規 API
"""
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from models.config import PHIConfig
from models.regulation import RegulationRule, RegulationContent
from services.regulation_service import get_regulation_service

router = APIRouter()


@router.get("/settings/phi-types")
async def get_phi_types():
    """取得所有可用的 PHI 類型"""
    # 嘗試從核心模組取得
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from core.domain import PHIType
        return [
            {
                "type": phi_type.value,
                "name": phi_type.name,
                "description": _get_phi_description(phi_type.value),
                "default_masking": "mask",
            }
            for phi_type in PHIType
        ]
    except ImportError:
        # 預設 PHI 類型
        default_types = [
            "NAME", "DATE", "PHONE", "EMAIL", "ADDRESS",
            "ID_NUMBER", "MEDICAL_RECORD", "SSN", "AGE_OVER_89"
        ]
        return [
            {
                "type": t,
                "name": t.replace("_", " ").title(),
                "description": _get_phi_description(t),
                "default_masking": "mask",
            }
            for t in default_types
        ]


def _get_phi_description(phi_type: str) -> str:
    """取得 PHI 類型描述"""
    descriptions = {
        "NAME": "個人姓名",
        "DATE": "日期（出生日期、就診日期等）",
        "PHONE": "電話號碼",
        "EMAIL": "電子郵件地址",
        "ADDRESS": "地址",
        "ID_NUMBER": "身分證字號、護照號碼等",
        "MEDICAL_RECORD": "病歷號",
        "SSN": "社會安全號碼",
        "AGE_OVER_89": "89歲以上的年齡",
        "LOCATION": "地理位置",
        "FAX": "傳真號碼",
        "ACCOUNT": "帳號",
        "LICENSE": "證照號碼",
        "VEHICLE": "車輛識別碼",
        "DEVICE": "設備識別碼",
        "URL": "網址",
        "IP": "IP 位址",
        "BIOMETRIC": "生物辨識資料",
        "PHOTO": "照片",
    }
    return descriptions.get(phi_type, f"{phi_type} 類型的個人識別資訊")


@router.get("/settings/config")
async def get_config():
    """取得目前的設定"""
    return PHIConfig().model_dump()


@router.put("/settings/config")
async def update_config(config: PHIConfig):
    """更新設定"""
    # TODO: 持久化設定
    return {"message": "設定已更新", "config": config.model_dump()}


@router.get("/regulations", response_model=list[RegulationRule])
async def list_regulations():
    """列出所有法規規則"""
    regulation_service = get_regulation_service()
    return regulation_service.list_regulations()


@router.get("/regulations/{rule_id}/content")
async def get_regulation_content(rule_id: str):
    """取得法規的完整內容"""
    regulation_service = get_regulation_service()
    content = regulation_service.get_regulation_content(rule_id)
    
    if not content:
        raise HTTPException(404, f"找不到法規內容: {rule_id}")
    
    return content.model_dump()


@router.put("/regulations/{rule_id}")
async def update_regulation(rule_id: str, enabled: bool):
    """更新法規啟用狀態"""
    regulation_service = get_regulation_service()
    
    if regulation_service.update_regulation(rule_id, enabled):
        return {"message": "法規已更新", "rule_id": rule_id, "enabled": enabled}
    
    raise HTTPException(404, "法規不存在")


@router.post("/regulations/upload")
async def upload_regulation(file: UploadFile = File(...)):
    """上傳自訂法規"""
    allowed_extensions = {".md", ".txt", ".json"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            400,
            f"不支援的檔案類型: {file_ext}。支援: md, txt, json"
        )
    
    content = await file.read()
    regulation_service = get_regulation_service()
    
    result = await regulation_service.upload_regulation(file.filename, content)
    
    return result
