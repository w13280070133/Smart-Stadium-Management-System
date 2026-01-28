"""
教培签到管理模块

提供学员签到、查询签到记录、撤销签到等功能。
签到是教培模块课时消耗的唯一合法方式，确保课时管理的严格性。

核心业务规则：
1. 签到时必须扣减报名的剩余课时
2. 只有"在读"状态的报名才能签到
3. 剩余课时必须大于0才能签到
4. 删除签到记录时需要恢复课时
5. 使用数据库事务确保数据一致性
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any, Optional
from datetime import datetime
from ..database import get_db
from ..deps import require_action
from ..services.audit import write_operation_log
from ..services.notifications import create_admin_notifications

router = APIRouter(prefix="/training/attendances", tags=["Training Attendances"])


@router.get("")
def list_attendances(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    enrollment_id: Optional[int] = None,
    schedule_id: Optional[int] = None,
    student_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user=Depends(require_action("attendance.view")),
):
    """
    查询签到记录列表
    
    支持多条件筛选：
    - 按报名记录筛选（enrollment_id）
    - 按排期筛选（schedule_id）
    - 按学员筛选（student_id）
    - 按日期范围筛选（date_from, date_to）
    
    返回信息包括：
    - 签到记录基本信息
    - 学员姓名和联系方式
    - 课程名称和类型
    - 签到后的剩余课时
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        conditions = []
        params = []

        if enrollment_id:
            conditions.append("a.enrollment_id = %s")
            params.append(enrollment_id)

        if schedule_id:
            conditions.append("a.schedule_id = %s")
            params.append(schedule_id)

        if student_id:
            conditions.append("e.student_id = %s")
            params.append(student_id)

        if date_from:
            conditions.append("sch.date >= %s")
            params.append(date_from)

        if date_to:
            conditions.append("sch.date <= %s")
            params.append(date_to)

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        # 查询总数
        count_sql = f"""
            SELECT COUNT(*) as total
            FROM attendances a
            JOIN enrollments e ON a.enrollment_id = e.id
            JOIN schedules sch ON a.schedule_id = sch.id
            {where_clause}
        """
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # 查询列表
        offset = (page - 1) * page_size
        list_sql = f"""
            SELECT a.*,
                   s.name as student_name,
                   s.phone as student_phone,
                   c.name as course_name,
                   c.type as course_type,
                   e.remaining_lessons,
                   sch.date as schedule_date,
                   sch.start_time,
                   sch.end_time
            FROM attendances a
            JOIN enrollments e ON a.enrollment_id = e.id
            JOIN students s ON e.student_id = s.id
            JOIN courses c ON e.course_id = c.id
            JOIN schedules sch ON a.schedule_id = sch.id
            {where_clause}
            ORDER BY a.attended_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params + [page_size, offset]))
        items = cursor.fetchall() or []

        return {"total": total, "items": items, "page": page, "page_size": page_size}
    finally:
        cursor.close()
        db.close()


@router.get("/{attendance_id}")
def get_attendance(
    attendance_id: int,
    current_user=Depends(require_action("attendance.view")),
):
    """
    获取签到记录详情
    
    返回完整的签到信息，包括：
    - 签到记录基本信息
    - 学员详细信息
    - 课程和排期信息
    - 当前剩余课时
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT a.*,
                   s.name as student_name,
                   s.phone as student_phone,
                   c.name as course_name,
                   c.type as course_type,
                   e.remaining_lessons,
                   e.total_lessons,
                   sch.date as schedule_date,
                   sch.start_time,
                   sch.end_time
            FROM attendances a
            JOIN enrollments e ON a.enrollment_id = e.id
            JOIN students s ON e.student_id = s.id
            JOIN courses c ON e.course_id = c.id
            JOIN schedules sch ON a.schedule_id = sch.id
            WHERE a.id = %s
        """,
            (attendance_id,),
        )
        attendance = cursor.fetchone()
        if not attendance:
            raise HTTPException(status_code=404, detail="签到记录不存在")

        return attendance
    finally:
        cursor.close()
        db.close()


@router.post("")
def create_attendance(
    data: Dict[str, Any],
    request: Request,
    current_user=Depends(require_action("attendance.create")),
):
    """
    创建签到记录（学员签到）
    
    这是教培模块课时消耗的唯一合法方式。签到时会自动扣减报名的剩余课时。
    
    业务流程：
    1. 验证报名记录存在且状态为"在读"
    2. 验证剩余课时大于0
    3. 验证排期存在且状态为"正常"
    4. 检查是否重复签到（同一报名同一排期只能签到一次）
    5. 扣减剩余课时（-1）
    6. 创建签到记录
    7. 如果剩余课时为0，更新报名状态为"已结课"
    
    关键业务规则：
    - 使用数据库事务确保课时扣减和签到记录创建的原子性
    - 只有"在读"状态的报名才能签到
    - 剩余课时为0时自动标记报名为"已结课"
    - 签到时间自动记录为当前时间
    
    Args:
        data: 签到信息，必须包含：
            - enrollment_id: 报名记录 ID
            - schedule_id: 排期 ID
            - remark: 备注（可选）
        request: 请求对象
        current_user: 当前用户
        
    Returns:
        dict: {
            "id": 签到记录 ID,
            "remaining_lessons": 签到后的剩余课时,
            "message": "签到成功"
        }
        
    Raises:
        HTTPException(400): 缺少必填字段、报名状态异常、课时不足、重复签到
        HTTPException(404): 报名或排期不存在
    """
    required = ["enrollment_id", "schedule_id"]
    for field in required:
        if field not in data or data[field] is None:
            raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor2 = db.cursor()
    try:
        enrollment_id = int(data["enrollment_id"])
        schedule_id = int(data["schedule_id"])

        db.start_transaction()

        # 验证报名记录（使用行锁防止并发签到导致课时错误）
        cursor.execute(
            """
            SELECT e.*, s.name as student_name, c.name as course_name
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            JOIN courses c ON e.course_id = c.id
            WHERE e.id = %s
            FOR UPDATE
        """,
            (enrollment_id,),
        )
        enrollment = cursor.fetchone()
        if not enrollment:
            raise HTTPException(status_code=404, detail="报名记录不存在")

        if enrollment["status"] != "在读":
            raise HTTPException(
                status_code=400, detail=f"报名状态为 {enrollment['status']}，无法签到"
            )

        remaining = enrollment["remaining_lessons"]
        if remaining <= 0:
            raise HTTPException(status_code=400, detail="剩余课时不足，无法签到")

        # 验证排期
        cursor.execute(
            "SELECT * FROM schedules WHERE id = %s", (schedule_id,)
        )
        schedule = cursor.fetchone()
        if not schedule:
            raise HTTPException(status_code=404, detail="排期不存在")

        if schedule.get("status") not in ["正常", None]:
            raise HTTPException(status_code=400, detail="该排期无法签到")

        # 检查重复签到
        cursor.execute(
            """
            SELECT COUNT(*) as cnt FROM attendances
            WHERE enrollment_id = %s AND schedule_id = %s
        """,
            (enrollment_id, schedule_id),
        )
        if cursor.fetchone()["cnt"] > 0:
            raise HTTPException(status_code=400, detail="该学员已在此排期签到，请勿重复签到")

        # 创建签到记录
        attend_sql = """
            INSERT INTO attendances (
                enrollment_id, schedule_id, attended_at, status, remark
            ) VALUES (%s, %s, %s, %s, %s)
        """
        now = datetime.now()
        cursor2.execute(
            attend_sql,
            (
                enrollment_id,
                schedule_id,
                now,
                "已签到",
                data.get("remark"),
            ),
        )
        attendance_id = cursor2.lastrowid

        # 扣减课时
        new_remaining = remaining - 1
        cursor2.execute(
            "UPDATE enrollments SET remaining_lessons = %s WHERE id = %s",
            (new_remaining, enrollment_id),
        )

        # 如果课时用完，更新报名状态为"已结课"
        if new_remaining == 0:
            cursor2.execute(
                "UPDATE enrollments SET status = %s WHERE id = %s",
                ("已结课", enrollment_id),
            )

        db.commit()

        # 记录操作日志
        try:
            uid = current_user["id"] if isinstance(current_user, dict) else current_user.id
            uname = current_user["username"] if isinstance(current_user, dict) else current_user.username
            write_operation_log(
                user_id=uid,
                username=uname,
                action="签到",
                module="课程签到",
                target_id=attendance_id,
                target_desc=f"{enrollment['student_name']} 签到 {enrollment['course_name']}",
                detail={
                    "remaining_lessons": new_remaining,
                    "schedule_id": schedule_id,
                    "status": "已结课" if new_remaining == 0 else "在读",
                },
                ip=request.client.host if request.client else None,
            )
            
            # 发送管理员通知
            create_admin_notifications(
                title="学员签到",
                content=f"{enrollment['student_name']} 签到成功，剩余 {new_remaining} 节课",
                level="info",
            )
        except Exception:
            pass

        return {
            "id": attendance_id,
            "remaining_lessons": new_remaining,
            "status": "已结课" if new_remaining == 0 else "在读",
            "message": "签到成功" + ("，课程已结课" if new_remaining == 0 else ""),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"签到失败: {str(e)}")
    finally:
        cursor.close()
        cursor2.close()
        db.close()


@router.delete("/{attendance_id}")
def delete_attendance(
    attendance_id: int,
    request: Request,
    current_user=Depends(require_action("attendance.delete")),
):
    """
    删除签到记录（撤销签到）
    
    撤销签到时需要恢复报名的剩余课时，并更新报名状态（如果需要）。
    
    业务流程：
    1. 查询签到记录
    2. 查询关联的报名记录（使用行锁）
    3. 恢复剩余课时（+1）
    4. 如果报名状态是"已结课"，恢复为"在读"
    5. 删除签到记录
    
    关键业务规则：
    - 使用数据库事务确保课时恢复和删除操作的原子性
    - 使用 FOR UPDATE 行锁防止并发修改
    - 如果报名已结课，撤销签到后自动恢复为"在读"状态
    
    Args:
        attendance_id: 签到记录 ID
        request: 请求对象
        current_user: 当前用户
        
    Returns:
        dict: {
            "message": "签到记录已删除，课时已恢复"
        }
        
    Raises:
        HTTPException(404): 签到记录或报名记录不存在
        HTTPException(500): 删除失败
        
    注意：
        删除签到记录是敏感操作，建议只在特殊情况下使用。
        所有删除操作都会记录到操作日志中，便于追溯。
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor2 = db.cursor()
    try:
        db.start_transaction()

        # 查询签到记录
        cursor.execute(
            """
            SELECT a.*, s.name as student_name, c.name as course_name
            FROM attendances a
            JOIN enrollments e ON a.enrollment_id = e.id
            JOIN students s ON e.student_id = s.id
            JOIN courses c ON e.course_id = c.id
            WHERE a.id = %s
        """,
            (attendance_id,),
        )
        attendance = cursor.fetchone()
        if not attendance:
            raise HTTPException(status_code=404, detail="签到记录不存在")

        enrollment_id = attendance["enrollment_id"]

        # 查询报名记录（使用行锁）
        cursor.execute(
            "SELECT * FROM enrollments WHERE id = %s FOR UPDATE",
            (enrollment_id,),
        )
        enrollment = cursor.fetchone()
        if not enrollment:
            raise HTTPException(status_code=404, detail="报名记录不存在")

        # 恢复课时
        new_remaining = enrollment["remaining_lessons"] + 1
        cursor2.execute(
            "UPDATE enrollments SET remaining_lessons = %s WHERE id = %s",
            (new_remaining, enrollment_id),
        )

        # 如果原状态是"已结课"，恢复为"在读"
        if enrollment["status"] == "已结课":
            cursor2.execute(
                "UPDATE enrollments SET status = %s WHERE id = %s",
                ("在读", enrollment_id),
            )

        # 删除签到记录
        cursor2.execute("DELETE FROM attendances WHERE id = %s", (attendance_id,))

        db.commit()

        # 记录操作日志
        try:
            uid = current_user["id"] if isinstance(current_user, dict) else current_user.id
            uname = current_user["username"] if isinstance(current_user, dict) else current_user.username
            write_operation_log(
                user_id=uid,
                username=uname,
                action="删除签到",
                module="课程签到",
                target_id=attendance_id,
                target_desc=f"{attendance['student_name']} 撤销签到 {attendance['course_name']}",
                detail={
                    "restored_lessons": new_remaining,
                    "status": "在读" if enrollment["status"] == "已结课" else enrollment["status"],
                },
                ip=request.client.host if request.client else None,
            )
            
            create_admin_notifications(
                title="撤销签到",
                content=f"{attendance['student_name']} 签到已撤销，课时已恢复至 {new_remaining} 节",
                level="warning",
            )
        except Exception:
            pass

        return {"message": "签到记录已删除，课时已恢复"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    finally:
        cursor.close()
        cursor2.close()
        db.close()


@router.put("/{attendance_id}")
def update_attendance(
    attendance_id: int,
    data: Dict[str, Any],
    request: Request,
    current_user=Depends(require_action("attendance.edit")),
):
    """
    更新签到记录备注
    
    只允许更新签到记录的备注信息，不允许修改报名ID、排期ID等关键信息。
    如果需要修改这些信息，应该删除原签到记录并重新创建。
    
    Args:
        attendance_id: 签到记录 ID
        data: 更新信息，可包含：
            - remark: 备注
        request: 请求对象
        current_user: 当前用户
        
    Returns:
        dict: {"message": "更新成功"}
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor2 = db.cursor()
    try:
        # 验证签到记录存在
        cursor.execute("SELECT * FROM attendances WHERE id = %s", (attendance_id,))
        attendance = cursor.fetchone()
        if not attendance:
            raise HTTPException(status_code=404, detail="签到记录不存在")

        # 只允许更新备注
        remark = data.get("remark", attendance.get("remark"))
        cursor2.execute(
            "UPDATE attendances SET remark = %s WHERE id = %s",
            (remark, attendance_id),
        )
        db.commit()

        return {"message": "更新成功"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
    finally:
        cursor.close()
        cursor2.close()
        db.close()





