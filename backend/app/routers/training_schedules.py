# backend/app/routers/training_schedules.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime, date, time as dt_time
from ..database import get_db
from ..deps import require_action

router = APIRouter(prefix="/training/schedules", tags=["Training Schedules"])


@router.get("")
def list_schedules(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    course_id: Optional[int] = None,
    coach_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    current_user=Depends(require_action("schedule.view")),
):
    """
    获取排期列表
    - 支持按课程、教练、日期范围、状态筛选
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        conditions = []
        params = []

        if course_id:
            conditions.append("sch.course_id = %s")
            params.append(course_id)

        if coach_id:
            conditions.append("sch.coach_id = %s")
            params.append(coach_id)

        if date_from:
            conditions.append("sch.date >= %s")
            params.append(date_from)

        if date_to:
            conditions.append("sch.date <= %s")
            params.append(date_to)

        if status:
            conditions.append("sch.status = %s")
            params.append(status)

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM schedules sch{where_clause}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # 查询列表
        offset = (page - 1) * page_size
        list_sql = f"""
            SELECT sch.*,
                   c.name as course_name,
                   c.type as course_type,
                   coach.name as coach_name,
                   (SELECT COUNT(*) FROM attendances WHERE schedule_id = sch.id) as attendance_count
            FROM schedules sch
            LEFT JOIN courses c ON sch.course_id = c.id
            LEFT JOIN coaches coach ON sch.coach_id = coach.id
            {where_clause}
            ORDER BY sch.date DESC, sch.start_time DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params + [page_size, offset]))
        items = cursor.fetchall() or []

        return {"total": total, "items": items, "page": page, "page_size": page_size}
    finally:
        cursor.close()
        db.close()


@router.get("/{schedule_id}")
def get_schedule(
    schedule_id: int,
    current_user=Depends(require_action("schedule.view")),
):
    """获取排期详情（包含签到情况）"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT sch.*,
                   c.name as course_name,
                   c.type as course_type,
                   coach.name as coach_name
            FROM schedules sch
            LEFT JOIN courses c ON sch.course_id = c.id
            LEFT JOIN coaches coach ON sch.coach_id = coach.id
            WHERE sch.id = %s
        """,
            (schedule_id,),
        )
        schedule = cursor.fetchone()
        if not schedule:
            raise HTTPException(status_code=404, detail="排期不存在")

        # 获取签到记录
        cursor.execute(
            """
            SELECT a.*, s.name as student_name, e.remaining_lessons
            FROM attendances a
            JOIN enrollments e ON a.enrollment_id = e.id
            JOIN students s ON e.student_id = s.id
            WHERE a.schedule_id = %s
            ORDER BY a.attended_at
        """,
            (schedule_id,),
        )
        attendances = cursor.fetchall() or []

        schedule["attendances"] = attendances
        return schedule
    finally:
        cursor.close()
        db.close()


@router.post("")
def create_schedule(
    data: Dict[str, Any],
    current_user=Depends(require_action("schedule.create")),
):
    """
    创建排期
    - 检查教练时间冲突
    - 检查场地时间冲突（如果提供了 venue）
    """
    required = ["course_id", "date", "start_time", "end_time"]
    for field in required:
        if field not in data or not data[field]:
            raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        course_id = data["course_id"]
        coach_id = data.get("coach_id")
        schedule_date = data["date"]
        start_time = data["start_time"]
        end_time = data["end_time"]
        venue = data.get("venue")

        # 验证课程存在
        cursor.execute("SELECT id, coach_id FROM courses WHERE id = %s", (course_id,))
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 如果没指定教练，使用课程默认教练
        if not coach_id:
            coach_id = course["coach_id"]

        # 检查教练时间冲突
        if coach_id:
            cursor.execute(
                """
                SELECT COUNT(*) as cnt FROM schedules
                WHERE coach_id = %s AND date = %s AND status = '正常'
                  AND NOT (end_time <= %s OR start_time >= %s)
            """,
                (coach_id, schedule_date, start_time, end_time),
            )
            if cursor.fetchone()["cnt"] > 0:
                raise HTTPException(status_code=400, detail="该教练在此时间段已有排期")

        # 检查场地冲突（如果提供了场地）
        if venue:
            cursor.execute(
                """
                SELECT COUNT(*) as cnt FROM schedules
                WHERE venue = %s AND date = %s AND status = '正常'
                  AND NOT (end_time <= %s OR start_time >= %s)
            """,
                (venue, schedule_date, start_time, end_time),
            )
            if cursor.fetchone()["cnt"] > 0:
                raise HTTPException(status_code=400, detail="该场地在此时间段已被占用")

        # 创建排期
        sql = """
            INSERT INTO schedules (
                course_id, coach_id, date, start_time, end_time,
                venue, status, remark
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            (
                course_id,
                coach_id,
                schedule_date,
                start_time,
                end_time,
                venue,
                data.get("status", "正常"),
                data.get("remark"),
            ),
        )
        db.commit()
        schedule_id = cursor.lastrowid
        return {"id": schedule_id, "message": "排期创建成功"}
    finally:
        cursor.close()
        db.close()


@router.put("/{schedule_id}")
def update_schedule(
    schedule_id: int,
    data: Dict[str, Any],
    current_user=Depends(require_action("schedule.edit")),
):
    """更新排期信息"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM schedules WHERE id = %s", (schedule_id,))
        old_schedule = cursor.fetchone()
        if not old_schedule:
            raise HTTPException(status_code=404, detail="排期不存在")

        # 如果已有签到记录，不允许修改日期和时间
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM attendances WHERE schedule_id = %s",
            (schedule_id,),
        )
        if cursor.fetchone()["cnt"] > 0:
            if any(k in data for k in ["date", "start_time", "end_time"]):
                raise HTTPException(
                    status_code=400, detail="该排期已有签到记录，不能修改日期和时间"
                )

        updates = []
        params = []

        fields = [
            "course_id",
            "coach_id",
            "date",
            "start_time",
            "end_time",
            "venue",
            "status",
            "remark",
        ]
        for field in fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])

        if not updates:
            raise HTTPException(status_code=400, detail="没有可更新的字段")

        params.append(schedule_id)
        sql = f"UPDATE schedules SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(sql, tuple(params))
        db.commit()

        return {"message": "排期已更新"}
    finally:
        cursor.close()
        db.close()


@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    current_user=Depends(require_action("schedule.delete")),
):
    """
    删除排期
    - 如果已有签到记录，不允许删除，只能修改状态为"已取消"
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM schedules WHERE id = %s", (schedule_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="排期不存在")

        # 检查是否有签到记录
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM attendances WHERE schedule_id = %s",
            (schedule_id,),
        )
        if cursor.fetchone()["cnt"] > 0:
            raise HTTPException(
                status_code=400, detail="该排期已有签到记录，不能删除，请修改状态为'已取消'"
            )

        cursor.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
        db.commit()

        return {"message": "排期已删除"}
    finally:
        cursor.close()
        db.close()





