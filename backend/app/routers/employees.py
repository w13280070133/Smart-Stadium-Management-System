# app/routers/employees.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

from ..database import get_db
from ..deps import require_super_admin
from ..services.audit import write_operation_log
from ..services.notifications import create_admin_notifications

router = APIRouter(prefix="/employees", tags=["Employees"])


def _get_current_user_id_name(current_user):
    """
    兼容 current_user 可能是 dict 或 Pydantic 模型，统一取 id 和 username
    """
    if current_user is None:
        return None, None

    user_id = getattr(current_user, "id", None)
    username = getattr(current_user, "username", None)

    if isinstance(current_user, dict):
        user_id = user_id or current_user.get("id")
        username = username or current_user.get("username")

    return user_id, username


@router.get("", response_model=List[Dict[str, Any]])
def list_employees(current_user=Depends(require_super_admin)):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        sql = """
        SELECT e.id,
               e.user_id,
               e.name,
               e.phone,
               e.position,
               e.hire_date,
               e.is_active,
               u.username,
               u.role,
               u.is_active AS user_active
        FROM employees e
        JOIN users u ON e.user_id = u.id
        ORDER BY e.id DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


@router.post("")
def create_employee(data: Dict[str, Any], current_user=Depends(require_super_admin)):
    """
    创建员工：同时写 users + employees
    """
    required = ["name", "username", "password", "role"]
    for f in required:
        if f not in data or not data[f]:
            raise HTTPException(status_code=400, detail=f"缺少字段: {f}")

    from ..security import get_password_hash  # 避免循环引用，局部导入

    db = get_db()
    cursor = db.cursor()
    try:
        # 1) 创建用户账号
        sql_user = """
        INSERT INTO users (username, password_hash, role, phone, is_active)
        VALUES (%s, %s, %s, %s, 1)
        """
        cursor.execute(
            sql_user,
            (
                data["username"],
                get_password_hash(data["password"]),
                data["role"],
                data.get("phone"),
            ),
        )
        user_id = cursor.lastrowid

        # 2) 创建员工档案
        sql_emp = """
        INSERT INTO employees (user_id, name, phone, position, hire_date, is_active)
        VALUES (%s, %s, %s, %s, %s, 1)
        """
        cursor.execute(
            sql_emp,
            (
                user_id,
                data["name"],
                data.get("phone"),
                data.get("position"),
                data.get("hire_date"),
            ),
        )
        emp_id = cursor.lastrowid

        db.commit()

        # 记录操作日志
        uid, uname = _get_current_user_id_name(current_user)
        if uid and uname:
            write_operation_log(
                user_id=uid,
                username=uname,
                action="CREATE_EMPLOYEE",
                module="employee",
                target_id=emp_id,
                target_desc=data["name"],
                detail={"data": data},
            )
            try:
                create_admin_notifications(
                    title="新增员工",
                    content=f"管理员 {uname} 新增员工：{data['name']}（账号：{data['username']}）",
                    level="info",
                )
            except Exception:
                pass

        return {"id": emp_id}
    finally:
        cursor.close()
        db.close()


@router.put("/{emp_id}")
def update_employee(emp_id: int, data: Dict[str, Any], current_user=Depends(require_super_admin)):
    """
    更新员工信息 / 启用禁用 / 重置密码
    - 前端传 { is_active: true/false } 时，只切换启用状态
    - 传完整信息时，更新员工 + 用户角色/电话/密码
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # 查出原始数据
        cursor.execute("SELECT * FROM employees WHERE id = %s", (emp_id,))
        emp = cursor.fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail="员工不存在")

        cursor.execute("SELECT * FROM users WHERE id = %s", (emp["user_id"],))
        user = cursor.fetchone()

        # 只传 is_active，说明是启用/禁用操作
        only_toggle_active = set(data.keys()) == {"is_active"}

        if only_toggle_active:
            is_active = 1 if data.get("is_active") else 0
            cursor.execute(
                "UPDATE employees SET is_active = %s WHERE id = %s",
                (is_active, emp_id),
            )
            cursor.execute(
                "UPDATE users SET is_active = %s WHERE id = %s",
                (is_active, emp["user_id"]),
            )
        else:
            # 其他字段做“覆盖式 + 保底用原值”，避免 name 变成 NULL
            name = data.get("name", emp["name"])
            phone = data.get("phone", emp.get("phone"))
            position = data.get("position", emp.get("position"))
            hire_date = data.get("hire_date", emp.get("hire_date"))
            is_active = 1 if data.get("is_active", emp["is_active"]) else 0

            cursor.execute(
                """
                UPDATE employees
                SET name=%s, phone=%s, position=%s, hire_date=%s, is_active=%s
                WHERE id=%s
                """,
                (name, phone, position, hire_date, is_active, emp_id),
            )

            if user:
                new_role = data.get("role", user["role"])
                cursor.execute(
                    """
                    UPDATE users
                    SET phone=%s, role=%s, is_active=%s
                    WHERE id=%s
                    """,
                    (phone, new_role, is_active, emp["user_id"]),
                )

                # 重置密码
                reset_password = data.get("reset_password")
                if reset_password:
                    from ..security import get_password_hash
                    cursor.execute(
                        "UPDATE users SET password_hash=%s WHERE id=%s",
                        (get_password_hash(reset_password), emp["user_id"]),
                    )

        db.commit()

        # 日志
        uid, uname = _get_current_user_id_name(current_user)
        if uid and uname:
            write_operation_log(
                user_id=uid,
                username=uname,
                action="UPDATE_EMPLOYEE",
                module="employee",
                target_id=emp_id,
                target_desc=data.get("name") or emp["name"],
                detail={"data": data},
            )
            try:
                create_admin_notifications(
                    title="员工信息变更",
                    content=f"管理员 {uname} 更新员工：{data.get('name') or emp['name']}",
                    level="info",
                )
            except Exception:
                pass

        return {"success": True}
    finally:
        cursor.close()
        db.close()


@router.delete("/{emp_id}")
def delete_employee(emp_id: int, current_user=Depends(require_super_admin)):
    """
    删除员工档案 + 对应用户账号，并记录操作日志
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM employees WHERE id = %s", (emp_id,))
        emp = cursor.fetchone()
        if not emp:
            raise HTTPException(status_code=404, detail="员工不存在")

        cursor.execute("SELECT * FROM users WHERE id = %s", (emp["user_id"],))
        user = cursor.fetchone()

        cursor.execute("DELETE FROM employees WHERE id = %s", (emp_id,))
        if user:
            cursor.execute("DELETE FROM users WHERE id = %s", (emp["user_id"],))

        db.commit()

        # 日志
        uid, uname = _get_current_user_id_name(current_user)
        if uid and uname:
            write_operation_log(
                user_id=uid,
                username=uname,
                action="DELETE_EMPLOYEE",
                module="employee",
                target_id=emp_id,
                target_desc=emp.get("name"),
                detail=None,
            )
            try:
                create_admin_notifications(
                    title="删除员工",
                    content=f"管理员 {uname} 删除员工：{emp.get('name')}",
                    level="warning",
                )
            except Exception:
                pass

        return {"success": True}
    finally:
        cursor.close()
        db.close()
