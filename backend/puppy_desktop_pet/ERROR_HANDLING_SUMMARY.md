# 错误处理与边界情况 - 增强总结

## 📋 概述

本次增强为小黑狗桌宠添加了全面的错误处理、输入验证、边界情况处理和日志记录功能，提高了程序的健壮性和可维护性。

## 🆕 新增模块

### 1. `error_recovery.py` - 错误恢复模块

提供全局错误处理和恢复机制：

| 组件 | 功能 |
|------|------|
| `GlobalExceptionHandler` | 捕获未处理异常，生成崩溃报告 |
| `ResourceMonitor` | 监控内存使用，防止资源泄漏 |
| `WatchdogTimer` | 检测主循环挂起，触发自动恢复 |
| `InputSanitizer` | 输入消毒（字符串、数字、颜色、坐标） |
| `GracefulShutdown` | 优雅关闭管理器，带超时保护 |
| `safe_execute()` | 安全执行函数，异常时返回默认值 |
| `retry_on_failure()` | 失败重试机制，支持指数退避 |

### 2. 增强的 `logger.py` - 日志模块

新增功能：

| 功能 | 说明 |
|------|------|
| `sanitize_log_message()` | 过滤敏感信息（密码、token、API key） |
| `SensitiveFilter` | 日志过滤器，自动脱敏 |
| `JsonFormatter` | JSON 格式化器，便于日志分析 |
| `log_performance()` | 性能日志记录 |
| `performance_timer` | 性能计时装饰器 |
| `LogManager` | 全局日志管理器 |

## 🔧 增强的模块

### `config.py` - 配置模块

新增验证函数：

```python
validate_timeout()        # 超时值验证
validate_speed()          # 速度值验证（含 NaN/Inf 检查）
validate_probability()    # 概率值验证（0.0 - 1.0）
get_safe_screen_position() # 安全屏幕位置计算
is_valid_hex_color()      # 十六进制颜色验证
clamp_value()             # 值范围限制
```

### `puppy.py` - 小黑狗核心

增强功能：

- `recover()` 返回布尔值表示恢复是否成功
- `safe_update()` 带自动恢复的更新方法
- `validate_position()` 位置验证与修正
- `get_state_duration()` 获取状态持续时间
- `is_in_safe_zone()` 检查是否在安全区域
- `destroy()` 资源清理方法

### `pet_window.py` - 窗口管理

增强功能：

- 气泡消息消毒（移除控制字符）
- Tk 特殊字符转义（防解析错误）
- 持续时间范围限制（0.5s - 30s）
- 双重边界验证（`validate_position` + `get_safe_screen_position`）
- 更完善的 TclError 处理

### `puppy_drawer.py` - 绘制模块

增强功能：

- `_safe_coords()` 安全坐标转换
- NaN/Inf 坐标检测
- 坐标类型自动转换
- 更宽松的可见区域检查（margin: 100 → 150）

### `main.py` - 主程序

集成错误恢复系统：

- 初始化时启动错误恢复系统
- 注册清理任务到优雅关闭管理器
- 更新循环中喂狗（重置看门狗）
- 气泡消息消毒
- 性能计时装饰器
- 关闭时完整清理错误恢复系统

## 📊 测试覆盖

新增测试类：

| 测试类 | 测试数量 | 覆盖范围 |
|--------|----------|----------|
| `TestInputSanitizer` | 18 | 输入消毒工具 |
| `TestSafeExecute` | 4 | 安全执行器 |
| `TestRetryOnFailure` | 3 | 重试机制 |
| `TestLogSanitization` | 5 | 日志消毒 |
| `TestPerformanceLogging` | 3 | 性能日志 |
| `TestConfigEnhancements` | 16 | 配置增强 |
| `TestGracefulShutdown` | 3 | 优雅关闭 |
| `TestWatchdogTimer` | 2 | 看门狗定时器 |
| `TestResourceManager` | 2 | 资源管理 |

**总计：105 个测试通过，22 个跳过（需要 tkinter）**

## 🛡️ 防护机制

### 1. 输入验证

```python
# 字符串消毒
sanitizer = InputSanitizer()
safe_text = sanitizer.sanitize_string(user_input, max_length=100)

# 数字范围限制
x = sanitizer.sanitize_coordinate(mouse_x, min_val=0, max_val=1920)
```

### 2. 异常捕获

```python
# 全局异常捕获（自动生成崩溃报告）
initialize_error_recovery(log_dir="logs")

# 安全执行
result = safe_execute(risky_function, default=fallback_value)
```

### 3. 资源保护

```python
# 看门狗（检测主循环挂起）
feed_watchdog()  # 在主循环中调用

# 资源监控
ResourceMonitor(memory_warning_mb=200, memory_critical_mb=500)
```

### 4. 优雅关闭

```python
# 注册清理任务
register_cleanup_task("window", window.destroy)
register_cleanup_task("logger", logger.shutdown)

# 执行关闭（带超时）
shutdown_manager.execute_shutdown()  # 5秒超时
```

### 5. 日志安全

```python
# 自动过滤敏感信息
logger.info(f"Connecting with token={api_token}")  # token 会被替换为 ***

# JSON 格式日志（便于分析）
setup_logging(json_format=True)
```

## 📁 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `error_recovery.py` | 新增 | 错误恢复模块 |
| `logger.py` | 增强 | 添加敏感信息过滤、性能日志等 |
| `config.py` | 增强 | 添加更多验证函数 |
| `puppy.py` | 增强 | 添加错误恢复和位置验证 |
| `pet_window.py` | 增强 | 添加输入消毒和边界保护 |
| `puppy_drawer.py` | 增强 | 添加坐标安全转换 |
| `main.py` | 增强 | 集成错误恢复系统 |
| `test_error_handling.py` | 增强 | 添加新功能测试 |
| `ERROR_HANDLING_SUMMARY.md` | 新增 | 本文档 |

## 🚀 使用示例

### 初始化错误恢复

```python
from error_recovery import initialize_error_recovery

# 在程序启动时调用
initialize_error_recovery(
    log_dir="logs",
    enable_resource_monitor=True,
    enable_watchdog=True,
    watchdog_timeout=15.0
)
```

### 输入消毒

```python
from error_recovery import InputSanitizer

sanitizer = InputSanitizer()

# 消毒用户输入
safe_name = sanitizer.sanitize_string(user_name, max_length=50)
safe_age = sanitizer.sanitize_integer(user_age, min_val=0, max_val=150, default=0)
safe_color = sanitizer.sanitize_color(color_input, default="#000000")
```

### 性能监控

```python
from logger import performance_timer, get_performance_stats

@performance_timer(logger, "draw_frame")
def draw_frame():
    # 绘制逻辑
    pass

# 获取性能统计
stats = get_performance_stats()
```

## 📝 注意事项

1. **tkinter 测试**：需要 GUI 环境的测试在无头环境中会自动跳过
2. **psutil 依赖**：资源监控功能需要 `psutil` 库，不可用时会优雅降级
3. **日志文件**：崩溃报告保存在 `logs/` 目录，建议定期清理
4. **看门狗超时**：默认 15 秒，可根据实际调整

## 🔗 相关文件

- `test_error_handling.py` - 完整测试套件
- `logs/` - 日志和崩溃报告目录
