# backend/app/routers/coaches.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from ..database import get_db
from ..deps import require_action

router = APIRouter(prefix="/training/coaches", tags=["Coaches"])


@router.get("")
def list_coaches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    specialty: Optional[str] = None,
    current_user=Depends(require_action("coach.view")),
):
    """
    获取教练列表
    - 支持关键字搜索（姓名、电话）
    - 支持按状态筛选
    - 支持按擅长项目筛选
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        conditions = []
        params = []

        if keyword:
            conditions.append("(name LIKE %s OR phone LIKE %s)")
            kw = f"%{keyword}%"
            params.extend([kw, kw])

        if status:
            conditions.append("status = %s")
            params.append(status)

        if specialty:
            conditions.append("specialties LIKE %s")
            params.append(f"%{specialty}%")

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM coaches{where_clause}"
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # 查询列表
        offset = (page - 1) * page_size
        list_sql = f"""
            SELECT * FROM coaches
            {where_clause}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params + [page_size, offset]))
        items = cursor.fetchall() or []

        return {"total": total, "items": items, "page": page, "page_size": page_size}
    finally:
        cursor.close()
        db.close()


@router.get("/{coach_id}")
def get_coach(
    coach_id: int,
    current_user=Depends(require_action("coach.view")),
):
    """获取教练详情"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM coaches WHERE id = %s", (coach_id,))
        coach = cursor.fetchone()
        if not coach:
            raise HTTPException(status_code=404, detail="教练不存在")
        return coach
    finally:
        cursor.close()
        db.close()


@router.post("")
def create_coach(
    data: Dict[str, Any],
    current_user=Depends(require_action("coach.create")),
):
    """创建教练"""
    required = ["name"]
    for field in required:
        if field not in data or not data[field]:
            raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        sql = """
            INSERT INTO coaches (
                name, phone, gender, specialties, hourly_rate,
                certificates, status, employee_id, remark
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            (
                data["name"],
                data.get("phone"),
                data.get("gender", "未知"),
                data.get("specialties"),
                data.get("hourly_rate", 0),
                data.get("certificates"),
                data.get("status", "在职"),
                data.get("employee_id"),
                data.get("remark"),
            ),
        )
        db.commit()
        coach_id = cursor.lastrowid
        return {"id": coach_id, "message": "教练创建成功"}
    finally:
        cursor.close()
        db.close()


@router.put("/{coach_id}")
def update_coach(
    coach_id: int,
    data: Dict[str, Any],
    current_user=Depends(require_action("coach.edit")),
):
    """更新教练信息"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM coaches WHERE id = %s", (coach_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="教练不存在")

        updates = []
        params = []

        fields = [
            "name",
            "phone",
            "gender",
            "specialties",
            "hourly_rate",
            "certificates",
            "status",
            "employee_id",
            "remark",
        ]
        for field in fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])

        if not updates:
            raise HTTPException(status_code=400, detail="没有可更新的字段")

        params.append(coach_id)
        sql = f"UPDATE coaches SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(sql, tuple(params))
        db.commit()

        return {"message": "教练信息已更新"}
    finally:
        cursor.close()
        db.close()


@router.delete("/{coach_id}")
def delete_coach(
    coach_id: int,
    current_user=Depends(require_action("coach.delete")),
):
    """
    删除教练
    - 检查是否有关联的课程或排期
    - 如果有在读的课程，禁止删除
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM coaches WHERE id = %s", (coach_id,))
        coach = cursor.fetchone()
        if not coach:
            raise HTTPException(status_code=404, detail="教练不存在")

        # 检查是否有关联的进行中课程
        cursor.execute(
            """
            SELECT COUNT(*) as cnt FROM courses
            WHERE coach_id = %s AND status IN ('招生中', '进行中')
        """,
            (coach_id,),
        )
        active_courses = cursor.fetchone()["cnt"]
        if active_courses > 0:
            raise HTTPException(
                status_code=400,
                detail=f"该教练有 {active_courses} 门进行中的课程，无法删除",
            )

        # 检查是否有未来的排期
        cursor.execute(
            """
            SELECT COUNT(*) as cnt FROM schedules
            WHERE coach_id = %s AND date >= CURDATE() AND status = '正常'
        """,
            (coach_id,),
        )
        future_schedules = cursor.fetchone()["cnt"]
        if future_schedules > 0:
            raise HTTPException(
                status_code=400,
                detail=f"该教练有 {future_schedules} 个未来排期，无法删除",
            )

        cursor.execute("DELETE FROM coaches WHERE id = %s", (coach_id,))
        db.commit()

        return {"message": f"教练【{coach['name']}】已删除"}
    finally:
        cursor.close()
        db.close()


@router.get("/specialties/list")
def get_specialties(current_user=Depends(require_action("coach.view"))):
    """获取所有已使用过的擅长项目（用于前端筛选下拉）"""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            SELECT DISTINCT specialties FROM coaches
            WHERE specialties IS NOT NULL AND specialties != ''
        """
        )
        items = cursor.fetchall()
        # 拆分逗号分隔的项目
        specialties = set()
        for (item,) in items:
            if item:
                for s in item.split(","):
                    specialties.add(s.strip())
        return sorted(list(specialties))
    finally:
        cursor.close()
        db.close()


