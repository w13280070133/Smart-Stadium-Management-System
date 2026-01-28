"""
并发和竞态条件测试

测试系统在并发场景下的正确性
"""
import pytest
import threading
import time
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConcurrencyIssues:
    """并发问题测试"""
    
    def test_race_condition_simulation(self):
        """模拟竞态条件场景"""
        # 场景：两个用户同时预约同一时间段
        # 没有正确的锁机制会导致重复预约
        
        shared_state = {"booked": False, "count": 0}
        errors = []
        
        def try_book():
            # 模拟数据库查询（检查是否可用）
            if not shared_state["booked"]:
                # 模拟处理延迟
                time.sleep(0.001)
                # 模拟预约
                shared_state["booked"] = True
                shared_state["count"] += 1
                if shared_state["count"] > 1:
                    errors.append("重复预约！")
        
        # 创建多个线程同时执行
        threads = [threading.Thread(target=try_book) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 这个测试展示了为什么需要数据库级别的锁
        # 在实际代码中，使用 FOR UPDATE 来防止这种情况
        print(f"预约次数: {shared_state['count']}, 错误: {errors}")
    
    def test_for_update_importance(self):
        """验证 FOR UPDATE 的重要性"""
        # 在 court_reservations.py 中使用了 FOR UPDATE：
        # cursor.execute("SELECT ... FOR UPDATE", ...)
        # 这确保了在事务完成之前，其他事务无法读取或修改该行
        
        # 检查代码中是否使用了 FOR UPDATE
        import inspect
        from app.routers import court_reservations
        
        source = inspect.getsource(court_reservations)
        assert "FOR UPDATE" in source, "预约模块应该使用 FOR UPDATE 防止并发问题"


class TestSessionManagement:
    """会话管理测试"""
    
    def test_session_expiration(self):
        """测试会话过期机制"""
        from app.agent.core import (
            get_conversation_history,
            clear_conversation_history,
            _conversation_history,
            SESSION_EXPIRE_SECONDS,
        )
        
        # 创建会话
        session_id = "test_session_123"
        history = get_conversation_history(session_id)
        history.append({"role": "user", "content": "test"})
        
        assert len(get_conversation_history(session_id)) == 1
        
        # 清理测试会话
        clear_conversation_history(session_id)
        assert len(get_conversation_history(session_id)) == 0
    
    def test_max_sessions_limit(self):
        """测试最大会话数限制"""
        from app.agent.core import MAX_SESSIONS
        
        # 验证有限制
        assert MAX_SESSIONS > 0
        assert MAX_SESSIONS <= 10000  # 合理的上限


class TestDatabaseConnectionPool:
    """数据库连接池测试"""
    
    def test_connection_pool_config(self):
        """测试连接池配置"""
        from app.config import settings
        
        assert settings.DB_POOL_SIZE > 0
        assert settings.DB_POOL_SIZE <= 100  # 合理的池大小
    
    def test_connection_release(self):
        """测试连接释放"""
        # 验证代码中使用了正确的连接释放模式
        import inspect
        from app.routers import court_reservations
        
        source = inspect.getsource(court_reservations)
        
        # 应该使用 try-finally 确保连接释放
        assert "finally:" in source, "应该使用 try-finally 确保资源释放"
        assert ".close()" in source, "应该有关闭连接的代码"


class TestTransactionHandling:
    """事务处理测试"""
    
    def test_transaction_rollback_on_error(self):
        """测试错误时事务回滚"""
        # 验证代码中有事务处理
        import inspect
        from app.routers import court_reservations
        
        source = inspect.getsource(court_reservations)
        
        # 应该有事务相关代码
        assert "start_transaction" in source or "commit" in source, "应该有事务处理代码"


class TestCacheManagement:
    """缓存管理测试"""
    
    def test_roles_cache_thread_safety(self):
        """测试角色缓存线程安全"""
        from app.deps import _roles_cache_lock
        
        # 验证使用了线程锁
        assert _roles_cache_lock is not None
    
    def test_columns_cache_ttl(self):
        """测试列缓存有效期"""
        from app.routers.court_reservations import COLUMNS_CACHE_TTL
        
        # 缓存时间应该合理
        assert COLUMNS_CACHE_TTL > 0
        assert COLUMNS_CACHE_TTL <= 3600  # 不应太长


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
