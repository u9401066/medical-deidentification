"""
Regulation Service
法規管理服務
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

from loguru import logger

# 處理相對 import
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from config import REGULATIONS_DIR
from models.regulation import RegulationContent, RegulationRule


class RegulationService:
    """法規管理服務"""

    def __init__(self, regulations_dir: Path = REGULATIONS_DIR):
        self.regulations_dir = regulations_dir
        self.regulations_dir.mkdir(parents=True, exist_ok=True)

        # 專案根目錄的法規來源
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.source_docs_dir = self.project_root / "regulations" / "source_documents"

        # 內建法規對照表
        self.source_files = {
            "hipaa-safe-harbor": "hipaa_safe_harbor.md",
            "hipaa-phi": "hipaa_phi_definition.md",
            "taiwan-pdpa": "taiwan_pdpa.md",
        }

    def list_regulations(self) -> list[RegulationRule]:
        """列出所有法規"""
        regulations = []

        # 載入內建法規
        builtin_rules = [
            RegulationRule(
                id="hipaa-safe-harbor",
                name="HIPAA Safe Harbor",
                description="HIPAA 安全港規則 - 18 類識別項",
                enabled=True,
                source="built-in",
                rules_count=18,
            ),
            RegulationRule(
                id="hipaa-phi",
                name="HIPAA PHI Definition",
                description="HIPAA 受保護健康資訊定義",
                enabled=True,
                source="built-in",
                rules_count=18,
            ),
        ]
        regulations.extend(builtin_rules)

        # 載入自訂法規
        custom_rules_file = self.regulations_dir / "custom_rules.json"
        if custom_rules_file.exists():
            with open(custom_rules_file, encoding="utf-8") as f:
                custom_rules = json.load(f)
                for rule in custom_rules:
                    regulations.append(
                        RegulationRule(
                            id=rule["id"],
                            name=rule["name"],
                            description=rule.get("description", ""),
                            enabled=rule.get("enabled", True),
                            source="custom",
                            rules_count=rule.get("rules_count", 0),
                        )
                    )

        return regulations

    def get_regulation_content(self, rule_id: str) -> RegulationContent | None:
        """取得法規完整內容"""
        # 先找內建法規
        source_file = self.source_files.get(rule_id)
        if source_file:
            file_path = self.source_docs_dir / source_file
            if file_path.exists():
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                return RegulationContent(
                    id=rule_id,
                    name=rule_id.replace("-", " ").title(),
                    content=content,
                    source_file=source_file,
                )

        # 找自訂法規
        custom_rules_file = self.regulations_dir / "custom_rules.json"
        if custom_rules_file.exists():
            with open(custom_rules_file, encoding="utf-8") as f:
                custom_rules = json.load(f)
                for rule in custom_rules:
                    if rule.get("id") == rule_id and rule.get("content"):
                        return RegulationContent(
                            id=rule_id,
                            name=rule.get("name", rule_id),
                            content=rule.get("content", ""),
                            source_file=None,
                        )

        return None

    def update_regulation(self, rule_id: str, enabled: bool) -> bool:
        """更新法規啟用狀態"""
        custom_rules_file = self.regulations_dir / "custom_rules.json"

        # 載入或初始化
        if custom_rules_file.exists():
            with open(custom_rules_file, encoding="utf-8") as f:
                custom_rules = json.load(f)
        else:
            custom_rules = []

        # 找到並更新
        found = False
        for rule in custom_rules:
            if rule["id"] == rule_id:
                rule["enabled"] = enabled
                found = True
                break

        # 對於內建法規，也需要追蹤狀態
        if not found and rule_id in self.source_files:
            custom_rules.append(
                {
                    "id": rule_id,
                    "name": rule_id.replace("-", " ").title(),
                    "enabled": enabled,
                    "source": "built-in-override",
                }
            )
            found = True

        if found:
            with open(custom_rules_file, "w", encoding="utf-8") as f:
                json.dump(custom_rules, f, indent=2, ensure_ascii=False)
            logger.info(f"📝 Updated regulation {rule_id}: enabled={enabled}")

        return found

    async def upload_regulation(self, filename: str, content: bytes) -> dict[str, Any]:
        """上傳自訂法規"""
        original_name = Path(filename).name
        suffix = Path(original_name).suffix.lower()
        stem = Path(original_name).stem
        safe_stem = re.sub(r"[^a-zA-Z0-9_.-]+", "-", stem).strip(".-") or "regulation"
        safe_filename = f"{safe_stem}{suffix}"
        save_path = (self.regulations_dir / safe_filename).resolve()
        allowed_dir = self.regulations_dir.resolve()
        if not save_path.is_relative_to(allowed_dir):
            raise PermissionError("禁止的檔案路徑")

        with open(save_path, "wb") as f:
            f.write(content)

        # 解析法規內容
        rules_count = self._count_rules(content.decode("utf-8", errors="ignore"))

        # 建立法規記錄
        rule_id = safe_stem.lower().replace("_", "-")
        new_rule = {
            "id": rule_id,
            "name": safe_stem,
            "description": f"Custom regulation: {safe_filename}",
            "enabled": True,
            "source": "custom",
            "rules_count": rules_count,
            "content": content.decode("utf-8", errors="ignore")[:10000],  # 限制大小
        }

        # 更新自訂法規列表
        custom_rules_file = self.regulations_dir / "custom_rules.json"
        if custom_rules_file.exists():
            with open(custom_rules_file, encoding="utf-8") as f:
                custom_rules = json.load(f)
        else:
            custom_rules = []

        # 移除同 ID 的舊規則
        custom_rules = [r for r in custom_rules if r["id"] != rule_id]
        custom_rules.append(new_rule)

        with open(custom_rules_file, "w", encoding="utf-8") as f:
            json.dump(custom_rules, f, indent=2, ensure_ascii=False)

        logger.info(f"📚 Uploaded regulation: {safe_filename} ({rules_count} rules)")

        return {
            "message": f"已上傳 {safe_filename}",
            "rules": [new_rule],
        }

    def _count_rules(self, content: str) -> int:
        """估算法規中的規則數量"""
        # 簡單的啟發式方法：計算編號列表項目
        import re

        numbered_items = len(re.findall(r"^\s*\d+\.", content, re.MULTILINE))
        bullet_items = len(re.findall(r"^\s*[-*•]", content, re.MULTILINE))
        return max(numbered_items, bullet_items, 1)


# 單例模式
_regulation_service: RegulationService | None = None


def get_regulation_service() -> RegulationService:
    """取得 RegulationService 單例"""
    global _regulation_service
    if _regulation_service is None:
        _regulation_service = RegulationService()
    return _regulation_service


__all__ = ["RegulationService", "get_regulation_service"]
