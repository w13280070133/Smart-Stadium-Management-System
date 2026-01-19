from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from ..database import get_db

router = APIRouter(prefix="/reports", tags=["Reports"])


def _safe_float(val: Any) -> float:
    try:
        return float(val or 0)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(val: Any) -> int:
    try:
        return int(val or 0)
    except (TypeError, ValueError):
        return 0


@router.get("/overview")
def get_overview():
    """
    数据总览：今日/本月预约数、收入（含退款扣减）、会员数与余额总额。查询异常时返回 0，避免 500。
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # 场地预约数
        try:
            cursor.execute(
                """
                SELECT
                  IFNULL(SUM(CASE WHEN DATE(start_time) = CURDATE() THEN 1 ELSE 0 END), 0) AS today_cnt,
                  IFNULL(SUM(CASE WHEN DATE_FORMAT(start_time, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m') THEN 1 ELSE 0 END), 0) AS month_cnt
                FROM court_reservations
                """
            )
            row = cursor.fetchone() or {}
            today_reservations = _safe_int(row.get("today_cnt"))
            month_reservations = _safe_int(row.get("month_cnt"))
        except Exception:
            today_reservations = 0
            month_reservations = 0

        # 会员数量 & 余额总额
        try:
            cursor.execute("SELECT COUNT(*) AS member_count, IFNULL(SUM(balance), 0) AS balance_total FROM members")
            mrow = cursor.fetchone() or {}
            member_count = _safe_int(mrow.get("member_count"))
            member_balance = _safe_float(mrow.get("balance_total"))
        except Exception:
            member_count = 0
            member_balance = 0.0

        # 收入（court/goods/course/refund），退款记为负数
        try:
            cursor.execute(
                """
                SELECT
                  IFNULL(SUM(CASE WHEN DATE(created_at) = CURDATE() THEN amount ELSE 0 END), 0) AS today_income,
                  IFNULL(SUM(CASE WHEN DATE_FORMAT(created_at, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m') THEN amount ELSE 0 END), 0) AS month_income
                FROM (
                  SELECT
                    created_at,
                    IFNULL(pay_amount, total_amount) *
                      CASE WHEN LOWER(status) IN ('refunded', 'partial_refund') THEN -1 ELSE 1 END AS amount,
                    LOWER(order_type) AS ot
                  FROM orders
                  WHERE LOWER(order_type) IN ('court', 'goods', 'product', 'course', 'refund')
                ) t
                """
            )
            irow = cursor.fetchone() or {}
            today_income = _safe_float(irow.get("today_income"))
            month_income = _safe_float(irow.get("month_income"))
        except Exception:
            today_income = 0.0
            month_income = 0.0

        return {
            "today_reservations": today_reservations,
            "month_reservations": month_reservations,
            "today_income": round(today_income, 2),
            "month_income": round(month_income, 2),
            "member_count": member_count,
            "member_balance": round(member_balance, 2),
        }
    finally:
        cursor.close()
        db.close()


@router.get("/revenue-daily")
def revenue_daily(days: int = 7):
    """
    近 N 天收入（场地预约 + 商品售卖 + 培训报名），退款记为负数。
    来源：orders.order_type in (court, goods, course, refund)
    """
    if days < 1:
        days = 1
    if days > 90:
        days = 90

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
              DATE(created_at) AS d,
              LOWER(order_type) AS ot,
              SUM(
                IFNULL(pay_amount, total_amount) *
                CASE WHEN LOWER(status) IN ('refunded', 'partial_refund') THEN -1 ELSE 1 END
              ) AS amt
            FROM orders
            WHERE DATE(created_at) BETWEEN %s AND %s
              AND LOWER(order_type) IN ('court', 'goods', 'product', 'course', 'refund')
            GROUP BY DATE(created_at), LOWER(order_type)
            """,
            (start_date, end_date),
        )
        rows = cursor.fetchall() or []
        res_map: Dict[str, float] = {}
        goods_map: Dict[str, float] = {}
        course_map: Dict[str, float] = {}
        for r in rows:
            dval = r.get("d")
            key = dval.strftime("%Y-%m-%d") if isinstance(dval, (date, datetime)) else str(dval)
            amt = _safe_float(r.get("amt"))
            ot = r.get("ot")
            if ot == "court":
                res_map[key] = res_map.get(key, 0.0) + amt
            elif ot in {"goods", "product"}:
                goods_map[key] = goods_map.get(key, 0.0) + amt
            elif ot == "course":
                course_map[key] = course_map.get(key, 0.0) + amt
            elif ot == "refund":
                # 退款订单直接累加到合计，按 total_amount 方向修正
                res_map[key] = res_map.get(key, 0.0) + amt

        result = []
        cur = start_date
        while cur <= end_date:
            key = cur.strftime("%Y-%m-%d")
            ra = res_map.get(key, 0.0)
            ga = goods_map.get(key, 0.0)
            ca = course_map.get(key, 0.0)
            total = ra + ga + ca
            result.append(
                {
                    "date": key,
                    "reservation_amount": round(ra, 2),
                    "goods_amount": round(ga, 2),
                    "product_amount": round(ga, 2),  # 向后兼容旧字段
                    "course_amount": round(ca, 2),
                    "total_amount": round(total, 2),
                }
            )
            cur += timedelta(days=1)

        return result
    finally:
        cursor.close()
        db.close()


@router.get("/training-income-summary")
def training_income_summary():
    """
    培训收入汇总：今日/本月/累计收入及报名数
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
              IFNULL(SUM(CASE WHEN DATE(enrolled_at) = CURDATE() AND status <> '已退课' THEN paid_amount ELSE 0 END), 0) AS today_income,
              IFNULL(SUM(CASE WHEN DATE_FORMAT(enrolled_at, '%%Y-%%m') = DATE_FORMAT(CURDATE(), '%%Y-%%m') AND status <> '已退课' THEN paid_amount ELSE 0 END), 0) AS month_income,
              IFNULL(SUM(CASE WHEN status <> '已退课' THEN paid_amount ELSE 0 END), 0) AS total_income
            FROM training_enrollments
            """
        )
        income_row = cursor.fetchone() or {}

        cursor.execute(
            """
            SELECT COUNT(*) AS total_enrollments, COUNT(DISTINCT member_id) AS total_students
            FROM training_enrollments
            WHERE status <> '已退课'
            """
        )
        count_row = cursor.fetchone() or {}

        return {
            "today_training_income": _safe_float(income_row.get("today_income")),
            "month_training_income": _safe_float(income_row.get("month_income")),
            "total_training_income": _safe_float(income_row.get("total_income")),
            "total_enrollments": _safe_int(count_row.get("total_enrollments")),
            "total_students": _safe_int(count_row.get("total_students")),
        }
    finally:
        cursor.close()
        db.close()


@router.get("/training-income-daily")
def training_income_daily(days: int = 30):
    """
    培训收入按日统计，默认 30 天，退款退课不计入
    """
    if days <= 0 or days > 365:
        days = 30

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT DATE(enrolled_at) AS d, IFNULL(SUM(paid_amount), 0) AS income
            FROM training_enrollments
            WHERE enrolled_at >= (CURDATE() - INTERVAL %s DAY)
              AND status <> '已退课'
            GROUP BY DATE(enrolled_at)
            ORDER BY d
            """,
            (days - 1,),
        )
        rows = cursor.fetchall() or []

        today = date.today()
        start_day = today - timedelta(days=days - 1)
        income_map = {}
        for r in rows:
            dval = r.get("d")
            key = dval.strftime("%Y-%m-%d") if isinstance(dval, (date, datetime)) else str(dval)
            income_map[key] = _safe_float(r.get("income"))

        day_list: List[str] = []
        income_list: List[float] = []
        cur = start_day
        while cur <= today:
            key = cur.strftime("%Y-%m-%d")
            day_list.append(key)
            income_list.append(income_map.get(key, 0.0))
            cur += timedelta(days=1)

        return {"days": day_list, "income": income_list}
    finally:
        cursor.close()
        db.close()


@router.get("/coach-workload")
def coach_workload(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    coach: Optional[str] = None,
):
    """
    教练工作量：课程数、报名学员数、考勤次数、出勤次数
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        sql = """
        SELECT
          c.coach_name,
          COUNT(DISTINCT c.id) AS course_count,
          COUNT(DISTINCT e.member_id) AS student_count,
          COUNT(a.id) AS attendance_count,
          SUM(CASE WHEN a.status = '已上课' THEN 1 ELSE 0 END) AS attended_count
        FROM training_courses c
        LEFT JOIN training_enrollments e ON e.course_id = c.id AND e.status <> '已退课'
        LEFT JOIN training_attendances a ON a.course_id = c.id
        WHERE c.coach_name IS NOT NULL AND c.coach_name <> ''
        """
        params: List[Any] = []

        if coach:
            sql += " AND c.coach_name LIKE %s"
            params.append(f"%{coach}%")
        if start_date:
            sql += " AND (a.attend_date IS NULL OR a.attend_date >= %s)"
            params.append(start_date)
        if end_date:
            sql += " AND (a.attend_date IS NULL OR a.attend_date <= %s)"
            params.append(end_date)

        sql += " GROUP BY c.coach_name ORDER BY c.coach_name"

        cursor.execute(sql, params)
        rows = cursor.fetchall() or []

        result = []
        for r in rows:
            result.append(
                {
                    "coach_name": r.get("coach_name"),
                    "course_count": _safe_int(r.get("course_count")),
                    "student_count": _safe_int(r.get("student_count")),
                    "attendance_count": _safe_int(r.get("attendance_count")),
                    "attended_count": _safe_int(r.get("attended_count")),
                }
            )
        return result
    finally:
        cursor.close()
        db.close()
