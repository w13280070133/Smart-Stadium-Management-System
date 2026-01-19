# backend/app/routers/training_enrollments.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from ..database import get_db
from ..deps import require_action, get_current_user
from ..services.audit import write_operation_log
from ..services.orders import generate_order_no

router = APIRouter(prefix="/training/enrollments", tags=["Training Enrollments"])


@router.get("")
def list_enrollments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    course_id: Optional[int] = None,
    student_id: Optional[int] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user=Depends(require_action("enrollment.view")),
):
    """
    获取报名列表
    - 支持按课程、学员、状态筛选
    - 支持关键字搜索（学员姓名、课程名称）
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        conditions = []
        params = []

        if course_id:
            conditions.append("e.course_id = %s")
            params.append(course_id)

        if student_id:
            conditions.append("e.student_id = %s")
            params.append(student_id)

        if status:
            conditions.append("e.status = %s")
            params.append(status)

        if keyword:
            conditions.append("(s.name LIKE %s OR c.name LIKE %s)")
            kw = f"%{keyword}%"
            params.extend([kw, kw])

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

        # 查询总数
        count_sql = f"""
            SELECT COUNT(*) as total
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            JOIN courses c ON e.course_id = c.id
            {where_clause}
        """
        cursor.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        # 查询列表
        offset = (page - 1) * page_size
        list_sql = f"""
            SELECT e.*,
                   s.name as student_name,
                   s.phone as student_phone,
                   c.name as course_name,
                   c.type as course_type,
                   (SELECT COUNT(*) FROM attendances a WHERE a.enrollment_id = e.id) as attendance_count
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            JOIN courses c ON e.course_id = c.id
            {where_clause}
            ORDER BY e.id DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, tuple(params + [page_size, offset]))
        items = cursor.fetchall() or []

        return {"total": total, "items": items, "page": page, "page_size": page_size}
    finally:
        cursor.close()
        db.close()


@router.get("/{enrollment_id}")
def get_enrollment(
    enrollment_id: int,
    current_user=Depends(require_action("enrollment.view")),
):
    """获取报名详情（包含签到记录）"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT e.*,
                   s.name as student_name,
                   s.phone as student_phone,
                   c.name as course_name,
                   c.type as course_type
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            JOIN courses c ON e.course_id = c.id
            WHERE e.id = %s
        """,
            (enrollment_id,),
        )
        enrollment = cursor.fetchone()
        if not enrollment:
            raise HTTPException(status_code=404, detail="报名记录不存在")

        # 获取签到记录
        cursor.execute(
            """
            SELECT a.*, sch.date, sch.start_time, sch.end_time
            FROM attendances a
            JOIN schedules sch ON a.schedule_id = sch.id
            WHERE a.enrollment_id = %s
            ORDER BY sch.date DESC, sch.start_time DESC
        """,
            (enrollment_id,),
        )
        attendances = cursor.fetchall() or []

        enrollment["attendances"] = attendances
        return enrollment
    finally:
        cursor.close()
        db.close()


@router.post("")
def create_enrollment(
    data: Dict[str, Any],
    request: Request,
    current_user=Depends(require_action("enrollment.create")),
):
    """
    创建教培课程报名
    
    这是教培模块的核心业务流程，实现学员报名课程的完整逻辑。
    报名成功后会生成统一订单记录，便于财务统计和退费追溯。
    
    业务流程：
    1. 验证必填字段（course_id, student_id, total_lessons, paid_amount）
    2. 验证课程和学员是否存在
    3. 检查课程状态（只有"招生中"或"进行中"的课程可报名）
    4. 检查学员是否已报名该课程（防止重复报名）
    5. 检查课程是否满员（max_students 限制）
    6. 创建报名记录（remaining_lessons 初始等于 total_lessons）
    7. 生成订单记录（order_type='training'，status='paid'）
    8. 发送通知给管理员
    9. 记录操作日志
    
    关键业务规则：
    - 支付方式固定为"现金"（移动支付也算现金，由前台确认收款）
    - 初始剩余课时等于总课时，后续通过签到扣减
    - 订单状态直接标记为"已支付"（前台确认收款后再创建报名）
    - 使用数据库事务确保报名和订单同时成功或失败
    
    Args:
        data: 报名信息，必须包含：
            - course_id: 课程 ID
            - student_id: 学员 ID
            - total_lessons: 总课时数
            - paid_amount: 实付金额
            - remark: 备注（可选）
        request: 请求对象（用于获取客户端信息）
        current_user: 当前用户（需要 enrollment.create 权限）
        
    Returns:
        dict: {
            "id": 报名记录 ID,
            "order_no": 订单编号
        }
        
    Raises:
        HTTPException(400): 缺少必填字段、课程不接受报名、已报名、课程满员
        HTTPException(404): 课程或学员不存在
    """
    required = ["course_id", "student_id", "total_lessons", "paid_amount"]
    for field in required:
        if field not in data or data[field] is None:
            raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor2 = db.cursor()
    try:
        course_id = int(data["course_id"])
        student_id = int(data["student_id"])
        total_lessons = int(data["total_lessons"])
        paid_amount = float(data["paid_amount"])

        db.start_transaction()

        # 验证课程和学员存在
        cursor.execute(
            "SELECT id, name, max_students, status FROM courses WHERE id = %s",
            (course_id,),
        )
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")
        
        if course["status"] not in ["招生中", "进行中"]:
            raise HTTPException(status_code=400, detail="该课程当前不接受报名")

        cursor.execute("SELECT id, name FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="学员不存在")

        # 检查是否已报名
        cursor.execute(
            """
            SELECT COUNT(*) as cnt FROM enrollments
            WHERE course_id = %s AND student_id = %s AND status = '在读'
        """,
            (course_id, student_id),
        )
        if cursor.fetchone()["cnt"] > 0:
            raise HTTPException(status_code=400, detail="该学员已报名此课程")

        # 检查是否满员
        cursor.execute(
            """
            SELECT COUNT(*) as cnt FROM enrollments
            WHERE course_id = %s AND status = '在读'
        """,
            (course_id,),
        )
        current_students = cursor.fetchone()["cnt"]
        if current_students >= course["max_students"]:
            raise HTTPException(
                status_code=400,
                detail=f"课程已满员（最多 {course['max_students']} 人）",
            )

        # 创建报名记录
        enroll_sql = """
            INSERT INTO enrollments (
                course_id, student_id, total_lessons, remaining_lessons,
                paid_amount, pay_method, status, remark
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor2.execute(
            enroll_sql,
            (
                course_id,
                student_id,
                total_lessons,
                total_lessons,  # remaining_lessons 初始等于 total_lessons
                paid_amount,
                "cash",  # 固定为现金
                "在读",
                data.get("remark"),
            ),
        )
        enrollment_id = cursor2.lastrowid

        # 生成订单（使用统一的订单服务）
        from ..services.orders import create_course_order
        
        order_info = create_course_order(
            cursor=cursor,
            related_id=enrollment_id,
            member_id=None,  # 学员与会员无关
            member_name=student["name"],
            total_amount=paid_amount,
            pay_method="cash",
            status="paid",
            remark=data.get("remark"),
        )
        order_id = order_info["order_id"]
        order_no = order_info["order_no"]

        db.commit()

        # 记录操作日志
        try:
            uid = current_user["id"] if isinstance(current_user, dict) else current_user.id
            uname = current_user["username"] if isinstance(current_user, dict) else current_user.username
            write_operation_log(
                user_id=uid,
                username=uname,
                action="创建",
                module="课程报名",
                target_id=enrollment_id,
                target_desc=f"{student['name']} 报名 {course['name']}",
                detail={
                    "total_lessons": total_lessons,
                    "paid_amount": paid_amount,
                    "order_no": order_no,
                },
                ip=request.client.host if request.client else None,
            )
        except Exception:
            pass

        return {
            "id": enrollment_id,
            "order_id": order_id,
            "order_no": order_no,
            "message": "报名成功",
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"报名失败: {str(e)}")
    finally:
        cursor.close()
        cursor2.close()
        db.close()


@router.post("/{enrollment_id}/refund")
def refund_enrollment(
    enrollment_id: int,
    data: Dict[str, Any],
    request: Request,
    current_user=Depends(require_action("enrollment.refund")),
):
    """
    教培课程退费
    
    实现课程退费的完整业务逻辑，按剩余课时比例计算退款金额。
    退费后会生成负向订单记录，保证财务可追溯。
    
    退费算法：
    退款金额 = (实付金额 / 总课时) × 剩余课时
    
    示例：
    - 报名：60课时，实付 ¥6000（¥100/课时）
    - 已上：20课时（通过签到扣减）
    - 剩余：40课时
    - 退款：(6000 / 60) × 40 = ¥4000
    
    业务流程：
    1. 查询报名信息（关联课程和学员）
    2. 验证报名状态（已退费的不能再退）
    3. 验证剩余课时（课时用完无法退费）
    4. 按比例计算退款金额
    5. 修改报名状态为"退费"
    6. 查找原订单记录
    7. 生成退款订单（负向金额，order_type='refund'）
    8. 更新原订单状态为"已退款"
    9. 记录操作日志
    
    关键设计：
    - 退款金额为负数，便于财务统计（收入 - 退款 = 净收入）
    - 退款订单关联原报名 ID（related_id），保证可追溯
    - 原订单状态更新为"refunded"，标识该笔业务已部分或全部退款
    - 不删除任何记录，保留完整的业务历史
    
    Args:
        enrollment_id: 报名记录 ID
        data: 退费信息，包含：
            - remark: 退费原因（可选）
        request: 请求对象
        current_user: 当前用户（需要 enrollment.refund 权限）
        
    Returns:
        dict: {
            "refund_amount": 退款金额,
            "refund_order_no": 退款订单编号,
            "remaining_lessons": 剩余课时
        }
        
    Raises:
        HTTPException(404): 报名记录不存在
        HTTPException(400): 已退费或课时已用完
        
    注意：
        退费后报名状态变为"退费"，学员无法继续签到上课。
        退款需要线下完成，系统只记录退款金额和原因。
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor2 = db.cursor()
    try:
        db.start_transaction()

        # 获取报名信息
        cursor.execute(
            """
            SELECT e.*, c.name as course_name, s.name as student_name
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            JOIN students s ON e.student_id = s.id
            WHERE e.id = %s
        """,
            (enrollment_id,),
        )
        enrollment = cursor.fetchone()
        if not enrollment:
            raise HTTPException(status_code=404, detail="报名记录不存在")

        if enrollment["status"] == "退费":
            raise HTTPException(status_code=400, detail="该报名已退费")

        # 计算退款金额
        total_lessons = enrollment["total_lessons"]
        remaining_lessons = enrollment["remaining_lessons"]
        paid_amount = float(enrollment["paid_amount"])

        if remaining_lessons <= 0:
            raise HTTPException(status_code=400, detail="课时已用完，无剩余可退")

        # 按剩余课时比例计算退款
        refund_amount = (paid_amount / total_lessons) * remaining_lessons

        # 修改报名状态
        cursor2.execute(
            "UPDATE enrollments SET status = %s WHERE id = %s", ("退费", enrollment_id)
        )

        # 查找原订单（兼容 training 和 course 两种类型）
        cursor.execute(
            """
            SELECT * FROM orders
            WHERE related_id = %s AND order_type IN ('training', 'course')
            ORDER BY id DESC LIMIT 1
        """,
            (enrollment_id,),
        )
        original_order = cursor.fetchone()

        # 生成退款订单
        refund_order_no = generate_order_no("REFUND")
        refund_order_sql = """
            INSERT INTO orders (
                order_no, order_type, related_id, member_id, member_name,
                total_amount, pay_amount, discount_amount, currency,
                pay_method, status, paid_at, remark
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor2.execute(
            refund_order_sql,
            (
                refund_order_no,
                "refund",
                enrollment_id,
                None,
                enrollment["student_name"],
                -refund_amount,
                -refund_amount,
                0,
                "CNY",
                None,
                "refunded",
                datetime.now(),
                data.get("remark", f"课程退费：剩余 {remaining_lessons} 节课"),
            ),
        )
        refund_order_id = cursor2.lastrowid

        # 更新原订单状态
        if original_order:
            cursor2.execute(
                "UPDATE orders SET status = %s WHERE id = %s",
                ("refunded", original_order["id"]),
            )

        db.commit()

        # 记录操作日志
        try:
            uid = current_user["id"] if isinstance(current_user, dict) else current_user.id
            uname = current_user["username"] if isinstance(current_user, dict) else current_user.username
            write_operation_log(
                user_id=uid,
                username=uname,
                action="退费",
                module="课程报名",
                target_id=enrollment_id,
                target_desc=f"{enrollment['student_name']} 退出 {enrollment['course_name']}",
                detail={
                    "refund_amount": refund_amount,
                    "remaining_lessons": remaining_lessons,
                    "refund_order_no": refund_order_no,
                },
                ip=request.client.host if request.client else None,
            )
        except Exception:
            pass

        return {
            "message": "退费成功",
            "refund_amount": refund_amount,
            "refund_order_id": refund_order_id,
            "refund_order_no": refund_order_no,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"退费失败: {str(e)}")
    finally:
        cursor.close()
        cursor2.close()
        db.close()
