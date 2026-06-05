"""
冒泡排序算法实现模块

提供基础冒泡排序和优化版本的实现，包含完整的输入验证和错误处理。
"""

import logging
from typing import Any

# 模块级日志记录器
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 自定义异常
# ──────────────────────────────────────────────

class SortInputError(Exception):
    """排序输入错误基类"""
    pass


class InvalidTypeError(SortInputError):
    """输入类型不正确时抛出"""
    pass


class IncomparableElementsError(SortInputError):
    """列表中包含不可比较的元素时抛出"""
    pass


# ──────────────────────────────────────────────
# 输入验证
# ──────────────────────────────────────────────

def _validate_input(arr: Any) -> None:
    """
    验证排序输入的有效性

    Args:
        arr: 待验证的输入

    Raises:
        InvalidTypeError: 输入不是 list 类型
        IncomparableElementsError: 列表中包含不可比较的元素
    """
    if not isinstance(arr, list):
        logger.warning("输入类型错误: 期望 list, 实际为 %s", type(arr).__name__)
        raise InvalidTypeError(
            f"期望 list 类型, 收到 {type(arr).__name__}"
        )

    if len(arr) <= 1:
        return

    # 检查元素是否可比较：对相邻元素做一次比较测试
    for i in range(len(arr) - 1):
        try:
            _ = arr[i] <= arr[i + 1]
        except TypeError:
            logger.warning(
                "不可比较的元素: arr[%d]=%r (%s) 与 arr[%d]=%r (%s)",
                i, arr[i], type(arr[i]).__name__,
                i + 1, arr[i + 1], type(arr[i + 1]).__name__,
            )
            raise IncomparableElementsError(
                f"列表中包含不可比较的元素: "
                f"arr[{i}]={arr[i]!r} ({type(arr[i]).__name__}) 与 "
                f"arr[{i + 1}]={arr[i + 1]!r} ({type(arr[i + 1]).__name__})"
            )


def bubble_sort(arr: list) -> list:
    """
    冒泡排序算法实现

    Args:
        arr: 待排序的列表

    Returns:
        排序后的新列表（不修改原列表）

    Raises:
        InvalidTypeError: 输入不是 list 类型
        IncomparableElementsError: 列表中包含不可比较的元素

    时间复杂度: O(n²)
    空间复杂度: O(n) - 因为创建了新列表

    示例:
        >>> bubble_sort([64, 34, 25, 12, 22, 11, 90])
        [11, 12, 22, 25, 34, 64, 90]
    """
    _validate_input(arr)

    if not arr:
        logger.debug("输入为空列表，直接返回")
        return []

    logger.debug("开始排序: 列表大小=%d", len(arr))

    # 创建副本，避免修改原数组
    result = arr.copy()
    n = len(result)

    # 外层循环：控制排序轮数
    for i in range(n):
        # 内层循环：比较相邻元素
        for j in range(0, n - i - 1):
            # 如果前一个元素大于后一个，交换它们
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]

    logger.debug("排序完成: 列表大小=%d", len(result))
    return result


def bubble_sort_optimized(arr: list) -> list:
    """
    优化版冒泡排序算法

    使用标志位检测是否已排序完成，提前终止。

    Args:
        arr: 待排序的列表

    Returns:
        排序后的新列表（不修改原列表）

    Raises:
        InvalidTypeError: 输入不是 list 类型
        IncomparableElementsError: 列表中包含不可比较的元素

    时间复杂度: 最好 O(n)，最坏 O(n²)
    空间复杂度: O(n) - 因为创建了新列表
    """
    _validate_input(arr)

    if not arr:
        logger.debug("优化排序: 输入为空列表，直接返回")
        return []

    logger.debug("优化排序开始: 列表大小=%d", len(arr))

    result = arr.copy()
    n = len(result)

    for i in range(n):
        # 标记本轮是否发生交换
        swapped = False

        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
                swapped = True

        # 如果没有发生交换，说明已经排序完成
        if not swapped:
            logger.debug("优化排序: 第 %d 轮无交换，提前终止", i + 1)
            break

    logger.debug("优化排序完成: 列表大小=%d", len(result))
    return result


def bubble_sort_inplace(arr: list) -> None:
    """
    原地冒泡排序（直接修改输入列表）

    Args:
        arr: 待排序的列表（会被直接修改）

    Raises:
        InvalidTypeError: 输入不是 list 类型
        IncomparableElementsError: 列表中包含不可比较的元素

    时间复杂度: O(n²)
    空间复杂度: O(1)
    """
    _validate_input(arr)

    if not arr:
        logger.debug("原地排序: 输入为空列表，跳过")
        return

    logger.debug("原地排序开始: 列表大小=%d", len(arr))

    n = len(arr)

    for i in range(n):
        swapped = False

        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True

        if not swapped:
            logger.debug("原地排序: 第 %d 轮无交换，提前终止", i + 1)
            break

    logger.debug("原地排序完成: 列表大小=%d", len(arr))


# 便捷函数
def sort(arr: list, reverse: bool = False) -> list:
    """
    排序函数，支持升序和降序

    Args:
        arr: 待排序列表
        reverse: 是否降序排序，默认为 False（升序）

    Returns:
        排序后的新列表

    Raises:
        InvalidTypeError: 输入不是 list 类型
        IncomparableElementsError: 列表中包含不可比较的元素
    """
    logger.debug("sort() 调用: reverse=%s", reverse)
    result = bubble_sort(arr)
    if reverse:
        result.reverse()
    return result
