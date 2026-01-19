from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from ..deps import get_current_user
from ..services.notifications import (
    list_notifications,
    mark_notification_read,
    create_notification,
    mark_all_notifications_read,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def get_my_notifications(
    page: int = 1,
    page_size: int = 20,
    is_read: Optional[int] = None,  # 0 未读 / 1 已读，其他值表示全部
    level: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """
    获取当前登录用户的通知列表
    GET /api/notifications
    """
    uid = current_user["id"] if isinstance(current_user, dict) else current_user.id
    return list_notifications(
        user_id=uid,
        is_read=is_read if is_read in (0, 1) else None,
        level=level,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )


@router.post("")
def create_manual_notification(
    data: dict,
    current_user=Depends(get_current_user),
):
    """
    手工创建一条通知（只允许 admin 用于测试）
    body: { user_id, title, content, level? }
    """
    role = current_user["role"] if isinstance(current_user, dict) else getattr(current_user, "role", None)
    if role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以创建通知")

    target_user_id = data.get("user_id")
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    level = (data.get("level") or "info").strip() or "info"

    if not target_user_id or not title or not content:
        raise HTTPException(status_code=400, detail="user_id / title / content 不能为空")

    nid = create_notification(
        user_id=int(target_user_id),
        title=title,
        content=content,
        level=level,
    )
    return {"id": nid}


@router.put("/{notif_id}/read")
def set_notification_read(
    notif_id: int,
    current_user=Depends(get_current_user),
):
    """
    将一条通知标记为已读
    """
    uid = current_user["id"] if isinstance(current_user, dict) else current_user.id
    ok = mark_notification_read(user_id=uid, notif_id=notif_id)
    if not ok:
        raise HTTPException(status_code=404, detail="通知不存在")
    return {"success": True}


@router.put("/read-all")
def set_all_notification_read(
    current_user=Depends(get_current_user),
):
    """
    将当前用户所有通知标记为已读
    """
    uid = current_user["id"] if isinstance(current_user, dict) else current_user.id
    count = mark_all_notifications_read(user_id=uid)
    return {"success": True, "count": count}
