"""
桌面宠物小狗 - 核心模块
使用tkinter绘制可爱的小狗，支持拖拽、右键菜单和自动动作

功能:
  - 透明无边框窗口，置顶显示
  - 可爱小狗绘制（圆形身体、三角形耳朵、小尾巴）
  - 左键拖拽移动
  - 右键弹出菜单
  - 自动随机动作（摇尾巴、走动、坐下）
  - 快捷键: q退出, w走动, 空格做动作, s坐下
"""

import tkinter as tk
import random
import math


class DogPet:
    """可爱的小狗桌面宠物类"""

    def __init__(self):
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("桌面小狗")

        # 窗口设置：无边框、置顶、透明背景
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes('-topmost', True)  # 置顶
        self.root.attributes('-transparentcolor', '#F0F0F0')  # 透明背景色

        # 画布大小
        self.canvas_width = 160
        self.canvas_height = 160

        # 创建画布
        self.canvas = tk.Canvas(
            self.root,
            width=self.canvas_width,
            height=self.canvas_height,
            bg='#F0F0F0',
            highlightthickness=0
        )
        self.canvas.pack()

        # 窗口初始位置（屏幕右下角）
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.x = screen_width - 250
        self.y = screen_height - 280
        self.root.geometry(f'+{self.x}+{self.y}')

        # 拖拽相关变量
        self._drag_data = {'x': 0, 'y': 0}

        # 动画状态
        self.state = 'idle'       # idle, walking, sitting, wagging
        self.direction = 1        # 1=右, -1=左（朝向，预留）
        self.move_direction = 1   # 走动方向: 1=右, -1=左
        self.anim_frame = 0       # 全局帧计数（用于持续性动画：浮动、耳朵、腿）
        self.state_frame = 0      # 当前状态帧计数（状态切换时重置，用于限时动作）
        self.tail_angle = 0
        self.tail_direction = 1
        self.walk_step = 0
        self.blink_timer = 0      # 眨眼计时器
        self.is_blinking = False

        # 自动动作定时器
        self.auto_action_timer = 0
        self.auto_action_interval = random.randint(150, 400)

        # 绑定事件
        self._bind_events()

        # 创建右键菜单
        self._create_context_menu()

        # 开始动画循环（约30fps）
        self._animate()

    def _bind_events(self):
        """绑定鼠标和键盘事件"""
        # 拖拽事件
        self.canvas.bind('<Button-1>', self._on_drag_start)
        self.canvas.bind('<B1-Motion>', self._on_drag_motion)
        self.canvas.bind('<ButtonRelease-1>', self._on_drag_stop)

        # 右键菜单
        self.canvas.bind('<Button-3>', self._show_context_menu)

        # 快捷键
        self.root.bind('<q>', lambda e: self.root.destroy())
        self.root.bind('<Q>', lambda e: self.root.destroy())
        self.root.bind('<w>', lambda e: self._start_walking())
        self.root.bind('<W>', lambda e: self._start_walking())
        self.root.bind('<space>', lambda e: self._do_trick())
        self.root.bind('<s>', lambda e: self._start_sitting())
        self.root.bind('<S>', lambda e: self._start_sitting())

        # 让窗口可以接收键盘焦点
        self.canvas.focus_set()
        # 点击时重新获取焦点（确保快捷键始终可用）
        self.canvas.bind('<Button-1>', lambda e: (self._on_drag_start(e), self.canvas.focus_set()), add='+')

    def _create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="🐾 走动", command=self._start_walking)
        self.context_menu.add_command(label="🐕 坐下", command=self._start_sitting)
        self.context_menu.add_command(label="✨ 做动作", command=self._do_trick)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="👋 退出", command=self.root.destroy)

    def _show_context_menu(self, event):
        """显示右键菜单"""
        self.context_menu.post(event.x_root, event.y_root)

    # ─── 拖拽逻辑 ───────────────────────────────────────────────

    def _on_drag_start(self, event):
        """开始拖拽"""
        self._drag_data['x'] = event.x
        self._drag_data['y'] = event.y

    def _on_drag_motion(self, event):
        """拖拽移动"""
        dx = event.x - self._drag_data['x']
        dy = event.y - self._drag_data['y']
        self.x += dx
        self.y += dy
        self.root.geometry(f'+{self.x}+{self.y}')

    def _on_drag_stop(self, event):
        """停止拖拽"""
        self._drag_data['x'] = 0
        self._drag_data['y'] = 0

    # ─── 状态切换 ───────────────────────────────────────────────

    def _set_state(self, new_state):
        """切换状态，重置状态帧计数"""
        if self.state != new_state:
            self.state = new_state
            self.state_frame = 0

    def _start_walking(self):
        """开始走动"""
        self._set_state('walking')
        self.walk_step = 0
        self.move_direction = random.choice([-1, 1])

    def _start_sitting(self):
        """开始坐下"""
        self._set_state('sitting')

    def _do_trick(self):
        """做一个可爱的动作（摇尾巴+跳跃）"""
        self._set_state('wagging')

    # ─── 主动画循环 ──────────────────────────────────────────────

    def _animate(self):
        """主动画循环，约30fps"""
        self.canvas.delete('all')

        # 更新帧计数
        self.anim_frame += 1
        self.state_frame += 1

        # 更新眨眼计时器
        self._update_blink()

        # 根据状态绘制小狗
        if self.state == 'idle':
            self._draw_idle()
        elif self.state == 'walking':
            self._draw_walking()
        elif self.state == 'sitting':
            self._draw_sitting()
        elif self.state == 'wagging':
            self._draw_wagging()

        # 自动动作检查
        self._auto_action()

        # 约30fps
        self.root.after(33, self._animate)

    def _update_blink(self):
        """更新眨眼状态"""
        self.blink_timer += 1
        if not self.is_blinking and self.blink_timer > random.randint(80, 160):
            self.is_blinking = True
            self.blink_timer = 0
        if self.is_blinking and self.blink_timer > 6:
            self.is_blinking = False
            self.blink_timer = 0

    def _auto_action(self):
        """自动执行随机动作（仅在待机状态触发）"""
        if self.state != 'idle':
            return

        self.auto_action_timer += 1
        if self.auto_action_timer >= self.auto_action_interval:
            self.auto_action_timer = 0
            self.auto_action_interval = random.randint(150, 400)

            # 随机选择动作（走动概率更高，更自然）
            action = random.choice(['wag', 'walk', 'walk', 'idle'])
            if action == 'wag':
                self._do_trick()
            elif action == 'walk':
                self._start_walking()

    # ─── 绘图方法 ────────────────────────────────────────────────

    def _draw_dog_base(self, body_y_offset=0, sitting=False, jump_offset=0):
        """
        绘制小狗基础图形（身体、腿、头、五官）

        Args:
            body_y_offset: 身体Y轴偏移（坐下时下移）
            sitting: 是否为坐下姿势
            jump_offset: 跳跃偏移（负值=向上跳）
        """
        cx = 80  # 水平中心
        cy = 80 + body_y_offset + jump_offset  # 垂直中心

        # ── 颜色定义 ──
        body_color = '#D2691E'    # 巧克力色（身体）
        dark_color = '#8B4513'    # 深棕色（耳朵、轮廓）
        light_color = '#DEB887'   # 浅棕色（肚皮）
        nose_color = '#2C1810'    # 深褐色（鼻子）
        tongue_color = '#FF6B6B'  # 粉红色（舌头）

        # ── 后腿 ──
        if sitting:
            # 坐下时后腿折叠（两个椭圆）
            self.canvas.create_oval(
                cx - 25, cy + 15, cx - 8, cy + 35,
                fill=dark_color, outline=dark_color
            )
            self.canvas.create_oval(
                cx + 8, cy + 15, cx + 25, cy + 35,
                fill=dark_color, outline=dark_color
            )
        else:
            # 站立/走动时后腿交替摆动
            leg_bob = math.sin(self.anim_frame * 0.2) * 4 if self.state == 'walking' else 0
            self.canvas.create_oval(
                cx - 28, cy + 10, cx - 16, cy + 38 + leg_bob,
                fill=dark_color, outline=dark_color
            )
            self.canvas.create_oval(
                cx + 16, cy + 10, cx + 28, cy + 38 - leg_bob,
                fill=dark_color, outline=dark_color
            )

        # ── 身体（椭圆）──
        if sitting:
            self.canvas.create_oval(
                cx - 30, cy - 15, cx + 30, cy + 25,
                fill=body_color, outline=dark_color, width=2
            )
        else:
            self.canvas.create_oval(
                cx - 35, cy - 20, cx + 35, cy + 20,
                fill=body_color, outline=dark_color, width=2
            )

        # ── 前腿（站立时才画）──
        if not sitting:
            leg_bob = math.sin(self.anim_frame * 0.2 + math.pi) * 4 if self.state == 'walking' else 0
            self.canvas.create_oval(
                cx - 22, cy + 3, cx - 10, cy + 33 + leg_bob,
                fill=body_color, outline=dark_color
            )
            self.canvas.create_oval(
                cx + 10, cy + 3, cx + 22, cy + 33 - leg_bob,
                fill=body_color, outline=dark_color
            )

        # ── 肚皮（浅色椭圆）──
        belly_y = cy - 5 if sitting else cy - 10
        self.canvas.create_oval(
            cx - 16, belly_y, cx + 16, cy + 16,
            fill=light_color, outline=''
        )

        # ── 头部（圆形）──
        head_y = cy - 32
        self.canvas.create_oval(
            cx - 26, head_y - 22, cx + 26, head_y + 22,
            fill=body_color, outline=dark_color, width=2
        )

        # ── 耳朵（三角形，微微抖动）──
        ear_wiggle = math.sin(self.anim_frame * 0.08) * 2

        # 左耳
        self.canvas.create_polygon(
            cx - 22, head_y - 15,
            cx - 34, head_y - 38 + ear_wiggle,
            cx - 10, head_y - 22,
            fill=dark_color, outline=dark_color, smooth=True
        )
        # 右耳
        self.canvas.create_polygon(
            cx + 22, head_y - 15,
            cx + 34, head_y - 38 - ear_wiggle,
            cx + 10, head_y - 22,
            fill=dark_color, outline=dark_color, smooth=True
        )

        # ── 眼睛 ──
        eye_y = head_y - 4

        if self.is_blinking:
            # 眨眼：画弧线（闭眼效果）
            self.canvas.create_arc(
                cx - 16, eye_y - 6, cx - 4, eye_y + 6,
                start=0, extent=180, style='arc', outline='black', width=2
            )
            self.canvas.create_arc(
                cx + 4, eye_y - 6, cx + 16, eye_y + 6,
                start=0, extent=180, style='arc', outline='black', width=2
            )
        else:
            # 左眼
            self.canvas.create_oval(
                cx - 16, eye_y - 9, cx - 4, eye_y + 9,
                fill='white', outline=dark_color
            )
            self.canvas.create_oval(
                cx - 13, eye_y - 5, cx - 7, eye_y + 5,
                fill='black'
            )
            self.canvas.create_oval(
                cx - 12, eye_y - 4, cx - 9, eye_y - 1,
                fill='white'
            )
            # 右眼
            self.canvas.create_oval(
                cx + 4, eye_y - 9, cx + 16, eye_y + 9,
                fill='white', outline=dark_color
            )
            self.canvas.create_oval(
                cx + 7, eye_y - 5, cx + 13, eye_y + 5,
                fill='black'
            )
            self.canvas.create_oval(
                cx + 9, eye_y - 4, cx + 12, eye_y - 1,
                fill='white'
            )

        # ── 鼻子 ──
        self.canvas.create_oval(
            cx - 6, head_y + 6, cx + 6, head_y + 17,
            fill=nose_color, outline=nose_color
        )
        # 鼻子高光
        self.canvas.create_oval(
            cx - 3, head_y + 8, cx + 1, head_y + 12,
            fill='#4A3020'
        )

        # ── 嘴巴（微笑弧线）──
        self.canvas.create_arc(
            cx - 10, head_y + 12, cx + 10, head_y + 26,
            start=0, extent=-180,
            style='arc', outline=nose_color, width=2
        )

        # ── 舌头（做动作或偶尔伸出）──
        show_tongue = self.state == 'wagging' or (self.state == 'idle' and self.anim_frame % 200 < 40)
        if show_tongue:
            self.canvas.create_oval(
                cx - 3, head_y + 20, cx + 3, head_y + 30,
                fill=tongue_color, outline='#FF4444'
            )

        return cx, cy, head_y

    def _draw_tail(self, cx, body_y, wagging=False):
        """
        绘制尾巴

        Args:
            cx: 身体中心X
            body_y: 身体中心Y
            wagging: 是否快速摇摆
        """
        if wagging:
            self.tail_angle += self.tail_direction * 0.35
            if abs(self.tail_angle) > 1.8:
                self.tail_direction *= -1
        else:
            self.tail_angle = math.sin(self.anim_frame * 0.04) * 0.4

        tail_start_x = cx + 32
        tail_start_y = body_y - 5
        tail_end_x = tail_start_x + 28 * math.cos(self.tail_angle)
        tail_end_y = tail_start_y - 22 + 18 * math.sin(self.tail_angle)

        # 尾巴用粗圆角线绘制，三段贝塞尔更自然
        mid_x = (tail_start_x + tail_end_x) / 2 + 5
        mid_y = (tail_start_y + tail_end_y) / 2

        self.canvas.create_line(
            tail_start_x, tail_start_y,
            mid_x, mid_y,
            tail_end_x, tail_end_y,
            fill='#D2691E', width=7, capstyle='round', smooth=True
        )

    # ─── 各状态的绘制 ────────────────────────────────────────────

    def _draw_idle(self):
        """待机状态：轻微浮动 + 尾巴慢摆"""
        float_y = math.sin(self.anim_frame * 0.04) * 2
        cx, body_y, head_y = self._draw_dog_base(body_y_offset=float_y)
        self._draw_tail(cx, body_y, wagging=False)

    def _draw_walking(self):
        """走动状态：移动位置 + 腿部动画 + 摇尾巴"""
        self.x += self.move_direction * 2
        self.walk_step += 1

        # 边界检测
        screen_width = self.root.winfo_screenwidth()
        if self.x < 10:
            self.x = 10
            self.move_direction = 1
        elif self.x > screen_width - self.canvas_width - 10:
            self.x = screen_width - self.canvas_width - 10
            self.move_direction = -1

        self.root.geometry(f'+{int(self.x)}+{self.y}')

        cx, body_y, head_y = self._draw_dog_base()
        self._draw_tail(cx, body_y, wagging=True)

        # 走动一段时间后自动停止
        if self.walk_step > 120:
            self._set_state('idle')

    def _draw_sitting(self):
        """坐下状态：身体下移、后腿折叠、尾巴轻摆"""
        cx, body_y, head_y = self._draw_dog_base(body_y_offset=12, sitting=True)
        self._draw_tail(cx, body_y, wagging=False)

        # 坐一段时间后站起来
        if self.state_frame > 180:
            self._set_state('idle')

    def _draw_wagging(self):
        """做动作状态：快速摇尾巴 + 跳跃"""
        # 跳跃偏移（前半段跳起，后半段落下）
        if self.state_frame < 25:
            jump_offset = -math.sin(self.state_frame * math.pi / 25) * 15
        else:
            jump_offset = 0

        cx, body_y, head_y = self._draw_dog_base(jump_offset=jump_offset)
        self._draw_tail(cx, body_y, wagging=True)

        # 动作持续一段时间
        if self.state_frame > 90:
            self._set_state('idle')

    # ─── 运行 ───────────────────────────────────────────────────

    def run(self):
        """运行应用，进入主事件循环"""
        self.root.mainloop()


if __name__ == '__main__':
    pet = DogPet()
    pet.run()
