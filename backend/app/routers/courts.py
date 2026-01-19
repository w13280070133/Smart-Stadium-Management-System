from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..database import get_db

router = APIRouter(prefix="/courts", tags=["Courts"])


# 1. 场地列表
@router.get("")
def list_courts():
    """
    场地列表，给管理端“场地管理”页面用。
    返回直接是数组，保持和原前端兼容。
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, name, type, price_per_hour, status, location, remark, created_at
            FROM courts
            ORDER BY id DESC
            """
        )
        rows = cursor.fetchall()
        # 确保 price_per_hour 是数字类型，前端 toFixed 才不会报错
        for r in rows:
            if r["price_per_hour"] is None:
                r["price_per_hour"] = 0
        return rows
    finally:
        cursor.close()
        db.close()


# 2. 新增场地
@router.post("")
def add_court(data: Dict[str, Any]):
    required_fields = ["name", "type", "price_per_hour"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"缺少字段: {field}")

    db = get_db()
    cursor = db.cursor()
    try:
        sql = """
            INSERT INTO courts (name, type, price_per_hour, status, location, remark)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            (
                data["name"],
                data["type"],
                float(data.get("price_per_hour", 0) or 0),
                "可用",  # 新增默认可用
                data.get("location"),
                data.get("remark"),
            ),
        )
        db.commit()
        return {"id": cursor.lastrowid}
    finally:
        cursor.close()
        db.close()


# 3. 更新场地状态（可用 / 维护 / 停用）
@router.put("/{court_id}/status")
def update_court_status(court_id: int, data: Dict[str, Any]):
    new_status = data.get("status")
    if new_status not in ("可用", "维护", "停用"):
        raise HTTPException(status_code=400, detail="非法的状态值")

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM courts WHERE id=%s", (court_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="场地不存在")

        cursor.execute(
            "UPDATE courts SET status=%s WHERE id=%s",
            (new_status, court_id),
        )
        db.commit()
        return {"message": "状态已更新"}
    finally:
        cursor.close()
        db.close()


# 4. 编辑场地（名称 / 类型 / 单价 / 位置 / 备注）
@router.put("/{court_id}")
def update_court(court_id: int, data: Dict[str, Any]):
    """
    简单做法：前端编辑时把完整表单发过来，这里整行更新。
    """
    db = get_db()
    cursor = db.cursor()
    try:
        # 先确认是否存在
        cursor.execute("SELECT id FROM courts WHERE id=%s", (court_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="场地不存在")

        sql = """
            UPDATE courts
            SET name=%s,
                type=%s,
                price_per_hour=%s,
                location=%s,
                remark=%s
            WHERE id=%s
        """
        cursor.execute(
            sql,
            (
                data.get("name"),
                data.get("type"),
                float(data.get("price_per_hour", 0) or 0),
                data.get("location"),
                data.get("remark"),
                court_id,
            ),
        )
        db.commit()
        return {"message": "场地信息已更新"}
    finally:
        cursor.close()
        db.close()


# 5. 删除场地（带预约约束）
@router.delete("/{court_id}")
def delete_court(court_id: int):
    """
    删除场地前检查是否存在未完成的预约：
    只要有不是 已完成/已取消 的预约，就不允许删除。
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # 1. 先检查是否有未完成的预约
        # 这里假设 court_reservations.status 使用英文编码：
        #  FINISHED / CANCELLED / RESERVED 等
        sql_check = """
            SELECT COUNT(*) AS cnt
            FROM court_reservations
            WHERE court_id = %s
              AND status NOT IN ('FINISHED', 'CANCELLED')
        """
        cursor.execute(sql_check, (court_id,))
        row = cursor.fetchone() or {"cnt": 0}
        active_count = row["cnt"] or 0

        if active_count > 0:
            raise HTTPException(
                status_code=400,
                detail="该场地存在未完成的预约，无法删除，请先取消或结束相关预约。",
            )

        # 2. 没有未完成预约，执行删除
        cursor.execute("DELETE FROM courts WHERE id = %s", (court_id,))
        db.commit()
        return {"message": "删除成功"}
    finally:
        cursor.close()
        db.close()
