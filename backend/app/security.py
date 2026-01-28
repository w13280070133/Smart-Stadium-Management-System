"""
安全认证模块

提供密码哈希、JWT Token 生成和验证等安全相关功能。
使用 PBKDF2-SHA256 算法进行密码哈希，使用 JWT 进行用户身份认证。
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# 密码哈希上下文，使用 PBKDF2-SHA256 算法
# 该算法是 Python 标准库推荐的密码哈希算法，安全性高且性能良好
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希密码匹配
    
    使用 passlib 库进行安全的密码验证，防止时序攻击。
    
    Args:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的密码哈希值
        
    Returns:
        bool: 密码匹配返回 True，否则返回 False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码的哈希值
    
    将明文密码转换为不可逆的哈希值，用于安全存储。
    每次调用生成的哈希值都不同（因为使用了随机 salt）。
    
    Args:
        password: 明文密码
        
    Returns:
        str: 密码哈希值，格式：$pbkdf2-sha256$29000$<salt>$<hash>
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌
    
    生成包含用户信息的 JWT Token，用于后续请求的身份验证。
    Token 包含过期时间，过期后需要重新登录。
    
    Args:
        data: 要编码到 Token 中的数据，通常包含用户 ID 和角色信息
        expires_delta: Token 有效期，默认使用配置文件中的设置
        
    Returns:
        str: JWT Token 字符串
        
    示例:
        >>> create_access_token({"sub": "123", "role": "admin"})
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    to_encode = data.copy()
    # 设置 Token 过期时间（使用时区感知的 UTC 时间）
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    # 使用密钥签名生成 Token
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str):
    """
    解码并验证 JWT Token
    
    验证 Token 的签名和过期时间，返回其中包含的用户信息。
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        dict: Token 中包含的用户信息（payload）
        
    Raises:
        HTTPException: Token 无效或已过期时抛出 401 异常
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
