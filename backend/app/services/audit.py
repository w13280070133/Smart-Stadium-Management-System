# app/services/audit.py
from typing import Optional, Dict, Any

from ..database import get_db


def get_setting(group_key: str, setting_key: str, default: Optional[str] = None) -> Optional[str]:
    """
    从 system_settings 表中读取配置项。
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            SELECT setting_value
            FROM system_settings
            WHERE group_key = %s AND setting_key = %s
            """,
            (group_key, setting_key),
        )
        row = cursor.fetchone()
        return row[0] if row else default
    finally:
        cursor.close()
        db.close()


def is_login_log_enabled() -> bool:
    return (get_setting("audit", "enable_login_log", "1") or "1") == "1"


def is_operation_log_enabled() -> bool:
    return (get_setting("audit", "enable_operation_log", "1") or "1") == "1"


def write_login_log(
    user_id: int,
    username: str,
    success: bool,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    message: Optional[str] = None,
) -> None:
    """
    写登录日志。
    """
    if not is_login_log_enabled():
        return

    db = get_db()
    cursor = db.cursor()
    try:
        sql = """
        INSERT INTO login_logs (user_id, username, ip, user_agent, success, message)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            (
                user_id,
                username,
                ip,
                user_agent,
                1 if success else 0,
                message,
            ),
        )
        db.commit()
    finally:
        cursor.close()
        db.close()


def write_operation_log(
    user_id: int,
    username: str,
    action: str,
    module: str,
    target_id: Optional[int] = None,
    target_desc: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
    ip: Optional[str] = None,
) -> None:
    """
    写操作日志。
    """
    if not is_operation_log_enabled():
        return

    import json

    detail_json = json.dumps(detail, ensure_ascii=False) if detail is not None else None

    db = get_db()
    cursor = db.cursor()
    try:
        sql = """
        INSERT INTO operation_logs
        (user_id, username, action, module, target_id, target_desc, detail, ip)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            (
                user_id,
                username,
                action,
                module,
                target_id,
                target_desc,
                detail_json,
                ip,
            ),
        )
        db.commit()
    finally:
        cursor.close()
        db.close()
