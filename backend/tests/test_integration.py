"""
数据库集成测试

需要数据库连接的完整 API 测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

# 创建测试客户端
client = TestClient(app)


class TestDatabaseConnection:
    """数据库连接测试"""
    
    def test_database_connection(self):
        """测试数据库可以正常连接"""
        from app.database import get_db
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        db.close()
        
        assert result == (1,), "数据库连接失败"
    
    def test_tables_exist(self):
        """测试核心表是否存在"""
        from app.database import get_db
        
        required_tables = [
            'members', 'courts', 'court_reservations', 
            'orders', 'products', 'users'
        ]
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        db.close()
        
        missing_tables = [t for t in required_tables if t not in tables]
        assert len(missing_tables) == 0, f"缺少表: {missing_tables}"


class TestHealthEndpoints:
    """健康检查接口测试"""
    
    def test_ping(self):
        """测试 ping 接口"""
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {"msg": "pong"}
    
    def test_health_check(self):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAuthAPI:
    """认证 API 测试"""
    
    def test_login_missing_credentials(self):
        """测试登录缺少凭证"""
        response = client.post("/api/auth/token", data={})
        assert response.status_code == 422  # FastAPI 验证错误
    
    def test_login_invalid_credentials(self):
        """测试无效凭证登录"""
        response = client.post(
            "/api/auth/token",
            data={"username": "nonexistent_user_xyz", "password": "wrong_password"}
        )
        assert response.status_code == 400
        assert "用户名或密码错误" in response.json().get("detail", "")
    
    def test_login_with_valid_admin(self):
        """测试有效管理员登录（如果存在默认管理员）"""
        from app.database import get_db
        
        # 先查询是否有管理员账户
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT username FROM users WHERE is_active = 1 LIMIT 1")
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        if not user:
            pytest.skip("没有可用的测试用户")
        
        # 注意：这里不知道密码，所以只测试用户存在的情况
        response = client.post(
            "/api/auth/token",
            data={"username": user["username"], "password": "wrong"}
        )
        # 用户存在但密码错误应该返回 400
        assert response.status_code == 400


class TestProtectedEndpoints:
    """受保护接口测试"""
    
    def test_members_without_token(self):
        """测试无 Token 访问会员列表"""
        response = client.get("/api/members")
        # 根据实际情况，可能是 200（无认证）或 401（需要认证）
        # 这里我们只是记录实际行为
        print(f"无 Token 访问 /api/members 返回: {response.status_code}")
        # 如果返回 200，说明接口没有认证保护（这是一个风险）
        if response.status_code == 200:
            print("警告: /api/members 接口没有认证保护!")
    
    def test_members_with_invalid_token(self):
        """测试无效 Token 访问会员列表"""
        response = client.get(
            "/api/members",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )
        assert response.status_code == 401, "无效 Token 应该返回 401"
    
    def test_courts_list(self):
        """测试场地列表接口"""
        response = client.get("/api/courts")
        print(f"访问 /api/courts 返回: {response.status_code}")
        # 记录是否需要认证
        if response.status_code == 200:
            data = response.json()
            print(f"场地数量: {len(data) if isinstance(data, list) else 'N/A'}")
    
    def test_products_list(self):
        """测试商品列表接口"""
        response = client.get("/api/products")
        print(f"访问 /api/products 返回: {response.status_code}")


class TestCourtReservationAPI:
    """场地预约 API 测试"""
    
    def test_list_reservations(self):
        """测试预约列表接口"""
        response = client.get("/api/court-reservations")
        print(f"访问 /api/court-reservations 返回: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"预约记录数: {len(data) if isinstance(data, list) else 'N/A'}")
    
    def test_create_reservation_without_auth(self):
        """测试无认证创建预约"""
        response = client.post(
            "/api/court-reservations",
            json={
                "court_id": 1,
                "start_time": "2026-01-29 14:00:00",
                "end_time": "2026-01-29 16:00:00"
            }
        )
        # 应该返回 401 未授权
        assert response.status_code == 401, f"创建预约应该需要认证，实际返回: {response.status_code}"


class TestMemberAuthAPI:
    """会员认证 API 测试"""
    
    def test_member_login_empty_fields(self):
        """测试会员登录空字段"""
        response = client.post(
            "/api/member-auth/token",
            data={"username": "", "password": ""}
        )
        # FastAPI 表单验证会返回 422 或业务验证返回 400
        assert response.status_code in [400, 422]
    
    def test_member_login_invalid(self):
        """测试无效会员登录"""
        response = client.post(
            "/api/member-auth/token",
            data={"username": "13800000000", "password": "wrongpassword"}
        )
        # 应该返回认证失败
        assert response.status_code in [400, 401]
    
    def test_member_profile_without_token(self):
        """测试无 Token 获取会员资料"""
        response = client.get("/api/member-auth/me")
        assert response.status_code in [401, 422]


class TestOrdersAPI:
    """订单 API 测试"""
    
    def test_list_orders_without_auth(self):
        """测试无认证获取订单列表"""
        response = client.get("/api/orders")
        print(f"无认证访问 /api/orders 返回: {response.status_code}")
        # 订单是敏感数据，应该需要认证
        if response.status_code == 200:
            print("警告: /api/orders 接口没有认证保护!")


class TestSQLInjection:
    """SQL 注入测试"""
    
    def test_sql_injection_in_login(self):
        """测试登录接口 SQL 注入防护"""
        malicious_inputs = [
            "' OR '1'='1",
            "admin'--",
            "'; DROP TABLE users;--",
            "1; SELECT * FROM users",
            "' UNION SELECT * FROM users--",
        ]
        
        for payload in malicious_inputs:
            response = client.post(
                "/api/auth/token",
                data={"username": payload, "password": payload}
            )
            # 应该返回正常的认证失败，而不是服务器错误
            assert response.status_code in [400, 401, 422], \
                f"SQL 注入测试失败，payload: {payload}, status: {response.status_code}"
    
    def test_sql_injection_in_member_login(self):
        """测试会员登录 SQL 注入防护"""
        payload = "' OR '1'='1"
        response = client.post(
            "/api/member-auth/token",
            data={"username": payload, "password": payload}
        )
        assert response.status_code in [400, 401, 422]
    
    def test_sql_injection_in_query_params(self):
        """测试查询参数 SQL 注入防护"""
        # 测试会员列表的关键字搜索
        payload = "'; DROP TABLE members;--"
        response = client.get(f"/api/members?keyword={payload}")
        # 不应该导致服务器错误
        assert response.status_code < 500, "SQL 注入导致服务器错误"


class TestXSSPrevention:
    """XSS 防护测试"""
    
    def test_xss_in_login_response(self):
        """测试登录响应中的 XSS 防护"""
        xss_payload = "<script>alert('xss')</script>"
        response = client.post(
            "/api/auth/token",
            data={"username": xss_payload, "password": "test"}
        )
        
        # 响应中不应该直接包含未转义的脚本
        response_text = response.text.lower()
        # JSON 响应中的 < > 应该被转义或不应该原样返回
        if "<script>" in response_text:
            print("警告: 响应中可能存在 XSS 风险")


class TestDataIntegrity:
    """数据完整性测试"""
    
    def test_members_data_format(self):
        """测试会员数据格式"""
        response = client.get("/api/members")
        if response.status_code != 200:
            pytest.skip("无法访问会员接口")
        
        data = response.json()
        if "items" in data:
            items = data["items"]
        else:
            items = data if isinstance(data, list) else []
        
        if items:
            member = items[0]
            # 检查必要字段
            expected_fields = ["id", "name", "phone"]
            for field in expected_fields:
                assert field in member, f"会员数据缺少字段: {field}"
    
    def test_courts_data_format(self):
        """测试场地数据格式"""
        response = client.get("/api/courts")
        if response.status_code != 200:
            pytest.skip("无法访问场地接口")
        
        data = response.json()
        courts = data if isinstance(data, list) else data.get("items", [])
        
        if courts:
            court = courts[0]
            expected_fields = ["id", "name"]
            for field in expected_fields:
                assert field in court, f"场地数据缺少字段: {field}"


class TestErrorHandling:
    """错误处理测试"""
    
    def test_404_not_found(self):
        """测试 404 错误"""
        response = client.get("/api/nonexistent_endpoint_xyz")
        assert response.status_code == 404
    
    def test_invalid_json_body(self):
        """测试无效 JSON 请求体"""
        response = client.post(
            "/api/court-reservations",
            content="not valid json {{{",
            headers={"Content-Type": "application/json"}
        )
        # 应该返回 4xx 错误，而不是 500
        assert response.status_code < 500
    
    def test_invalid_id_parameter(self):
        """测试无效 ID 参数"""
        response = client.get("/api/members?page=abc")
        # 应该返回验证错误
        assert response.status_code in [200, 422]  # 可能忽略无效参数或返回验证错误


class TestReportsAPI:
    """报表 API 测试"""
    
    def test_overview_report(self):
        """测试概览报表"""
        response = client.get("/api/reports/overview")
        print(f"访问 /api/reports/overview 返回: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"报表数据: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")


class TestSystemSettings:
    """系统设置 API 测试"""
    
    def test_grouped_settings(self):
        """测试分组设置"""
        response = client.get("/api/system-settings/grouped")
        print(f"访问 /api/system-settings/grouped 返回: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
