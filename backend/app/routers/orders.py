# app/routers/orders.py
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, Query, HTTPException

from ..database import get_db
from ..deps import require_action
from ..services.orders import create_refund_order
from ..services.audit import write_operation_log
from ..services.notifications import create_admin_notifications

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("")
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_type: str | None = None,
    status: str | None = None,
    member_name: str | None = None,
    related_id: int | None = None,
    keyword: str | None = None,
    date_from: str | None = None,  # 'YYYY-MM-DD'
    date_to: str | None = None,    # 'YYYY-MM-DD'
    _current_user=Depends(require_action("order.view")),
) -> Dict[str, Any]:
    """
    订单列表，支持按类型 / 状态 / 会员名 / 日期过滤 + 分页
    返回 { total, items }
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        where: List[str] = []
        params: List[Any] = []

        if order_type:
            ot = order_type.lower()
            if ot == "goods" or ot == "product":
                where.append("LOWER(o.order_type) IN ('goods', 'product')")
            elif ot == "training" or ot == "course":
                where.append("LOWER(o.order_type) IN ('training', 'course')")
            else:
                where.append("LOWER(o.order_type) = %s")
                params.append(ot)

        if status:
            where.append("o.status = %s")
            params.append(status)

        if member_name:
            where.append("o.member_name LIKE %s")
            params.append(f"%{member_name}%")

        if related_id is not None:
            where.append("o.related_id = %s")
            params.append(related_id)

        if keyword:
            where.append("(o.order_no LIKE %s OR o.remark LIKE %s)")
            kw = f"%{keyword}%"
            params.extend([kw, kw])

        if date_from:
            where.append("o.created_at >= %s")
            params.append(f"{date_from} 00:00:00")

        if date_to:
            where.append("o.created_at <= %s")
            params.append(f"{date_to} 23:59:59")

        where_sql = "WHERE " + " AND ".join(where) if where else ""

        count_sql = f"SELECT COUNT(*) AS cnt FROM orders o {where_sql}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["cnt"]

        data_sql = f"""
        SELECT
          o.id,
          o.order_no,
          o.order_type,
          o.related_id,
          o.member_id,
          o.member_name,
          o.total_amount,
          o.pay_amount,
          o.discount_amount,
          o.currency,
          o.pay_method,
          o.status,
          o.created_at,
          o.paid_at,
          o.remark
        FROM orders o
        {where_sql}
        ORDER BY o.id DESC
        LIMIT %s OFFSET %s
        """
        params2 = list(params)
        params2.extend([page_size, (page - 1) * page_size])
        cursor.execute(data_sql, tuple(params2))
        items = cursor.fetchall()
        # 统一订单类型命名
        normalized = []
        for it in items:
            t = (it.get("order_type") or "").lower()
            # 统一 product → goods
            if t == "product":
                it["order_type"] = "goods"
            # 统一 course → training
            elif t == "course":
                it["order_type"] = "training"
            elif t:
                it["order_type"] = t
            normalized.append(it)

        return {"total": total, "items": normalized}
    finally:
        cursor.close()
        db.close()


@router.post("/{order_id}/refund")
def refund_order(
    order_id: int,
    amount: float | None = None,
    remark: str | None = None,
    current_user=Depends(require_action("order.refund")),
) -> Dict[str, Any]:
    """
    后台指定订单手动退款（生成负向退款订单，原订单标记 refunded）
    - amount 缺省时默认取 pay_amount/total_amount
    - 仅支持未退款的订单
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        raw_status = (order.get("status") or order.get("order_status") or "").lower()
        if raw_status in {"refunded", "partial_refund", "cancelled", "canceled"}:
            raise HTTPException(status_code=400, detail="当前状态不可再退款")

        order_type = (order.get("order_type") or order.get("type") or "").lower() or "unknown"
        pay_amount = order.get("pay_amount")
        total_amount = order.get("total_amount")
        default_amount = pay_amount if pay_amount is not None else total_amount
        if default_amount is None:
            raise HTTPException(status_code=400, detail="原订单金额缺失，无法退款")

        refund_amount = float(amount) if amount is not None else float(default_amount)
        if refund_amount <= 0:
            raise HTTPException(status_code=400, detail="退款金额需大于 0")

        refund_info = create_refund_order(
            cursor=cursor,
            original_order_id=order_id,
            original_order_no=order.get("order_no"),
            member_id=order.get("member_id"),
            member_name=order.get("member_name"),
            amount=refund_amount,
            order_type=order_type,
            remark=remark,
        )

        update_fields = []
        params: List[Any] = []
        if "status" in order:
            update_fields.append("status = %s")
            params.append("refunded")
        if "order_status" in order:
            update_fields.append("order_status = %s")
            params.append("refunded")
        if not update_fields:
            raise HTTPException(status_code=500, detail="orders 缺少 status/order_status 字段，无法更新状态")

        sql = f"UPDATE orders SET {', '.join(update_fields)} WHERE id = %s"
        params.append(order_id)
        cursor.execute(sql, tuple(params))

        try:
            uid = current_user["id"] if isinstance(current_user, dict) else current_user.id
            uname = current_user["username"] if isinstance(current_user, dict) else current_user.username
            write_operation_log(
                user_id=uid,
                username=uname or "",
                action="ORDER_REFUND",
                module="order",
                target_id=order_id,
                target_desc=order.get("order_no"),
                detail={"refund_amount": refund_amount, "remark": remark},
                ip=None,
            )
            try:
                create_admin_notifications(
                    title="订单退款",
                    content=f"订单 {order.get('order_no')} 已手工退款 ¥{refund_amount}",
                    level="warning",
                )
            except Exception:
                pass
        except Exception:
            pass

        db.commit()
        return {"code": 200, "msg": "退款成功", "data": refund_info}
    finally:
        cursor.close()
        db.close()
