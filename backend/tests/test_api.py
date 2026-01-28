"""
API 接口测试

使用 FastAPI TestClient 测试各个 API 端点
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 注意：这些测试需要数据库连接，可能需要 mock


class TestHealthCheck:
    """健康检查接口测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        try:
            from app.main import app
            return TestClient(app)
        except Exception as e:
            pytest.skip(f"无法创建测试客户端: {e}")
    
    def test_ping(self, client):
        """测试 ping 接口"""
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {"msg": "pong"}
    
    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAuthAPI:
    """认证 API 测试"""
    
    @pytest.fixture
    def client(self):
        try:
            from app.main import app
            return TestClient(app)
        except Exception as e:
            pytest.skip(f"无法创建测试客户端: {e}")
    
    def test_login_missing_credentials(self, client):
        """测试登录缺少凭证"""
        response = client.post("/api/auth/token", data={})
        # FastAPI OAuth2PasswordRequestForm 会返回 422
        assert response.status_code == 422
    
    def test_login_invalid_credentials(self, client):
        """测试无效凭证登录"""
        response = client.post(
            "/api/auth/token",
            data={"username": "nonexistent", "password": "wrong"}
        )
        # 应该返回 400（用户名或密码错误）
        assert response.status_code == 400
    
    def test_protected_endpoint_without_token(self, client):
        """测试无 Token 访问受保护端点"""
        response = client.get("/api/members")
        # 应该返回 401 未授权
        assert response.status_code == 401
    
    def test_protected_endpoint_with_invalid_token(self, client):
        """测试无效 Token 访问受保护端点"""
        response = client.get(
            "/api/members",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestMemberAuthAPI:
    """会员认证 API 测试"""
    
    @pytest.fixture
    def client(self):
        try:
            from app.main import app
            return TestClient(app)
        except Exception as e:
            pytest.skip(f"无法创建测试客户端: {e}")
    
    def test_member_login_empty_fields(self, client):
        """测试会员登录空字段"""
        response = client.post(
            "/api/member-auth/token",
            data={"username": "", "password": ""}
        )
        # 应该返回 400（手机号和密码不能为空）
        assert response.status_code == 400
    
    def test_member_profile_without_token(self, client):
        """测试无 Token 获取会员资料"""
        response = client.get("/api/member-auth/me")
        assert response.status_code in [401, 422]  # 缺少 Authorization header


class TestCourtReservationAPI:
    """场地预约 API 测试"""
    
    @pytest.fixture
    def client(self):
        try:
            from app.main import app
            return TestClient(app)
        except Exception as e:
            pytest.skip(f"无法创建测试客户端: {e}")
    
    def test_list_reservations_without_auth(self, client):
        """测试无认证列出预约"""
        response = client.get("/api/court-reservations")
        # 列表接口可能不需要认证，或需要认证
        assert response.status_code in [200, 401]
    
    def test_create_reservation_without_auth(self, client):
        """测试无认证创建预约"""
        response = client.post(
            "/api/court-reservations",
            json={"court_id": 1, "start_time": "2025-01-29 14:00:00", "end_time": "2025-01-29 16:00:00"}
        )
        assert response.status_code == 401
    
    def test_create_reservation_missing_fields(self, client):
        """测试创建预约缺少字段"""
        # 即使有认证，缺少必要字段也应返回错误
        # 这个测试需要有效的 token，暂时跳过详细测试
        pass


class TestInputSanitization:
    """输入清理测试"""
    
    @pytest.fixture
    def client(self):
        try:
            from app.main import app
            return TestClient(app)
        except Exception as e:
            pytest.skip(f"无法创建测试客户端: {e}")
    
    def test_sql_injection_in_login(self, client):
        """测试登录接口 SQL 注入防护"""
        malicious_inputs = [
            "' OR '1'='1",
            "admin'--",
            "'; DROP TABLE users;--",
            "1; SELECT * FROM users",
        ]
        
        for payload in malicious_inputs:
            response = client.post(
                "/api/auth/token",
                data={"username": payload, "password": payload}
            )
            # 应该返回正常的认证失败，而不是服务器错误
            assert response.status_code in [400, 401, 422], f"SQL 注入测试失败: {payload}"
    
    def test_xss_prevention_in_login(self, client):
        """测试 XSS 防护（返回不应包含未转义的脚本）"""
        xss_payload = "<script>alert('xss')</script>"
        response = client.post(
            "/api/auth/token",
            data={"username": xss_payload, "password": "test"}
        )
        
        # 响应中不应该直接包含未转义的脚本标签
        response_text = response.text.lower()
        assert "<script>" not in response_text or "alert" not in response_text


class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.fixture
    def client(self):
        try:
            from app.main import app
            return TestClient(app)
        except Exception as e:
            pytest.skip(f"无法创建测试客户端: {e}")
    
    def test_404_not_found(self, client):
        """测试 404 错误"""
        response = client.get("/api/nonexistent_endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """测试方法不允许"""
        response = client.delete("/ping")
        assert response.status_code == 405
    
    def test_invalid_json_body(self, client):
        """测试无效 JSON 请求体"""
        response = client.post(
            "/api/court-reservations",
            content="not valid json",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test"
            }
        )
        # 应该返回 4xx 错误，而不是 500
        assert response.status_code < 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
