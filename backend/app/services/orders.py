from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Tuple

from ..database import get_db


def _detect_order_columns(cursor) -> set[str]:
    """探测 orders 表已有的列，避免 Unknown column 错误"""
    cursor.execute("SHOW COLUMNS FROM orders")
    rows = cursor.fetchall() or []
    cols = set()
    for r in rows:
        if isinstance(r, dict):
            cols.add(r.get("Field"))
        else:
            cols.add(r[0])
    return {c for c in cols if c}


def _get_order_prefix_and_currency() -> Tuple[str, str]:
    """从 system_settings 读取订单号前缀和默认货币，未配置则用 GYM/CNY"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    prefix = "GYM"
    currency = "CNY"
    try:
        cursor.execute(
            """
            SELECT setting_key, setting_value
            FROM system_settings
            WHERE group_key = 'order'
              AND setting_key IN ('order_no_prefix', 'default_currency')
            """
        )
        for row in cursor.fetchall():
            if row["setting_key"] == "order_no_prefix":
                prefix = row["setting_value"] or prefix
            elif row["setting_key"] == "default_currency":
                currency = row["setting_value"] or currency
    finally:
        cursor.close()
        db.close()

    return prefix, currency


def generate_order_no(order_type: str) -> str:
    """生成订单号：前缀 + 类型首字母 + 时间戳"""
    prefix, _ = _get_order_prefix_and_currency()
    now = datetime.now()
    ts = now.strftime("%Y%m%d%H%M%S%f")[:-3]
    type_code = order_type[:1].upper()
    return f"{prefix}-{type_code}-{ts}"


def create_court_order(
    *,
    cursor,
    related_id: int,
    member_id: int | None,
    member_name: str | None,
    total_amount: Decimal | float | str,
    pay_method: str | None,
    status: str = "paid",
    remark: str | None = None,
    source: str | None = None,
) -> Dict[str, Any]:
    """
    为场地预约生成订单（需外部 commit）
    - order_type 固定 court
    - status=paid 时 pay_amount=total_amount，paid_at 写 NOW()
    - 自动探测 orders 有哪些字段再写入
    """
    order_no = generate_order_no("court")
    _, currency = _get_order_prefix_and_currency()
    cols = _detect_order_columns(cursor)

    total_str = str(total_amount)
    pay_amount = total_amount if status == "paid" else 0
    pay_str = str(pay_amount)
    discount_str = "0"

    columns: List[str] = ["order_no"]
    placeholders: List[str] = ["%s"]
    params: List[Any] = [order_no]

    def add_col(name: str, value: Any, use_placeholder: bool = True):
        columns.append(name)
        if use_placeholder:
            placeholders.append("%s")
            params.append(value)
        else:
            placeholders.append(value)

    if "order_type" in cols:
        add_col("order_type", "court")
    elif "type" in cols:
        add_col("type", "court")

    if "related_id" in cols:
        add_col("related_id", related_id)

    if "source" in cols and source is not None:
        add_col("source", source)

    if "member_id" in cols:
        add_col("member_id", member_id)
    if "member_name" in cols:
        add_col("member_name", member_name)

    if "total_amount" in cols:
        add_col("total_amount", total_str)
    if "pay_amount" in cols:
        add_col("pay_amount", pay_str)
    if "discount_amount" in cols:
        add_col("discount_amount", discount_str)

    if "currency" in cols:
        add_col("currency", currency)
    if "pay_method" in cols:
        add_col("pay_method", pay_method)

    if "status" in cols:
        add_col("status", status)
    if "order_status" in cols:
        add_col("order_status", status)

    if "created_at" in cols:
        add_col("created_at", "NOW()", use_placeholder=False)
    if status == "paid" and "paid_at" in cols:
        add_col("paid_at", "NOW()", use_placeholder=False)

    if "remark" in cols and remark is not None:
        add_col("remark", remark)

    sql = f"INSERT INTO orders ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    cursor.execute(sql, tuple(params))
    order_id = cursor.lastrowid

    return {
        "order_id": order_id,
        "order_no": order_no,
        "status": status,
        "pay_amount": float(pay_amount),
        "total_amount": float(total_amount),
    }


def create_product_order(
    *,
    member_id: int | None,
    member_name: str | None,
    items: List[Dict[str, Any]],
    total_amount: Decimal,
    pay_method: str | None,
    remark: str | None = None,
    related_id: int | None = None,
) -> Dict[str, Any]:
    """为商品售卖生成 orders + order_items。"""
    if not items:
        raise ValueError("items 不能为空")

    _, currency = _get_order_prefix_and_currency()
    order_no = generate_order_no("goods")

    db = get_db()
    cursor = db.cursor()
    try:
        sql_order = """
        INSERT INTO orders (
            order_no, order_type, related_id,
            member_id, member_name,
            total_amount, pay_amount, discount_amount,
            currency, pay_method, status,
            created_at, paid_at, remark
        )
        VALUES (%s, 'goods', %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                NOW(), NOW(), %s)
        """
        total_str = str(total_amount)
        cursor.execute(
            sql_order,
            (
                order_no,
                related_id,
                member_id,
                member_name,
                total_str,
                total_str,
                "0",
                currency,
                pay_method,
                "paid",
                remark,
            ),
        )
        order_id = cursor.lastrowid

        sql_item = """
        INSERT INTO order_items (
            order_id, item_type, item_id,
            item_name, unit_price, quantity, amount
        )
        VALUES (%s, 'product', %s, %s, %s, %s, %s)
        """
        for it in items:
            product_id = it.get("product_id")
            name = it.get("name") or ""
            unit_price = Decimal(str(it.get("unit_price", "0")))
            qty = int(it.get("quantity", 0))
            amount = Decimal(str(it.get("amount", unit_price * qty)))
            cursor.execute(
                sql_item,
                (
                    order_id,
                    product_id,
                    name,
                    str(unit_price),
                    qty,
                    str(amount),
                ),
            )

        db.commit()
        return {"order_id": order_id, "order_no": order_no}
    finally:
        cursor.close()
        db.close()


def create_course_order(
    *,
    cursor,
    related_id: int,
    member_id: int | None,
    member_name: str | None,
    total_amount: Decimal | float | str,
    pay_method: str | None = None,
    status: str = "paid",
    remark: str | None = None,
) -> Dict[str, Any]:
    """
    生成培训报名订单：不写 order_items，只写 orders。
    order_type 固定 training；status=paid 时 paid_at 写 NOW()。
    """
    total_str = str(total_amount)
    order_no = generate_order_no("training")
    _, currency = _get_order_prefix_and_currency()

    cursor.execute(
        """
        INSERT INTO orders (
            order_no, order_type, related_id,
            member_id, member_name,
            total_amount, pay_amount, discount_amount,
            currency, pay_method, status,
            created_at, paid_at, remark
        )
        VALUES (%s, 'training', %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                NOW(), CASE WHEN %s='paid' THEN NOW() ELSE NULL END, %s)
        """,
        (
            order_no,
            related_id,
            member_id,
            member_name,
            total_str,
            total_str if status == "paid" else "0",
            "0",
            currency,
            pay_method,
            status,
            status,
            remark,
        ),
    )
    order_id = cursor.lastrowid
    return {
        "order_id": order_id,
        "order_no": order_no,
        "status": status,
        "pay_amount": float(total_amount if status == "paid" else 0),
        "total_amount": float(total_amount),
    }


def create_refund_order(
    *,
    cursor,
    original_order_id: int,
    original_order_no: str | None,
    member_id: int | None,
    member_name: str | None,
    amount: Decimal | float | str,
    order_type: str,
    remark: str | None = None,
) -> Dict[str, Any]:
    """
    生成一条退款订单（金额为负），需外部 commit。
    - status 固定 refunded
    - pay_amount/total_amount 记录为负值
    - related_id 指向原订单 id
    """
    order_no = generate_order_no(f"{order_type}-refund")
    _, currency = _get_order_prefix_and_currency()
    cols = _detect_order_columns(cursor)

    amount_val = Decimal(str(amount)) if not isinstance(amount, Decimal) else amount
    neg_amount = str(-abs(amount_val))

    columns: List[str] = ["order_no"]
    placeholders: List[str] = ["%s"]
    params: List[Any] = [order_no]

    def add_col(name: str, value: Any, use_placeholder: bool = True):
        columns.append(name)
        if use_placeholder:
            placeholders.append("%s")
            params.append(value)
        else:
            placeholders.append(value)

    if "order_type" in cols:
        add_col("order_type", order_type)
    elif "type" in cols:
        add_col("type", order_type)

    if "related_id" in cols:
        add_col("related_id", original_order_id)

    if "source" in cols:
        add_col("source", "refund")

    if "member_id" in cols:
        add_col("member_id", member_id)
    if "member_name" in cols:
        add_col("member_name", member_name)

    if "total_amount" in cols:
        add_col("total_amount", neg_amount)
    if "pay_amount" in cols:
        add_col("pay_amount", neg_amount)
    if "discount_amount" in cols:
        add_col("discount_amount", "0")

    if "currency" in cols:
        add_col("currency", currency)
    if "pay_method" in cols:
        add_col("pay_method", None)

    if "status" in cols:
        add_col("status", "refunded")
    if "order_status" in cols:
        add_col("order_status", "refunded")

    if "created_at" in cols:
        add_col("created_at", "NOW()", use_placeholder=False)
    if "paid_at" in cols:
        add_col("paid_at", "NOW()", use_placeholder=False)

    if "remark" in cols:
        refund_remark = remark or f"退款来源订单 {original_order_no or original_order_id}"
        add_col("remark", refund_remark)

    sql = f"INSERT INTO orders ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    cursor.execute(sql, tuple(params))
    refund_id = cursor.lastrowid

    return {
        "order_id": refund_id,
        "order_no": order_no,
        "status": "refunded",
        "amount": float(-abs(amount_val)),
        "related_order_id": original_order_id,
    }
