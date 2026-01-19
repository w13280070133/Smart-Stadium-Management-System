# backend/app/routers/training_courses.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from ..database import get_db
from ..deps import require_action

router = APIRouter(prefix="/training/courses", tags=["Training Courses"])


@router.get("")
def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    coach_id: Optional[int] = None,
    current_user=Depends(require_action("course.view")),
):
    """
    获取课程列表
    - 支持关键字搜索（课程名称）
    - 支持按类型、状态、教练筛选
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        conditions = []
        params = []

        if keyword:
            conditions.append("c.name LIKE %s")
            params.append(f"%{keyword}%")

        if type:
            conditions.append("c.type = %s")
            params.append(type)

        if status:
            conditions.append("c.status = %s")
            params.append(status)

        if coach_id:
            conditions.append("c.coach_id = %s")
            params.append(coach_id)

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM courses c{where_clause}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # 查询列表（带教练名称、报名统计）
        offset = (page - 1) * page_size
        list_sql = f"""
            SELECT c.*,
                   coach.name as coach_name,
                   (SELECT COUNT(*) FROM enrollments WHERE course_id = c.id AND status = '在读') as active_students,
                   (SELECT SUM(paid_amount) FROM enrollments WHERE course_id = c.id) as total_revenue
            FROM courses c
            LEFT JOIN coaches coach ON c.coach_id = coach.id
            {where_clause}
            ORDER BY c.id DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params + [page_size, offset]))
        items = cursor.fetchall() or []

        return {"total": total, "items": items, "page": page, "page_size": page_size}
    finally:
        cursor.close()
        db.close()


@router.get("/{course_id}")
def get_course(
    course_id: int,
    current_user=Depends(require_action("course.view")),
):
    """获取课程详情（包含报名学员、排期列表、收入统计）"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # 课程基本信息
        cursor.execute(
            """
            SELECT c.*, coach.name as coach_name
            FROM courses c
            LEFT JOIN coaches coach ON c.coach_id = coach.id
            WHERE c.id = %s
        """,
            (course_id,),
        )
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 报名学员列表
        cursor.execute(
            """
            SELECT e.*, s.name as student_name, s.phone as student_phone
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            WHERE e.course_id = %s
            ORDER BY e.enrolled_at DESC
        """,
            (course_id,),
        )
        enrollments = cursor.fetchall() or []

        # 排期列表（最近 20 条）
        cursor.execute(
            """
            SELECT sch.*, coach.name as coach_name
            FROM schedules sch
            LEFT JOIN coaches coach ON sch.coach_id = coach.id
            WHERE sch.course_id = %s
            ORDER BY sch.date DESC, sch.start_time DESC
            LIMIT 20
        """,
            (course_id,),
        )
        schedules = cursor.fetchall() or []

        # 统计数据
        cursor.execute(
            """
            SELECT
                COUNT(DISTINCT e.id) as total_enrollments,
                COUNT(DISTINCT CASE WHEN e.status = '在读' THEN e.id END) as active_enrollments,
                SUM(e.paid_amount) as total_revenue,
                SUM(CASE WHEN e.status = '在读' THEN e.remaining_lessons ELSE 0 END) as total_remaining_lessons
            FROM enrollments e
            WHERE e.course_id = %s
        """,
            (course_id,),
        )
        stats = cursor.fetchone() or {}

        course["enrollments"] = enrollments
        course["schedules"] = schedules
        course["stats"] = stats

        return course
    finally:
        cursor.close()
        db.close()


@router.post("")
def create_course(
    data: Dict[str, Any],
    current_user=Depends(require_action("course.create")),
):
    """创建课程"""
    required = ["name"]
    for field in required:
        if field not in data or not data[field]:
            raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        sql = """
            INSERT INTO courses (
                name, type, description, coach_id, total_lessons,
                price, max_students, status, remark
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            (
                data["name"],
                data.get("type"),
                data.get("description"),
                data.get("coach_id"),
                data.get("total_lessons", 12),
                data.get("price", 0),
                data.get("max_students", 20),
                data.get("status", "招生中"),
                data.get("remark"),
            ),
        )
        db.commit()
        course_id = cursor.lastrowid
        return {"id": course_id, "message": "课程创建成功"}
    finally:
        cursor.close()
        db.close()


@router.put("/{course_id}")
def update_course(
    course_id: int,
    data: Dict[str, Any],
    current_user=Depends(require_action("course.edit")),
):
    """更新课程信息"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM courses WHERE id = %s", (course_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="课程不存在")

        updates = []
        params = []

        fields = [
            "name",
            "type",
            "description",
            "coach_id",
            "total_lessons",
            "price",
            "max_students",
            "status",
            "remark",
        ]
        for field in fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])

        if not updates:
            raise HTTPException(status_code=400, detail="没有可更新的字段")

        params.append(course_id)
        sql = f"UPDATE courses SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(sql, tuple(params))
        db.commit()

        return {"message": "课程信息已更新"}
    finally:
        cursor.close()
        db.close()


@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    current_user=Depends(require_action("course.delete")),
):
    """
    删除课程
    - 只要没有"在读"状态的报名记录，课程就可以删除
    - 会级联删除关联的排期和考勤记录
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM courses WHERE id = %s", (course_id,))
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 检查是否有在读的报名记录
        cursor.execute(
            """
            SELECT COUNT(*) as cnt FROM enrollments
            WHERE course_id = %s AND status = '在读'
        """,
            (course_id,),
        )
        active_enrollments = cursor.fetchone()["cnt"]
        if active_enrollments > 0:
            raise HTTPException(
                status_code=400,
                detail=f"该课程有 {active_enrollments} 个在读学员，无法删除",
            )

        # 删除课程（外键约束会自动删除 schedules 和 attendances）
        cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        db.commit()

        return {"message": f"课程【{course['name']}】已删除"}
    finally:
        cursor.close()
        db.close()


@router.get("/types/list")
def get_course_types(current_user=Depends(require_action("course.view"))):
    """获取所有已使用过的课程类型（用于前端下拉）"""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            SELECT DISTINCT type FROM courses
            WHERE type IS NOT NULL AND type != ''
            ORDER BY type
        """
        )
        items = cursor.fetchall()
        return [item[0] for item in items]
    finally:
        cursor.close()
        db.close()
