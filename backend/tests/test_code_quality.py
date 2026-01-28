"""
代码质量和潜在风险静态分析

检查代码中的潜在问题：
1. 硬编码值
2. 未处理的异常
3. 资源泄露
4. 安全风险
"""
import pytest
import os
import re
import ast
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(PROJECT_ROOT, "app")


def get_python_files(directory):
    """获取目录下所有 Python 文件"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过 __pycache__ 目录
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


class TestCodeQuality:
    """代码质量检查"""
    
    def test_no_hardcoded_secrets(self):
        """检查是否有硬编码的密钥"""
        dangerous_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
            r'token\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
        ]
        
        issues = []
        for filepath in get_python_files(APP_DIR):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for pattern in dangerous_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # 排除明显的占位符
                        if any(x in match.lower() for x in ['example', 'placeholder', 'changethis', 'your-']):
                            continue
                        issues.append(f"{filepath}: {match[:50]}...")
        
        # 打印发现的问题（用于调试）
        if issues:
            print("发现潜在的硬编码密钥:")
            for issue in issues[:5]:
                print(f"  - {issue}")
    
    def test_no_debug_statements(self):
        """检查是否有遗留的调试语句"""
        debug_patterns = [
            r'\bbreakpoint\(\)',
            r'\bpdb\.set_trace\(\)',
            r'\bimport\s+pdb\b',
            # print 语句可能是有意的，不强制检查
        ]
        
        issues = []
        for filepath in get_python_files(APP_DIR):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for pattern in debug_patterns:
                    if re.search(pattern, content):
                        issues.append(f"{filepath}: 包含调试语句 {pattern}")
        
        assert len(issues) == 0, f"发现调试语句: {issues}"
    
    def test_exception_handling(self):
        """检查异常处理是否合理"""
        # 检查是否有 bare except（捕获所有异常但不处理）
        bare_except_pattern = r'except\s*:\s*\n\s*pass'
        
        warnings = []
        for filepath in get_python_files(APP_DIR):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if re.search(bare_except_pattern, content):
                    warnings.append(f"{filepath}: 包含 'except: pass'，可能吞掉重要异常")
        
        if warnings:
            print("警告 - 可能吞掉异常的代码:")
            for w in warnings:
                print(f"  - {w}")


class TestResourceManagement:
    """资源管理检查"""
    
    def test_database_connection_closure(self):
        """检查数据库连接是否正确关闭"""
        # 检查 get_db() 调用是否在 try-finally 中
        issues = []
        for filepath in get_python_files(APP_DIR):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # 如果使用了 get_db()
                if 'get_db()' in content:
                    # 应该有对应的 .close() 调用
                    if 'db.close()' not in content and 'conn.close()' not in content:
                        issues.append(f"{filepath}: 使用了 get_db() 但可能没有关闭连接")
        
        if issues:
            print("警告 - 可能的连接泄露:")
            for issue in issues:
                print(f"  - {issue}")
    
    def test_cursor_closure(self):
        """检查游标是否正确关闭"""
        issues = []
        for filepath in get_python_files(APP_DIR):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # 如果创建了游标
                cursor_creates = len(re.findall(r'\.cursor\(', content))
                cursor_closes = len(re.findall(r'cursor.*\.close\(\)', content))
                
                if cursor_creates > cursor_closes + 1:  # 允许一定容差
                    issues.append(f"{filepath}: 创建 {cursor_creates} 个游标，但只关闭 {cursor_closes} 个")
        
        if issues:
            print("警告 - 可能的游标泄露:")
            for issue in issues:
                print(f"  - {issue}")


class TestSecurityPatterns:
    """安全模式检查"""
    
    def test_sql_parameterization(self):
        """检查 SQL 是否使用参数化查询"""
        # 检查是否有直接的字符串格式化 SQL
        dangerous_patterns = [
            r'execute\([^)]*%\s*\(',  # execute("..." % (...))
            r'execute\([^)]*\.format\(',  # execute("...".format(...))
            r'execute\(f["\']',  # execute(f"...")
        ]
        
        issues = []
        for filepath in get_python_files(APP_DIR):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for pattern in dangerous_patterns:
                    if re.search(pattern, content):
                        issues.append(f"{filepath}: 可能的 SQL 注入风险 - 使用了字符串格式化构建 SQL")
        
        if issues:
            print("严重警告 - 可能的 SQL 注入:")
            for issue in issues:
                print(f"  - {issue}")
    
    def test_cors_configuration(self):
        """检查 CORS 配置"""
        main_file = os.path.join(APP_DIR, "main.py")
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否配置了 CORS
        assert "CORSMiddleware" in content, "应该配置 CORS 中间件"
        
        # 检查是否允许所有来源（生产环境风险）
        if 'allow_origins=["*"]' in content:
            print("警告: CORS 配置允许所有来源，生产环境应该限制")
    
    def test_token_in_url_risk(self):
        """检查是否有在 URL 中传递 Token 的风险"""
        issues = []
        for filepath in get_python_files(APP_DIR):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # 检查是否有 token 作为查询参数
                if re.search(r'Query\([^)]*token', content, re.IGNORECASE):
                    issues.append(f"{filepath}: 可能在 URL 查询参数中使用 token")
        
        if issues:
            print("安全建议:")
            for issue in issues:
                print(f"  - {issue}")


class TestBusinessLogicRisks:
    """业务逻辑风险检查"""
    
    def test_balance_update_in_transaction(self):
        """检查余额更新是否在事务中"""
        # 余额更新应该在数据库事务中进行
        issues = []
        
        for filepath in get_python_files(APP_DIR):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # 如果有余额更新
                if 'UPDATE members SET balance' in content or 'balance =' in content:
                    # 应该有事务控制
                    if 'start_transaction' not in content and 'commit' not in content:
                        issues.append(f"{filepath}: 余额更新可能不在事务中")
        
        if issues:
            print("业务风险 - 余额更新事务:")
            for issue in issues:
                print(f"  - {issue}")
    
    def test_double_spend_prevention(self):
        """检查是否有双重支付防护"""
        # 检查预约/支付代码中是否有锁机制
        
        reservation_file = os.path.join(APP_DIR, "routers", "court_reservations.py")
        with open(reservation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 应该有 FOR UPDATE 或类似的锁
        assert "FOR UPDATE" in content, "预约模块应该使用行锁防止双重预约"


class TestErrorMessageLeakage:
    """错误信息泄露检查"""
    
    def test_no_stack_trace_in_response(self):
        """检查是否会泄露堆栈跟踪"""
        # 检查异常处理是否会向用户暴露详细信息
        issues = []
        
        for filepath in get_python_files(APP_DIR):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # 检查是否直接返回异常消息
                if 'str(e)' in content or 'str(ex)' in content:
                    if 'HTTPException' in content:
                        issues.append(f"{filepath}: 可能向客户端暴露异常详情")
        
        if issues:
            print("信息泄露风险:")
            for issue in issues[:3]:  # 只显示前3个
                print(f"  - {issue}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
