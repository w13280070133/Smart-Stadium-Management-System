"""
依赖注入模块

提供用户认证、权限控制等依赖注入函数，用于 FastAPI 路由的权限验证。

核心功能：
1. 管理端用户认证（get_current_user）
2. 会员端用户认证（get_current_member）  
3. 基于角色的访问控制（RBAC）
4. 操作权限验证（require_action）

权限控制说明：
- 角色配置存储在 system_settings 表中
- 支持菜单权限（menus）和操作权限（actions）
- 通配符 "*" 表示拥有所有权限
- 使用缓存机制减少数据库查询
"""
from datetime import datetime
from typing import Dict, Any, List
import json
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .config import settings
from .database import get_db
from .security import decode_access_token

# ========== 管理端（后台）认证 ==========
# OAuth2 密码模式的 Bearer Token 认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    获取当前登录的管理端用户信息
    
    从 JWT Token 中解析用户 ID，然后从数据库查询用户详细信息。
    这是管理端所有需要认证的接口的依赖函数。
    
    Args:
        token: JWT Token 字符串（由 FastAPI 自动从 Authorization header 提取）
        
    Returns:
        dict: 用户信息，包含 id, username, role, is_active
        
    Raises:
        HTTPException(401): Token 无效或用户不存在/被禁用
    """
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效 token")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, username, role, is_active FROM users WHERE id = %s",
            (user_id,),
        )
        user = cursor.fetchone()
        if not user or not user.get("is_active"):
            raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
        return user
    finally:
        cursor.close()
        db.close()


def require_super_admin(current_user=Depends(get_current_user)):
    """
    要求超级管理员权限
    
    用于需要最高权限的操作，如系统设置、数据格式化等。
    只有角色为 "super_admin" 或 "admin" 的用户才能通过此检查。
    注意：为了区分，建议使用 "super_admin" 作为超级管理员角色代码。
    
    Args:
        current_user: 当前用户信息（由 get_current_user 注入）
        
    Returns:
        dict: 用户信息
        
    Raises:
        HTTPException(403): 用户不是超级管理员
    """
    role = current_user.get("role") or ""
    if role not in ("super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足，需要超级管理员权限")
    return current_user


# ========== 会员端认证 ==========
member_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/member/auth/login")


def get_current_member(token: str = Depends(member_oauth2_scheme)) -> Dict[str, Any]:
    """
    获取当前登录的会员信息
    
    从 JWT Token 中解析会员 ID，查询数据库获取会员详细信息。
    验证会员身份和状态，确保会员可以正常使用系统。
    
    Args:
        token: JWT Token 字符串（从 Authorization header 提取）
        
    Returns:
        dict: 会员信息，包含 id, name, phone, status, balance
        
    Raises:
        HTTPException(401): Token 无效或会员不存在
        HTTPException(400): 会员状态异常，无法使用服务
    """
    payload = decode_access_token(token)
    scope = payload.get("scope")
    if scope != "member":
        raise HTTPException(status_code=401, detail="无效的会员 token")

    member_id = payload.get("sub")
    if not member_id:
        raise HTTPException(status_code=401, detail="无效 token")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, name, phone, status, balance
            FROM members
            WHERE id = %s
            """,
            (member_id,),
        )
        member = cursor.fetchone()
        if not member:
            raise HTTPException(status_code=401, detail="会员不存在")

        if member.get("status") not in ("正常", "active", 1, "1"):
            raise HTTPException(status_code=400, detail="会员状态异常")

        # 统一一下字段类型
        member["balance"] = float(member.get("balance") or 0.0)
        return member
    finally:
        cursor.close()
        db.close()


# ========== 基于角色的访问控制（RBAC）==========
# 角色配置缓存，避免频繁查询数据库
# 缓存有效期 60 秒，60 秒后自动重新加载最新配置
_roles_cache: Dict[str, Any] = {"data": None, "ts": 0}


def _load_roles_config() -> List[Dict[str, Any]]:
    """
    加载角色权限配置
    
    从数据库 system_settings 表读取角色配置（JSON 格式）。
    使用 60 秒缓存减少数据库查询，提高性能。
    
    角色配置示例：
    [
        {
            "code": "admin",
            "name": "管理员",
            "menus": ["*"],
            "actions": ["*"],
            "data_scope": "all"
        },
        {
            "code": "staff",
            "name": "普通员工",
            "menus": ["dashboard", "members"],
            "actions": ["view", "create"],
            "data_scope": "own"
        }
    ]
    
    Returns:
        list: 角色配置列表，如果配置不存在则返回默认配置
    """
    now = time.time()
    if _roles_cache["data"] and now - _roles_cache["ts"] < 60:
        return _roles_cache["data"]
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT setting_value
            FROM system_settings
            WHERE group_key = 'permission' AND setting_key = 'roles_json'
            """
        )
        row = cursor.fetchone()
        if row and row.get("setting_value"):
            try:
                roles = json.loads(row["setting_value"])
            except Exception:
                roles = []
        else:
            roles = []
        if not roles:
            roles = [
                {"code": "admin", "name": "管理员", "menus": ["*"], "actions": ["*"], "data_scope": "all"},
                {"code": "staff", "name": "员工", "menus": ["dashboard"], "actions": ["view"], "data_scope": "own"},
            ]
        _roles_cache["data"] = roles
        _roles_cache["ts"] = now
        return roles
    finally:
        cursor.close()
        db.close()


def _user_has_action(user: Dict[str, Any], action_code: str) -> bool:
    """
    检查用户是否拥有指定操作权限
    
    根据用户角色查找对应的权限配置，判断是否拥有指定的操作权限。
    权限判断规则：
    1. 如果 actions 包含 "*"，表示拥有所有权限
    2. 如果 actions 包含指定的 action_code，表示拥有该权限
    3. 否则无权限
    
    Args:
        user: 用户信息，包含 role 字段
        action_code: 操作权限码，如 "member.create"、"reservation.delete" 等
        
    Returns:
        bool: 有权限返回 True，否则返回 False
    """
    role = user.get("role") or ""
    roles = _load_roles_config()
    # 查找用户角色对应的权限配置
    role_conf = next((r for r in roles if r.get("code") == role), None)
    actions = role_conf.get("actions") if role_conf else ["*"]
    if not isinstance(actions, list) or not actions:
        actions = ["*"]
    actions = [str(a) for a in actions]
    # 检查是否拥有全部权限或指定权限
    return "*" in actions or action_code in actions


def require_action(action_code: str):
    """
    创建操作权限检查依赖
    
    这是一个依赖工厂函数，返回一个权限检查依赖。
    使用方式：在路由装饰器中添加 Depends(require_action("member.create"))
    
    示例：
        @router.post("/members", dependencies=[Depends(require_action("member.create"))])
        def create_member(...):
            pass
    
    Args:
        action_code: 操作权限码
        
    Returns:
        function: 依赖函数，用于 FastAPI 的 Depends
        
    Raises:
        HTTPException(403): 用户没有指定操作权限时抛出
    """
    def dependency(current_user=Depends(get_current_user)):
        if not _user_has_action(current_user, action_code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无操作权限")
        return current_user

    return dependency
