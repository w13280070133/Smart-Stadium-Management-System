import json
from typing import Any, Dict, List, Tuple

DEFAULT_LEVEL_NAME = "普通会员"


def load_member_config(cursor) -> Dict[str, Any]:
    """
    读取会员等级/卡种配置：
    {
        "default_level": "normal",
        "levels": [
            {"name": "普通会员", "code": "normal", "discount": 100, "enabled": True},
            ...
        ]
    }
    """
    config: Dict[str, Any] = {"default_level": DEFAULT_LEVEL_NAME, "levels": []}

    cursor.execute(
        """
        SELECT setting_value
        FROM system_settings
        WHERE group_key = 'member' AND setting_key = 'default_level'
        """
    )
    row = cursor.fetchone()
    if row:
        value = row.get("setting_value") if isinstance(row, dict) else row[0]
        if value:
            config["default_level"] = str(value)

    cursor.execute(
        """
        SELECT setting_value
        FROM system_settings
        WHERE group_key = 'member' AND setting_key = 'member_levels_json'
        """
    )
    row = cursor.fetchone()
    levels_json = row.get("setting_value") if isinstance(row, dict) else (row[0] if row else None)
    levels: List[Dict[str, Any]] = []
    if levels_json:
        try:
            parsed = json.loads(levels_json)
            if isinstance(parsed, list):
                for item in parsed:
                    name = str(item.get("name") or item.get("code") or DEFAULT_LEVEL_NAME)
                    code = str(item.get("code") or name)
                    try:
                        discount = float(item.get("discount", 100))
                    except (TypeError, ValueError):
                        discount = 100.0
                    levels.append(
                        {
                            "name": name,
                            "code": code,
                            "discount": discount,
                            "enabled": bool(item.get("enabled", True)),
                        }
                    )
        except json.JSONDecodeError:
            levels = []

    config["levels"] = levels
    return config


def normalize_level(value: str | None, config: Dict[str, Any]) -> Tuple[str, Dict[str, Any] | None]:
    """
    根据配置把任意 level 值规范化为配置中的 code；若找不到匹配则返回原值。
    返回 (level_value, level_config_dict|None)
    """
    level = (value or "").strip()
    levels: List[Dict[str, Any]] = config.get("levels", [])

    def match_level(target: str) -> Tuple[str, Dict[str, Any] | None]:
        target_lower = target.lower()
        for lv in levels:
            candidates = {
                str(lv.get("code") or "").lower(),
                str(lv.get("name") or "").lower(),
            }
            if target_lower and target_lower in candidates and lv.get("enabled", True):
                return str(lv.get("code") or lv.get("name")), lv
        return target, None

    if level:
        normalized, cfg = match_level(level)
        if cfg:
            return normalized, cfg

    default_level = str(config.get("default_level") or DEFAULT_LEVEL_NAME)
    normalized, cfg = match_level(default_level)
    if cfg:
        return normalized, cfg

    # 若配置中找不到，仍返回原始值，保持兼容
    return level or default_level, None


def get_level_display(level_value: str | None, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据 level 值返回 {name, code, discount}，用于展示。
    如果找不到匹配，将 name 返回 level_value 本身。
    """
    level = (level_value or "").strip()
    levels: List[Dict[str, Any]] = config.get("levels", [])
    for lv in levels:
        if not lv.get("enabled", True):
            continue
        if level.lower() == str(lv.get("code") or "").lower() or level.lower() == str(lv.get("name") or "").lower():
            return {
                "code": lv.get("code"),
                "name": lv.get("name"),
                "discount": lv.get("discount", 100),
            }
    return {
        "code": level or config.get("default_level") or DEFAULT_LEVEL_NAME,
        "name": level or config.get("default_level") or DEFAULT_LEVEL_NAME,
        "discount": 100,
    }





