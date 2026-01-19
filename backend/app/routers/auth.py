"""
管理端认证模块

提供管理员登录认证功能，验证用户名和密码，生成 JWT Token。
所有登录尝试（成功或失败）都会记录到登录日志表，用于安全审计。
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

from ..database import get_db
from ..security import verify_password, create_access_token
from ..config import settings
from ..services.audit import write_login_log

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token")
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    管理端用户登录接口
    
    验证用户名和密码，成功后返回 JWT Token 和用户信息。
    使用 OAuth2 密码模式，符合标准的身份认证流程。
    
    安全特性：
    1. 密码使用哈希验证，不传输明文
    2. 所有登录尝试都记录日志（包括失败的）
    3. 错误提示模糊化，避免暴露用户是否存在
    4. 记录客户端 IP 和 User-Agent，便于安全审计
    
    业务流程：
    1. 查询用户信息
    2. 验证账号状态（是否存在、是否禁用）
    3. 验证密码
    4. 生成 JWT Token（包含用户 ID 和角色）
    5. 记录登录日志
    6. 返回 Token 和用户基本信息
    
    Args:
        request: 请求对象，用于获取客户端 IP
        form_data: OAuth2 表单数据，包含 username 和 password
        
    Returns:
        dict: {
            "access_token": JWT Token 字符串,
            "token_type": "bearer",
            "user": {用户基本信息}
        }
        
    Raises:
        HTTPException(400): 用户名或密码错误、账号被禁用
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        sql = "SELECT id, username, password_hash, role, is_active FROM users WHERE username = %s"
        cursor.execute(sql, (form_data.username,))
        user = cursor.fetchone()

        # 获取客户端 IP 和 User-Agent
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

        # 用户不存在
        if not user:
            write_login_log(
                user_id=0,
                username=form_data.username,
                success=False,
                ip=client_ip,
                user_agent=user_agent,
                message="用户不存在",
            )
            # 对外仍然保持模糊提示，避免暴露用户信息
            raise HTTPException(status_code=400, detail="用户名或密码错误")

        # 账号被禁用
        if not user["is_active"]:
            write_login_log(
                user_id=user["id"],
                username=user["username"],
                success=False,
                ip=client_ip,
                user_agent=user_agent,
                message="账号已被禁用",
            )
            raise HTTPException(status_code=400, detail="用户不存在或已被禁用")

        # 密码错误
        if not verify_password(form_data.password, user["password_hash"]):
            write_login_log(
                user_id=user["id"],
                username=user["username"],
                success=False,
                ip=client_ip,
                user_agent=user_agent,
                message="密码错误",
            )
            raise HTTPException(status_code=400, detail="用户名或密码错误")

        # 登录成功：生成 token
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": str(user["id"]), "role": user["role"]},
            expires_delta=access_token_expires,
        )

        # 记录成功登录日志
        write_login_log(
            user_id=user["id"],
            username=user["username"],
            success=True,
            ip=client_ip,
            user_agent=user_agent,
            message="登录成功",
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
            },
        }
    finally:
        cursor.close()
        db.close()
