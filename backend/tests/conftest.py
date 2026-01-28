"""
pytest 配置文件
"""
import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置测试环境
os.environ.setdefault("ENV", "development")


def pytest_configure(config):
    """pytest 配置钩子"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "database: marks tests that require database connection"
    )
    config.addinivalue_line(
        "markers", "integration: marks integration tests"
    )


@pytest.fixture(scope="session")
def app():
    """创建测试用 FastAPI 应用"""
    try:
        from app.main import app
        return app
    except Exception as e:
        pytest.skip(f"无法导入应用: {e}")


@pytest.fixture(scope="function")
def test_client(app):
    """创建测试客户端"""
    from fastapi.testclient import TestClient
    return TestClient(app)
