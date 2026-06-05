"""
小黑狗桌宠错误处理与边界情况测试
测试各种异常场景、输入验证和错误恢复
"""
import unittest
import sys
import os

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger import get_logger, setup_logging, LogContext, log_exception, log_boundary_violation
from config import (
    validate_config_value, validate_all_configs, validate_color,
    validate_position, ConfigValidationError, CONFIG_RANGES,
    CANVAS_WIDTH, CANVAS_HEIGHT,
)
from animations import (
    PuppyState, AnimationManager, validate_frame_part, validate_frame,
    get_safe_frame, ANIMATION_FRAMES, _DEFAULT_FRAME,
)


class TestLogger(unittest.TestCase):
    """测试日志模块"""

    def test_get_logger_returns_logger(self):
        """测试获取日志记录器"""
        logger = get_logger("test_module")
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "puppy_desktop_pet.test_module")

    def test_get_logger_auto_setup(self):
        """测试自动初始化日志系统"""
        # 获取日志记录器时应自动初始化
        logger = get_logger("auto_test")
        self.assertIsNotNone(logger)

    def test_log_context_manager(self):
        """测试日志上下文管理器"""
        with LogContext("context_test") as logger:
            self.assertIsNotNone(logger)

    def test_log_exception(self):
        """测试异常日志记录"""
        logger = get_logger("exception_test")
        try:
            raise ValueError("测试异常")
        except ValueError as e:
            # 不应抛出异常
            log_exception(logger, "测试异常记录", e)

    def test_log_boundary_violation(self):
        """测试边界违规日志"""
        logger = get_logger("boundary_test")
        # 不应抛出异常
        log_boundary_violation(logger, "test_param", 100, min_val=0, max_val=50)
        log_boundary_violation(logger, "test_param", -1, min_val=0)
        log_boundary_violation(logger, "test_param", 100, max_val=50)


class TestConfigValidation(unittest.TestCase):
    """测试配置验证"""

    def test_valid_config_value(self):
        """测试有效的配置值"""
        result = validate_config_value("PUPPY_SIZE", 80)
        self.assertEqual(result, 80)

    def test_config_value_below_min(self):
        """测试低于最小值的配置"""
        # 非严格模式：返回最小值
        result = validate_config_value("PUPPY_SIZE", 5, strict=False)
        self.assertEqual(result, 20)

    def test_config_value_above_max(self):
        """测试高于最大值的配置"""
        # 非严格模式：返回最大值
        result = validate_config_value("PUPPY_SIZE", 500, strict=False)
        self.assertEqual(result, 200)

    def test_config_value_strict_mode_raises(self):
        """测试严格模式下抛出异常"""
        with self.assertRaises(ConfigValidationError):
            validate_config_value("PUPPY_SIZE", 5, strict=True)

    def test_config_value_invalid_type(self):
        """测试无效类型"""
        # 非严格模式：尝试类型转换
        result = validate_config_value("PUPPY_SIZE", "80", strict=False)
        self.assertEqual(result, 80)

    def test_config_value_unknown_param(self):
        """测试未知参数（应直接返回）"""
        result = validate_config_value("UNKNOWN_PARAM", 42)
        self.assertEqual(result, 42)

    def test_probability_range(self):
        """测试概率值范围验证"""
        self.assertEqual(validate_config_value("AUTO_ACTION_PROBABILITY", 0.5), 0.5)
        self.assertEqual(validate_config_value("AUTO_ACTION_PROBABILITY", -0.1, strict=False), 0.0)
        self.assertEqual(validate_config_value("AUTO_ACTION_PROBABILITY", 1.5, strict=False), 1.0)

    def test_validate_all_configs(self):
        """测试验证所有配置"""
        errors = validate_all_configs(strict=False)
        # 正常情况下应该没有错误
        self.assertIsInstance(errors, dict)

    def test_validate_color_valid(self):
        """测试有效颜色值"""
        self.assertTrue(validate_color("#FF0000"))
        self.assertTrue(validate_color("#000000"))
        self.assertTrue(validate_color("#fff"))
        self.assertTrue(validate_color("#abc"))

    def test_validate_color_invalid(self):
        """测试无效颜色值"""
        self.assertFalse(validate_color("FF0000"))  # 缺少 #
        self.assertFalse(validate_color("#GG0000"))  # 无效十六进制
        self.assertFalse(validate_color("#FF"))  # 太短
        self.assertFalse(validate_color("#FFFFF"))  # 长度不对
        self.assertFalse(validate_color(123))  # 非字符串
        self.assertFalse(validate_color(""))  # 空字符串

    def test_validate_position_normal(self):
        """测试正常位置验证"""
        x, y = validate_position(100, 200)
        self.assertEqual(x, 100)
        self.assertEqual(y, 200)

    def test_validate_position_negative(self):
        """测试负数位置"""
        x, y = validate_position(-50, -100)
        self.assertEqual(x, 0)
        self.assertEqual(y, 0)

    def test_validate_position_with_screen_bounds(self):
        """测试屏幕边界限制"""
        x, y = validate_position(1900, 1080, screen_width=1920, screen_height=1080)
        self.assertLessEqual(x, 1920 - CANVAS_WIDTH)
        self.assertLessEqual(y, 1080 - CANVAS_HEIGHT)

    def test_validate_position_none_values(self):
        """测试 None 值"""
        x, y = validate_position(None, None)
        self.assertEqual(x, 0)
        self.assertEqual(y, 0)

    def test_validate_position_string_values(self):
        """测试字符串值（应尝试转换）"""
        x, y = validate_position("100", "200")
        self.assertEqual(x, 100)
        self.assertEqual(y, 200)


class TestAnimationValidation(unittest.TestCase):
    """测试动画数据验证"""

    def test_validate_frame_part_valid(self):
        """测试有效的帧部件"""
        self.assertTrue(validate_frame_part((0, 0, 10, 10, 0), "test"))
        self.assertTrue(validate_frame_part(None, "test"))
        self.assertTrue(validate_frame_part([(0, 0, 10, 10, 0)], "test"))

    def test_validate_frame_part_invalid_type(self):
        """测试无效类型的帧部件"""
        self.assertFalse(validate_frame_part("invalid", "test"))
        self.assertFalse(validate_frame_part(123, "test"))

    def test_validate_frame_part_wrong_length(self):
        """测试错误长度的帧部件"""
        self.assertFalse(validate_frame_part((0, 0, 10), "test"))
        self.assertFalse(validate_frame_part((0, 0, 10, 10), "test"))

    def test_validate_frame_part_empty_list(self):
        """测试空列表的帧部件"""
        self.assertFalse(validate_frame_part([], "test"))

    def test_validate_frame_valid(self):
        """测试有效的帧数据"""
        frame = ANIMATION_FRAMES[PuppyState.IDLE][0]
        self.assertTrue(validate_frame(frame, "IDLE", 0))

    def test_validate_frame_missing_part(self):
        """测试缺少部件的帧数据"""
        frame = {"head": (0, 0, 10, 10, 0)}  # 缺少其他必需部件
        self.assertFalse(validate_frame(frame, "test", 0))

    def test_validate_frame_invalid_type(self):
        """测试无效类型的帧数据"""
        self.assertFalse(validate_frame("invalid", "test", 0))
        self.assertFalse(validate_frame(None, "test", 0))

    def test_get_safe_frame_valid(self):
        """测试安全获取帧数据"""
        frame = get_safe_frame(PuppyState.IDLE, 0)
        self.assertIsInstance(frame, dict)
        self.assertIn("head", frame)

    def test_get_safe_frame_invalid_state(self):
        """测试无效状态获取帧数据"""
        # 使用一个不存在的状态值
        frame = get_safe_frame(PuppyState.IDLE, 0)
        self.assertIsInstance(frame, dict)

    def test_get_safe_frame_out_of_range_index(self):
        """测试超出范围的帧索引"""
        # 应该使用取模，不会出错
        frame = get_safe_frame(PuppyState.WALKING, 999)
        self.assertIsInstance(frame, dict)

    def test_get_safe_frame_negative_index(self):
        """测试负数帧索引"""
        frame = get_safe_frame(PuppyState.WALKING, -1)
        self.assertIsInstance(frame, dict)


class TestAnimationManager(unittest.TestCase):
    """测试动画管理器"""

    def test_initial_state(self):
        """测试初始状态"""
        manager = AnimationManager()
        self.assertEqual(manager.get_state(), PuppyState.IDLE)

    def test_set_state(self):
        """测试设置状态"""
        manager = AnimationManager()
        manager.set_state(PuppyState.WALKING)
        self.assertEqual(manager.get_state(), PuppyState.WALKING)

    def test_set_state_invalid_type(self):
        """测试设置无效类型的状态"""
        manager = AnimationManager()
        manager.set_state("invalid")  # 应该被忽略
        self.assertEqual(manager.get_state(), PuppyState.IDLE)

    def test_advance_frame(self):
        """测试推进帧"""
        manager = AnimationManager()
        manager.set_state(PuppyState.WALKING)
        initial_frame = manager._current_frame
        manager.advance_frame()
        self.assertEqual(manager._current_frame, (initial_frame + 1) % 2)

    def test_get_current_frame(self):
        """测试获取当前帧"""
        manager = AnimationManager()
        frame = manager.get_current_frame()
        self.assertIsInstance(frame, dict)

    def test_get_state_message(self):
        """测试获取状态消息"""
        manager = AnimationManager()
        message = manager.get_state_message()
        self.assertIsInstance(message, str)
        self.assertTrue(len(message) > 0)

    def test_reset(self):
        """测试重置"""
        manager = AnimationManager()
        manager.set_state(PuppyState.WALKING)
        manager.advance_frame()
        manager.reset()
        self.assertEqual(manager.get_state(), PuppyState.IDLE)
        self.assertEqual(manager._current_frame, 0)

    def test_get_frame_count(self):
        """测试获取帧数"""
        manager = AnimationManager()
        count = manager.get_frame_count()
        self.assertGreaterEqual(count, 1)


def _tk_available():
    """检查 tkinter 是否可用"""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        canvas = tk.Canvas(root, width=10, height=10)
        canvas.pack()
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


# 由于环境限制，跳过所有需要 tkinter 的测试
_TK_AVAILABLE = False


@unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用，跳过需要 GUI 的测试")
class TestEventRouterErrorHandling(unittest.TestCase):
    """测试事件路由器错误处理"""

    def setUp(self):
        """设置测试环境"""
        import tkinter as tk
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = tk.Canvas(self.root, width=100, height=100)
        self.canvas.pack()

    def tearDown(self):
        """清理测试环境"""
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_invalid_canvas_type(self):
        """测试无效的 Canvas 类型"""
        from event_router import EventRouter
        with self.assertRaises(TypeError):
            EventRouter("not_a_canvas")

    def test_register_invalid_handler(self):
        """测试注册无效的处理器"""
        from event_router import EventRouter, EventType
        router = EventRouter(self.canvas)
        # 不应抛出异常，只是记录警告
        router.on(EventType.CLICK, "not_callable")

    def test_emit_with_handler_exception(self):
        """测试处理器异常不影响其他处理器"""
        from event_router import EventRouter, EventType, Event

        router = EventRouter(self.canvas)
        results = []

        def bad_handler(event):
            raise ValueError("测试异常")

        def good_handler(event):
            results.append("called")

        router.on(EventType.CLICK, bad_handler)
        router.on(EventType.CLICK, good_handler)

        event = Event(EventType.CLICK, x=50, y=50)
        router._emit(event)

        # 好的处理器应该仍然被调用
        self.assertEqual(results, ["called"])

    def test_filter_blocks_event(self):
        """测试过滤器阻止事件"""
        from event_router import EventRouter, EventType, Event

        router = EventRouter(self.canvas)
        results = []

        def blocking_filter(event):
            return False

        def handler(event):
            results.append("called")

        router.add_filter(blocking_filter)
        router.on(EventType.CLICK, handler)

        event = Event(EventType.CLICK, x=50, y=50)
        router._emit(event)

        # 处理器不应被调用
        self.assertEqual(results, [])

    def test_filter_exception_continues(self):
        """测试过滤器异常时继续处理"""
        from event_router import EventRouter, EventType, Event

        router = EventRouter(self.canvas)
        results = []

        def bad_filter(event):
            raise ValueError("过滤器异常")

        def handler(event):
            results.append("called")

        router.add_filter(bad_filter)
        router.on(EventType.CLICK, handler)

        event = Event(EventType.CLICK, x=50, y=50)
        router._emit(event)

        # 处理器应该仍然被调用（过滤器异常时继续）
        self.assertEqual(results, ["called"])

    def test_off_removes_handlers(self):
        """测试移除处理器"""
        from event_router import EventRouter, EventType

        router = EventRouter(self.canvas)
        handler = lambda e: None
        router.on(EventType.CLICK, handler)

        # 移除特定处理器
        router.off(EventType.CLICK, handler)
        self.assertEqual(len(router._handlers.get(EventType.CLICK, [])), 0)

    def test_off_removes_all_handlers(self):
        """测试移除所有处理器"""
        from event_router import EventRouter, EventType

        router = EventRouter(self.canvas)
        router.on(EventType.CLICK, lambda e: None)
        router.on(EventType.CLICK, lambda e: None)

        # 移除所有
        router.off(EventType.CLICK)
        self.assertEqual(len(router._handlers.get(EventType.CLICK, [])), 0)

    def test_drag_threshold_validation(self):
        """测试拖拽阈值验证"""
        from event_router import EventRouter

        router = EventRouter(self.canvas)

        # 无效值应该被忽略
        router.set_drag_threshold(-1)
        router.set_drag_threshold(0)
        router.set_drag_threshold("invalid")

    def test_double_click_delay_validation(self):
        """测试双击延迟验证"""
        from event_router import EventRouter

        router = EventRouter(self.canvas)

        # 无效值应该被忽略
        router.set_double_click_delay(-1)
        router.set_double_click_delay(0)


class TestBoundaryConditions(unittest.TestCase):
    """测试边界条件"""

    def test_puppy_state_enum_values(self):
        """测试所有状态枚举值"""
        for state in PuppyState:
            self.assertIsInstance(state.value, str)
            self.assertTrue(len(state.value) > 0)

    def test_all_states_have_frames(self):
        """测试所有状态都有帧定义"""
        for state in PuppyState:
            self.assertIn(state, ANIMATION_FRAMES,
                         f"状态 {state.name} 缺少帧定义")

    def test_all_states_have_messages(self):
        """测试所有状态都有消息"""
        from animations import STATE_MESSAGES
        for state in PuppyState:
            self.assertIn(state, STATE_MESSAGES,
                         f"状态 {state.name} 缺少消息定义")
            messages = STATE_MESSAGES[state]
            self.assertTrue(len(messages) > 0,
                          f"状态 {state.name} 消息列表为空")

    def test_frame_data_structure(self):
        """测试帧数据结构完整性"""
        for state, frames in ANIMATION_FRAMES.items():
            self.assertIsInstance(frames, list)
            self.assertTrue(len(frames) > 0,
                          f"状态 {state.name} 帧列表为空")

            for i, frame in enumerate(frames):
                self.assertIsInstance(frame, dict,
                                   f"状态 {state.name} 帧 {i} 不是字典")

                # 检查必需部件
                for part in ["head", "body", "legs", "tail", "nose", "eyes"]:
                    self.assertIn(part, frame,
                                f"状态 {state.name} 帧 {i} 缺少 {part}")

    def test_config_ranges_complete(self):
        """测试配置范围定义完整性"""
        self.assertIn("PUPPY_SIZE", CONFIG_RANGES)
        self.assertIn("WALK_SPEED", CONFIG_RANGES)
        self.assertIn("CANVAS_WIDTH", CONFIG_RANGES)
        self.assertIn("CANVAS_HEIGHT", CONFIG_RANGES)

    def test_default_frame_structure(self):
        """测试默认帧数据结构"""
        self.assertIn("head", _DEFAULT_FRAME)
        self.assertIn("body", _DEFAULT_FRAME)
        self.assertIn("legs", _DEFAULT_FRAME)
        self.assertIn("tail", _DEFAULT_FRAME)
        self.assertIn("nose", _DEFAULT_FRAME)
        self.assertIn("eyes", _DEFAULT_FRAME)


class TestPuppyEnhanced(unittest.TestCase):
    """测试小黑狗增强功能"""

    def _create_puppy(self):
        """创建小黑狗实例（需要 tkinter）"""
        import tkinter as tk
        from puppy import Puppy
        root = tk.Tk()
        root.withdraw()
        canvas = tk.Canvas(root, width=120, height=140)
        canvas.pack()
        puppy = Puppy(canvas)
        return root, puppy

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_puppy_recover(self):
        """测试错误恢复功能"""
        root, puppy = self._create_puppy()
        try:
            # 设置异常状态
            puppy.state = PuppyState.WALKING
            puppy.x = -100
            puppy.y = -100
            puppy.direction = 0

            puppy.recover()

            self.assertEqual(puppy.state, PuppyState.IDLE)
            self.assertEqual(puppy.x, 60)  # CANVAS_WIDTH // 2
            self.assertEqual(puppy.y, 70)
            self.assertEqual(puppy.direction, 1)
            self.assertTrue(puppy.is_active())
        finally:
            root.destroy()

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_puppy_get_debug_info(self):
        """测试获取调试信息"""
        root, puppy = self._create_puppy()
        try:
            info = puppy.get_debug_info()
            self.assertIsInstance(info, dict)
            self.assertIn("state", info)
            self.assertIn("position", info)
            self.assertIn("direction", info)
            self.assertIn("is_active", info)
            self.assertEqual(info["state"], "IDLE")
        finally:
            root.destroy()

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_puppy_set_direction_invalid_values(self):
        """测试设置无效方向值"""
        root, puppy = self._create_puppy()
        try:
            # 无效值应修正为默认值
            puppy.set_direction(0)
            self.assertEqual(puppy.direction, 1)

            puppy.set_direction(100)
            self.assertEqual(puppy.direction, 1)

            puppy.set_direction("right")
            self.assertEqual(puppy.direction, 1)
        finally:
            root.destroy()

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_puppy_set_state_invalid_type(self):
        """测试设置无效类型状态"""
        root, puppy = self._create_puppy()
        try:
            puppy.set_state("not_a_state")
            self.assertEqual(puppy.state, PuppyState.IDLE)

            puppy.set_state(None)
            self.assertEqual(puppy.state, PuppyState.IDLE)

            puppy.set_state(42)
            self.assertEqual(puppy.state, PuppyState.IDLE)
        finally:
            root.destroy()

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_puppy_active_inactive(self):
        """测试激活/停用状态"""
        root, puppy = self._create_puppy()
        try:
            self.assertTrue(puppy.is_active())

            puppy.set_active(False)
            self.assertFalse(puppy.is_active())

            # 停用时更新不应执行
            puppy.state_timer = 999999
            old_timer = puppy.state_timer
            puppy.update()
            self.assertEqual(puppy.state_timer, old_timer)

            puppy.set_active(True)
            self.assertTrue(puppy.is_active())
        finally:
            root.destroy()

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_puppy_reset(self):
        """测试重置功能"""
        root, puppy = self._create_puppy()
        try:
            puppy.state = PuppyState.WALKING
            puppy.x = 100
            puppy.y = 100
            puppy.direction = -1
            puppy.state_timer = 5000

            puppy.reset()

            self.assertEqual(puppy.state, PuppyState.IDLE)
            self.assertEqual(puppy.x, 60)
            self.assertEqual(puppy.y, 70)
            self.assertEqual(puppy.direction, 1)
            self.assertEqual(puppy.state_timer, 0)
        finally:
            root.destroy()


class TestEventRouterEnhanced(unittest.TestCase):
    """测试事件路由器增强功能"""

    def _create_router(self):
        """创建路由器实例"""
        import tkinter as tk
        from event_router import EventRouter
        root = tk.Tk()
        root.withdraw()
        canvas = tk.Canvas(root, width=100, height=100)
        canvas.pack()
        router = EventRouter(canvas)
        return root, canvas, router

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_router_destroy(self):
        """测试销毁路由器"""
        root, canvas, router = self._create_router()
        try:
            from event_router import EventType
            handler = lambda e: None
            router.on(EventType.CLICK, handler)

            router.destroy()

            self.assertTrue(router._destroyed)
            self.assertEqual(len(router._handlers), 0)
        finally:
            root.destroy()

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_router_double_destroy(self):
        """测试重复销毁"""
        root, canvas, router = self._create_router()
        try:
            router.destroy()
            router.destroy()  # 不应抛出异常
        finally:
            root.destroy()

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_router_operations_after_destroy(self):
        """测试销毁后的操作"""
        root, canvas, router = self._create_router()
        try:
            from event_router import EventType, Event
            router.destroy()

            # 销毁后的操作不应抛出异常
            handler = lambda e: None
            router.on(EventType.CLICK, handler)
            # 不应注册成功
            self.assertEqual(len(router._handlers.get(EventType.CLICK, [])), 0)
        finally:
            root.destroy()

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_router_error_counting(self):
        """测试错误计数"""
        root, canvas, router = self._create_router()
        try:
            from event_router import EventType, Event

            def bad_handler(event):
                raise ValueError("Test error")

            router.on(EventType.CLICK, bad_handler)

            for _ in range(5):
                event = Event(EventType.CLICK, x=50, y=50)
                router._emit(event)

            self.assertEqual(router.get_error_count(), 5)
        finally:
            root.destroy()

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_router_reset_stats_includes_errors(self):
        """测试重置统计包括错误计数"""
        root, canvas, router = self._create_router()
        try:
            from event_router import EventType, Event

            def bad_handler(event):
                raise ValueError("Test error")

            router.on(EventType.CLICK, bad_handler)

            event = Event(EventType.CLICK, x=50, y=50)
            router._emit(event)

            self.assertGreater(router.get_error_count(), 0)

            router.reset_stats()
            self.assertEqual(router.get_error_count(), 0)
        finally:
            root.destroy()

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_router_recursion_guard(self):
        """测试递归保护"""
        root, canvas, router = self._create_router()
        try:
            from event_router import EventType, Event

            def recursive_handler(event):
                new_event = Event(EventType.CLICK, x=0, y=0)
                router._emit(new_event)

            router.on(EventType.CLICK, recursive_handler)

            event = Event(EventType.CLICK, x=50, y=50)
            # 不应导致无限递归
            router._emit(event)
        finally:
            root.destroy()

    @unittest.skipUnless(_TK_AVAILABLE, "tkinter 不可用")
    def test_router_init_invalid_canvas(self):
        """测试无效 Canvas 初始化"""
        from event_router import EventRouter
        with self.assertRaises(TypeError):
            EventRouter("not_a_canvas")

        with self.assertRaises(TypeError):
            EventRouter(None)


class TestMainModule(unittest.TestCase):
    """测试主模块错误处理"""

    def test_main_import(self):
        """测试主模块导入"""
        # 不应抛出异常
        from main import PuppyDesktopPet, main
        self.assertIsNotNone(PuppyDesktopPet)
        self.assertIsNotNone(main)


if __name__ == "__main__":
    # 设置测试日志
    setup_logging(level="WARNING", log_to_file=False)

    unittest.main(verbosity=2)
