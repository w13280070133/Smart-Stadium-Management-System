"""
业务逻辑测试

测试核心业务功能：
1. 场地预约冲突检测
2. 金额计算
3. 会员折扣
4. 订单创建
"""
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestReservationConflictDetection:
    """预约冲突检测测试"""
    
    def test_conflict_detection_sql_logic(self):
        """测试冲突检测 SQL 逻辑是否正确"""
        # 核心公式：NOT (end_time <= new_start_time OR start_time >= new_end_time)
        # 两个时间段 [A_start, A_end] 和 [B_start, B_end] 冲突当且仅当：
        # A_start < B_end AND A_end > B_start
        
        def is_conflict(existing_start, existing_end, new_start, new_end):
            """模拟冲突检测逻辑"""
            # NOT (end_time <= new_start_time OR start_time >= new_end_time)
            return not (existing_end <= new_start or existing_start >= new_end)
        
        # 测试用例 1: 完全不重叠（新预约在已有预约之后）
        assert is_conflict(10, 12, 12, 14) is False, "边界相邻不应冲突"
        
        # 测试用例 2: 完全不重叠（新预约在已有预约之前）
        assert is_conflict(14, 16, 10, 12) is False, "完全在前不应冲突"
        
        # 测试用例 3: 部分重叠
        assert is_conflict(10, 14, 12, 16) is True, "部分重叠应冲突"
        
        # 测试用例 4: 新预约完全包含在已有预约内
        assert is_conflict(10, 18, 12, 14) is True, "被包含应冲突"
        
        # 测试用例 5: 已有预约完全包含在新预约内
        assert is_conflict(12, 14, 10, 18) is True, "包含已有应冲突"
        
        # 测试用例 6: 完全相同
        assert is_conflict(10, 12, 10, 12) is True, "完全相同应冲突"


class TestAmountCalculation:
    """金额计算测试"""
    
    def test_basic_amount_calculation(self):
        """测试基础金额计算"""
        price_per_hour = 100.0
        duration_hours = 2.5
        
        expected = 250.0
        actual = round(price_per_hour * duration_hours, 2)
        
        assert actual == expected
    
    def test_discount_calculation(self):
        """测试折扣计算"""
        original_amount = 100.0
        discount_rate = 85  # 85折
        
        expected = 85.0
        actual = round(original_amount * discount_rate / 100.0, 2)
        
        assert actual == expected
    
    def test_discount_edge_cases(self):
        """测试折扣边界情况"""
        original_amount = 100.0
        
        # 100折（无折扣）
        assert round(original_amount * 100 / 100.0, 2) == 100.0
        
        # 0折（免费）
        assert round(original_amount * 0 / 100.0, 2) == 0.0
        
        # 超过100的情况（应该不允许，但测试计算）
        assert round(original_amount * 110 / 100.0, 2) == 110.0
    
    def test_floating_point_precision(self):
        """测试浮点数精度问题"""
        # 经典的浮点数精度问题：0.1 + 0.2 != 0.3
        price = 0.1
        hours = 0.2
        
        # 不使用 round 可能会有精度问题
        result = round(price * hours * 1000, 2)  # 模拟更复杂的计算
        assert isinstance(result, float)
        
        # 使用 Decimal 进行精确计算
        from decimal import Decimal
        precise_result = Decimal("0.1") * Decimal("0.2") * Decimal("1000")
        assert float(precise_result) == 20.0


class TestDateTimeHandling:
    """日期时间处理测试"""
    
    def test_date_parsing(self):
        """测试日期解析"""
        date_str = "2025-01-28"
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        
        assert parsed.year == 2025
        assert parsed.month == 1
        assert parsed.day == 28
    
    def test_datetime_parsing_variations(self):
        """测试多种日期时间格式"""
        # 标准格式
        dt1 = datetime.fromisoformat("2025-01-28 14:00:00".replace(" ", "T"))
        assert dt1.hour == 14
        
        # ISO 格式
        dt2 = datetime.fromisoformat("2025-01-28T14:00:00")
        assert dt2.hour == 14
        
        # 验证两种格式解析结果相同
        assert dt1 == dt2
    
    def test_cross_day_reservation(self):
        """测试跨天预约（23:00 - 次日 02:00）"""
        date_str = "2025-01-28"
        base_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        start_dt = base_date.replace(hour=23, minute=0)
        end_dt = (base_date + timedelta(days=1)).replace(hour=2, minute=0)
        
        # 持续时间应该是 3 小时
        duration = (end_dt - start_dt).total_seconds() / 3600
        assert duration == 3.0


class TestOrderNoGeneration:
    """订单号生成测试"""
    
    def test_order_no_format(self):
        """测试订单号格式"""
        from app.services.orders import generate_order_no
        
        order_no = generate_order_no("court")
        
        # 格式：前缀-类型首字母-时间戳
        parts = order_no.split("-")
        assert len(parts) == 3, f"订单号格式不正确: {order_no}"
        assert parts[1] == "C", "场地订单类型应为 C"
    
    def test_order_no_uniqueness(self):
        """测试订单号唯一性"""
        from app.services.orders import generate_order_no
        
        # 生成多个订单号，检查是否唯一
        order_nos = set()
        for _ in range(100):
            order_no = generate_order_no("court")
            order_nos.add(order_no)
        
        assert len(order_nos) == 100, "订单号应该唯一"


class TestMemberBalanceLogic:
    """会员余额逻辑测试"""
    
    def test_balance_deduction(self):
        """测试余额扣减"""
        balance = 1000.0
        amount = 250.0
        
        new_balance = round(balance - amount, 2)
        assert new_balance == 750.0
    
    def test_insufficient_balance(self):
        """测试余额不足检测"""
        balance = 100.0
        amount = 250.0
        
        is_sufficient = balance >= amount
        assert is_sufficient is False
    
    def test_balance_refund(self):
        """测试余额退款"""
        balance = 750.0
        refund_amount = 250.0
        
        new_balance = balance + refund_amount
        assert new_balance == 1000.0
    
    def test_negative_balance_prevention(self):
        """测试防止负余额"""
        balance = 0.0
        amount = 100.0
        
        # 应该在扣款前检查余额
        assert balance < amount, "余额不足时不应允许扣款"


class TestInputValidation:
    """输入验证测试"""
    
    def test_court_id_validation(self):
        """测试场地 ID 验证"""
        # 有效的场地 ID
        valid_ids = [1, 10, 100, 999]
        for id in valid_ids:
            assert isinstance(int(id), int)
        
        # 无效的场地 ID
        invalid_ids = [0, -1, None, "", "abc"]
        for id in invalid_ids:
            try:
                val = int(id) if id else 0
                assert val <= 0 or id is None, f"{id} 应该被识别为无效"
            except (ValueError, TypeError):
                pass  # 预期的异常
    
    def test_phone_format_validation(self):
        """测试手机号格式验证"""
        import re
        
        phone_pattern = r'^1[3-9]\d{9}$'
        
        valid_phones = ["13800138000", "15912345678", "18888888888"]
        invalid_phones = ["123", "12345678901", "23800138000", "1380013800a", "138 0013 8000"]
        
        for phone in valid_phones:
            assert re.match(phone_pattern, phone), f"{phone} 应该是有效手机号"
        
        for phone in invalid_phones:
            assert not re.match(phone_pattern, phone), f"{phone} 应该是无效手机号"
    
    def test_time_range_validation(self):
        """测试时间范围验证"""
        # 有效范围
        assert 0 <= 9 <= 23
        assert 0 <= 18 <= 23
        
        # 结束时间必须大于开始时间
        start_hour = 14
        end_hour = 16
        assert end_hour > start_hour
        
        # 无效：结束时间等于开始时间
        assert not (16 > 16)
        
        # 无效：结束时间小于开始时间
        assert not (14 > 16)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
