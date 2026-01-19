# app/member_deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from .config import settings
from .database import get_db

# 会员端使用的 token 获取方式（和后台管理员的 tokenUrl 不同）
oauth2_scheme_member = OAuth2PasswordBearer(tokenUrl="/api/member/login")


def get_current_member(token: str = Depends(oauth2_scheme_member)):
    """
    从 Authorization: Bearer <token> 中解析当前会员信息
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证会员身份，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        # 我们约定：member 的 token 里面 user_type 必须是 "member"
        if payload.get("user_type") != "member":
            raise credentials_exception

        member_id: str | None = payload.get("sub")
        if member_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, name, phone, balance, status
            FROM members
            WHERE id = %s
            """,
            (member_id,),
        )
        member = cursor.fetchone()
        # 仅允许“正常”的会员登录
        if not member or member.get("status") != "正常":
            raise credentials_exception

        # balance 统一转成 float，方便前端展示
        member["balance"] = float(member.get("balance") or 0.0)
        return member
    finally:
        cursor.close()
        db.close()
