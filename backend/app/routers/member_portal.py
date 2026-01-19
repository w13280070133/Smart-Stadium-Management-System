# app/routers/member_portal.py
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from .member_auth import get_current_member
from ..database import get_db
from ..services.member_config import load_member_config, get_level_display
from ..security import verify_password, get_password_hash

router = APIRouter(prefix="/member", tags=["Member Portal"])


# ------- 请求模型 -------
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# ------- 工具函数 -------

def _to_datetime_str(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value) if value is not None else ""


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _status_to_label(raw_status: Any) -> str:
    """
    把数据库里的英文/数字状态，转换成会员端看的中文文案。
    尽量兼容：字符串/数字/布尔。
    """
    if raw_status is None:
        return "——"

    s = str(raw_status).strip().lower()

    mapping = {
        "pending": "待支付",
        "paid": "已支付",
        "completed": "已完成",
        "done": "已完成",
        "reserved": "已预约",
        "using": "使用中",
        "cancel": "已取消",
        "cancelled": "已取消",
        "canceled": "已取消",
        "refunded": "已退款",
        "refund": "已退款",
        "success": "已完成",
    }
    return mapping.get(s, str(raw_status))


# ------- 会员基本信息 -------

@router.get("/profile")
def get_member_profile(
    current_member: Dict[str, Any] = Depends(get_current_member),
) -> Dict[str, Any]:
    """
    会员个人资料（会员端首页顶部、账号设置用）
    """
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        member_id = current_member["id"]
        cursor.execute("SELECT * FROM members WHERE id = %s", (member_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="会员不存在")

        status_raw = row.get("status", 1)

        # 尽量宽松地把"正常/启用"识别为已启用
        s = str(status_raw).strip().lower()
        if s in ("1", "true", "enabled", "enable", "normal", "active", "启用", "正常", ""):
            status_text = "已启用"
        else:
            status_text = "已停用"

        balance = _to_float(
            row.get("balance") or
            row.get("amount") or
            row.get("account_balance")
        )

        # 加载会员等级配置并获取等级显示信息
        level_value = row.get("level") or ""
        config = load_member_config(cursor)
        level_detail = get_level_display(level_value, config)

        return {
            "id": row.get("id"),
            "name": row.get("name") or row.get("nickname") or current_member.get("name") or "",
            "mobile": row.get("mobile") or row.get("phone") or current_member.get("mobile") or "",
            "status": status_raw,
            "status_text": status_text,
            "balance": balance,
            "level": level_value,
            "level_name": level_detail.get("name") or "普通会员",
            "level_discount": level_detail.get("discount", 100),
        }
    finally:
        cursor.close()
        conn.close()


# ------- 会员首页概览（卡片统计） -------

@router.get("/overview")
def member_overview(
    current_member: Dict[str, Any] = Depends(get_current_member),
) -> Dict[str, Any]:
    """
    会员首页概览卡片：
    - 历史订单数
    - 已报名课次数（目前培训模块停用，统一返回 0）
    - 本月预约次数
    """
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    member_id = current_member["id"]

    data = {
        "total_orders": 0,
        "total_courses": 0,       # 暂时不启用培训报名，固定为 0
        "month_reservations": 0,
    }

    try:
        # 历史订单总数
        try:
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM orders WHERE member_id = %s",
                (member_id,),
            )
            row = cursor.fetchone()
            if row and row.get("cnt") is not None:
                data["total_orders"] = int(row["cnt"])
        except Exception:
            pass

        # 本月预约次数（自然月）
        try:
            cursor.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM court_reservations
                WHERE member_id = %s
                  AND DATE(reservation_date) >= DATE_FORMAT(CURDATE(), '%%Y-%%m-01')
                """,
                (member_id,),
            )
            row = cursor.fetchone()
            if row and row.get("cnt") is not None:
                data["month_reservations"] = int(row["cnt"])
        except Exception:
            pass

        # 培训相关暂时停用
        data["total_courses"] = 0

        return data
    finally:
        cursor.close()
        conn.close()


# ------- 会员“我的订单”列表（首页 & 我的订单页会用） -------

@router.get("/orders")
def member_orders(
    current_member: Dict[str, Any] = Depends(get_current_member),
    limit: Optional[int] = Query(
        None,
        ge=1,
        description="限制返回前几条，空则返回全部",
    ),
) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    member_id = current_member["id"]

    try:
        sql = """
            SELECT *
            FROM orders
            WHERE member_id = %s
            ORDER BY id DESC
        """
        params: List[Any] = [member_id]
        if limit:
            sql += " LIMIT %s"
            params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        result: List[Dict[str, Any]] = []
        for r in rows:
            created_at = r.get("created_at") or r.get("create_time")

            # 统一金额字段：优先使用 pay_amount（实付金额），如果没有则使用 total_amount
            amount = _to_float(r.get("pay_amount") or r.get("amount") or r.get("total_amount"))

            # 业务类型文案兼容（统一使用 order_type 字段）
            order_type = r.get("order_type") or r.get("business_type") or ""
            ot = str(order_type).lower()
            
            # 统一类型命名
            if ot == "product":
                order_type = "goods"
                business_type_text = "商品消费"
            elif ot == "goods":
                order_type = "goods"
                business_type_text = "商品消费"
            elif ot == "court":
                order_type = "court"
                business_type_text = "场地预约"
            elif ot == "training":
                order_type = "training"
                business_type_text = "培训报名"
            elif ot == "course":
                order_type = "training"
                business_type_text = "培训报名"
            elif ot == "refund":
                order_type = "refund"
                business_type_text = "退款"
            else:
                business_type_text = r.get("business_type_text") or str(order_type or "")

            result.append(
                {
                    "id": r.get("id"),
                    "order_no": r.get("order_no") or r.get("order_sn") or "",
                    "order_type": order_type,  # 统一使用 order_type
                    "business_type": order_type,  # 兼容旧字段
                    "business_type_text": business_type_text,
                    "type": business_type_text,  # 前端显示用
                    "amount": amount,
                    "status": r.get("status"),
                    "status_text": r.get("status_text") or _status_to_label(r.get("status")),
                    "created_at": _to_datetime_str(created_at),
                }
            )
        return result
    finally:
        cursor.close()
        conn.close()


# ------- 会员“我的预约”列表 -------

@router.get("/reservations")
def member_reservations(
    current_member: Dict[str, Any] = Depends(get_current_member),
) -> List[Dict[str, Any]]:
    """
    我的场地预约列表（会员端）

    注意：
    - 这里 **不再声明任何查询参数**，避免空字符串/非法值触发 422。
    - 如需筛选，在前端本地做过滤（你现在的 Reservations.vue 就是这样的）。
    """
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    member_id = current_member["id"]

    try:
        sql = """
            SELECT r.*, c.name AS court_name
            FROM court_reservations AS r
            JOIN courts AS c ON r.court_id = c.id
            WHERE r.member_id = %s
            ORDER BY r.id DESC
        """
        cursor.execute(sql, (member_id,))
        rows = cursor.fetchall()

        result: List[Dict[str, Any]] = []
        for r in rows:
            reservation_date = (
                r.get("reservation_date")
                or r.get("date")
                or r.get("reserve_date")
            )

            created_at = (
                r.get("created_at")
                or r.get("create_time")
            )

            amount = _to_float(
                r.get("total_amount")
                or r.get("total_price")
                or r.get("amount")
                or r.get("price")
            )

            raw_status = r.get("status") or r.get("reservation_status")
            display_status = _status_to_label(raw_status)

            result.append(
                {
                    "id": r.get("id"),
                    "court_name": r.get("court_name") or "",
                    "date": _to_datetime_str(reservation_date),
                    "start_time": r.get("start_time"),
                    "end_time": r.get("end_time"),
                    "amount": amount,
                    "status": display_status,
                    "raw_status": raw_status,
                    "remark": r.get("remark") or "",
                    "created_at": _to_datetime_str(created_at),
                }
            )

        return result
    finally:
        cursor.close()
        conn.close()


# ------- 会员端创建预约 -------

@router.post("/reservations")
def create_member_reservation(
    data: Dict[str, Any],
    current_member: Dict[str, Any] = Depends(get_current_member),
) -> Dict[str, Any]:
    """
    会员端创建场地预约
    
    请求体：
    - court_id: 场地ID
    - date: 预约日期 (YYYY-MM-DD)
    - start_time: 开始时间 (HH:MM)
    - end_time: 结束时间 (HH:MM)
    - remark: 备注（可选）
    """
    from ..services.orders import create_court_order
    from ..services.discounts import get_member_discount
    from ..services.cards import get_best_card
    from datetime import datetime
    
    # 验证必填字段
    required = ["court_id", "date", "start_time", "end_time"]
    for field in required:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"缺少字段: {field}")
    
    court_id = int(data["court_id"])
    date_str = str(data["date"])
    start_time = str(data["start_time"])
    end_time = str(data["end_time"])
    
    # 组合完整的日期时间
    try:
        start_dt = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="日期时间格式不正确")
    
    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")
    
    if end_dt <= datetime.now():
        raise HTTPException(status_code=400, detail="不能预约已经结束的时间段")
    
    member_id = current_member["id"]
    member_name = current_member.get("name") or ""
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor2 = conn.cursor()
    
    try:
        conn.start_transaction()
        
        # 1. 获取场地价格
        cursor.execute(
            "SELECT id, name, price_per_hour FROM courts WHERE id = %s",
            (court_id,)
        )
        court = cursor.fetchone()
        if not court:
            raise HTTPException(status_code=404, detail="场地不存在")
        
        price_per_hour = float(court.get("price_per_hour") or 0)
        if price_per_hour <= 0:
            raise HTTPException(status_code=400, detail="场地价格未配置")
        
        court_name = court.get("name") or "场地"
        
        # 2. 计算时长和金额
        duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
        if duration_hours <= 0:
            raise HTTPException(status_code=400, detail="预约时长必须大于0")
        
        total_amount = round(price_per_hour * duration_hours, 2)
        
        # 3. 应用会员折扣
        card, _ = get_best_card(cursor, member_id)
        if card and card.get("discount") is not None:
            card_discount = float(card.get("discount") or 100)
            if card_discount < 100:
                total_amount = round(total_amount * card_discount / 100.0, 2)
        else:
            discount = get_member_discount(cursor, member_id)
            if discount < 100:
                total_amount = round(total_amount * discount / 100.0, 2)
        
        # 4. 检查时间段冲突
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM court_reservations
            WHERE court_id = %s
              AND status <> '已取消'
              AND NOT (end_time <= %s OR start_time >= %s)
            """,
            (court_id, start_dt, end_dt)
        )
        row = cursor.fetchone()
        if (row.get("cnt") or 0) > 0:
            raise HTTPException(status_code=400, detail="该时间段已被预约，请选择其他时间")
        
        # 5. 检查会员余额
        cursor.execute(
            "SELECT balance, status FROM members WHERE id = %s FOR UPDATE",
            (member_id,)
        )
        member = cursor.fetchone()
        if not member:
            raise HTTPException(status_code=404, detail="会员不存在")
        
        if str(member.get("status") or "正常") != "正常":
            raise HTTPException(status_code=400, detail="会员状态异常，无法预约")
        
        balance = float(member.get("balance") or 0)
        if balance < total_amount:
            raise HTTPException(
                status_code=400,
                detail=f"余额不足，当前余额：{balance:.2f}元，需要：{total_amount:.2f}元"
            )
        
        # 6. 创建预约记录
        cursor2.execute(
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
                total_amount,
                "已预约",
                data.get("remark"),
                "会员端",
            )
        )
        reservation_id = cursor2.lastrowid
        
        # 7. 扣除余额
        new_balance = round(balance - total_amount, 2)
        cursor2.execute(
            "UPDATE members SET balance = %s WHERE id = %s",
            (new_balance, member_id)
        )
        
        # 8. 记录流水
        cursor2.execute(
            """
            INSERT INTO member_transactions (member_id, type, amount, balance_after, remark)
            VALUES (%s, '消费', %s, %s, %s)
            """,
            (
                member_id,
                -total_amount,
                new_balance,
                f"场地预约：{court_name} {start_dt.strftime('%Y-%m-%d %H:%M')}"
            )
        )
        
        # 9. 生成订单
        order_info = create_court_order(
            cursor=cursor,
            related_id=reservation_id,
            member_id=member_id,
            member_name=member_name,
            total_amount=total_amount,
            pay_method="会员余额",
            status="paid",
            remark=data.get("remark"),
            source="会员端",
        )
        
        conn.commit()
        
        # 10. 发送通知
        try:
            from ..services.notifications import create_notification
            time_range = f"{start_dt.strftime('%Y-%m-%d %H:%M')} ~ {end_dt.strftime('%H:%M')}"
            content = f"{court_name} {time_range} 预约成功，金额 ¥{total_amount:.2f}"
            create_notification(
                member_id=member_id,
                title="预约成功",
                content=content,
                level="info"
            )
        except Exception:
            pass
        
        return {
            "id": reservation_id,
            "order": order_info,
            "message": "预约成功"
        }
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"预约失败：{str(e)}")
    finally:
        cursor.close()
        cursor2.close()
        conn.close()


@router.post("/reservations/{reservation_id}/cancel")
def cancel_member_reservation(
    reservation_id: int,
    data: Dict[str, Any],
    current_member: Dict[str, Any] = Depends(get_current_member),
) -> Dict[str, Any]:
    """
    会员端取消预约并退款
    
    请求体：
    - remark: 取消原因（可选）
    """
    from ..services.orders import create_refund_order
    
    member_id = current_member["id"]
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor2 = conn.cursor()
    
    try:
        conn.start_transaction()
        
        # 1. 查询预约记录
        cursor.execute(
            """
            SELECT r.*, c.name AS court_name
            FROM court_reservations r
            LEFT JOIN courts c ON r.court_id = c.id
            WHERE r.id = %s AND r.member_id = %s
            """,
            (reservation_id, member_id)
        )
        reservation = cursor.fetchone()
        
        if not reservation:
            raise HTTPException(status_code=404, detail="预约记录不存在")
        
        if reservation.get("status") == "已取消":
            raise HTTPException(status_code=400, detail="该预约已取消")
        
        # 2. 查找关联订单
        cursor.execute(
            """
            SELECT * FROM orders
            WHERE related_id = %s AND order_type = 'court'
            ORDER BY id DESC LIMIT 1
            """,
            (reservation_id,)
        )
        order = cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="未找到关联订单")
        
        status_raw = (order.get("status") or "").lower()
        if status_raw in {"refunded", "partial_refund", "cancelled", "canceled"}:
            raise HTTPException(status_code=400, detail="该订单已退款")
        
        # 3. 计算退款金额
        refund_amount = float(order.get("pay_amount") or order.get("total_amount") or 0)
        if refund_amount <= 0:
            raise HTTPException(status_code=400, detail="退款金额异常")
        
        # 4. 生成退款订单
        refund_info = create_refund_order(
            cursor=cursor,
            original_order_id=order["id"],
            original_order_no=order.get("order_no"),
            member_id=member_id,
            member_name=current_member.get("name"),
            amount=refund_amount,
            order_type="court",
            remark=data.get("remark") or "会员端取消预约",
        )
        
        # 5. 更新原订单状态
        cursor2.execute(
            "UPDATE orders SET status = %s WHERE id = %s",
            ("refunded", order["id"])
        )
        
        # 6. 更新预约状态
        cursor2.execute(
            "UPDATE court_reservations SET status = %s WHERE id = %s",
            ("已取消", reservation_id)
        )
        
        # 7. 退回余额
        cursor.execute(
            "SELECT balance FROM members WHERE id = %s FOR UPDATE",
            (member_id,)
        )
        member = cursor.fetchone()
        if member:
            balance = float(member.get("balance") or 0)
            new_balance = balance + refund_amount
            cursor2.execute(
                "UPDATE members SET balance = %s WHERE id = %s",
                (new_balance, member_id)
            )
            
            # 8. 记录流水
            cursor2.execute(
                """
                INSERT INTO member_transactions (member_id, type, amount, balance_after, remark)
                VALUES (%s, '退款', %s, %s, %s)
                """,
                (
                    member_id,
                    refund_amount,
                    new_balance,
                    data.get("remark") or f"取消预约退款：{reservation_id}"
                )
            )
        
        conn.commit()
        
        # 9. 发送通知
        try:
            from ..services.notifications import create_notification
            court_name = reservation.get("court_name") or "场地"
            start_time = reservation.get("start_time")
            if isinstance(start_time, datetime):
                time_str = start_time.strftime("%Y-%m-%d %H:%M")
            else:
                time_str = str(start_time) if start_time else ""
            
            content = f"{court_name} {time_str} 预约已取消，费用 ¥{refund_amount:.2f} 已退回余额"
            create_notification(
                member_id=member_id,
                title="预约取消通知",
                content=content,
                level="warning"
            )
        except Exception:
            pass
        
        return {
            "message": "预约已取消并退款",
            "refund_order": refund_info
        }
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"取消失败：{str(e)}")
    finally:
        cursor.close()
        cursor2.close()
        conn.close()


# ------- 会员端消息通知列表 -------

@router.get("/notifications")
def member_notifications(
    current_member: Dict[str, Any] = Depends(get_current_member),
    is_read: Optional[int] = Query(
        None,
        description="0=未读, 1=已读, 其他/空=全部",
    ),
) -> List[Dict[str, Any]]:
    """
    会员端消息通知列表：
    GET /api/member/notifications?is_read=0/1
    """
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    member_id = current_member["id"]

    try:
        sql = """
            SELECT id, title, content, level, is_read, created_at
            FROM notifications
            WHERE member_id = %s
        """
        params: List[Any] = [member_id]

        if is_read in (0, 1):
            sql += " AND is_read = %s"
            params.append(is_read)

        sql += " ORDER BY id DESC LIMIT 100"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        result: List[Dict[str, Any]] = []
        for r in rows:
            result.append(
                {
                    "id": r.get("id"),
                    "title": r.get("title") or "",
                    "content": r.get("content") or "",
                    "level": r.get("level") or "info",
                    "is_read": int(r.get("is_read") or 0),
                    "created_at": _to_datetime_str(r.get("created_at")),
                }
            )
        return result
    finally:
        cursor.close()
        conn.close()


@router.put("/notifications/{notif_id}/read")
def member_set_notification_read(
    notif_id: int,
    current_member: Dict[str, Any] = Depends(get_current_member),
) -> Dict[str, Any]:
    """
    会员端：将一条通知标记为已读
    PUT /api/member/notifications/{id}/read
    """
    conn = get_db()
    cursor = conn.cursor()
    member_id = current_member["id"]

    try:
        cursor.execute(
            """
            UPDATE notifications
            SET is_read = 1
            WHERE id = %s AND member_id = %s
            """,
            (notif_id, member_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="通知不存在")
        return {"success": True}
    finally:
        cursor.close()
        conn.close()


# ------- 会员更新个人资料 -------
@router.put("/profile")
def update_member_profile(
    data: Dict[str, Any],
    current_member: Dict[str, Any] = Depends(get_current_member),
) -> Dict[str, Any]:
    """
    会员更新个人资料
    
    可更新字段：
    - name: 姓名
    - phone: 手机号
    """
    member_id = current_member["id"]
    
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    
    if not name:
        raise HTTPException(status_code=400, detail="姓名不能为空")
    
    if not phone:
        raise HTTPException(status_code=400, detail="手机号不能为空")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 检查手机号是否被其他会员使用
        cursor.execute(
            """
            SELECT id FROM members
            WHERE phone = %s AND id != %s
            LIMIT 1
            """,
            (phone, member_id)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="该手机号已被其他会员使用")
        
        # 更新资料
        cursor.execute(
            """
            UPDATE members
            SET name = %s, phone = %s, mobile = %s
            WHERE id = %s
            """,
            (name, phone, phone, member_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="会员不存在")
        
        return {"success": True, "message": "资料更新成功"}
    finally:
        cursor.close()
        conn.close()


# ------- 会员修改密码 -------
@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_member: Dict[str, Any] = Depends(get_current_member),
) -> Dict[str, Any]:
    """
    会员修改登录密码
    
    需要提供：
    - old_password: 当前密码
    - new_password: 新密码（至少6位）
    """
    old_password = (data.old_password or "").strip()
    new_password = (data.new_password or "").strip()
    
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="密码不能为空")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度至少6位")
    
    member_id = current_member["id"]
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. 查询会员信息，获取当前密码哈希
        cursor.execute(
            """
            SELECT id, login_password_hash, status
            FROM members
            WHERE id = %s
            """,
            (member_id,),
        )
        member = cursor.fetchone()
        
        if not member:
            raise HTTPException(status_code=404, detail="会员不存在")
        
        if member.get("status") != "正常":
            raise HTTPException(status_code=403, detail="会员状态异常，无法修改密码")
        
        login_password_hash = member.get("login_password_hash")
        if not login_password_hash:
            raise HTTPException(status_code=400, detail="该会员尚未设置登录密码，请联系前台设置")
        
        # 2. 验证旧密码
        if not verify_password(old_password, login_password_hash):
            raise HTTPException(status_code=400, detail="当前密码错误")
        
        # 3. 生成新密码哈希
        new_password_hash = get_password_hash(new_password)
        
        # 4. 更新密码
        cursor.execute(
            """
            UPDATE members
            SET login_password_hash = %s
            WHERE id = %s
            """,
            (new_password_hash, member_id),
        )
        conn.commit()
        
        return {"success": True, "message": "密码修改成功"}
    finally:
        cursor.close()
        conn.close()
