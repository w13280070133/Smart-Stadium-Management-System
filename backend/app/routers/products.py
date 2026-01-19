from fastapi import APIRouter, HTTPException
from typing import Optional, List
from datetime import datetime

from ..database import get_db

router = APIRouter(prefix="/products", tags=["Products"])


def _to_str(dt):
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt


@router.get("")
def list_products(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
):
    """
    获取商品列表
    GET /api/products?keyword=水&status=上架
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        sql = """
        SELECT id, name, category, price, stock, status, remark, created_at
        FROM products
        WHERE 1=1
        """
        params: List = []

        if keyword:
            sql += " AND (name LIKE %s OR category LIKE %s)"
            kw = f"%{keyword}%"
            params.extend([kw, kw])

        if status:
            sql += " AND status = %s"
            params.append(status)

        sql += " ORDER BY id DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        for r in rows:
            r["created_at"] = _to_str(r["created_at"])

        return rows
    finally:
        cursor.close()
        db.close()


@router.post("", status_code=201)
def create_product(data: dict):
    """
    新增商品
    body: { name, category?, price, stock, remark? }
    """
    required = ["name", "price", "stock"]
    for f in required:
        if f not in data:
            raise HTTPException(status_code=400, detail=f"缺少字段: {f}")

    name = data["name"].strip()
    category = (data.get("category") or "").strip()
    remark = (data.get("remark") or "").strip()

    try:
        price = float(data["price"])
    except Exception:
        raise HTTPException(status_code=400, detail="价格格式不正确")

    try:
        stock = int(data["stock"])
    except Exception:
        raise HTTPException(status_code=400, detail="库存格式不正确")

    if not name:
        raise HTTPException(status_code=400, detail="商品名称不能为空")
    if price < 0:
        raise HTTPException(status_code=400, detail="价格不能为负数")
    if stock < 0:
        raise HTTPException(status_code=400, detail="库存不能为负数")

    db = get_db()
    cursor = db.cursor()
    try:
        sql = """
        INSERT INTO products (name, category, price, stock, status, remark)
        VALUES (%s, %s, %s, %s, '上架', %s)
        """
        cursor.execute(sql, (name, category, price, stock, remark))
        db.commit()
        return {"id": cursor.lastrowid}
    finally:
        cursor.close()
        db.close()


@router.put("/{product_id}")
def update_product(product_id: int, data: dict):
    """
    编辑商品信息
    body: { name, category?, price, stock, remark? }
    """
    required = ["name", "price", "stock"]
    for f in required:
        if f not in data:
            raise HTTPException(status_code=400, detail=f"缺少字段: {f}")

    name = data["name"].strip()
    category = (data.get("category") or "").strip()
    remark = (data.get("remark") or "").strip()

    try:
        price = float(data["price"])
    except Exception:
        raise HTTPException(status_code=400, detail="价格格式不正确")

    try:
        stock = int(data["stock"])
    except Exception:
        raise HTTPException(status_code=400, detail="库存格式不正确")

    if not name:
        raise HTTPException(status_code=400, detail="商品名称不能为空")
    if price < 0:
        raise HTTPException(status_code=400, detail="价格不能为负数")
    if stock < 0:
        raise HTTPException(status_code=400, detail="库存不能为负数")

    db = get_db()
    cursor = db.cursor()
    try:
        sql = """
        UPDATE products
        SET name = %s, category = %s, price = %s, stock = %s, remark = %s
        WHERE id = %s
        """
        cursor.execute(sql, (name, category, price, stock, remark, product_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="商品不存在")

        db.commit()
        return {"message": "ok"}
    finally:
        cursor.close()
        db.close()


@router.put("/{product_id}/status")
def update_product_status(product_id: int, data: dict):
    """
    上下架
    body: { status }  status: '上架' | '下架'
    """
    status = data.get("status")
    if status not in ("上架", "下架"):
        raise HTTPException(status_code=400, detail="非法状态")

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE products SET status = %s WHERE id = %s",
            (status, product_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="商品不存在")

        db.commit()
        return {"message": "ok"}
    finally:
        cursor.close()
        db.close()


@router.delete("/{product_id}")
def delete_product(product_id: int):
    """
    删除商品（注意：如果已经有销售记录，真实项目里一般不允许直接删，这里先简单处理）
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="商品不存在")
        db.commit()
        return {"message": "deleted"}
    finally:
        cursor.close()
        db.close()
