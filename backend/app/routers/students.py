# backend/app/routers/students.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from ..database import get_db
from ..deps import require_action

router = APIRouter(prefix="/training/students", tags=["Students"])


@router.get("")
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    current_user=Depends(require_action("student.view")),
):
    """
    获取学员列表
    - 支持关键字搜索（姓名、电话、监护人）
    - 支持按状态筛选
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        conditions = []
        params = []

        if keyword:
            conditions.append(
                "(name LIKE %s OR phone LIKE %s OR guardian_name LIKE %s OR guardian_phone LIKE %s)"
            )
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw, kw])

        if status:
            conditions.append("status = %s")
            params.append(status)

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM students{where_clause}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # 查询列表
        offset = (page - 1) * page_size
        list_sql = f"""
            SELECT s.*,
                   (SELECT COUNT(*) FROM enrollments WHERE student_id = s.id AND status = '在读') as active_enrollments
            FROM students s
            {where_clause}
            ORDER BY s.id DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params + [page_size, offset]))
        items = cursor.fetchall() or []

        return {"total": total, "items": items, "page": page, "page_size": page_size}
    finally:
        cursor.close()
        db.close()


@router.get("/{student_id}")
def get_student(
    student_id: int,
    current_user=Depends(require_action("student.view")),
):
    """获取学员详情（包含报名记录）"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学员不存在")

        # 获取报名记录
        cursor.execute(
            """
            SELECT e.*, c.name as course_name, c.type as course_type
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE e.student_id = %s
            ORDER BY e.enrolled_at DESC
        """,
            (student_id,),
        )
        enrollments = cursor.fetchall() or []

        student["enrollments"] = enrollments
        return student
    finally:
        cursor.close()
        db.close()


@router.post("")
def create_student(
    data: Dict[str, Any],
    current_user=Depends(require_action("student.create")),
):
    """创建学员"""
    required = ["name"]
    for field in required:
        if field not in data or not data[field]:
            raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        sql = """
            INSERT INTO students (
                name, phone, gender, birthday, guardian_name,
                guardian_phone, status, remark
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            (
                data["name"],
                data.get("phone"),
                data.get("gender", "未知"),
                data.get("birthday"),
                data.get("guardian_name"),
                data.get("guardian_phone"),
                data.get("status", "在读"),
                data.get("remark"),
            ),
        )
        db.commit()
        student_id = cursor.lastrowid
        return {"id": student_id, "message": "学员创建成功"}
    finally:
        cursor.close()
        db.close()


@router.put("/{student_id}")
def update_student(
    student_id: int,
    data: Dict[str, Any],
    current_user=Depends(require_action("student.edit")),
):
    """更新学员信息"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="学员不存在")

        updates = []
        params = []

        fields = [
            "name",
            "phone",
            "gender",
            "birthday",
            "guardian_name",
            "guardian_phone",
            "status",
            "remark",
        ]
        for field in fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])

        if not updates:
            raise HTTPException(status_code=400, detail="没有可更新的字段")

        params.append(student_id)
        sql = f"UPDATE students SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(sql, tuple(params))
        db.commit()

        return {"message": "学员信息已更新"}
    finally:
        cursor.close()
        db.close()


@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    current_user=Depends(require_action("student.delete")),
):
    """
    删除学员
    - 只有没有"在读"状态的报名记录时才可以删除
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学员不存在")

        # 检查是否有在读的报名记录
        cursor.execute(
            """
            SELECT COUNT(*) as cnt FROM enrollments
            WHERE student_id = %s AND status = '在读'
        """,
            (student_id,),
        )
        active_enrollments = cursor.fetchone()["cnt"]
        if active_enrollments > 0:
            raise HTTPException(
                status_code=400,
                detail=f"该学员有 {active_enrollments} 个在读课程，无法删除",
            )

        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        db.commit()

        return {"message": f"学员【{student['name']}】已删除"}
    finally:
        cursor.close()
        db.close()
