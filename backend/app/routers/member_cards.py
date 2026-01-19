from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from ..database import get_db

router = APIRouter(prefix="/member-cards", tags=["Member Cards"])


def _to_str(dt: Any) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt) if dt is not None else ""


def _normalize(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row.get("id"),
        "member_id": row.get("member_id"),
        "member_name": row.get("member_name"),
        "member_phone": row.get("member_phone"),
        "card_name": row.get("card_name"),
        "card_type": row.get("card_type"),
        "total_times": row.get("total_times"),
        "remaining_times": row.get("remaining_times"),
        "discount": row.get("discount"),
        "start_date": row.get("start_date"),
        "end_date": row.get("end_date"),
        "status": row.get("status"),
        "remark": row.get("remark"),
        "created_at": _to_str(row.get("created_at")),
        "updated_at": _to_str(row.get("updated_at")),
    }


@router.get("")
def list_cards(member_id: Optional[int] = None):
    """会员卡列表，支持按 member_id 过滤"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        sql = """
        SELECT c.*, m.name AS member_name, m.phone AS member_phone
        FROM member_cards c
        LEFT JOIN members m ON c.member_id = m.id
        WHERE 1=1
        """
        params: List[Any] = []
        if member_id:
            sql += " AND c.member_id = %s"
            params.append(member_id)
        sql += " ORDER BY c.id DESC"
        cursor.execute(sql, params)
        rows = cursor.fetchall() or []
        return [_normalize(r) for r in rows]
    finally:
        cursor.close()
        db.close()


def _validate_dates(start_date: str | None, end_date: str | None):
    if not start_date or not end_date:
        raise HTTPException(status_code=400, detail="请选择有效期")
    try:
        start = datetime.fromisoformat(str(start_date))
        end = datetime.fromisoformat(str(end_date))
    except Exception:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    if end < start:
        raise HTTPException(status_code=400, detail="结束日期必须晚于开始日期")
    return start.date(), end.date()


@router.post("", status_code=201)
def create_card(data: Dict[str, Any]):
    required = ["member_id", "card_name", "card_type", "start_date", "end_date"]
    for f in required:
        if f not in data:
            raise HTTPException(status_code=400, detail=f"缺少字段: {f}")

    member_id = data.get("member_id")
    try:
        member_id = int(member_id)
    except Exception:
        raise HTTPException(status_code=400, detail="会员ID格式错误")

    card_type = (data.get("card_type") or "").strip()
    if card_type not in ("times", "discount", "month", "year"):
        raise HTTPException(status_code=400, detail="卡类型不合法")

    start_date, end_date = _validate_dates(data.get("start_date"), data.get("end_date"))

    total_times = data.get("total_times")
    remaining_times = data.get("remaining_times")
    discount = data.get("discount")

    if card_type == "times":
        try:
            total_times = int(total_times or 0)
            remaining_times = int(remaining_times if remaining_times is not None else total_times)
        except Exception:
            raise HTTPException(status_code=400, detail="次数格式错误")
    else:
        total_times = None
        remaining_times = None

    if card_type == "discount":
        try:
            discount = float(discount or 100)
        except Exception:
            raise HTTPException(status_code=400, detail="折扣格式错误")
    else:
        discount = None

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM members WHERE id = %s", (member_id,))
        member_row = cursor.fetchone()
        if not member_row:
            raise HTTPException(status_code=404, detail="会员不存在")

        cursor.execute(
            """
            INSERT INTO member_cards
              (member_id, card_name, card_type, total_times, remaining_times, discount, start_date, end_date, status, remark, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active', %s, NOW(), NOW())
            """,
            (
                member_id,
                data.get("card_name"),
                card_type,
                total_times,
                remaining_times,
                discount,
                start_date,
                end_date,
                data.get("remark"),
            ),
        )
        card_id = cursor.lastrowid
        db.commit()

        cursor.execute(
            """
            SELECT c.*, m.name AS member_name, m.phone AS member_phone
            FROM member_cards c
            LEFT JOIN members m ON c.member_id = m.id
            WHERE c.id = %s
            """,
            (card_id,),
        )
        row = cursor.fetchone()
        return _normalize(row) if row else {"id": card_id}
    finally:
        cursor.close()
        db.close()


@router.put("/{card_id}")
def update_card(card_id: int, data: Dict[str, Any]):
    """支持更新剩余次数、有效期、折扣、备注等"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM member_cards WHERE id = %s", (card_id,))
        origin = cursor.fetchone()
        if not origin:
            raise HTTPException(status_code=404, detail="会员卡不存在")

        fields: List[str] = []
        params: List[Any] = []

        if "card_name" in data:
            fields.append("card_name = %s")
            params.append(data.get("card_name"))

        if "remaining_times" in data:
            try:
                rt = int(data.get("remaining_times"))
            except Exception:
                raise HTTPException(status_code=400, detail="剩余次数格式错误")
            fields.append("remaining_times = %s")
            params.append(rt)

        if "total_times" in data:
            try:
                tt = int(data.get("total_times"))
            except Exception:
                raise HTTPException(status_code=400, detail="总次数格式错误")
            fields.append("total_times = %s")
            params.append(tt)

        if "discount" in data:
            try:
                dval = float(data.get("discount"))
            except Exception:
                raise HTTPException(status_code=400, detail="折扣格式错误")
            fields.append("discount = %s")
            params.append(dval)

        if data.get("start_date") or data.get("end_date"):
            start_date = data.get("start_date") or origin.get("start_date")
            end_date = data.get("end_date") or origin.get("end_date")
            _validate_dates(start_date, end_date)
            fields.append("start_date = %s")
            fields.append("end_date = %s")
            params.extend([start_date, end_date])

        if "status" in data:
            fields.append("status = %s")
            params.append(data.get("status"))

        if "remark" in data:
            fields.append("remark = %s")
            params.append(data.get("remark"))

        if not fields:
            raise HTTPException(status_code=400, detail="无可更新字段")

        fields.append("updated_at = NOW()")

        sql = f"UPDATE member_cards SET {', '.join(fields)} WHERE id = %s"
        params.append(card_id)
        cursor.execute(sql, tuple(params))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="会员卡不存在")
        db.commit()
        return {"message": "updated"}
    finally:
        cursor.close()
        db.close()


@router.delete("/{card_id}")
def delete_card(card_id: int):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM member_cards WHERE id = %s", (card_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="会员卡不存在")
        db.commit()
        return {"message": "deleted"}
    finally:
        cursor.close()
        db.close()
