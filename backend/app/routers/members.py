from datetime import datetime, date
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from ..database import get_db
from ..deps import require_super_admin, require_action
from ..security import get_password_hash
from ..services.member_config import (
    load_member_config,
    normalize_level,
    get_level_display,
    DEFAULT_LEVEL_NAME,
)

router = APIRouter(prefix="/members", tags=["Members"])


def _to_date(val):
    """把任意值转成 date，兼容字符串/None。"""
    if val is None or val == "":
        return None
    if isinstance(val, (datetime, date)):
        return val
    try:
        return datetime.strptime(str(val), "%Y-%m-%d").date()
    except Exception:
        return None


def normalize_member(row: Dict[str, Any], level_config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """把一行记录转成前端友好的字典。"""
    created_at = row.get("created_at")
    created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else ""
    level_value = row.get("level") or DEFAULT_LEVEL_NAME

    result = {
        "id": row["id"],
        "name": row["name"],
        "phone": row["phone"],
        "gender": row.get("gender") or "未知",
        "birthday": row.get("birthday"),
        "level": level_value,
        "status": row.get("status") or "正常",
        "remark": row.get("remark") or "",
        "balance": float(row.get("balance") or 0),
        "total_spent": float(row.get("total_spent") or 0),
        "created_at": created_at_str,
    }

    if level_config is not None:
        detail = get_level_display(level_value, level_config)
        result["level_name"] = detail.get("name")
        result["level_discount"] = detail.get("discount", 100)

    return result


@router.get("", response_model=List[Dict[str, Any]])
def list_members():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id,
                   name,
                   phone,
                   gender,
                   birthday,
                   level,
                   status,
                   remark,
                   balance,
                   total_spent,
                   created_at
            FROM members
            ORDER BY id DESC
            """
        )
        rows = cursor.fetchall()
        config = load_member_config(cursor)
        return [normalize_member(r, config) for r in rows]
    finally:
        cursor.close()
        db.close()


@router.post("", status_code=201)
def create_member(data: Dict[str, Any]):
    """
    新增会员：
    - 姓名、手机号必填
    - 性别：男/女/未知
    - 状态：正常/禁用/注销
    - 会员等级如果前端不传，默认“普通会员”
    - 办卡：支持计次卡(times)、折扣卡(discount)、时限卡(time/月卡/年卡)
    """
    name = data.get("name")
    phone = data.get("phone")
    if not name or not phone:
        raise HTTPException(status_code=400, detail="姓名和手机号必填")

    gender = data.get("gender") or "未知"
    birthday = data.get("birthday") or None
    level = data.get("level") or "普通会员"
    status_val = data.get("status") or "正常"
    remark = data.get("remark") or None

    initial_balance = data.get("initial_balance", 0)
    try:
        initial_balance = float(initial_balance or 0)
        if initial_balance < 0:
            raise ValueError()
    except ValueError:
        raise HTTPException(status_code=400, detail="初始余额必须是非负数字")

    if gender not in ("男", "女", "未知"):
        raise HTTPException(status_code=400, detail="性别只能是 男 / 女 / 未知")
    if status_val not in ("正常", "禁用", "注销"):
        raise HTTPException(status_code=400, detail="状态只能是 正常 / 禁用 / 注销")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        config = load_member_config(cursor)
        level_value, _ = normalize_level(level, config)

        cursor.execute("SELECT id FROM members WHERE phone = %s", (phone,))
        exists = cursor.fetchone()
        if exists:
            raise HTTPException(status_code=400, detail="该手机号已存在，请勿重复添加")

        cursor.execute(
            """
            INSERT INTO members
                (name, phone, gender, birthday, level, status, remark, balance, total_spent)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0)
            """,
            (name, phone, gender, birthday, level_value, status_val, remark, initial_balance),
        )
        db.commit()
        member_id = cursor.lastrowid

        # 办卡信息（可选）
        card_data = data.get("card") or {}
        card_type = (card_data.get("card_type") or "").strip().lower()
        if card_type in {"times", "discount", "time", "month", "year"}:
            start_date = _to_date(card_data.get("start_date")) or date.today()
            end_date = _to_date(card_data.get("end_date")) or start_date
            if end_date < start_date:
                raise HTTPException(status_code=400, detail="卡的结束日期不能早于开始日期")

            total_times = card_data.get("total_times")
            remaining_times = card_data.get("remaining_times", total_times)
            if card_type == "times":
                if total_times is None:
                    raise HTTPException(status_code=400, detail="计次卡需填写总次数")
                try:
                    total_times = int(total_times)
                except (TypeError, ValueError):
                    raise HTTPException(status_code=400, detail="总次数必须是整数")
                if total_times <= 0:
                    raise HTTPException(status_code=400, detail="总次数必须大于 0")
                if remaining_times is None:
                    remaining_times = total_times
                else:
                    try:
                        remaining_times = int(remaining_times)
                    except (TypeError, ValueError):
                        raise HTTPException(status_code=400, detail="剩余次数必须是整数")
                    if remaining_times < 0:
                        remaining_times = 0
                    elif remaining_times > total_times:
                        remaining_times = total_times
            else:
                total_times = None
                remaining_times = None

            try:
                discount_val = int(card_data.get("discount", 100))
            except (TypeError, ValueError):
                discount_val = 100

            cursor.execute(
                """
                INSERT INTO member_cards
                    (member_id, card_name, card_type, total_times, remaining_times, discount, start_date, end_date, remark)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    member_id,
                    card_data.get("card_name") or ("计次卡" if card_type == "times" else "会员卡"),
                    card_type,
                    total_times,
                    remaining_times,
                    discount_val,
                    start_date,
                    end_date,
                    card_data.get("remark"),
                ),
            )

        cursor.execute(
            """
            SELECT id,
                   name,
                   phone,
                   gender,
                   birthday,
                   level,
                   status,
                   remark,
                   balance,
                   total_spent,
                   created_at
            FROM members
            WHERE id = %s
            """,
            (member_id,),
        )
        row = cursor.fetchone()
        return normalize_member(row, config)
    finally:
        cursor.close()
        db.close()


@router.put("/{member_id}")
def update_member(member_id: int, data: Dict[str, Any]):
    """编辑会员信息（不强制会员等级）。"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        config = load_member_config(cursor)
        cursor.execute("SELECT * FROM members WHERE id = %s", (member_id,))
        origin = cursor.fetchone()
        if not origin:
            raise HTTPException(status_code=404, detail="会员不存在")

        new_phone = data.get("phone", origin.get("phone"))
        if new_phone != origin.get("phone"):
            cursor.execute(
                "SELECT id FROM members WHERE phone = %s AND id <> %s",
                (new_phone, member_id),
            )
            exists = cursor.fetchone()
            if exists:
                raise HTTPException(status_code=400, detail="该手机号已被其他会员使用")

        name = data.get("name", origin.get("name"))
        gender = data.get("gender", origin.get("gender") or "未知")
        birthday = data.get("birthday", origin.get("birthday"))
        level_input = data.get("level", origin.get("level"))
        level, _ = normalize_level(level_input, config)
        status_val = data.get("status", origin.get("status") or "正常")
        remark = data.get("remark", origin.get("remark"))

        if gender not in ("男", "女", "未知"):
            raise HTTPException(status_code=400, detail="性别只能是 男 / 女 / 未知")
        if status_val not in ("正常", "禁用", "注销"):
            raise HTTPException(status_code=400, detail="状态只能是 正常 / 禁用 / 注销")

        cursor.execute(
            """
            UPDATE members
            SET name=%s,
                phone=%s,
                gender=%s,
                birthday=%s,
                level=%s,
                status=%s,
                remark=%s
            WHERE id=%s
            """,
            (name, new_phone, gender, birthday, level, status_val, remark, member_id),
        )
        db.commit()

        cursor.execute(
            """
            SELECT id,
                   name,
                   phone,
                   gender,
                   birthday,
                   level,
                   status,
                   remark,
                   balance,
                   total_spent,
                   created_at
            FROM members
            WHERE id = %s
            """,
            (member_id,),
        )
        row = cursor.fetchone()
        return normalize_member(row, config)
    finally:
        cursor.close()
        db.close()


@router.put("/{member_id}/status")
def update_member_status(member_id: int, data: Dict[str, Any]):
    new_status = data.get("status")
    if new_status not in ("正常", "禁用", "注销"):
        raise HTTPException(status_code=400, detail="状态只能是 正常 / 禁用 / 注销")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM members WHERE id=%s", (member_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="会员不存在")

        cursor.execute(
            "UPDATE members SET status=%s WHERE id=%s",
            (new_status, member_id),
        )
        db.commit()
        return {"message": "状态已更新"}
    finally:
        cursor.close()
        db.close()


@router.delete("/{member_id}")
def delete_member(member_id: int, current_user=Depends(require_action("member.delete"))):
    """
    删除会员及其所有关联数据
    
    这是级联删除操作，会删除会员的所有关联数据，包括：
    - 历史订单和订单项
    - 会员流水记录
    - 场地预约记录
    - 商品销售记录
    - 会员卡信息
    - 通知消息
    
    重要说明：
    1. 使用数据库事务确保数据一致性（要么全部删除，要么全部保留）
    2. 按照外键依赖关系的顺序删除（先删除子表，再删除父表）
    3. 删除订单项时需要先查询出订单 ID，避免外键约束错误
    4. 任何步骤失败都会回滚整个删除操作
    
    删除顺序（按数据库依赖关系）：
    1. 旧课程报名记录（course_enrollments_old）
    2. 商品销售记录（product_sales）
    3. 会员卡（member_cards）
    4. 会员流水（member_transactions）
    5. 订单项（order_items）→ 订单（orders）
    6. 场地预约（court_reservations）
    7. 通知（notifications）
    8. 会员本身（members）
    
    Args:
        member_id: 会员 ID
        current_user: 当前用户（需要 member.delete 权限）
        
    Returns:
        dict: {"message": "会员及其关联数据已删除"}
        
    Raises:
        HTTPException(404): 会员不存在
        HTTPException(500): 删除失败（事务已回滚）
    
    注意：
        此操作不可逆！删除后无法恢复会员的任何数据。
        建议在生产环境使用软删除（修改状态为"注销"）而不是物理删除。
    """
    db = get_db()
    cursor = db.cursor()
    try:
        db.start_transaction()
        
        cursor.execute("SELECT id FROM members WHERE id=%s", (member_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="会员不存在")

        # 按依赖关系顺序删除关联数据
        cursor.execute("DELETE FROM course_enrollments_old WHERE member_id=%s", (member_id,))
        cursor.execute("DELETE FROM product_sales WHERE member_id=%s", (member_id,))
        cursor.execute("DELETE FROM member_cards WHERE member_id=%s", (member_id,))
        cursor.execute("DELETE FROM member_transactions WHERE member_id=%s", (member_id,))
        
        # 先删除订单项（子表），再删除订单（父表）
        cursor.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE member_id=%s)", (member_id,))
        cursor.execute("DELETE FROM orders WHERE member_id=%s", (member_id,))
        
        cursor.execute("DELETE FROM court_reservations WHERE member_id=%s", (member_id,))
        cursor.execute("DELETE FROM notifications WHERE member_id=%s", (member_id,))
        
        # 最后删除会员本身
        cursor.execute("DELETE FROM members WHERE id=%s", (member_id,))
        
        db.commit()
        return {"message": "会员及其关联数据已删除"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    finally:
        cursor.close()
        db.close()


@router.put("/{member_id}/login-password")
def set_member_login_password(
    member_id: int,
    data: dict,
    current_user=Depends(require_super_admin),
):
    """
    设置会员登录密码。
    body: { "password": "123456" }
    """
    password = (data.get("password") or "").strip()
    if not password:
        raise HTTPException(status_code=400, detail="密码不能为空")

    pwd_hash = get_password_hash(password)

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE members SET login_password_hash = %s WHERE id = %s",
            (pwd_hash, member_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="会员不存在")
        db.commit()
        return {"success": True}
    finally:
        cursor.close()
        db.close()


@router.post("/{member_id}/reset-password")
def admin_reset_member_password(
    member_id: int,
    db=Depends(get_db),
):
    """
    管理员重置会员登录密码：
    - 默认重置为 123456
    - 自动识别 members 表中实际使用的密码字段（password / login_password_hash）
    """
    cursor = db.cursor(dictionary=True)
    try:
        # 1. 确认会员存在
        cursor.execute(
            "SELECT * FROM members WHERE id = %s",
            (member_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="会员不存在")

        # 2. 判断密码列名
        password_column = None
        if "login_password_hash" in row:
            password_column = "login_password_hash"
        elif "password" in row:
            password_column = "password"

        if not password_column:
            raise HTTPException(
                status_code=500,
                detail="系统未配置会员密码字段，请联系开发人员",
            )

        # 3. 重置密码（默认 123456）
        new_plain = "123456"
        new_hash = get_password_hash(new_plain)

        cursor.execute(
            f"UPDATE members SET {password_column} = %s WHERE id = %s",
            (new_hash, member_id),
        )
        db.commit()

        return {
            "message": "密码已重置为默认值",
            "new_password": new_plain,
        }
    finally:
        cursor.close()
