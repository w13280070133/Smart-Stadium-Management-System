from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request

from ..database import get_db
from ..deps import get_current_user
from ..services.orders import create_product_order, create_refund_order
from ..services.audit import write_operation_log
from ..services.notifications import create_notification, create_admin_notifications
from ..services.discounts import get_member_discount
from ..services.cards import get_best_card, consume_card_times

router = APIRouter(prefix="/product-sales", tags=["Product Sales"])


def _to_str(dt):
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt


@router.get("")
def list_sales():
    """获取商品售卖记录列表"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        sql = """
        SELECT
            s.id,
            s.product_id,
            p.name AS product_name,
            s.member_id,
            m.name AS member_name,
            s.quantity,
            s.unit_price,
            s.total_price,
            s.pay_method,
            s.remark,
            s.order_id,
            s.created_at
        FROM product_sales s
        JOIN products p ON s.product_id = p.id
        LEFT JOIN members m ON s.member_id = m.id
        ORDER BY s.created_at DESC, s.id DESC
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        for r in rows:
            r["created_at"] = _to_str(r["created_at"])
        return rows
    finally:
        cursor.close()
        db.close()


@router.post("", status_code=201)
def create_sale(data: Dict[str, Any], request: Request, current_user=Depends(get_current_user)):
    """
    新增商品售卖：扣库存、会员余额/流水、创建订单、操作日志、通知
    body: { product_id, quantity, member_id?, pay_method(现金/会员余额), remark? }
    """
    required = ["product_id", "quantity", "pay_method"]
    for f in required:
        if f not in data:
            raise HTTPException(status_code=400, detail=f"缺少字段: {f}")

    product_id = data["product_id"]
    quantity = data["quantity"]
    member_id = data.get("member_id")
    pay_method = data["pay_method"]
    remark = (data.get("remark") or "").strip()

    try:
        quantity = int(quantity)
    except Exception:
        raise HTTPException(status_code=400, detail="数量格式不正确")
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="数量必须大于 0")

    if pay_method not in ("现金", "会员余额"):
        raise HTTPException(status_code=400, detail="非法的支付方式")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor2 = db.cursor()
    try:
        db.start_transaction()

        cursor.execute(
            "SELECT id, name, price, stock FROM products WHERE id = %s FOR UPDATE",
            (product_id,),
        )
        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")

        stock = int(product["stock"] or 0)
        if stock < quantity:
            raise HTTPException(status_code=400, detail="库存不足")

        unit_price = float(product["price"])
        total_price = round(unit_price * quantity, 2)

        # 应用会员折扣（会员卡折扣或等级折扣）
        try:
            if member_id:
                # 优先使用会员卡折扣
                card, _ = get_best_card(cursor, member_id)
                if card and card.get("discount") is not None:
                    try:
                        card_discount = float(card.get("discount") or 100)
                    except Exception:
                        card_discount = 100.0
                    if card_discount < 100:
                        total_price = round(total_price * card_discount / 100.0, 2)
                else:
                    # 没有会员卡折扣，使用会员等级折扣
                    discount = get_member_discount(cursor, member_id)
                    if discount < 100:
                        total_price = round(total_price * discount / 100.0, 2)
        except Exception:
            pass

        member_name = None
        if member_id is not None:
            member_id = int(member_id)
            cursor.execute(
                "SELECT id, name, balance, status FROM members WHERE id = %s FOR UPDATE",
                (member_id,),
            )
            member = cursor.fetchone()
            if not member:
                raise HTTPException(status_code=404, detail="会员不存在")
            member_name = member.get("name")

            if str(member.get("status") or "正常") != "正常":
                raise HTTPException(status_code=400, detail="会员状态异常，无法使用余额支付")

            if pay_method == "会员余额":
                balance = float(member.get("balance") or 0.0)
                if balance < total_price:
                    raise HTTPException(status_code=400, detail="会员余额不足")
                new_balance = round(balance - total_price, 2)
                cursor2.execute(
                    "UPDATE members SET balance = %s WHERE id = %s",
                    (new_balance, member_id),
                )
                mt_sql = """
                INSERT INTO member_transactions (member_id, type, amount, balance_after, remark)
                VALUES (%s, '消费', %s, %s, %s)
                """
                mt_remark = remark or f"商品消费：{product['name']} x {quantity}"
                cursor2.execute(mt_sql, (member_id, -total_price, new_balance, mt_remark))
        else:
            if pay_method == "会员余额":
                raise HTTPException(status_code=400, detail="使用会员余额支付时必须选择会员")

        new_stock = stock - quantity
        cursor2.execute("UPDATE products SET stock = %s WHERE id = %s", (new_stock, product_id))

        sale_sql = """
        INSERT INTO product_sales
            (product_id, member_id, quantity, unit_price, total_price, pay_method, remark)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor2.execute(
            sale_sql,
            (product_id, member_id, quantity, unit_price, total_price, pay_method, remark),
        )
        sale_id = cursor2.lastrowid

        pay_method_code = "cash" if pay_method == "现金" else "member_balance"
        order_items = [
            {
                "product_id": product_id,
                "name": product["name"],
                "unit_price": Decimal(str(unit_price)),
                "quantity": quantity,
                "amount": Decimal(str(total_price)),
            }
        ]
        order_result = create_product_order(
            member_id=member_id,
            member_name=member_name,
            items=order_items,
            total_amount=Decimal(str(total_price)),
            pay_method=pay_method_code,
            remark=remark or None,
            related_id=sale_id,
        )
        order_id = order_result["order_id"]

        cursor2.execute("UPDATE product_sales SET order_id = %s WHERE id = %s", (order_id, sale_id))

        try:
            uid = current_user["id"] if isinstance(current_user, dict) else current_user.id
            uname = current_user["username"] if isinstance(current_user, dict) else current_user.username
            write_operation_log(
                user_id=uid,
                username=uname or "",
                action="CREATE_PRODUCT_SALE",
                module="product",
                target_id=sale_id,
                target_desc=product["name"],
                detail={
                    "total_price": total_price,
                    "quantity": quantity,
                    "pay_method": pay_method,
                    "order_id": order_id,
                    "order_no": order_result.get("order_no"),
                },
                ip=request.client.host if request.client else None,
            )
        except Exception:
            pass

        try:
            if member_id:
                create_notification(
                    member_id=member_id,
                    title="商品购买成功",
                    content=f"已购买 {product['name']} x {quantity}，金额：¥{total_price}",
                )
            create_admin_notifications(
                title="商品售卖",
                content=f"{member_name or '散客'} 购买 {product['name']} x {quantity}，金额 ¥{total_price}",
                level="info",
            )
        except Exception:
            pass

        db.commit()
        return {
            "id": sale_id,
            "order_id": order_id,
            "order_no": order_result.get("order_no"),
            "total_price": total_price,
            "member_id": member_id,
        }
    finally:
        cursor.close()
        cursor2.close()
        db.close()


@router.post("/{sale_id}/refund")
def refund_sale(sale_id: int, data: Dict[str, Any], current_user=Depends(get_current_user)):
    """商品售卖退款：生成退款订单，返还会员余额（如有），记录操作日志与通知"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor2 = db.cursor()
    try:
        db.start_transaction()

        cursor.execute("SELECT * FROM product_sales WHERE id = %s", (sale_id,))
        sale = cursor.fetchone()
        if not sale:
            raise HTTPException(status_code=404, detail="销售记录不存在")

        member_id = sale.get("member_id")
        member_name = None
        if member_id:
            cursor.execute("SELECT id, name, balance FROM members WHERE id = %s FOR UPDATE", (member_id,))
            mrow = cursor.fetchone()
            if not mrow:
                raise HTTPException(status_code=404, detail="会员不存在")
            member_name = mrow.get("name") if isinstance(mrow, dict) else None

        cursor.execute(
            "SELECT * FROM orders WHERE related_id = %s AND order_type = 'goods' ORDER BY id DESC LIMIT 1",
            (sale_id,),
        )
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="未找到关联订单")

        raw_status = (order.get("status") or order.get("order_status") or "").lower()
        if raw_status in {"refunded", "partial_refund", "cancelled", "canceled"}:
            raise HTTPException(status_code=400, detail="订单已退款或已取消")

        refund_amount = data.get("amount")
        if refund_amount is None:
            refund_amount = order.get("pay_amount") or order.get("total_amount")
        try:
            refund_amount = float(refund_amount or 0)
        except Exception:
            refund_amount = 0.0

        refund_info = create_refund_order(
            cursor=cursor,
            original_order_id=order["id"],
            original_order_no=order.get("order_no"),
            member_id=member_id,
            member_name=member_name,
            amount=refund_amount,
            order_type="goods",
            remark=data.get("remark"),
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
            mt_remark = data.get("remark") or f"商品售卖退款：{sale.get('product_id')}"
            cursor2.execute(mt_sql, (member_id, refund_amount, new_balance, mt_remark))

        try:
            uid = current_user["id"] if isinstance(current_user, dict) else current_user.id
            uname = current_user["username"] if isinstance(current_user, dict) else current_user.username
            write_operation_log(
                user_id=uid,
                username=uname or "",
                action="REFUND_PRODUCT_SALE",
                module="product",
                target_id=sale_id,
                target_desc=sale.get("product_id"),
                detail={"refund_amount": refund_amount, "order_id": order["id"], "order_no": order.get("order_no")},
                ip=None,
            )
            try:
                # 给会员发通知
                if member_id:
                    cursor.execute("SELECT name FROM products WHERE id = %s", (sale.get("product_id"),))
                    prod_row = cursor.fetchone()
                    product_name = prod_row.get("name") if prod_row else "商品"
                    create_notification(
                        member_id=member_id,
                        title="商品退款成功",
                        content=f"{product_name} 已退款 ¥{refund_amount:.2f}，金额已退回账户余额",
                        level="info",
                    )
                
                # 给管理员发通知
                create_admin_notifications(
                    title="商品售卖退款",
                    content=f"订单 {order.get('order_no')} 已退款 ¥{refund_amount}",
                    level="warning",
                )
            except Exception:
                pass
        except Exception:
            pass

        db.commit()
        return {"message": "已退款", "refund_order": refund_info}
    except HTTPException:
        db.rollback()
        raise
    finally:
        cursor.close()
        cursor2.close()
        db.close()
