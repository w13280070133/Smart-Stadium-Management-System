# backend/app/database.py
import mysql.connector
from mysql.connector import Error
from .config import settings

dbconfig = {
    "host": settings.DB_HOST,
    "port": int(settings.DB_PORT),
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "database": settings.DB_NAME,
    "charset": "utf8mb4",
}


def get_db():
    """
    每次请求新建一个数据库连接，用完记得 cursor.close() 和 db.close()
    （你现在的各个 router 里基本都有 finally 里 close，没问题）
    """
    try:
        conn = mysql.connector.connect(**dbconfig)
        return conn
    except Error as e:
        # 这里打印一下方便排查（比如账号密码错、数据库没开）
        print("数据库连接失败：", e)
        raise
