# backend/app/database.py
import logging
import mysql.connector
from mysql.connector import Error, pooling
from .config import settings

logger = logging.getLogger(__name__)

dbconfig = {
    "host": settings.DB_HOST,
    "port": int(settings.DB_PORT),
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "database": settings.DB_NAME,
    "charset": "utf8mb4",
}

# 数据库连接池（单例）
_db_pool = None


def _init_pool():
    """初始化数据库连接池（懒加载单例）"""
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = pooling.MySQLConnectionPool(
                pool_name=settings.DB_POOL_NAME,
                pool_size=settings.DB_POOL_SIZE,
                pool_reset_session=True,
                **dbconfig
            )
            logger.info(f"数据库连接池初始化成功，池大小: {settings.DB_POOL_SIZE}")
        except Error as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            raise
    return _db_pool


def get_db():
    """
    从连接池获取数据库连接。
    用完记得 cursor.close() 和 db.close()（close 会将连接归还到池中）
    """
    try:
        pool = _init_pool()
        conn = pool.get_connection()
        return conn
    except Error as e:
        logger.error(f"获取数据库连接失败: {e}")
        raise


def close_pool():
    """关闭连接池（用于应用关闭时清理资源）"""
    global _db_pool
    if _db_pool is not None:
        # MySQL Connector 的连接池没有显式 close 方法，
        # 但我们可以将引用置为 None，让 GC 处理
        _db_pool = None
        logger.info("数据库连接池已关闭")
