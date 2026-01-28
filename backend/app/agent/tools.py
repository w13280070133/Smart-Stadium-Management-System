"""
AI Agent Tools for Database Access

This module provides tool functions for AI agents to interact with the database.
All database operations use raw SQL (no ORM) with parameterized queries to prevent SQL injection.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import random

from ..database import get_db


# ============================================================================
# Pydantic Models for Tool Arguments (for JSON Schema generation)
# ============================================================================

class SearchCourtsArgs(BaseModel):
    """Arguments for searching available courts"""
    sport_type: Optional[str] = Field(None, description="运动类型，例如：羽毛球、篮球、瑜伽")
    target_date: str = Field(..., description="目标日期，格式：YYYY-MM-DD")
    start_hour: int = Field(..., ge=0, le=23, description="开始小时 (0-23)")
    end_hour: int = Field(..., ge=0, le=23, description="结束小时 (0-23)")


class BookCourtArgs(BaseModel):
    """Arguments for booking a court"""
    court_id: int = Field(..., description="场地ID")
    target_date: str = Field(..., description="预订日期，格式：YYYY-MM-DD")
    start_hour: int = Field(..., ge=0, le=23, description="开始小时 (0-23)")
    end_hour: int = Field(..., ge=0, le=23, description="结束小时 (0-23)")


class GetGymRulesArgs(BaseModel):
    """Arguments for getting gym rules (no parameters needed)"""
    pass


# ============================================================================
# Tool Functions
# ============================================================================

def search_courts_tool(
    sport_type: Optional[str] = None,
    target_date: str = "",
    start_hour: int = 9,
    end_hour: int = 10,
) -> List[Dict[str, Any]]:
    """
    搜索可用场地
    
    根据日期和时间段，查询状态为"可用"且未被预约的场地。
    
    核心逻辑：
    1. 构造目标时间段的 datetime 对象
    2. 查询该时间段内已被占用的场地 ID（排除已取消的预约）
    3. 查询所有可用场地，排除已占用的场地
    
    冲突检测公式：
    NOT (end_time <= new_start_time OR start_time >= new_end_time)
    
    Args:
        sport_type: 运动类型（可选），如 "羽毛球"、"篮球"
        target_date: 目标日期，格式 "YYYY-MM-DD"
        start_hour: 开始小时 (0-23)
        end_hour: 结束小时 (0-23)
    
    Returns:
        可用场地列表，每个场地包含：
        - id: 场地ID
        - name: 场地名称
        - type: 场地类型
        - price: 每小时价格
    
    Example:
        >>> search_courts_tool(sport_type="羽毛球", target_date="2025-01-26", start_hour=14, end_hour=16)
        [
            {"id": 1, "name": "1号羽毛球场", "type": "羽毛球", "price": 50.0},
            {"id": 2, "name": "2号羽毛球场", "type": "羽毛球", "price": 50.0}
        ]
    """
    # 1. 参数验证
    if not target_date:
        raise ValueError("target_date 不能为空")
    
    if start_hour < 0 or start_hour > 23:
        raise ValueError("start_hour 必须在 0-23 之间")
    
    if end_hour < 0 or end_hour > 23:
        raise ValueError("end_hour 必须在 0-23 之间")
    
    if end_hour <= start_hour:
        raise ValueError("end_hour 必须大于 start_hour")
    
    # 2. 构造时间段
    try:
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("target_date 格式不正确，应为 YYYY-MM-DD")
    
    start_dt = date_obj.replace(hour=start_hour, minute=0, second=0)
    end_dt = date_obj.replace(hour=end_hour, minute=0, second=0)
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # 3. 查询该时间段内已被占用的场地 ID
        # 冲突检测：NOT (end_time <= start_dt OR start_time >= end_dt)
        occupied_sql = """
            SELECT DISTINCT court_id
            FROM court_reservations
            WHERE status <> '已取消'
              AND NOT (end_time <= %s OR start_time >= %s)
        """
        cursor.execute(occupied_sql, (start_dt, end_dt))
        occupied_rows = cursor.fetchall()
        occupied_ids = [row["court_id"] for row in occupied_rows]
        
        # 4. 查询所有可用场地，排除已占用的场地
        available_sql = """
            SELECT id, name, type, price_per_hour AS price, status, location
            FROM courts
            WHERE status = '可用'
        """
        params: List[Any] = []
        
        # 添加运动类型过滤
        if sport_type:
            available_sql += " AND type = %s"
            params.append(sport_type)
        
        # 排除已占用的场地
        if occupied_ids:
            placeholders = ", ".join(["%s"] * len(occupied_ids))
            available_sql += f" AND id NOT IN ({placeholders})"
            params.extend(occupied_ids)
        
        available_sql += " ORDER BY id ASC"
        
        cursor.execute(available_sql, params)
        courts = cursor.fetchall()
        
        # 5. 格式化返回结果
        result = []
        for court in courts:
            result.append({
                "id": court["id"],
                "name": court["name"],
                "type": court["type"],
                "price": float(court["price"] or 0),
            })
        
        return result
    
    finally:
        cursor.close()
        db.close()


def get_gym_rules_tool() -> str:
    """
    获取场馆规则
    
    返回场馆的营业时间、取消规则等信息。
    目前返回 Mock 数据，后续可以从 system_settings 表读取。
    
    Returns:
        场馆规则字符串
    
    Example:
        >>> get_gym_rules_tool()
        "取消规则：提前2小时免费取消，否则扣费50%。营业时间：09:00 - 22:00"
    """
    # Mock 数据，后续可以从 system_settings 表读取
    rules = (
        "【场馆规则】\n"
        "1. 营业时间：09:00 - 22:00\n"
        "2. 取消规则：提前2小时免费取消，否则扣费50%\n"
        "3. 预约规则：最多提前7天预约，单次预约不超过3小时\n"
        "4. 支付方式：支持会员余额、现金、微信、支付宝\n"
        "5. 会员折扣：会员卡享受不同折扣优惠"
    )
    return rules


def book_court_tool(
    court_id: int,
    target_date: str,
    start_hour: int,
    end_hour: int,
    member_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    预订场地（完整商业闭环逻辑）
    
    当用户明确表示要下单、预订某个具体的场地时调用此工具。
    执行完整的事务流程：冲突检测 -> 价格计算 -> 余额检查 -> 扣款 -> 记录流水 -> 创建预约。
    
    核心逻辑（Transaction Script）：
    1. 参数校验（必须登录会员）
    2. 锁定与冲突检测（Double Check）
    3. 获取价格与计算
    4. 余额检查与扣款
    5. 记录交易流水
    6. 创建预约记录
    
    所有操作在一个数据库事务中，任何一步失败都会回滚。
    
    Args:
        court_id: 场地ID
        target_date: 预订日期，格式 "YYYY-MM-DD"
        start_hour: 开始小时 (0-23)
        end_hour: 结束小时 (0-23)
        member_id: 会员ID（必须提供，否则抛出异常）
    
    Returns:
        预订结果字典，包含：
        - status: 预订状态 ("success" 或 "failed")
        - reservation_id: 预约记录ID
        - court_name: 场地名称
        - date: 预订日期
        - time_range: 时间段
        - total_price: 总价格
        - balance_after: 扣款后余额
        - message: 提示信息
    
    Raises:
        ValueError: 参数验证失败、余额不足、时间段已被占用等
    
    Example:
        >>> book_court_tool(court_id=1, target_date="2025-01-27", start_hour=14, end_hour=16, member_id=1)
        {
            "status": "success",
            "reservation_id": 123,
            "court_name": "1号羽毛球场",
            "date": "2025-01-27",
            "time_range": "14:00-16:00",
            "total_price": 100.0,
            "balance_after": 900.0,
            "message": "预订成功！已从您的账户扣款 ¥100.00 元，当前余额 ¥900.00 元。"
        }
    """
    # ========================================================================
    # 1. 参数校验
    # ========================================================================
    
    # 检查 member_id 是否存在
    if member_id is None:
        raise ValueError("请先登录会员账号后再进行预订")
    
    if not target_date:
        raise ValueError("target_date 不能为空")
    
    if start_hour < 0 or start_hour > 23:
        raise ValueError("start_hour 必须在 0-23 之间")
    
    if end_hour < 0 or end_hour > 23:
        raise ValueError("end_hour 必须在 0-23 之间")
    
    if end_hour <= start_hour:
        raise ValueError("end_hour 必须大于 start_hour")
    
    # 构造时间段
    try:
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("target_date 格式不正确，应为 YYYY-MM-DD")
    
    start_dt = date_obj.replace(hour=start_hour, minute=0, second=0)
    end_dt = date_obj.replace(hour=end_hour, minute=0, second=0)
    
    # 检查是否预订过去的时间
    if start_dt < datetime.now():
        raise ValueError("不能预订过去的时间，请选择当前时间之后的时段")
    
    # ========================================================================
    # 开始数据库事务
    # ========================================================================
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # ====================================================================
        # 2. 锁定与冲突检测 (Double Check)
        # ====================================================================
        
        # 再次查询该时间段是否已被占用（防止并发问题）
        conflict_sql = """
            SELECT COUNT(*) AS cnt
            FROM court_reservations
            WHERE court_id = %s
              AND status <> '已取消'
              AND NOT (end_time <= %s OR start_time >= %s)
        """
        cursor.execute(conflict_sql, (court_id, start_dt, end_dt))
        conflict_row = cursor.fetchone()
        
        if (conflict_row.get("cnt") or 0) > 0:
            raise ValueError(f"该时间段已被预约，请重新选择其他时间或场地")
        
        # ====================================================================
        # 3. 获取价格与计算
        # ====================================================================
        
        # 查询场地信息
        cursor.execute(
            "SELECT id, name, type, price_per_hour, status FROM courts WHERE id = %s",
            (court_id,)
        )
        court = cursor.fetchone()
        
        if not court:
            raise ValueError(f"场地ID {court_id} 不存在")
        
        if court["status"] != "可用":
            raise ValueError(f"场地 {court['name']} 当前状态为 {court['status']}，无法预订")
        
        court_name = court["name"]
        court_type = court.get("type")
        price_per_hour = float(court["price_per_hour"] or 0)
        
        if price_per_hour <= 0:
            raise ValueError("场地价格未配置，无法预订")
        
        # 计算总价
        duration_hours = end_hour - start_hour
        total_amount = round(price_per_hour * duration_hours, 2)
        
        # ====================================================================
        # 4. 余额检查与扣款 (核心财务逻辑)
        # ====================================================================
        
        # 查询会员余额
        cursor.execute(
            "SELECT id, name, balance FROM members WHERE id = %s",
            (member_id,)
        )
        member = cursor.fetchone()
        
        if not member:
            raise ValueError(f"会员ID {member_id} 不存在，请先注册会员")
        
        current_balance = float(member["balance"] or 0)
        member_name = member["name"]
        
        # 余额检查
        if current_balance < total_amount:
            raise ValueError(
                f"余额不足，需支付 ¥{total_amount:.2f} 元，当前余额 ¥{current_balance:.2f} 元。请先充值。"
            )
        
        # 执行扣款
        cursor.execute(
            "UPDATE members SET balance = balance - %s WHERE id = %s",
            (total_amount, member_id)
        )
        
        # 计算扣款后余额
        balance_after = round(current_balance - total_amount, 2)
        
        # ====================================================================
        # 5. 记录交易流水 (Audit Log)
        # ====================================================================
        
        transaction_remark = f"AI助手自动预订: {court_name} {target_date} {start_hour:02d}:00-{end_hour:02d}:00"
        
        cursor.execute(
            """
            INSERT INTO member_transactions
                (member_id, type, amount, balance_after, remark, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (
                member_id,
                "消费",
                -total_amount,  # 负数表示扣款
                balance_after,
                transaction_remark
            )
        )
        
        transaction_id = cursor.lastrowid
        
        # ====================================================================
        # 6. 创建预约记录
        # ====================================================================
        
        reservation_remark = f"AI助手自动预订 (会员: {member_name}, 交易ID: {transaction_id})"
        
        cursor.execute(
            """
            INSERT INTO court_reservations
                (court_id, member_id, start_time, end_time, total_amount, status, source, remark, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                court_id,
                member_id,
                start_dt,
                end_dt,
                total_amount,
                "已预约",
                "AI_Agent",
                reservation_remark
            )
        )
        
        reservation_id = cursor.lastrowid
        
        # ====================================================================
        # 7. 创建订单记录 (Orders Table)
        # ====================================================================
        
        # 生成订单号：GYM-C-{YYYYMMDDHHMMSS}{3位随机数}
        now = datetime.now()
        order_no = f"GYM-C-{now.strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
        
        cursor.execute(
            """
            INSERT INTO orders
                (order_no, order_type, related_id, member_id, member_name, 
                 total_amount, pay_amount, status, pay_method, 
                 created_at, paid_at, remark)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
            """,
            (
                order_no,
                "court",
                reservation_id,
                member_id,
                member_name,
                total_amount,
                total_amount,
                "paid",
                "会员余额",
                "AI助手自动下单"
            )
        )
        
        order_id = cursor.lastrowid
        
        # ====================================================================
        # 提交事务
        # ====================================================================
        
        db.commit()
        
        # ====================================================================
        # 7. 返回成功结果
        # ====================================================================
        
        success_message = (
            f"预订成功！{court_name} 已为您预订 {target_date} {start_hour:02d}:00-{end_hour:02d}:00，"
            f"总价 ¥{total_amount:.2f} 元。已从您的账户扣款，当前余额 ¥{balance_after:.2f} 元。"
            f"订单号：{order_no}"
        )
        
        return {
            "status": "success",
            "reservation_id": reservation_id,
            "transaction_id": transaction_id,
            "order_id": order_id,
            "order_no": order_no,
            "court_name": court_name,
            "court_type": court_type,
            "member_name": member_name,
            "date": target_date,
            "time_range": f"{start_hour:02d}:00-{end_hour:02d}:00",
            "duration_hours": duration_hours,
            "price_per_hour": price_per_hour,
            "total_price": total_amount,
            "balance_before": current_balance,
            "balance_after": balance_after,
            "message": success_message
        }
    
    except ValueError as e:
        # 业务逻辑错误，回滚事务
        db.rollback()
        print(f"[book_court_tool] 业务逻辑错误: {e}")
        raise e
    
    except Exception as e:
        # 其他错误（如数据库错误），回滚事务
        db.rollback()
        print(f"[book_court_tool] 系统错误: {e}")
        raise ValueError(f"预订失败：{str(e)}")
    
    finally:
        cursor.close()
        db.close()


# ============================================================================
# Tool Registry (for AI Agent to discover available tools)
# ============================================================================

AVAILABLE_TOOLS = {
    "search_courts": {
        "function": search_courts_tool,
        "args_model": SearchCourtsArgs,
        "description": "搜索可用场地，根据日期和时间段查询未被预约的场地",
    },
    "book_court": {
        "function": book_court_tool,
        "args_model": BookCourtArgs,
        "description": "预订场地。当用户明确表示要下单、预订某个具体的场地时调用此工具。会自动从会员余额扣款并记录交易流水。",
    },
    "get_gym_rules": {
        "function": get_gym_rules_tool,
        "args_model": GetGymRulesArgs,
        "description": "获取场馆规则，包括营业时间、取消规则等",
    },
}


def get_tool_schemas() -> List[Dict[str, Any]]:
    """
    获取所有工具的 JSON Schema
    
    用于 AI Agent 理解可用的工具及其参数。
    
    Returns:
        工具 Schema 列表
    """
    schemas = []
    for tool_name, tool_info in AVAILABLE_TOOLS.items():
        schema = {
            "name": tool_name,
            "description": tool_info["description"],
            "parameters": tool_info["args_model"].model_json_schema(),
        }
        schemas.append(schema)
    return schemas


def execute_tool(tool_name: str, **kwargs) -> Any:
    """
    执行指定的工具函数
    
    Args:
        tool_name: 工具名称
        **kwargs: 工具参数（包含 LLM 生成的参数和上下文参数如 member_id）
    
    Returns:
        工具执行结果
    
    Raises:
        ValueError: 工具不存在
    """
    if tool_name not in AVAILABLE_TOOLS:
        raise ValueError(f"工具 '{tool_name}' 不存在")
    
    tool_info = AVAILABLE_TOOLS[tool_name]
    function = tool_info["function"]
    args_model = tool_info["args_model"]
    
    # 分离上下文参数（如 member_id）和 LLM 生成的参数
    # member_id 不在 Pydantic 模型中，需要单独处理
    context_params = {}
    llm_params = {}
    
    for key, value in kwargs.items():
        if key == "member_id":
            context_params[key] = value
        else:
            llm_params[key] = value
    
    # 验证 LLM 生成的参数
    validated_args = args_model(**llm_params)
    
    # 检查函数签名，如果函数需要 member_id，则注入
    import inspect
    sig = inspect.signature(function)
    
    call_args = validated_args.model_dump()
    
    # 如果函数接受 member_id 参数，且上下文中提供了，就注入
    if "member_id" in sig.parameters and "member_id" in context_params:
        call_args["member_id"] = context_params["member_id"]
    
    # 执行工具函数
    return function(**call_args)
