# app/services/notifications.py
from typing import Optional, List, Dict, Any
from ..database import get_db


def _detect_columns(cursor) -> set[str]:
    cursor.execute("SHOW COLUMNS FROM notifications")
    rows = cursor.fetchall() or []
    cols = set()
    for r in rows:
        if isinstance(r, dict):
            cols.add(r.get("Field"))
        else:
            cols.add(r[0])
    return {c for c in cols if c}


def create_notification(
    *,
    user_id: int | None = None,
    member_id: int | None = None,
    title: str,
    content: str,
    level: str = "info",
) -> int:
    """
    创建一条通知，支持 user_id（员工/管理员）或 member_id（会员）。
    - 若表结构要求 user_id 非空且未传，则回退为首个管理员用户 id；如无管理员则抛错。
    - 自动探测列存在性，兼容 member_id 可选场景。
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cols = _detect_columns(cursor)

        final_user_id = user_id
        if final_user_id is None:
            # 回退首个 admin 用户
            cursor.execute("SHOW TABLES LIKE 'users'")
            if cursor.fetchone():
                cursor.execute("SELECT id FROM users WHERE role = 'admin' AND is_active = 1 ORDER BY id ASC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    final_user_id = row.get("id")
            if final_user_id is None:
                raise ValueError("no admin user found for notification and user_id is required")

        columns: List[str] = []
        placeholders: List[str] = []
        params: List[Any] = []

        if "user_id" in cols:
            columns.append("user_id")
            placeholders.append("%s")
            params.append(final_user_id)
        if "member_id" in cols and member_id is not None:
            columns.append("member_id")
            placeholders.append("%s")
            params.append(member_id)

        columns.extend(["title", "content", "level"])
        placeholders.extend(["%s", "%s", "%s"])
        params.extend([title, content, level])

        sql = f"INSERT INTO notifications ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(sql, tuple(params))
        db.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        db.close()


def create_admin_notifications(title: str, content: str, level: str = "info") -> None:
    """
    发送给所有 admin 用户的通知（按 users.role='admin' 且 is_active=1）
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            return
        cursor.execute("SELECT id FROM users WHERE role = 'admin' AND is_active = 1")
        admins = cursor.fetchall() or []
        for a in admins:
            uid = a.get("id")
            if uid:
                try:
                    create_notification(user_id=uid, title=title, content=content, level=level)
                except Exception:
                    # 单个失败不影响整体
                    continue
    finally:
        cursor.close()
        db.close()


def list_notifications(
    *,
    user_id: int | None = None,
    member_id: int | None = None,
    is_read: Optional[int] = None,
    level: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """
    列出通知，优先按 member_id 过滤，其次 user_id；支持已读状态筛选 + 分页。
    """
    offset = (page - 1) * page_size
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        where_sql = "WHERE 1=1"
        params: List[Any] = []

        if member_id is not None:
            where_sql += " AND member_id = %s"
            params.append(member_id)
        elif user_id is not None:
            where_sql += " AND user_id = %s"
            params.append(user_id)

        if is_read in (0, 1):
            where_sql += " AND is_read = %s"
            params.append(is_read)

        if level:
            where_sql += " AND level = %s"
            params.append(level)

        if keyword:
            where_sql += " AND (title LIKE %s OR content LIKE %s)"
            kw = f"%{keyword}%"
            params.extend([kw, kw])

        count_sql = f"SELECT COUNT(*) AS cnt FROM notifications {where_sql}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["cnt"]

        data_sql = f"""
        SELECT id, user_id, member_id, title, content, level, is_read, created_at, read_at
        FROM notifications
        {where_sql}
        ORDER BY created_at DESC, id DESC
        LIMIT %s OFFSET %s
        """
        params2 = params + [page_size, offset]
        cursor.execute(data_sql, tuple(params2))
        items = cursor.fetchall()

        return {"total": total, "items": items}
    finally:
        cursor.close()
        db.close()


def mark_notification_read(*, user_id: int | None = None, member_id: int | None = None, notif_id: int) -> bool:
    """
    将通知标记为已读，优先 member_id，再 user_id。
    """
    db = get_db()
    cursor = db.cursor()
    try:
        where_sql = "id = %s"
        params: List[Any] = [notif_id]

        if member_id is not None:
            where_sql += " AND member_id = %s"
            params.append(member_id)
        elif user_id is not None:
            where_sql += " AND user_id = %s"
            params.append(user_id)

        sql = f"""
        UPDATE notifications
        SET is_read = 1, read_at = NOW()
        WHERE {where_sql}
        """
        cursor.execute(sql, tuple(params))
        db.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        db.close()


def mark_all_notifications_read(*, user_id: int | None = None, member_id: int | None = None) -> int:
    """
    将当前用户或会员的全部通知标记为已读
    """
    if user_id is None and member_id is None:
        return 0
    db = get_db()
    cursor = db.cursor()
    try:
        where_sql = []
        params: List[Any] = []
        if member_id is not None:
            where_sql.append("member_id = %s")
            params.append(member_id)
        if user_id is not None:
            where_sql.append("user_id = %s")
            params.append(user_id)
        if not where_sql:
            return 0
        sql = f"""
        UPDATE notifications
        SET is_read = 1, read_at = NOW()
        WHERE {' AND '.join(where_sql)} AND is_read = 0
        """
        cursor.execute(sql, tuple(params))
        db.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        db.close()
