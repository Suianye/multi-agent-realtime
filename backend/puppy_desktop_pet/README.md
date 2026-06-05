# 小黑狗桌宠 🐕

一个基于 Python + tkinter 的桌面宠物应用，在屏幕上显示一个可爱的小黑狗卡通形象。

## 功能特性

- 🐶 显示可爱的小黑狗卡通形象
- 🚶 小黑狗能在桌面上自由走动
- 🖱️ 点击小黑狗触发互动动作（摇尾巴、坐下）
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
   - **点击**：点击小黑狗触发互动动作
   - **拖拽**：按住左键拖动小黑狗移动位置
   - **关闭**：右键点击选择退出，或直接关闭终端

## 项目结构

```
puppy_desktop_pet/
├── main.py              # 程序入口
├── pet_window.py        # 窗口管理（透明窗口、拖拽）
├── puppy.py             # 小黑狗核心逻辑（状态机、动画）
├── puppy_drawer.py      # 绘制逻辑（Canvas 绘制各个部件）
├── animations.py        # 动画帧定义和管理
├── config.py            # 配置常量（颜色、尺寸、速度）
├── README.md            # 使用说明（本文件）
└── tests/               # 测试文件
```

## 配置说明

所有配置项位于 `config.py`，可根据需要调整：

- `PUPPY_SIZE`：小黑狗尺寸（默认 80 像素）
- `WALK_SPEED`：移动速度（默认 2 像素/帧）
- `ANIMATION_FPS`：动画帧率（默认 8 FPS）
- `IDLE_TIMEOUT`：空闲超时（默认 3000 毫秒）
- `SITTING_TIMEOUT`：坐下超时（默认 3000 毫秒）
- `WAGGING_TIMEOUT`：摇尾巴超时（默认 2000 毫秒）

## 运行测试

```bash
cd puppy_desktop_pet
pytest tests/ -v
```

## 跨平台兼容

- **Windows**：完美支持，透明效果最佳
- **macOS**：支持，透明效果可能略有差异
- **Linux**：需要 compositor 支持（如 picom、compton）

## 未来计划

- [ ] 添加更多互动动作（睡觉、跑步）
- [ ] 支持声音效果
- [ ] 添加宠物对话气泡
- [ ] 支持多只宠物
- [ ] 添加宠物成长系统

## 许可证

MIT License
