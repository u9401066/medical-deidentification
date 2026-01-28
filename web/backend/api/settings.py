"""
Settings API Router
設定與法規 API
"""

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from models.config import PHIConfig
from models.regulation import RegulationRule
from services.phi_config_service import get_phi_config_service
from services.regulation_service import get_regulation_service

router = APIRouter()


# === PHI 類型定義 ===


@router.get("/settings/phi-types")
async def get_phi_types() -> list[dict[str, Any]]:
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
            "NAME",
            "DATE",
            "PHONE",
            "EMAIL",
            "ADDRESS",
            "ID_NUMBER",
            "MEDICAL_RECORD",
            "SSN",
            "AGE_OVER_89",
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
async def get_config() -> dict[str, Any]:
    """取得目前的 PHI 設定"""
    phi_config_service = get_phi_config_service()
    return phi_config_service.get_config().model_dump()


@router.put("/settings/config")
async def update_config(config: PHIConfig) -> dict[str, Any]:
    """更新 PHI 設定"""
    phi_config_service = get_phi_config_service()
    updated = phi_config_service.update_config(config)
    return {"message": "設定已更新", "config": updated.model_dump()}


# === PHI 類型個別設定 ===


class PHITypeUpdateRequest(BaseModel):
    """PHI 類型更新請求"""

    enabled: bool | None = None
    masking: str | None = None
    replace_with: str | None = None


@router.get("/settings/phi-types/{phi_type}")
async def get_phi_type_config(phi_type: str) -> dict[str, Any]:
    """取得單一 PHI 類型的設定"""
    phi_config_service = get_phi_config_service()
    type_config = phi_config_service.get_phi_type_config(phi_type)
    if type_config is None:
        return {"type": phi_type, "enabled": True, "masking": "mask", "replace_with": None}
    return {"type": phi_type, **type_config.model_dump()}


@router.put("/settings/phi-types/{phi_type}")
async def update_phi_type_config(phi_type: str, request: PHITypeUpdateRequest) -> dict[str, Any]:
    """更新單一 PHI 類型的設定"""
    phi_config_service = get_phi_config_service()
    updated = phi_config_service.update_phi_type_config(
        phi_type,
        enabled=request.enabled,
        masking=request.masking,
        replace_with=request.replace_with,
    )
    return {"message": "類型設定已更新", "type": phi_type, "config": updated.model_dump()}


# === 設定導入/導出 ===


@router.get("/settings/export")
async def export_config() -> dict[str, Any]:
    """導出目前的 PHI 設定為 JSON"""
    phi_config_service = get_phi_config_service()
    return phi_config_service.export_config(include_metadata=True)


@router.get("/settings/export/download")
async def download_config() -> FileResponse:
    """下載 PHI 設定檔"""
    phi_config_service = get_phi_config_service()
    export_file = phi_config_service.export_config_file()
    return FileResponse(
        path=export_file,
        filename=export_file.name,
        media_type="application/json",
    )


@router.post("/settings/import")
async def import_config(file: UploadFile = File(...)) -> dict[str, Any]:
    """從 JSON 檔案導入 PHI 設定"""
    if not file.filename:
        raise HTTPException(400, "未提供檔案名稱")

    if not file.filename.endswith(".json"):
        raise HTTPException(400, "只支援 JSON 格式的設定檔")

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"無效的 JSON 格式: {e}") from e

    phi_config_service = get_phi_config_service()
    try:
        imported = phi_config_service.import_config(data)
        return {"message": "設定已導入", "config": imported.model_dump()}
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/settings/import/json")
async def import_config_json(data: dict[str, Any]) -> dict[str, Any]:
    """直接從 JSON 資料導入 PHI 設定"""
    phi_config_service = get_phi_config_service()
    try:
        imported = phi_config_service.import_config(data)
        return {"message": "設定已導入", "config": imported.model_dump()}
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/settings/reset")
async def reset_config() -> dict[str, Any]:
    """重置 PHI 設定為預設值"""
    phi_config_service = get_phi_config_service()
    reset_config = phi_config_service.reset_to_default()
    return {
        "message": "設定已重置為預設值",
        "config": reset_config.model_dump(),
    }


@router.get("/settings/default")
async def get_default_config() -> dict[str, Any]:
    """取得預設 PHI 設定 (不影響目前設定)"""
    phi_config_service = get_phi_config_service()
    default = phi_config_service.get_default_config()
    return default.model_dump()


# === Preset 管理 ===


@router.get("/settings/presets")
async def list_presets() -> list[dict[str, Any]]:
    """列出所有可用的設定範本"""
    phi_config_service = get_phi_config_service()
    return phi_config_service.list_presets()


@router.get("/settings/presets/{preset_id}")
async def get_preset(preset_id: str) -> dict[str, Any]:
    """取得指定的設定範本"""
    phi_config_service = get_phi_config_service()
    preset = phi_config_service.get_preset(preset_id)
    if not preset:
        raise HTTPException(404, f"找不到設定範本: {preset_id}")
    return preset


@router.post("/settings/presets/{preset_id}/apply")
async def apply_preset(preset_id: str) -> dict[str, Any]:
    """套用指定的設定範本"""
    phi_config_service = get_phi_config_service()
    try:
        applied = phi_config_service.apply_preset(preset_id)
        return {"message": f"已套用範本: {preset_id}", "config": applied.model_dump()}
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


class SavePresetRequest(BaseModel):
    """儲存 Preset 請求"""

    name: str
    description: str = ""


@router.post("/settings/presets/{preset_id}")
async def save_preset(preset_id: str, request: SavePresetRequest) -> dict[str, Any]:
    """將目前設定儲存為新的設定範本"""
    phi_config_service = get_phi_config_service()
    return phi_config_service.save_as_preset(preset_id, request.name, request.description)


@router.delete("/settings/presets/{preset_id}")
async def delete_preset(preset_id: str) -> dict[str, Any]:
    """刪除設定範本"""
    phi_config_service = get_phi_config_service()
    try:
        phi_config_service.delete_preset(preset_id)
        return {"message": f"已刪除範本: {preset_id}"}
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


# === 法規管理 ===


@router.get("/regulations", response_model=list[RegulationRule])
async def list_regulations() -> list[RegulationRule]:
    """列出所有法規規則"""
    regulation_service = get_regulation_service()
    return regulation_service.list_regulations()


@router.get("/regulations/{rule_id}/content")
async def get_regulation_content(rule_id: str) -> dict[str, Any]:
    """取得法規的完整內容"""
    regulation_service = get_regulation_service()
    content = regulation_service.get_regulation_content(rule_id)

    if not content:
        raise HTTPException(404, f"找不到法規內容: {rule_id}")

    return content.model_dump()


@router.put("/regulations/{rule_id}")
async def update_regulation(rule_id: str, enabled: bool) -> dict[str, Any]:
    """更新法規啟用狀態"""
    regulation_service = get_regulation_service()

    if regulation_service.update_regulation(rule_id, enabled):
        return {"message": "法規已更新", "rule_id": rule_id, "enabled": enabled}

    raise HTTPException(404, "法規不存在")


@router.post("/regulations/upload")
async def upload_regulation(file: UploadFile = File(...)) -> dict[str, Any]:
    """上傳自訂法規"""
    if not file.filename:
        raise HTTPException(400, "未提供檔案名稱")

    allowed_extensions = {".md", ".txt", ".json"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(400, f"不支援的檔案類型: {file_ext}。支援: md, txt, json")

    content = await file.read()
    regulation_service = get_regulation_service()

    result = await regulation_service.upload_regulation(file.filename, content)

    return result
