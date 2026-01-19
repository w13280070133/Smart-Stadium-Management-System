from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List
from datetime import datetime

from ..database import get_db

router = APIRouter(prefix="/member-transactions", tags=["Member Transactions"])


def _to_str(dt):
    """datetime 转字符串，避免 JSON 序列化问题"""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt


@router.get("")
def list_transactions(
    member_id: Optional[int] = None,
    type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """
    获取会员收支记录列表
    GET /api/member-transactions?member_id=1&type=充值&start_date=2025-01-01&end_date=2025-01-31
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        sql = """
        SELECT
            t.id,
            t.member_id,
            m.name      AS member_name,
            t.type,
            t.amount,
            t.balance_after,
            t.remark,
            t.created_at
        FROM member_transactions t
        JOIN members m ON t.member_id = m.id
        WHERE 1=1
        """
        params: List = []

        if member_id is not None:
            sql += " AND t.member_id = %s"
            params.append(member_id)

        if type:
            sql += " AND t.type = %s"
            params.append(type)

        if start_date:
            sql += " AND t.created_at >= %s"
            params.append(start_date + " 00:00:00")

        if end_date:
            sql += " AND t.created_at <= %s"
            params.append(end_date + " 23:59:59")

        sql += " ORDER BY t.created_at DESC, t.id DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        for r in rows:
            r["created_at"] = _to_str(r["created_at"])

        return rows
    finally:
        cursor.close()
        db.close()


@router.post("", status_code=201)
def create_transaction(data: dict):
    """
    新增一条会员收支记录（充值 / 扣费 / 消费）
    POST /api/member-transactions
    body: { member_id, type, amount, remark? }

    说明：
    - type 只能是：'充值' | '扣费' | '消费'
    - 充值：余额 += amount
    - 扣费/消费：余额 -= amount（余额不足时报错）
    """
    required = ["member_id", "type", "amount"]
    for field in required:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"缺少字段: {field}")

    member_id = data["member_id"]
    tx_type = data["type"]
    amount = data["amount"]
    remark = data.get("remark", "")

    # 统一使用中文枚举
    allowed_types = ("充值", "扣费", "消费")
    if tx_type not in allowed_types:
        raise HTTPException(status_code=400, detail="非法的交易类型")

    try:
        amount = float(amount)
    except Exception:
        raise HTTPException(status_code=400, detail="金额格式不正确")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="金额必须大于 0")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor2 = db.cursor()
    try:
        # 1) 查询当前余额
        cursor.execute("SELECT balance FROM members WHERE id = %s", (member_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="会员不存在")

        old_balance = float(row["balance"] or 0)

        # 2) 计算新余额
        if tx_type == "充值":
            new_balance = old_balance + amount
        else:  # 扣费 / 消费
            if old_balance < amount:
                raise HTTPException(status_code=400, detail="余额不足，无法扣费/消费")
            new_balance = old_balance - amount

        # 3) 更新会员余额
        cursor2.execute(
            "UPDATE members SET balance = %s WHERE id = %s",
            (new_balance, member_id),
        )

        # 4) 写入收支记录
        insert_sql = """
        INSERT INTO member_transactions
            (member_id, type, amount, balance_after, remark)
        VALUES
            (%s,        %s,   %s,     %s,            %s)
        """
        cursor2.execute(
            insert_sql,
            (member_id, tx_type, amount, new_balance, remark),
        )

        db.commit()

        return {
            "id": cursor2.lastrowid,
            "member_id": member_id,
            "type": tx_type,
            "amount": amount,
            "balance_after": new_balance,
        }
    finally:
        cursor.close()
        cursor2.close()
        db.close()
