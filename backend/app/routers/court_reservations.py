from datetime import datetime
from typing import Optional, List, Any, Dict

from fastapi import APIRouter, HTTPException, Depends

from ..database import get_db
from ..deps import require_action
from ..services.orders import create_court_order, create_refund_order
from ..services.cards import get_best_card, consume_card_times
from ..services.discounts import get_member_discount

router = APIRouter(prefix="/court-reservations", tags=["Court Reservations"])


def _to_str(dt: Any) -> Any:
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt


def _parse_dt(val: str, field_name: str) -> datetime:
    """解析 '2025-11-15 09:00:00' 或 ISO 形式"""
    if not val:
        raise HTTPException(status_code=400, detail=f"缺少字段: {field_name}")
    try:
        return datetime.fromisoformat(val.replace(" ", "T"))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} 格式不正确，需为 YYYY-MM-DD HH:MM:SS",
        )


# 场地表结构缓存（避免频繁执行 SHOW COLUMNS）
_courts_columns_cache: set = None
_courts_columns_cache_ts: float = 0
COLUMNS_CACHE_TTL = 300  # 缓存时间 5 分钟


def _get_courts_columns(cursor) -> set:
    """获取 courts 表的列名（带缓存）"""
    global _courts_columns_cache, _courts_columns_cache_ts
    import time
    now = time.time()
    
    if _courts_columns_cache is not None and now - _courts_columns_cache_ts < COLUMNS_CACHE_TTL:
        return _courts_columns_cache
    
    cursor.execute("SHOW COLUMNS FROM courts")
    rows = cursor.fetchall()
    if rows and isinstance(rows[0], dict):
        _courts_columns_cache = {r["Field"] for r in rows}
    else:
        _courts_columns_cache = {r[0] for r in rows}
    _courts_columns_cache_ts = now
    return _courts_columns_cache


def _get_court_price(cursor, court_id: int) -> float:
    """获取场地价格，优先 price_per_hour，否则 price（使用缓存优化）"""
    cols = _get_courts_columns(cursor)
    has_price_per_hour = "price_per_hour" in cols
    has_price = "price" in cols
    
    if has_price_per_hour and has_price:
        cursor.execute("SELECT price_per_hour, price FROM courts WHERE id = %s", (court_id,))
    elif has_price_per_hour:
        cursor.execute("SELECT price_per_hour FROM courts WHERE id = %s", (court_id,))
    elif has_price:
        cursor.execute("SELECT price FROM courts WHERE id = %s", (court_id,))
    else:
        raise HTTPException(
            status_code=500,
            detail="courts 未找到价格字段，price_per_hour / price 至少需存在一个",
        )

    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="场地不存在")

    if isinstance(row, dict):
        raw_price = row.get("price_per_hour")
        if raw_price is None:
            raw_price = row.get("price")
    else:
        raw_price = row[0] if len(row) > 0 else 0

    try:
        return float(raw_price or 0)
    except (TypeError, ValueError):
        return 0.0


def _calc_amount(cursor, court_id: int, start_dt: datetime, end_dt: datetime, current_amount: float) -> float:
    """金额未传时，按价格 * 时长自动计算"""
    if current_amount and current_amount > 0:
        return float(current_amount)

    duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
    if duration_hours <= 0:
        raise HTTPException(status_code=400, detail="预约时长必须大于 0")

    price_per_hour = _get_court_price(cursor, court_id)
    if price_per_hour <= 0:
        raise HTTPException(status_code=400, detail="场地价格未配置，请先设置 price_per_hour 或 price")

    amount = round(price_per_hour * duration_hours, 2)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="计算金额为 0，请检查场地价格或预约时长")
    return amount


def _apply_member_pricing(cursor, amount: float, member_id: int | None) -> float:
    """应用会员折扣：会员卡折扣或等级折扣"""
    if not member_id or amount <= 0:
        return amount
    try:
        # 优先使用会员卡折扣
        card, _ = get_best_card(cursor, member_id)
        if card and card.get("discount") is not None:
            try:
                card_discount = float(card.get("discount") or 100)
            except Exception:
                card_discount = 100.0
            if card_discount < 100:
                amount = round(amount * card_discount / 100.0, 2)
        else:
            # 没有会员卡折扣，使用会员等级折扣
            discount = get_member_discount(cursor, member_id)
            if discount < 100:
                amount = round(amount * discount / 100.0, 2)
    except Exception:
        pass
    return amount


@router.get("")
def list_reservations(court_id: Optional[int] = None, member_id: Optional[int] = None):
    """预约列表"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor_orders = db.cursor(dictionary=True)
    try:
        sql = """
        SELECT
          r.id,
          r.court_id,
          c.name AS court_name,
          r.member_id,
          m.name AS member_name,
          r.start_time,
          r.end_time,
          r.status,
          r.total_amount,
          r.source,
          r.remark,
          r.created_at
        FROM court_reservations r
        JOIN courts c ON r.court_id = c.id
        LEFT JOIN members m ON r.member_id = m.id
        WHERE 1=1
        """
        params: List = []
        if court_id is not None:
            sql += " AND r.court_id = %s"
            params.append(court_id)
        if member_id is not None:
            sql += " AND r.member_id = %s"
            params.append(member_id)
        sql += " ORDER BY r.id DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        reservation_ids = [r.get("id") for r in rows if r.get("id") is not None]
        order_map: Dict[int, Dict[str, Any]] = {}
        if reservation_ids:
            placeholders = ", ".join(["%s"] * len(reservation_ids))
            cursor_orders.execute(
                f"""
                SELECT *
                FROM orders
                WHERE related_id IN ({placeholders})
                  AND LOWER(order_type) = 'court'
                ORDER BY id DESC
                """,
                reservation_ids,
            )
            order_rows = cursor_orders.fetchall()
            for order in order_rows:
                rid = order.get("related_id")
                if rid is None or rid in order_map:
                    continue
                order_map[int(rid)] = order

        for r in rows:
            r["start_time"] = _to_str(r.get("start_time"))
            r["end_time"] = _to_str(r.get("end_time"))
            r["created_at"] = _to_str(r.get("created_at"))
            order = order_map.get(r.get("id"))
            if order:
                r["order_id"] = order.get("id")
                r["order_no"] = order.get("order_no")
                r["order_status"] = order.get("status") or order.get("order_status")
                r["order_pay_amount"] = order.get("pay_amount")
                r["order_pay_method"] = order.get("pay_method")
        return rows
    finally:
        cursor_orders.close()
        cursor.close()
        db.close()


@router.post("")
def create_reservation(
    data: Dict[str, Any],
    _current_user=Depends(require_action("reservation.create")),
):
    """
    后台创建场地预约：校验时间段自动计价，创建预约并生成已支付的订单(order_type=court，source=后台)
    """
    required_fields = ["court_id", "start_time", "end_time"]
    for f in required_fields:
        if f not in data:
            raise HTTPException(status_code=400, detail=f"缺少字段: {f}")

    court_id = int(data["court_id"])

    raw_member = data.get("member_id")
    if raw_member in (None, "", 0, "0"):
        member_id = None
    else:
        try:
            member_id = int(raw_member)
        except Exception:
            raise HTTPException(status_code=400, detail="会员ID格式不正确")

    start_dt = _parse_dt(str(data["start_time"]), "开始时间")
    end_dt = _parse_dt(str(data["end_time"]), "结束时间")

    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")
    if end_dt <= datetime.now():
        raise HTTPException(status_code=400, detail="不能预约已经结束的时间段，请选择当前时间之后的时段")

    amount_val = data.get("total_amount", data.get("amount", 0))
    try:
        amount_val = float(amount_val or 0)
    except (TypeError, ValueError):
        amount_val = 0.0

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        db.start_transaction()
        amount_val = _calc_amount(cursor, court_id, start_dt, end_dt, amount_val)
        amount_val = _apply_member_pricing(cursor, amount_val, member_id)

        # 【核心算法】时间段冲突检测
        # 检测逻辑：两个时间段冲突的条件是"不满足完全不重叠"
        # 完全不重叠的情况只有两种：
        #   1. 已有预约的结束时间 <= 新预约的开始时间（已有预约在前）
        #   2. 已有预约的开始时间 >= 新预约的结束时间（已有预约在后）
        # 因此，冲突的条件就是：NOT (情况1 OR 情况2)
        # 
        # 示例：
        # 假设新预约：10:00-12:00
        # - 不冲突：8:00-10:00（结束时间=开始时间，边界不冲突）
        # - 不冲突：12:00-14:00（开始时间=结束时间，边界不冲突）
        # - 冲突：9:00-11:00（部分重叠）
        # - 冲突：10:30-11:30（完全包含）
        # - 冲突：9:00-13:00（完全包含新预约）
        #
        # 注意：只检查非"已取消"状态的预约，已取消的预约不占用时间段
        check_sql = """
          SELECT COUNT(*) AS cnt
          FROM court_reservations
          WHERE court_id = %s
            AND status <> '已取消'
            AND NOT (end_time <= %s OR start_time >= %s)
        """
        cursor.execute(check_sql, (court_id, start_dt, end_dt))
        row = cursor.fetchone() or {"cnt": 0}
        if (row.get("cnt") or 0) > 0:
            raise HTTPException(status_code=400, detail="当前时间段已被预约，请选择其它时间")

        cursor.execute(
            """
            INSERT INTO court_reservations
                (court_id, member_id, start_time, end_time, total_amount, status, remark, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                court_id,
                member_id,
                start_dt,
                end_dt,
                amount_val,
                "已预约",
                data.get("remark"),
                data.get("source", "后台"),
            ),
        )
        reservation_id = cursor.lastrowid

        member_name = data.get("member_name")
        if not member_name and member_id:
            cursor.execute("SELECT name FROM members WHERE id = %s", (member_id,))
            mrow = cursor.fetchone()
            if mrow:
                member_name = mrow.get("name") if isinstance(mrow, dict) else mrow[0]

        # 获取场地名称用于通知
        cursor.execute("SELECT name FROM courts WHERE id = %s", (court_id,))
        court_row = cursor.fetchone()
        court_name = court_row.get("name") if court_row else "场地"

        # 扣除会员余额（只要有会员就扣款）
        pay_method = data.get("pay_method", "会员余额")  # 默认会员余额
        if member_id:
            cursor.execute(
                "SELECT balance, status FROM members WHERE id = %s FOR UPDATE",
                (member_id,)
            )
            member_row = cursor.fetchone()
            if not member_row:
                raise HTTPException(status_code=404, detail="会员不存在")
            
            member_status = member_row.get("status") if isinstance(member_row, dict) else member_row[1]
            if str(member_status or "正常") != "正常":
                raise HTTPException(status_code=400, detail="会员状态异常，无法使用余额支付")
            
            balance = float(member_row.get("balance") if isinstance(member_row, dict) else member_row[0] or 0)
            
            if amount_val > 0:
                if balance < amount_val:
                    raise HTTPException(status_code=400, detail=f"会员余额不足，当前余额：{balance:.2f}元，需要：{amount_val:.2f}元")
                
                new_balance = round(balance - amount_val, 2)
                cursor.execute(
                    "UPDATE members SET balance = %s WHERE id = %s",
                    (new_balance, member_id)
                )
                
                # 记录流水
                cursor.execute(
                    """
                    INSERT INTO member_transactions (member_id, type, amount, balance_after, remark)
                    VALUES (%s, '消费', %s, %s, %s)
                    """,
                    (member_id, -amount_val, new_balance, f"场地预约：{court_name} {start_dt.strftime('%Y-%m-%d %H:%M')}")
                )

        order_info = create_court_order(
            cursor=cursor,
            related_id=reservation_id,
            member_id=member_id,
            member_name=member_name,
            total_amount=amount_val,
            pay_method=data.get("pay_method"),
            status="paid",
            remark=data.get("remark"),
            source=data.get("source", "后台"),
        )

        db.commit()
        result = {"id": reservation_id, "order": order_info}
    finally:
        cursor.close()
        db.close()

    # 发送通知给会员（如果是会员预约）
    if member_id:
        try:
            from ..services.notifications import create_notification

            time_range = f"{start_dt.strftime('%Y-%m-%d %H:%M')} ~ {end_dt.strftime('%H:%M')}"
            content = f"{court_name} {time_range} 预约成功（后台创建），金额 ¥{amount_val:.2f}"
            create_notification(member_id=member_id, title="预约成功", content=content, level="info")
        except Exception:
            pass

    return result


@router.put("/{reservation_id}/status")
def update_reservation_status(
    reservation_id: int,
    data: dict,
    _current_user=Depends(require_action("reservation.edit")),
):
    """更新预约状态：已预约 / 已取消 / 进行中 / 已完成"""
    new_status = data.get("status")
    allowed = ("已预约", "已取消", "进行中", "已完成")
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail="不合法的预约状态")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor2 = db.cursor()
    try:
        db.start_transaction()
        # 使用 FOR UPDATE 行锁防止并发修改
        # 当多个用户同时修改同一条预约记录时：
        # - 第一个事务获得行锁，可以修改
        # - 后续事务会等待第一个事务提交或回滚
        # - 避免"丢失更新"问题（Lost Update）
        cursor.execute(
            "SELECT status, member_id, remark FROM court_reservations WHERE id = %s FOR UPDATE",
            (reservation_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="预约记录不存在")

        if row["status"] == new_status:
            raise HTTPException(status_code=400, detail=f"当前已是{new_status}状态")

        cursor.execute(
            "UPDATE court_reservations SET status = %s WHERE id = %s",
            (new_status, reservation_id),
        )

        if new_status == "已取消":
            _process_reservation_refund(
                cursor=cursor,
                cursor2=cursor2,
                reservation_id=reservation_id,
                reservation=row,
                remark=data.get("remark"),
                raise_if_missing=False,
            )

        db.commit()
        return {"code": 200, "msg": "状态更新成功", "data": {"id": reservation_id, "status": new_status}}
    finally:
        cursor.close()
        cursor2.close()
        db.close()


@router.delete("/{reservation_id}")
def delete_reservation(
    reservation_id: int,
    _current_user=Depends(require_action("reservation.delete")),
):
    """删除预约"""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM court_reservations WHERE id = %s", (reservation_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="预约记录不存在")
        db.commit()
        return {"message": "deleted"}
    finally:
        cursor.close()
        db.close()


@router.post("/{reservation_id}/refund")
def refund_reservation(
    reservation_id: int,
    data: Dict[str, Any],
    _current_user=Depends(require_action("reservation.refund")),
):
    """取消预约并发起退款"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor2 = db.cursor()
    try:
        db.start_transaction()

        cursor.execute(
            """
            SELECT r.*, c.name AS court_name
            FROM court_reservations r
            LEFT JOIN courts c ON r.court_id = c.id
            WHERE r.id = %s
            """,
            (reservation_id,),
        )
        reservation = cursor.fetchone()
        if not reservation:
            raise HTTPException(status_code=404, detail="预约记录不存在")

        refund_info = _process_reservation_refund(
            cursor=cursor,
            cursor2=cursor2,
            reservation_id=reservation_id,
            reservation=reservation,
            remark=data.get("remark"),
            raise_if_missing=True,
        )

        cursor.execute("UPDATE court_reservations SET status = %s WHERE id = %s", ("已取消", reservation_id))

        db.commit()
        result = {"message": "预约已取消并退款", "refund_order": refund_info}
    except HTTPException:
        db.rollback()
        raise
    finally:
        cursor.close()
        cursor2.close()
        db.close()

    # 发送通知给会员（如果是会员预约）
    try:
        member_id = reservation.get("member_id")
        if member_id:
            from ..services.notifications import create_notification
            from datetime import datetime

            start_time = reservation.get("start_time")
            if isinstance(start_time, datetime):
                start_dt = start_time
            elif isinstance(start_time, str):
                try:
                    start_dt = datetime.fromisoformat(start_time.replace(" ", "T"))
                except Exception:
                    start_dt = None
            else:
                start_dt = None

            content_time = start_dt.strftime("%Y-%m-%d %H:%M") if start_dt else ""
            court_name = reservation.get("court_name") or "场地"
            content = f"{court_name} {content_time} 预约已取消（后台操作），费用已退回"
            create_notification(member_id=member_id, title="预约取消通知", content=content, level="warning")
    except Exception:
        pass

    return result


def _find_latest_court_order(cursor, reservation_id: int):
    cursor.execute(
        """
        SELECT * FROM orders
        WHERE related_id = %s
        ORDER BY id DESC LIMIT 1
        """,
        (reservation_id,),
    )
    return cursor.fetchone()


def _process_reservation_refund(
    *,
    cursor,
    cursor2,
    reservation_id: int,
    reservation: Dict[str, Any],
    remark: str | None = None,
    order: Dict[str, Any] | None = None,
    raise_if_missing: bool = True,
) -> Dict[str, Any] | None:
    if order is None:
        order = _find_latest_court_order(cursor, reservation_id)
    if not order:
        if raise_if_missing:
            raise HTTPException(status_code=404, detail="未找到关联订单")
        return None

    status_raw = (order.get("status") or order.get("order_status") or "").lower()
    if status_raw in {"refunded", "partial_refund", "cancelled", "canceled"}:
        if raise_if_missing:
            raise HTTPException(status_code=400, detail="该订单已退款或已取消")
        return None

    refund_amount = order.get("pay_amount") or order.get("total_amount")
    if refund_amount is None:
        if raise_if_missing:
            raise HTTPException(status_code=400, detail="原订单金额缺失，无法退款")
        return None
    refund_amount = float(refund_amount)

    member_id = reservation.get("member_id")
    member_name = reservation.get("member_name")

    refund_info = create_refund_order(
        cursor=cursor,
        original_order_id=order["id"],
        original_order_no=order.get("order_no"),
        member_id=member_id,
        member_name=member_name,
        amount=refund_amount,
        order_type="court",
        remark=remark,
    )

    updates = []
    params: List[Any] = []
    if "status" in order:
        updates.append("status = %s")
        params.append("refunded")
    if "order_status" in order:
        updates.append("order_status = %s")
        params.append("refunded")
    if updates:
        sql = f"UPDATE orders SET {', '.join(updates)} WHERE id = %s"
        params.append(order["id"])
        cursor.execute(sql, tuple(params))

    if member_id:
        cursor.execute("SELECT balance FROM members WHERE id = %s FOR UPDATE", (member_id,))
        mrow = cursor.fetchone()
        if mrow:
            balance = float(mrow["balance"] if isinstance(mrow, dict) else mrow[0] or 0)
            new_balance = balance + refund_amount
            cursor2.execute(
                "UPDATE members SET balance = %s WHERE id = %s",
                (new_balance, member_id),
            )
            mt_sql = """
            INSERT INTO member_transactions (member_id, type, amount, balance_after, remark)
            VALUES (%s, '退款', %s, %s, %s)
            """
            mt_remark = remark or f"取消预约退款：{reservation_id}"
            cursor2.execute(mt_sql, (member_id, refund_amount, new_balance, mt_remark))

    return refund_info
