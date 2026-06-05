# 小黑狗桌宠 🐕

一个基于 Python + tkinter 的桌面宠物应用，在屏幕上显示一个可爱的小黑狗卡通形象。

## 功能特性

- 🐶 显示可爱的小黑狗卡通形象（带耳朵、斑点、舌头等细节）
- 🚶 小黑狗能在桌面上自由走动
- 🖱️ 点击小黑狗触发互动动作（摇尾巴、坐下、趴下）
- 🎭 丰富的状态系统：站立、走路、坐下、摇尾巴、打哈欠、伸懒腰、睡觉、趴下
- 💬 气泡消息显示（状态变化时自动显示）
- 🤖 自主动作（偶尔打哈欠、伸懒腰、睡觉）
- 🎨 精致卡通风格，纯 Canvas 绘制
- ⚡ 零外部依赖，仅使用 Python 标准库

## 运行要求

- Python 3.6+
- tkinter（Python 标准库，通常已预装）

## 使用方法

1. 进入项目目录：
   ```bash
   cd puppy_desktop_pet
   ```

2. 运行程序：
   ```bash
   python main.py
   ```

3. 互动方式：
   - **单击**：点击小黑狗触发互动动作（摇尾巴/坐下）
   - **双击**：趴下
   - **右键**：打哈欠
   - **拖拽**：按住左键拖动小黑狗移动位置
   - **键盘快捷键**：
     - `q`：退出
     - `p`：暂停
     - `r`：恢复
     - `s`：坐下
     - `w`：走动
     - `空格`：互动

## 状态说明

| 状态 | 描述 | 触发方式 |
|------|------|----------|
| IDLE | 站立 | 默认状态 |
| WALKING | 走路 | 自动触发 |
| SITTING | 坐下 | 点击走路中的小狗 |
| WAGGING | 摇尾巴 | 点击站立/坐下的小狗 |
| YAWNING | 打哈欠 | 右键点击 / 自动触发 |
| STRETCHING | 伸懒腰 | 自动触发 |
| SLEEPING | 睡觉 | 自动触发 |
| LYING_DOWN | 趴下 | 双击 |

## 项目结构

```
puppy_desktop_pet/
├── main.py              # 程序入口
├── pet_window.py        # 窗口管理（透明窗口、拖拽、气泡消息）
├── puppy.py             # 小黑狗核心逻辑（状态机、行为）
├── puppy_drawer.py      # 绘制逻辑（Canvas 绘制各个部件）
├── animations.py        # 动画帧定义和管理
├── event_router.py      # 事件路由系统
├── handlers.py          # 事件处理器
├── config.py            # 配置常量（颜色、尺寸、速度）
├── README.md            # 使用说明（本文件）
└── test_*.py            # 测试文件
```

## 配置说明

所有配置项位于 `config.py`，可根据需要调整：

- `PUPPY_SIZE`：小黑狗尺寸（默认 80 像素）
- `WALK_SPEED`：移动速度（默认 2 像素/帧）
- `ANIMATION_FPS`：动画帧率（默认 8 FPS）
- `IDLE_TIMEOUT`：空闲超时（默认 3000 毫秒）
- `SITTING_TIMEOUT`：坐下超时（默认 3000 毫秒）
- `WAGGING_TIMEOUT`：摇尾巴超时（默认 2000 毫秒）
- `YAWNING_TIMEOUT`：打哈欠超时（默认 2500 毫秒）
- `STRETCHING_TIMEOUT`：伸懒腰超时（默认 2000 毫秒）
- `SLEEPING_TIMEOUT`：睡觉超时（默认 5000 毫秒）
- `LYING_DOWN_TIMEOUT`：趴下超时（默认 4000 毫秒）
- `AUTO_ACTION_PROBABILITY`：自主动作触发概率（默认 0.02）
- `BUBBLE_DURATION`：气泡显示时长（默认 2000 毫秒）

## 运行测试

```bash
cd puppy_desktop_pet
pytest test_*.py -v
```

## 跨平台兼容

- **Windows**：完美支持，透明效果最佳
- **macOS**：支持，透明效果可能略有差异
- **Linux**：需要 compositor 支持（如 picom、compton）

## 技术特性

- **状态机管理**：使用枚举和状态机管理小狗的各种状态
- **事件路由**：自定义事件路由器，支持事件过滤、防抖
- **动画系统**：每状态多帧动画，支持动画过渡
- **气泡消息**：状态变化时自动显示可爱的气泡消息
- **自主行为**：随机触发打哈欠、伸懒腰、睡觉等动作

## 许可证

MIT License
