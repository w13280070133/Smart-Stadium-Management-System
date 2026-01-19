# app/routers/audit.py
from fastapi import APIRouter, Depends, Query, Request
from typing import List, Dict, Any, Optional

from ..database import get_db
from ..deps import require_super_admin

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/login-logs")
def list_login_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    username: Optional[str] = Query(None),
    success: Optional[int] = Query(None, description="1 成功, 0 失败"),
    current_user=Depends(require_super_admin),
):
    """
    登录日志列表
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        where = " WHERE 1=1 "
        params: List[Any] = []
        if username:
            where += " AND username LIKE %s "
            params.append(f"%{username}%")
        if success in (0, 1):
            where += " AND success = %s "
            params.append(success)

        count_sql = "SELECT COUNT(*) AS cnt FROM login_logs " + where
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["cnt"]

        offset = (page - 1) * page_size
        data_sql = """
        SELECT id, user_id, username, ip, user_agent, success, message, created_at
        FROM login_logs
        """ + where + " ORDER BY id DESC LIMIT %s OFFSET %s"
        params2 = params + [page_size, offset]
        cursor.execute(data_sql, tuple(params2))
        items = cursor.fetchall()

        return {"total": total, "items": items}
    finally:
        cursor.close()
        db.close()


@router.get("/operation-logs")
def list_operation_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    module: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user=Depends(require_super_admin),
):
    """
    操作日志列表
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        where = " WHERE 1=1 "
        params: List[Any] = []

        if module:
            where += " AND module = %s "
            params.append(module)
        if username:
            where += " AND username LIKE %s "
            params.append(f"%{username}%")
        if action:
            where += " AND action LIKE %s "
            params.append(f"%{action}%")
        if start_date:
            where += " AND DATE(created_at) >= %s "
            params.append(start_date)
        if end_date:
            where += " AND DATE(created_at) <= %s "
            params.append(end_date)

        count_sql = "SELECT COUNT(*) AS cnt FROM operation_logs " + where
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["cnt"]

        offset = (page - 1) * page_size
        data_sql = """
        SELECT
          id, user_id, username, action, module,
          target_id, target_desc, detail, ip, created_at
        FROM operation_logs
        """ + where + " ORDER BY id DESC LIMIT %s OFFSET %s"
        params2 = params + [page_size, offset]
        cursor.execute(data_sql, tuple(params2))
        items = cursor.fetchall()

        return {"total": total, "items": items}
    finally:
        cursor.close()
        db.close()
