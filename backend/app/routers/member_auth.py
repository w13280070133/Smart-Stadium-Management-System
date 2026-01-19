# backend/app/routers/member_auth.py
from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Any, Dict

from ..database import get_db
from ..security import verify_password, create_access_token, decode_access_token
from .members import normalize_member

router = APIRouter(prefix="/member-auth", tags=["MemberAuth"])


# --------- Pydantic 模型 ---------
class MemberLoginRequest(BaseModel):
    phone: str
    password: str


class TokenWithMember(BaseModel):
    access_token: str
    token_type: str = "bearer"
    member: Dict[str, Any]


# --------- 内部公共登录逻辑 ---------
def _login_core(phone: str, password: str) -> Dict[str, Any]:
    phone = (phone or "").strip()
    password = (password or "").strip()

    if not phone or not password:
        raise HTTPException(status_code=400, detail="手机号和密码不能为空")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, name, phone, gender, birthday,
                   level, status, remark,
                   balance, total_spent,
                   login_password_hash,
                   created_at
            FROM members
            WHERE phone = %s
            """,
            (phone,),
        )
        member = cursor.fetchone()

        if not member:
            # 不区分是手机号不存在还是密码错
            raise HTTPException(status_code=401, detail="手机号或密码错误")

        if member.get("status") != "正常":
            raise HTTPException(status_code=403, detail="会员状态异常，无法登录")

        if not member.get("login_password_hash"):
            raise HTTPException(status_code=401, detail="该会员尚未设置登录密码，请联系前台")

        if not verify_password(password, member["login_password_hash"]):
            raise HTTPException(status_code=401, detail="手机号或密码错误")

        payload = {
            "sub": str(member["id"]),
            "member_id": member["id"],
            "role": "member",
        }
        token = create_access_token(payload)

        member_data = normalize_member(member)
        return {
            "access_token": token,
            "token_type": "bearer",
            "member": member_data,
        }
    finally:
        cursor.close()
        db.close()


# --------- 1. JSON 方式登录（备用） ---------
@router.post("/login", response_model=TokenWithMember)
def member_login(data: MemberLoginRequest):
    return _login_core(data.phone, data.password)


# --------- 2. /token 表单登录（前端现在用的这个） ---------
@router.post("/token", response_model=TokenWithMember)
def member_login_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    兼容 axios 以 form-data 方式提交：
    username = 手机号, password = 密码
    """
    return _login_core(form_data.username, form_data.password)


# --------- 3. 从 token 获取当前会员 ---------
def get_current_member(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证信息无效")

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)

    if payload.get("role") != "member":
        raise HTTPException(status_code=403, detail="无权访问")

    member_id = payload.get("member_id") or payload.get("sub")
    if not member_id:
        raise HTTPException(status_code=401, detail="Token 中缺少会员信息")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, name, phone, gender, birthday,
                   level, status, remark,
                   balance, total_spent,
                   created_at
            FROM members
            WHERE id = %s
            """,
            (member_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="会员不存在")

        return normalize_member(row)
    finally:
        cursor.close()
        db.close()


# --------- 4. 会员端「我的资料」 ---------
@router.get("/me")
def get_me(current_member=Depends(get_current_member)):
    return current_member
