# 小黑狗桌宠桌面应用设计文档

## 概述

一个基于 Python + tkinter 的桌面宠物应用，在屏幕上显示一个可爱的小黑狗卡通形象，能够在桌面上自由走动，并支持点击互动。

## 需求

### 功能需求

1. **显示小黑狗**：在屏幕上显示一个精致卡通风格的小黑狗
2. **自由走动**：小黑狗能在桌面上随机走动
3. **点击互动**：点击小黑狗触发互动动作（摇尾巴、坐下）

### 非功能需求

- 零外部依赖，仅使用 Python 标准库
- 轻量级，资源占用低
- 支持 Windows/macOS/Linux

## 架构设计

### 目录结构

```
puppy_desktop_pet/
├── main.py              # 程序入口
├── pet_window.py        # 窗口管理（透明窗口、拖拽）
├── puppy.py             # 小黑狗核心逻辑（状态机、动画）
├── puppy_drawer.py      # 绘制逻辑（Canvas 绘制各个部件）
├── animations.py        # 动画帧定义和管理
├── config.py            # 配置常量（颜色、尺寸、速度）
└── README.md            # 使用说明
```

### 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| `main.py` | 程序入口，初始化窗口和小黑狗 | pet_window, puppy |
| `pet_window.py` | 管理透明窗口，处理拖拽移动 | tkinter |
| `puppy.py` | 状态机，管理小黑狗的行为状态 | animations, puppy_drawer |
| `puppy_drawer.py` | Canvas 绑定绘制，负责视觉呈现 | tkinter, config |
| `animations.py` | 定义动画帧序列，控制动画播放 | config |
| `config.py` | 集中管理配置常量 | 无 |

## 核心设计

### 状态机

#### 状态定义

```python
class PuppyState(Enum):
    IDLE = "idle"          # 空闲站立
    WALKING = "walking"    # 走路中
    SITTING = "sitting"    # 坐下
    WAGGING = "wagging"    # 摇尾巴
    SLEEPING = "sleeping"  # 睡觉（扩展）
```

#### 状态转换规则

```
IDLE ──(定时随机)──→ WALKING
IDLE ──(点击)──→ WAGGING (2秒后回到 IDLE)
WALKING ──(到达边界/定时)──→ IDLE
WALKING ──(点击)──→ SITTING
SITTING ──(3秒后)──→ IDLE
```

### 绘制设计

#### 小黑狗部件

- **头部**：圆形，带耳朵和眼睛
- **身体**：椭圆形
- **腿**：4 条短腿（走路时交替移动）
- **尾巴**：曲线（摇尾巴时摆动）
- **鼻子**：小黑点

#### 绘制方式

- 使用 `Canvas.create_oval()` 绘制圆形/椭圆
- 使用 `Canvas.create_arc()` 绘制曲线
- 使用 `Canvas.create_polygon()` 绘制多边形
- 颜色：黑色为主，眼睛白色，鼻子粉色

#### 动画实现

- 每个部件的坐标是相对于身体中心的偏移量
- 通过修改偏移量实现动画（如走路时腿的摆动）
- 使用 `Canvas.coords()` 更新部件位置

### 交互设计

#### 鼠标交互

- **左键点击**：触发互动动作（根据当前状态不同，动作不同）
- **拖拽**：按住左键拖动小黑狗移动位置
- **右键菜单**：显示设置选项（如退出、暂停）

#### 点击反馈

- IDLE 状态点击 → 播放摇尾巴动画
- WALKING 状态点击 → 停下来并坐下
- SITTING 状态点击 → 站起来继续走

#### 边界处理

- 小黑狗走到屏幕边缘时自动转向
- 支持多显示器场景（在主显示器内活动）

## 技术细节

### 窗口透明实现

```python
window = tk.Toplevel()
window.overrideredirect(True)  # 去掉标题栏
window.attributes('-transparentcolor', 'white')  # 白色透明
window.attributes('-topmost', True)  # 始终在最前
```

### 定时器管理

- 使用 `window.after(ms, callback)` 驱动动画
- 主循环：每 100ms 更新一次状态（10 FPS）
- 动画帧：每 125ms 切换一帧（8 FPS）

### 性能优化

- 只重绘变化的部件，不重绘整个 Canvas
- 使用 `Canvas.move()` 而非 `Canvas.coords()` 减少计算
- 空闲时降低更新频率（如 500ms 一次）

### 跨平台兼容

- **Windows**：使用 `-transparentcolor` 属性
- **macOS**：使用 `wm_attributes('-transparent', True)`
- **Linux**：需要 compositor 支持（如 picom）

## 配置参数

```python
# config.py
PUPPY_SIZE = 80          # 小黑狗尺寸（像素）
WALK_SPEED = 2           # 移动速度（像素/帧）
ANIMATION_FPS = 8        # 动画帧率
IDLE_TIMEOUT = 3000      # 空闲超时（毫秒）
SITTING_TIMEOUT = 3000   # 坐下超时（毫秒）
WAGGING_TIMEOUT = 2000   # 摇尾巴超时（毫秒）
```

## 测试策略

### 单元测试

- 状态机转换逻辑
- 动画帧序列
- 边界检测

### 集成测试

- 窗口创建和透明效果
- 鼠标交互响应
- 动画播放流畅度

### 手动测试

- 视觉效果检查
- 交互体验测试
- 跨平台兼容性

## 未来扩展

- 添加更多互动动作（睡觉、跑步）
- 支持声音效果
- 添加宠物对话气泡
- 支持多只宠物
- 添加宠物成长系统
