from typing import Dict, Any, List, Tuple

from fastapi import APIRouter, HTTPException, Depends

from ..database import get_db
from ..deps import get_current_user
from ..services.audit import write_operation_log
from ..security import verify_password

router = APIRouter(prefix="/system-settings", tags=["SystemSettings"])

# 默认配置：group_key, setting_key, value, value_type, description
DEFAULT_SETTINGS: List[Tuple[str, str, str, str, str | None]] = [
    # 基础信息
    ("basic", "system_name", "体育馆管理系统", "string", "系统标题"),
    ("basic", "gym_name", "XX体育馆", "string", "场馆名称"),
    ("basic", "contact_phone", "13800001234", "string", "联系电话"),
    ("basic", "address", "某市某区某路 XX 号", "string", "场馆地址"),

    # 系统与时区
    ("system", "timezone", "Asia/Shanghai", "string", "系统时区"),
    ("system", "time_format", "24", "string", "时间格式 12/24"),
    ("system", "date_format", "YYYY-MM-DD", "string", "日期显示格式"),
    ("system", "debug_mode", "0", "bool", "调试模式开关"),

    # 营业时间
    ("time", "business_open_time", "06:00", "string", "营业开始时间"),
    ("time", "business_close_time", "23:00", "string", "营业结束时间"),

    # 业务规则（预约）
    ("business", "reservation_slot_minutes", "60", "int", "每次预约时长（分钟）"),
    ("business", "reservation_open_days", "7", "int", "允许提前预约天数"),
    ("business", "reservation_cancel_limit_hours", "2", "int", "开场前多少小时内禁止取消"),
    ("business", "auto_cancel_minutes", "30", "int", "未支付自动取消时间（分钟）"),

    # 培训设置
    ("training", "default_course_lessons", "12", "int", "默认总课时"),
    ("training", "default_course_price", "2000", "float", "默认总课时价格"),
    ("training", "default_course_max_students", "20", "int", "默认班级最大学员数"),

    # 会员与套餐
    ("member", "allow_self_register", "1", "bool", "是否允许会员自助注册"),
    ("member", "default_level", "normal", "string", "新会员默认等级编码"),
    (
        "member",
        "member_levels_json",
        '[{"name":"普通会员","code":"normal","discount":100,"enabled":true},'
        '{"name":"银卡会员","code":"silver","discount":95,"enabled":true},'
        '{"name":"金卡会员","code":"gold","discount":90,"enabled":true},'
        '{"name":"钻石会员","code":"diamond","discount":85,"enabled":true}]',
        "json",
        "会员等级配置列表（JSON）",
    ),
    (
        "member",
        "card_packages_json",
        '[{"name":"次卡","type":"times","valid_days":90,"remark":"3 个月内使用","enabled":true},'
        '{"name":"月卡","type":"month","valid_days":30,"remark":"30 天有效","enabled":true},'
        '{"name":"年卡","type":"year","valid_days":365,"remark":"365 天有效","enabled":true}]',
        "json",
        "会员卡套餐规则列表（JSON）",
    ),

    # 功能模块
    ("modules", "enable_reservation", "1", "bool", "是否启用场地预约模块"),
    ("modules", "enable_member", "1", "bool", "是否启用会员管理模块"),
    ("modules", "enable_training", "1", "bool", "是否启用培训课程模块"),
    ("modules", "enable_products", "1", "bool", "是否启用商品售卖模块"),
    ("modules", "enable_finance", "1", "bool", "是否启用收入/订单模块"),
    ("modules", "enable_notifications", "1", "bool", "是否启用通知/消息模块"),

    # 界面与主题
    ("ui", "theme_mode", "light", "string", "主题模式：light/dark/system"),
    ("ui", "primary_color", "#409EFF", "string", "系统主色调"),
    ("ui", "admin_home_layout", "overview-first", "string", "后台首页布局"),
    ("ui", "front_home_layout", "member-center", "string", "前台首页布局"),

    # 帮助与说明
    ("help", "help_doc_url", "", "string", "帮助文档地址"),
    ("help", "help_doc_note", "", "string", "帮助文档说明备注"),

    # 订单
    ("order", "order_no_prefix", "GYM", "string", "订单号前缀"),
    ("order", "default_currency", "CNY", "string", "默认货币"),
    ("order", "allow_negative_amount", "0", "bool", "是否允许负金额订单"),
    ("order", "default_pay_methods", "cash,wechat,alipay,card", "string", "支付方式枚举"),
    ("order", "auto_close_minutes", "30", "int", "未支付订单自动关闭时间（分钟）"),

    # 审计日志
    ("audit", "enable_login_log", "1", "bool", "是否记录登录日志"),
    ("audit", "enable_operation_log", "1", "bool", "是否记录操作日志"),
    ("audit", "log_keep_days", "180", "int", "日志保留天数"),

    # 权限角色配置
    (
        "permission",
        "roles_json",
        '[{"code":"admin","name":"管理员","menus":["*"],"actions":["*"],"data_scope":"all","remark":"全量权限"},'
        '{"code":"staff","name":"员工","menus":["dashboard","members","training-enrollments","product-sales","orders"],"actions":["view","edit-self"],"data_scope":"own","remark":"常规员工权限"}]',
        "json",
        "角色与权限配置（JSON）",
    ),
]


def _ensure_default_settings():
    """确保 system_settings 表里至少有 DEFAULT_SETTINGS 这几条，不覆盖已有值。"""
    db = get_db()
    cursor = db.cursor()
    try:
        sql = """
        INSERT INTO system_settings (group_key, setting_key, setting_value, value_type, description)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          setting_value = setting_value
        """
        for item in DEFAULT_SETTINGS:
            cursor.execute(sql, item)
        db.commit()
    finally:
        cursor.close()
        db.close()


def _load_settings_dict() -> Dict[str, Dict[str, Any]]:
    _ensure_default_settings()
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT group_key, setting_key, setting_value
            FROM system_settings
            ORDER BY group_key, setting_key
            """
        )
        rows = cursor.fetchall()

        grouped: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            g = row["group_key"]
            k = row["setting_key"]
            v = row["setting_value"]
            grouped.setdefault(g, {})[k] = v
        return grouped
    finally:
        cursor.close()
        db.close()


def _parse_json_list(raw: str | None, fallback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not raw:
        return fallback
    try:
        import json
        arr = json.loads(raw)
        if isinstance(arr, list):
            return arr
    except Exception:
        pass
    return fallback


@router.get("/grouped")
def get_grouped_settings():
    """按 group_key 分组返回设置"""
    return _load_settings_dict()


@router.post("/grouped")
def save_grouped_settings(
    data: Dict[str, Dict[str, Any]],
    current_user=Depends(get_current_user)
):
    """
    前端提交的结构：
    {
      "basic": { "system_name": "...", ... },
      "business": { ... },
      ...
    }
    统一使用 INSERT ... ON DUPLICATE KEY UPDATE，避免重复键报错
    """
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="数据格式不正确")

    db = get_db()
    cursor = db.cursor()
    try:
        sql = """
        INSERT INTO system_settings
          (group_key, setting_key, setting_value, value_type, description)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          setting_value = VALUES(setting_value)
        """

        changed_groups = []
        for group_key, group_values in data.items():
            if not isinstance(group_values, dict):
                continue
            
            changed_groups.append(group_key)
            for setting_key, value in group_values.items():
                value_str = str(value) if value is not None else ""
                cursor.execute(sql, (group_key, setting_key, value_str, "string", None))

        db.commit()
        
        # 写入操作日志
        try:
            write_operation_log(
                user_id=current_user.get("id"),
                username=current_user.get("username"),
                action="批量更新",
                module="系统设置",
                target_desc=f"更新了系统配置：{', '.join(changed_groups)}"
            )
        except Exception as e:
            print(f"写入操作日志失败: {e}")
        
        return {"success": True}
    finally:
        cursor.close()
        db.close()


@router.get("/member-config")
def get_member_config():
    """
    返回会员等级与卡种配置，解析 JSON。
    {
      "default_level": "normal",
      "member_levels": [...],
      "card_packages": [...]
    }
    """
    settings = _load_settings_dict().get("member", {})
    default_level = settings.get("default_level") or "normal"
    member_levels = _parse_json_list(
        settings.get("member_levels_json"),
        [
            {"name": "普通会员", "code": "normal", "discount": 100, "enabled": True},
            {"name": "银卡会员", "code": "silver", "discount": 95, "enabled": True},
            {"name": "金卡会员", "code": "gold", "discount": 90, "enabled": True},
            {"name": "钻石会员", "code": "diamond", "discount": 85, "enabled": True},
        ],
    )
    card_packages = _parse_json_list(
        settings.get("card_packages_json"),
        [
            {"name": "次卡", "type": "times", "valid_days": 90, "remark": "3 个月内使用", "enabled": True},
            {"name": "月卡", "type": "month", "valid_days": 30, "remark": "30 天有效", "enabled": True},
            {"name": "年卡", "type": "year", "valid_days": 365, "remark": "365 天有效", "enabled": True},
        ],
    )
    return {
        "default_level": default_level,
        "member_levels": member_levels,
        "card_packages": card_packages,
    }


@router.get("/roles-config")
def get_roles_config():
    """
    返回角色权限配置列表
    """
    settings = _load_settings_dict().get("permission", {})
    roles = _parse_json_list(
        settings.get("roles_json"),
        [
            {"code": "admin", "name": "管理员", "menus": ["*"], "actions": ["*"], "data_scope": "all", "remark": "全量权限"},
            {"code": "staff", "name": "员工", "menus": ["dashboard"], "actions": ["view"], "data_scope": "own", "remark": ""},
        ],
    )
    return {"roles": roles}


@router.post("/roles-config")
def save_roles_config(payload: Dict[str, Any]):
    """
    保存角色配置（JSON），同时落库 system_settings.permission.roles_json
    payload 示例：
    { "roles": [ { code, name, menus:[], actions:[], data_scope, remark } ] }
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="数据格式不正确")
    roles = payload.get("roles")
    if not isinstance(roles, list):
        raise HTTPException(status_code=400, detail="roles 必须是列表")

    import json

    roles_json = json.dumps(roles, ensure_ascii=False)

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO system_settings (group_key, setting_key, setting_value, value_type, description)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
            """,
            ("permission", "roles_json", roles_json, "json", "角色与权限配置（JSON）"),
        )
        db.commit()
        return {"success": True}
    finally:
        cursor.close()
        db.close()


@router.get("/reservation-rules")
def get_reservation_rules():
    """
    获取预约相关规则，字段含：
    - reservation_slot_minutes: 每次预约时长（分钟）
    - reservation_open_days: 允许提前预约天数
    - reservation_cancel_limit_hours: 开场前多少小时内禁止取消
    - auto_cancel_minutes: 未支付自动取消时间
    - business_open_time / business_close_time: 营业时段
    """
    settings = _load_settings_dict()
    biz = settings.get("business", {})
    time_cfg = settings.get("time", {})
    return {
        "reservation_slot_minutes": int(biz.get("reservation_slot_minutes") or 0),
        "reservation_open_days": int(biz.get("reservation_open_days") or 0),
        "reservation_cancel_limit_hours": int(biz.get("reservation_cancel_limit_hours") or 0),
        "auto_cancel_minutes": int(biz.get("auto_cancel_minutes") or 0),
        "business_open_time": time_cfg.get("business_open_time") or "06:00",
        "business_close_time": time_cfg.get("business_close_time") or "23:00",
    }


@router.post("/reservation-rules")
def save_reservation_rules(data: Dict[str, Any]):
    """
    保存预约规则 + 营业时间
    """
    db = get_db()
    cursor = db.cursor()
    try:
        sql = """
        INSERT INTO system_settings (group_key, setting_key, setting_value, value_type, description)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
        """
        biz_fields = {
            "reservation_slot_minutes": ("business", "reservation_slot_minutes", "int", "每次预约时长（分钟）"),
            "reservation_open_days": ("business", "reservation_open_days", "int", "允许提前预约天数"),
            "reservation_cancel_limit_hours": ("business", "reservation_cancel_limit_hours", "int", "开场前多少小时内禁止取消"),
            "auto_cancel_minutes": ("business", "auto_cancel_minutes", "int", "未支付自动取消时间（分钟）"),
        }
        time_fields = {
            "business_open_time": ("time", "business_open_time", "string", "营业开始时间"),
            "business_close_time": ("time", "business_close_time", "string", "营业结束时间"),
        }
        for k, meta in biz_fields.items():
            g, s, vt, desc = meta
            cursor.execute(sql, (g, s, str(data.get(k) or ""), vt, desc))
        for k, meta in time_fields.items():
            g, s, vt, desc = meta
            cursor.execute(sql, (g, s, str(data.get(k) or ""), vt, desc))
        db.commit()
        return {"success": True}
    finally:
        cursor.close()
        db.close()


@router.get("/module-switches")
def get_module_switches():
    settings = _load_settings_dict().get("modules", {})
    return {
        "enable_reservation": settings.get("enable_reservation") == "1",
        "enable_member": settings.get("enable_member") == "1",
        "enable_training": settings.get("enable_training") == "1",
        "enable_products": settings.get("enable_products") == "1",
        "enable_finance": settings.get("enable_finance") == "1",
        "enable_notifications": settings.get("enable_notifications") == "1",
    }


@router.post("/module-switches")
def save_module_switches(data: Dict[str, Any]):
    db = get_db()
    cursor = db.cursor()
    try:
        sql = """
        INSERT INTO system_settings (group_key, setting_key, setting_value, value_type, description)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
        """
        for key in [
            "enable_reservation",
            "enable_member",
            "enable_training",
            "enable_products",
            "enable_finance",
            "enable_notifications",
        ]:
            cursor.execute(
                sql,
                ("modules", key, "1" if data.get(key) else "0", "bool", "模块开关"),
            )
        db.commit()
        return {"success": True}
    finally:
        cursor.close()
        db.close()


@router.post("/batch")
def save_batch_settings(
    data: Dict[str, Any],
    current_user=Depends(get_current_user)
):
    """
    批量保存所有系统设置
    
    接收前端提交的完整配置结构：
    {
      "basic": { "system_name": "...", ... },
      "business": { ... },
      "member": { ... },
      "order": { ... },
      "log": { ... },
      "member_levels": [...],
      "roles": [...]
    }
    """
    import json
    
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="数据格式不正确")
    
    db = get_db()
    cursor = db.cursor()
    try:
        sql = """
        INSERT INTO system_settings
          (group_key, setting_key, setting_value, value_type, description)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          setting_value = VALUES(setting_value)
        """
        
        changed_groups = []
        
        # 1. 处理简单配置组（basic, business, member, order, log）
        simple_groups = ["basic", "business", "member", "order", "log"]
        for group_key in simple_groups:
            if group_key not in data:
                continue
            group_values = data[group_key]
            if not isinstance(group_values, dict):
                continue
            
            changed_groups.append(group_key)
            for setting_key, value in group_values.items():
                value_str = str(value) if value is not None else ""
                cursor.execute(sql, (group_key, setting_key, value_str, "string", None))
        
        # 2. 处理会员等级配置
        if "member_levels" in data:
            member_levels = data["member_levels"]
            if isinstance(member_levels, list):
                changed_groups.append("member_levels")
                cursor.execute(
                    sql,
                    (
                        "member",
                        "member_levels_json",
                        json.dumps(member_levels, ensure_ascii=False),
                        "json",
                        "会员等级配置列表（JSON）",
                    ),
                )
        
        # 3. 处理角色配置
        if "roles" in data:
            roles = data["roles"]
            if isinstance(roles, list):
                changed_groups.append("roles")
                cursor.execute(
                    sql,
                    (
                        "permission",
                        "roles_json",
                        json.dumps(roles, ensure_ascii=False),
                        "json",
                        "角色与权限配置（JSON）",
                    ),
                )
        
        db.commit()
        
        # 写入操作日志
        try:
            write_operation_log(
                user_id=current_user.get("id"),
                username=current_user.get("username"),
                action="批量更新",
                module="系统设置",
                target_desc=f"更新了系统配置：{', '.join(changed_groups)}"
            )
        except Exception as e:
            print(f"写入操作日志失败: {e}")
        
        return {"success": True}
    finally:
        cursor.close()
        db.close()


@router.post("/member-config")
def save_member_config(payload: Dict[str, Any]):
    """
    保存会员等级与卡种配置
    """
    import json

    default_level = payload.get("default_level") or "normal"
    member_levels = payload.get("member_levels") or []
    card_packages = payload.get("card_packages") or []

    db = get_db()
    cursor = db.cursor()
    try:
        sql = """
        INSERT INTO system_settings (group_key, setting_key, setting_value, value_type, description)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
        """
        cursor.execute(sql, ("member", "default_level", default_level, "string", "新会员默认等级编码"))
        cursor.execute(
            sql,
            (
                "member",
                "member_levels_json",
                json.dumps(member_levels, ensure_ascii=False),
                "json",
                "会员等级配置列表（JSON）",
            ),
        )
        cursor.execute(
            sql,
            (
                "member",
                "card_packages_json",
                json.dumps(card_packages, ensure_ascii=False),
                "json",
                "会员卡套餐规则列表（JSON）",
            ),
        )
        db.commit()
        return {"success": True}
    finally:
        cursor.close()
        db.close()


@router.post("/data-clean")
def data_clean(password: str, current_user=Depends(get_current_user)):
    """
    数据清理/演示重置：清空业务流水但保留基础配置。
    需要管理员密码验证。
    清理表：attendances, enrollments, schedules, order_items, orders, court_reservations, member_transactions, product_sales, notifications, operation_logs
    """
    # 验证密码
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # 获取当前用户的密码哈希（从 users 表）
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=403, detail="管理员密码错误，操作已取消")
        
        # 按照正确的顺序删除（先删除子表，再删除父表）
        # 需要先禁用外键检查，清理后再启用
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        tables = [
            # 教培相关（子表优先）
            "attendances",           # 签到记录
            "enrollments",           # 报名记录
            "schedules",             # 排期
            # 订单相关（子表优先）
            "order_items",           # 订单项（子表）
            "orders",                # 订单（父表）
            # 场地预约
            "court_reservations",    # 场地预约
            # 其他业务数据
            "member_transactions",   # 会员流水
            "product_sales",         # 商品售卖
            "notifications",         # 通知
            "operation_logs",        # 操作日志
        ]
        
        for t in tables:
            try:
                cursor.execute(f"TRUNCATE TABLE {t}")
            except Exception as e:
                # 如果 TRUNCATE 失败，使用 DELETE（更慢但更安全）
                cursor.execute(f"DELETE FROM {t}")
        
        # 重新启用外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        db.commit()
        
        # 记录操作日志
        try:
            username = current_user.get("username") if isinstance(current_user, dict) else current_user.username
            write_operation_log(
                user_id=user_id,
                username=username or "",
                action="DATA_CLEAN",
                module="system",
                target_id=None,
                target_desc="数据格式化",
                detail={"cleaned_tables": tables},
                ip=None,
            )
        except Exception:
            pass
        
        return {"success": True, "message": "业务数据已清理（保留基础配置：会员、场地、商品、教练、学员、课程）"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据清理失败：{str(e)}")
    finally:
        cursor.close()
        db.close()


@router.post("/data-clean-all")
def data_clean_all(password: str, current_user=Depends(get_current_user)):
    """
    完全格式化：清空所有数据，包括基础配置（会员、场地、商品、教练、学员、课程等）。
    需要管理员密码验证。
    ⚠️ 极度危险操作，仅保留系统设置和管理员账号！
    """
    # 验证密码
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # 获取当前用户的密码哈希（从 users 表）
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=403, detail="管理员密码错误，操作已取消")
        
        # 禁用外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # 清空所有业务表和基础配置表
        tables = [
            # 教培相关（子表优先）
            "attendances",           # 签到记录
            "enrollments",           # 报名记录
            "schedules",             # 排期
            "courses",               # 课程（基础配置）
            "students",              # 学员（基础配置）
            "coaches",               # 教练（基础配置）
            # 订单相关（子表优先）
            "order_items",           # 订单项（子表）
            "orders",                # 订单（父表）
            # 场地预约
            "court_reservations",    # 场地预约
            "courts",                # 场地信息（基础配置）
            # 会员相关
            "member_transactions",   # 会员流水
            "members",               # 会员信息（基础配置）
            # 商品相关
            "product_sales",         # 商品售卖
            "products",              # 商品信息（基础配置）
            # 系统数据
            "notifications",         # 通知
            "operation_logs",        # 操作日志
            # 注意：不删除 employees（员工账号）和 system_settings（系统配置）
        ]
        
        for t in tables:
            try:
                cursor.execute(f"TRUNCATE TABLE {t}")
            except Exception:
                # 如果 TRUNCATE 失败，使用 DELETE（更慢但更安全）
                cursor.execute(f"DELETE FROM {t}")
        
        # 重新启用外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        db.commit()
        
        # 记录操作日志（如果日志表没被清空）
        try:
            username = current_user.get("username") if isinstance(current_user, dict) else current_user.username
            write_operation_log(
                user_id=user_id,
                username=username or "",
                action="DATA_CLEAN_ALL",
                module="system",
                target_id=None,
                target_desc="完全格式化",
                detail={"cleaned_tables": tables, "warning": "所有基础配置已清空"},
                ip=None,
            )
        except Exception:
            pass
        
        return {"success": True, "message": "所有数据已清空（仅保留系统设置和管理员账号）"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"完全格式化失败：{str(e)}")
    finally:
        cursor.close()
        db.close()
