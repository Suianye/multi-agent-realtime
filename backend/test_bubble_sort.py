"""
冒泡排序模块测试
"""

import logging
import pytest
from bubble_sort import (
    bubble_sort,
    bubble_sort_optimized,
    bubble_sort_inplace,
    sort,
    SortInputError,
    InvalidTypeError,
    IncomparableElementsError,
)


class TestBubbleSort:
    """基础冒泡排序测试"""

    def test_basic_sort(self):
        """测试基本排序功能"""
        assert bubble_sort([64, 34, 25, 12, 22, 11, 90]) == [11, 12, 22, 25, 34, 64, 90]

    def test_empty_list(self):
        """测试空列表"""
        assert bubble_sort([]) == []

    def test_single_element(self):
        """测试单个元素"""
        assert bubble_sort([1]) == [1]

    def test_already_sorted(self):
        """测试已排序列表"""
        assert bubble_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

    def test_reverse_sorted(self):
        """测试逆序列表"""
        assert bubble_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

    def test_duplicates(self):
        """测试包含重复元素"""
        assert bubble_sort([3, 1, 4, 1, 5, 9, 2, 6, 5, 3]) == [1, 1, 2, 3, 3, 4, 5, 5, 6, 9]

    def test_negative_numbers(self):
        """测试负数"""
        assert bubble_sort([-3, -1, -4, -1, -5]) == [-5, -4, -3, -1, -1]

    def test_mixed_numbers(self):
        """测试正负数混合"""
        assert bubble_sort([3, -1, 4, -5, 2]) == [-5, -1, 2, 3, 4]

    def test_not_modify_original(self):
        """测试不修改原列表"""
        original = [3, 1, 2]
        bubble_sort(original)
        assert original == [3, 1, 2]


class TestBubbleSortOptimized:
    """优化版冒泡排序测试"""

    def test_basic_sort(self):
        """测试基本排序功能"""
        assert bubble_sort_optimized([64, 34, 25, 12, 22, 11, 90]) == [11, 12, 22, 25, 34, 64, 90]

    def test_empty_list(self):
        """测试空列表"""
        assert bubble_sort_optimized([]) == []

    def test_already_sorted(self):
        """测试已排序列表（应该提前终止）"""
        assert bubble_sort_optimized([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

    def test_not_modify_original(self):
        """测试不修改原列表"""
        original = [3, 1, 2]
        bubble_sort_optimized(original)
        assert original == [3, 1, 2]


class TestBubbleSortInplace:
    """原地冒泡排序测试"""

    def test_basic_sort(self):
        """测试基本排序功能"""
        arr = [64, 34, 25, 12, 22, 11, 90]
        bubble_sort_inplace(arr)
        assert arr == [11, 12, 22, 25, 34, 64, 90]

    def test_modifies_original(self):
        """测试修改原列表"""
        arr = [3, 1, 2]
        bubble_sort_inplace(arr)
        assert arr == [1, 2, 3]

    def test_empty_list(self):
        """测试空列表"""
        arr = []
        bubble_sort_inplace(arr)
        assert arr == []


class TestSortFunction:
    """sort 便捷函数测试"""

    def test_ascending(self):
        """测试升序排序"""
        assert sort([3, 1, 2]) == [1, 2, 3]

    def test_descending(self):
        """测试降序排序"""
        assert sort([3, 1, 2], reverse=True) == [3, 2, 1]

    def test_empty_list(self):
        """测试空列表"""
        assert sort([]) == []


class TestInputValidation:
    """输入验证测试"""

    def test_non_list_input_string(self):
        """测试传入字符串应抛出 InvalidTypeError"""
        with pytest.raises(InvalidTypeError, match="期望 list 类型"):
            bubble_sort("hello")

    def test_non_list_input_int(self):
        """测试传入整数应抛出 InvalidTypeError"""
        with pytest.raises(InvalidTypeError, match="期望 list 类型"):
            bubble_sort(42)

    def test_non_list_input_none(self):
        """测试传入 None 应抛出 InvalidTypeError"""
        with pytest.raises(InvalidTypeError):
            bubble_sort(None)

    def test_non_list_input_dict(self):
        """测试传入字典应抛出 InvalidTypeError"""
        with pytest.raises(InvalidTypeError):
            bubble_sort({"a": 1})

    def test_optimized_non_list_input(self):
        """测试优化版对非列表输入的验证"""
        with pytest.raises(InvalidTypeError):
            bubble_sort_optimized("not a list")

    def test_inplace_non_list_input(self):
        """测试原地排序对非列表输入的验证"""
        with pytest.raises(InvalidTypeError):
            bubble_sort_inplace(123)

    def test_sort_non_list_input(self):
        """测试便捷函数对非列表输入的验证"""
        with pytest.raises(InvalidTypeError):
            sort(None)


class TestIncomparableElements:
    """不可比较元素测试"""

    def test_mixed_int_string(self):
        """测试列表中混合整数和字符串应抛出 IncomparableElementsError"""
        with pytest.raises(IncomparableElementsError):
            bubble_sort([1, "two", 3])

    def test_list_with_none_element(self):
        """测试列表中包含 None 应抛出 IncomparableElementsError"""
        with pytest.raises(IncomparableElementsError):
            bubble_sort([1, None, 3])

    def test_list_with_dict_element(self):
        """测试列表中包含字典应抛出 IncomparableElementsError"""
        with pytest.raises(IncomparableElementsError):
            bubble_sort([1, {"a": 1}, 3])

    def test_optimized_incomparable(self):
        """测试优化版对不可比较元素的处理"""
        with pytest.raises(IncomparableElementsError):
            bubble_sort_optimized([1, "two", 3])

    def test_inplace_incomparable(self):
        """测试原地排序对不可比较元素的处理"""
        with pytest.raises(IncomparableElementsError):
            bubble_sort_inplace([1, None, 3])


class TestBoundaryCases:
    """边界情况测试"""

    def test_large_list(self):
        """测试大列表排序"""
        import random
        large = random.sample(range(10000), 1000)
        result = bubble_sort(large)
        assert result == sorted(large)

    def test_all_same_elements(self):
        """测试所有元素相同"""
        assert bubble_sort([5, 5, 5, 5, 5]) == [5, 5, 5, 5, 5]

    def test_two_elements(self):
        """测试两个元素"""
        assert bubble_sort([2, 1]) == [1, 2]

    def test_float_elements(self):
        """测试浮点数排序"""
        assert bubble_sort([3.14, 1.41, 2.72]) == [1.41, 2.72, 3.14]

    def test_mixed_int_float(self):
        """测试整数和浮点数混合"""
        assert bubble_sort([3, 1.5, 2]) == [1.5, 2, 3]

    def test_tuple_elements(self):
        """测试元组排序（可比较）"""
        assert bubble_sort([(3, 'c'), (1, 'a'), (2, 'b')]) == [(1, 'a'), (2, 'b'), (3, 'c')]

    def test_generator_input(self):
        """测试生成器输入应抛出 InvalidTypeError（需要 list）"""
        with pytest.raises(InvalidTypeError):
            bubble_sort(x for x in range(5))

    def test_range_input(self):
        """测试 range 输入应抛出 InvalidTypeError（需要 list）"""
        with pytest.raises(InvalidTypeError):
            bubble_sort(range(5))

    def test_sort_with_none_key_uses_bubble_sort(self):
        """测试 sort 函数 reverse=False 时使用 bubble_sort"""
        result = sort([3, 1, 2], reverse=False)
        assert result == [1, 2, 3]


class TestLogging:
    """日志记录测试"""

    def test_sort_logs_operation(self, caplog):
        """测试排序操作会记录日志"""
        with caplog.at_level(logging.DEBUG, logger="bubble_sort"):
            bubble_sort([3, 1, 2])
        assert any("开始排序" in record.message for record in caplog.records)
        assert any("排序完成" in record.message for record in caplog.records)

    def test_sort_logs_size(self, caplog):
        """测试日志包含列表大小信息"""
        with caplog.at_level(logging.DEBUG, logger="bubble_sort"):
            bubble_sort([3, 1, 2])
        size_records = [r for r in caplog.records if "3" in r.message]
        assert len(size_records) > 0

    def test_validation_logs_warning(self, caplog):
        """测试输入验证失败时记录警告日志"""
        with caplog.at_level(logging.WARNING, logger="bubble_sort"):
            try:
                bubble_sort("not a list")
            except InvalidTypeError:
                pass
        assert any("输入类型错误" in record.message for record in caplog.records)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
