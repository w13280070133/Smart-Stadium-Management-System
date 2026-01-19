"""
会员折扣计算模块

提供会员等级折扣的计算逻辑，根据会员等级返回相应的折扣比例。
折扣配置存储在系统设置中，支持动态配置。
"""
import json
from typing import Any


def get_member_discount(cursor, member_id: int) -> float:
    """
    获取会员等级折扣
    
    折扣计算规则：
    1. 从 members 表获取会员的 level 字段
    2. 从 system_settings 表读取会员等级配置（JSON 格式）
    3. 匹配会员等级（按 code 或 name 匹配）
    4. 返回对应的折扣比例
    
    会员等级配置示例：
    [
        {"code": "vip", "name": "VIP会员", "discount": 90, "enabled": true},
        {"code": "gold", "name": "金卡会员", "discount": 85, "enabled": true},
        {"code": "normal", "name": "普通会员", "discount": 100, "enabled": true}
    ]
    
    Args:
        cursor: 数据库游标对象
        member_id: 会员 ID
        
    Returns:
        float: 折扣比例（百分比），100 表示无折扣（原价）
               例如：90 表示 9 折，85 表示 8.5 折
    
    注意：
        - 只有 enabled=true 的等级配置才会生效
        - 如果会员等级未配置或配置错误，返回 100（无折扣）
        - 异常情况下默认返回 100，保证业务可用性
    """
    discount = 100.0
    if not member_id:
        return discount

    try:
        cursor.execute("SELECT level FROM members WHERE id = %s", (member_id,))
        row = cursor.fetchone()
        if not row:
            return discount

        level_raw = row.get("level") if isinstance(row, dict) else (row[0] if isinstance(row, (list, tuple)) else None)
        if not level_raw:
            return discount
        level = str(level_raw)

        cursor.execute(
            """
            SELECT setting_value FROM system_settings
            WHERE group_key = 'member' AND setting_key = 'member_levels_json'
            """
        )
        srow = cursor.fetchone()
        levels_json = srow.get("setting_value") if isinstance(srow, dict) else (srow[0] if srow else None)
        if not levels_json:
            return discount

        levels = json.loads(levels_json)
        if not isinstance(levels, list):
            return discount

        for lv in levels:
            code = str(lv.get("code"))
            name = str(lv.get("name"))
            enabled = lv.get("enabled", True)
            if not enabled:
                continue
            if level == code or level == name:
                try:
                    d = float(lv.get("discount", 100))
                    if d > 0:
                        discount = d
                except Exception:
                    pass
                break
    except Exception:
        return 100.0

    return discount
