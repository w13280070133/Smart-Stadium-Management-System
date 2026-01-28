"""
安全相关测试

测试：
1. 密码哈希安全性
2. JWT Token 生成和验证
3. 潜在的安全漏洞
"""
import pytest
from datetime import timedelta
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPasswordSecurity:
    """密码安全测试"""
    
    def test_password_hash_different_each_time(self):
        """测试同一密码每次哈希结果不同（使用随机盐）"""
        from app.security import get_password_hash
        
        password = "test123456"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # 哈希应该不同（因为每次使用不同的盐）
        assert hash1 != hash2, "同一密码的多次哈希应该不同（使用随机盐）"
    
    def test_password_verification(self):
        """测试密码验证"""
        from app.security import get_password_hash, verify_password
        
        password = "secure_password_123"
        hashed = get_password_hash(password)
        
        # 正确密码应该验证成功
        assert verify_password(password, hashed) is True
        
        # 错误密码应该验证失败
        assert verify_password("wrong_password", hashed) is False
        assert verify_password("", hashed) is False
        assert verify_password("secure_password_12", hashed) is False  # 少一个字符
    
    def test_empty_password_handling(self):
        """测试空密码处理"""
        from app.security import get_password_hash, verify_password
        
        # 空密码也应该能正常哈希（虽然不建议使用）
        empty_hash = get_password_hash("")
        assert empty_hash is not None
        assert verify_password("", empty_hash) is True
        assert verify_password("non_empty", empty_hash) is False


class TestJWTToken:
    """JWT Token 测试"""
    
    def test_token_creation_and_decoding(self):
        """测试 Token 创建和解码"""
        from app.security import create_access_token, decode_access_token
        
        data = {"sub": "123", "role": "admin"}
        token = create_access_token(data)
        
        # Token 不应该为空
        assert token is not None
        assert len(token) > 0
        
        # 解码后应该包含原始数据
        decoded = decode_access_token(token)
        assert decoded["sub"] == "123"
        assert decoded["role"] == "admin"
        assert "exp" in decoded  # 应该有过期时间
    
    def test_token_expiration(self):
        """测试 Token 过期"""
        from app.security import create_access_token, decode_access_token
        from fastapi import HTTPException
        import time
        
        # 创建一个立即过期的 Token
        data = {"sub": "123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        # 解码过期 Token 应该抛出异常
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)
        assert exc_info.value.status_code == 401
    
    def test_invalid_token_handling(self):
        """测试无效 Token 处理"""
        from app.security import decode_access_token
        from fastapi import HTTPException
        
        invalid_tokens = [
            "invalid_token",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "a.b.c",
        ]
        
        for token in invalid_tokens:
            with pytest.raises(HTTPException) as exc_info:
                decode_access_token(token)
            assert exc_info.value.status_code == 401


class TestConfigSecurity:
    """配置安全测试"""
    
    def test_development_default_values(self):
        """测试开发环境默认值"""
        from app.config import settings
        
        # 开发环境应该有默认值，但应发出警告
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) >= 16  # 最小长度检查


class TestSQLInjectionPrevention:
    """SQL 注入防护测试"""
    
    def test_parameterized_queries_in_auth(self):
        """验证认证模块使用参数化查询"""
        import inspect
        from app.routers import auth
        
        source = inspect.getsource(auth)
        
        # 检查是否使用 %s 占位符（参数化查询）
        assert "%s" in source, "认证模块应该使用参数化查询"
        
        # 检查是否有明显的 SQL 拼接（潜在风险）
        dangerous_patterns = [
            'f"SELECT',
            "f'SELECT",
            '"SELECT " +',
            "'SELECT ' +",
        ]
        for pattern in dangerous_patterns:
            assert pattern not in source, f"发现潜在 SQL 注入风险: {pattern}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
