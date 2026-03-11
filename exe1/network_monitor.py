#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网速监控悬浮窗 - 液态玻璃风格 v2.0
实时显示上传、下载速度，支持详细模式
优化版：支持封装成exe，自动保存位置
"""

import tkinter as tk
from tkinter import font, ttk
import psutil
import threading
import time
import os
import json
import sys
from collections import deque
import platform

# 防止多开
def check_single_instance():
    """确保只有一个实例运行"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 37429))
        return sock
    except socket.error:
        return None

# Windows 相关
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes
    
    # 隐藏控制台窗口
    def hide_console():
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )


class Config:
    """配置管理"""
    CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".netmon_config.json")
    
    @classmethod
    def load(cls):
        """加载配置"""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    @classmethod
    def save(cls, data):
        """保存配置"""
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass


class NetworkSpeedMonitor:
    """网速监控主类"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        "window_x": None,
        "window_y": None,
        "mode": "compact",
        "topmost": True,
        "opacity": 0.9,
        "theme": "dark"
    }
    
    def __init__(self):
        # 加载配置
        self.config = {**self.DEFAULT_CONFIG, **Config.load()}
        
        self.root = tk.Tk()
        self.root.title("网速监控")
        self.root.resizable(False, False)
        
        # 窗口设置
        self.root.attributes('-topmost', self.config.get("topmost", True))
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', self.config.get("opacity", 0.9))
        
        # 防止任务栏显示（工具窗口样式）
        if IS_WINDOWS:
            self.root.wm_attributes('-toolwindow', True)
        
        # 窗口尺寸
        self.compact_width = 260
        self.compact_height = 130
        self.detailed_width = 500
        self.detailed_height = 650
        
        # 模式
        self.mode = self.config.get("mode", "compact")
        
        # 设置窗口位置
        self._set_window_position()
        
        # 颜色主题 - 液态玻璃风格
        self.colors = {
            "bg_dark": "#0d1117",
            "bg_card": "#161b22",
            "accent_blue": "#58a6ff",
            "accent_green": "#3fb950",
            "accent_red": "#f85149",
            "accent_purple": "#a371f7",
            "accent_cyan": "#39c5cf",
            "text_primary": "#c9d1d9",
            "text_secondary": "#8b949e"
        }
        
        # 数据历史
        self.download_history = deque(maxlen=60)
        self.upload_history = deque(maxlen=60)
        
        # 创建字体
        self.fonts = {
            "title": font.Font(family="Microsoft YaHei", size=11, weight="bold"),
            "speed_large": font.Font(family="Consolas", size=20, weight="bold"),
            "speed_small": font.Font(family="Consolas", size=12),
            "label": font.Font(family="Microsoft YaHei", size=9),
            "value": font.Font(family="Consolas", size=10),
            "tiny": font.Font(family="Microsoft YaHei", size=8)
        }
        
        # 创建UI
        self._create_main_frame()
        self._create_compact_ui()
        self._create_detailed_ui()
        self._bind_events()
        
        # 网络统计初始化
        self.last_io = psutil.net_io_counters()
        self.last_time = time.time()
        
        # 峰值记录
        self.peak_download = 0
        self.peak_upload = 0
        
        # 启动更新线程
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        # 显示当前模式
        if self.mode == "detailed":
            self._show_detailed()
        else:
            self._show_compact()
            
    def _set_window_position(self):
        """设置窗口位置"""
        x = self.config.get("window_x")
        y = self.config.get("window_y")
        
        if x is None or y is None:
            # 默认右上角
            screen_width = self.root.winfo_screenwidth()
            x = screen_width - self.compact_width - 20
            y = 20
        
        # 根据模式选择正确的窗口大小
        if self.mode == "detailed":
            width = self.detailed_width
            height = self.detailed_height
        else:
            width = self.compact_width
            height = self.compact_height
            
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def _save_position(self):
        """保存窗口位置"""
        self.config["window_x"] = self.root.winfo_x()
        self.config["window_y"] = self.root.winfo_y()
        self.config["mode"] = self.mode
        self.config["topmost"] = self.root.attributes('-topmost')
        self.config["opacity"] = self.root.attributes('-alpha')
        Config.save(self.config)
        
    def _create_main_frame(self):
        """创建主容器"""
        self.root.configure(bg=self.colors["bg_dark"])
        
        # 外层边框（模拟圆角效果）
        self.outer_frame = tk.Frame(self.root, bg=self.colors["bg_dark"])
        self.outer_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # 内边距容器
        self.content_frame = tk.Frame(self.outer_frame, bg=self.colors["bg_dark"])
        self.content_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
    def _create_compact_ui(self):
        """创建简洁模式UI"""
        self.compact_frame = tk.Frame(self.content_frame, bg=self.colors["bg_dark"])
        
        # 标题栏（可拖动）
        title_bar = tk.Frame(self.compact_frame, bg=self.colors["bg_dark"], cursor="fleur")
        title_bar.pack(fill="x", padx=12, pady=(10, 5))
        self.compact_title_bar = title_bar
        
        # 左侧：状态指示
        left_title = tk.Frame(title_bar, bg=self.colors["bg_dark"])
        left_title.pack(side="left")
        
        self.status_indicator = tk.Label(
            left_title, text="●", font=("Microsoft YaHei", 8),
            fg=self.colors["accent_green"], bg=self.colors["bg_dark"]
        )
        self.status_indicator.pack(side="left")
        
        tk.Label(
            left_title, text=" 网速监控", font=self.fonts["title"],
            fg=self.colors["text_primary"], bg=self.colors["bg_dark"]
        ).pack(side="left")
        
        # 右侧按钮
        right_btns = tk.Frame(title_bar, bg=self.colors["bg_dark"])
        right_btns.pack(side="right")
        
        # 展开按钮
        self.expand_btn = tk.Label(
            right_btns, text="◀", font=("Microsoft YaHei", 10),
            fg=self.colors["accent_blue"], bg=self.colors["bg_dark"],
            cursor="hand2"
        )
        self.expand_btn.pack(side="left", padx=5)
        self.expand_btn.bind("<Button-1>", lambda e: self._toggle_mode())
        
        # 关闭按钮
        close_btn = tk.Label(
            right_btns, text="✕", font=("Microsoft YaHei", 10),
            fg=self.colors["accent_red"], bg=self.colors["bg_dark"],
            cursor="hand2"
        )
        close_btn.pack(side="left")
        close_btn.bind("<Button-1>", lambda e: self._on_close())
        
        # 速度显示卡片
        cards_frame = tk.Frame(self.compact_frame, bg=self.colors["bg_dark"])
        cards_frame.pack(fill="x", padx=12, pady=5)
        
        # 下载卡片
        download_card = tk.Frame(cards_frame, bg=self.colors["bg_card"], highlightbackground="#21262d", highlightthickness=1)
        download_card.pack(fill="x", pady=(0, 6))
        
        dl_header = tk.Frame(download_card, bg=self.colors["bg_card"])
        dl_header.pack(fill="x", padx=10, pady=(8, 0))
        
        tk.Label(
            dl_header, text="⬇ 下载", font=self.fonts["label"],
            fg=self.colors["accent_green"], bg=self.colors["bg_card"]
        ).pack(side="left")
        
        self.download_peak = tk.Label(
            dl_header, text="峰值: 0 B/s", font=self.fonts["tiny"],
            fg=self.colors["text_secondary"], bg=self.colors["bg_card"]
        )
        self.download_peak.pack(side="right")
        
        self.download_value = tk.Label(
            download_card, text="0.00 MB/s", font=self.fonts["speed_large"],
            fg=self.colors["accent_green"], bg=self.colors["bg_card"]
        )
        self.download_value.pack(anchor="w", padx=10, pady=(0, 8))
        
        # 上传卡片
        upload_card = tk.Frame(cards_frame, bg=self.colors["bg_card"], highlightbackground="#21262d", highlightthickness=1)
        upload_card.pack(fill="x")
        
        ul_header = tk.Frame(upload_card, bg=self.colors["bg_card"])
        ul_header.pack(fill="x", padx=10, pady=(8, 0))
        
        tk.Label(
            ul_header, text="⬆ 上传", font=self.fonts["label"],
            fg=self.colors["accent_red"], bg=self.colors["bg_card"]
        ).pack(side="left")
        
        self.upload_peak = tk.Label(
            ul_header, text="峰值: 0 B/s", font=self.fonts["tiny"],
            fg=self.colors["text_secondary"], bg=self.colors["bg_card"]
        )
        self.upload_peak.pack(side="right")
        
        self.upload_value = tk.Label(
            upload_card, text="0.00 MB/s", font=self.fonts["speed_large"],
            fg=self.colors["accent_red"], bg=self.colors["bg_card"]
        )
        self.upload_value.pack(anchor="w", padx=10, pady=(0, 8))
        
        # 底部信息栏
        bottom_bar = tk.Frame(self.compact_frame, bg=self.colors["bg_dark"])
        bottom_bar.pack(fill="x", padx=12, pady=(5, 10))
        
        self.total_data_label = tk.Label(
            bottom_bar, text="总计: ↓0 GB ↑0 GB", font=self.fonts["tiny"],
            fg=self.colors["text_secondary"], bg=self.colors["bg_dark"]
        )
        self.total_data_label.pack(side="left")
        
        self.ping_label = tk.Label(
            bottom_bar, text="延迟: -- ms", font=self.fonts["tiny"],
            fg=self.colors["accent_cyan"], bg=self.colors["bg_dark"]
        )
        self.ping_label.pack(side="right")
        
    def _create_detailed_ui(self):
        """创建详细模式UI"""
        self.detailed_frame = tk.Frame(self.content_frame, bg=self.colors["bg_dark"])
        
        # 标题栏（可拖动）
        title_bar = tk.Frame(self.detailed_frame, bg=self.colors["bg_dark"], cursor="fleur")
        title_bar.pack(fill="x", padx=12, pady=(10, 5))
        self.detailed_title_bar = title_bar
        
        tk.Label(
            title_bar, text="📊 网络监控详情", font=self.fonts["title"],
            fg=self.colors["text_primary"], bg=self.colors["bg_dark"]
        ).pack(side="left")
        
        # 收起按钮
        collapse_btn = tk.Label(
            title_bar, text="▶", font=("Microsoft YaHei", 10),
            fg=self.colors["accent_blue"], bg=self.colors["bg_dark"],
            cursor="hand2"
        )
        collapse_btn.pack(side="right")
        collapse_btn.bind("<Button-1>", lambda e: self._toggle_mode())
        
        # 实时速度区域
        speed_section = tk.LabelFrame(
            self.detailed_frame, text=" 实时速度 ", font=self.fonts["label"],
            fg=self.colors["accent_blue"], bg=self.colors["bg_dark"]
        )
        speed_section.pack(fill="x", padx=12, pady=5)
        
        speed_grid = tk.Frame(speed_section, bg=self.colors["bg_dark"])
        speed_grid.pack(fill="x", padx=10, pady=8)
        
        # 下载速度
        dl_frame = tk.Frame(speed_grid, bg=self.colors["bg_dark"])
        dl_frame.grid(row=0, column=0, sticky="w", padx=(0, 20))
        
        tk.Label(
            dl_frame, text="⬇ 下载", font=self.fonts["label"],
            fg=self.colors["accent_green"], bg=self.colors["bg_dark"]
        ).pack(anchor="w")
        self.dl_detailed = tk.Label(
            dl_frame, text="0.00 MB/s", font=self.fonts["speed_large"],
            fg=self.colors["accent_green"], bg=self.colors["bg_dark"]
        )
        self.dl_detailed.pack(anchor="w")
        
        # 上传速度
        ul_frame = tk.Frame(speed_grid, bg=self.colors["bg_dark"])
        ul_frame.grid(row=0, column=1, sticky="w")
        
        tk.Label(
            ul_frame, text="⬆ 上传", font=self.fonts["label"],
            fg=self.colors["accent_red"], bg=self.colors["bg_dark"]
        ).pack(anchor="w")
        self.ul_detailed = tk.Label(
            ul_frame, text="0.00 MB/s", font=self.fonts["speed_large"],
            fg=self.colors["accent_red"], bg=self.colors["bg_dark"]
        )
        self.ul_detailed.pack(anchor="w")
        
        # 统计信息区域
        stats_section = tk.LabelFrame(
            self.detailed_frame, text=" 统计信息 ", font=self.fonts["label"],
            fg=self.colors["accent_purple"], bg=self.colors["bg_dark"]
        )
        stats_section.pack(fill="x", padx=12, pady=5)
        
        stats_grid = tk.Frame(stats_section, bg=self.colors["bg_dark"])
        stats_grid.pack(fill="x", padx=10, pady=8)
        
        stats = [
            ("总下载", "total_dl", self.colors["accent_green"]),
            ("总上传", "total_ul", self.colors["accent_red"]),
            ("连接数", "connections", self.colors["accent_blue"]),
            ("延迟", "latency", self.colors["accent_cyan"]),
            ("下载峰值", "peak_dl", self.colors["accent_green"]),
            ("上传峰值", "peak_ul", self.colors["accent_red"])
        ]
        
        self.stat_labels = {}
        for i, (name, key, color) in enumerate(stats):
            row = i // 3
            col = i % 3
            
            stat_frame = tk.Frame(stats_grid, bg=self.colors["bg_dark"])
            stat_frame.grid(row=row, column=col, sticky="w", padx=10, pady=5)
            
            tk.Label(
                stat_frame, text=name, font=self.fonts["tiny"],
                fg=self.colors["text_secondary"], bg=self.colors["bg_dark"]
            ).pack(anchor="w")
            
            label = tk.Label(
                stat_frame, text="--", font=self.fonts["value"],
                fg=color, bg=self.colors["bg_dark"]
            )
            label.pack(anchor="w")
            self.stat_labels[key] = label
        
        # 实时图表区域
        chart_section = tk.LabelFrame(
            self.detailed_frame, text=" 实时流量图 (最近60秒) ", font=self.fonts["label"],
            fg=self.colors["accent_cyan"], bg=self.colors["bg_dark"]
        )
        chart_section.pack(fill="x", padx=12, pady=5)
        
        self.chart_canvas = tk.Canvas(
            chart_section, height=100, bg=self.colors["bg_card"],
            highlightthickness=0
        )
        self.chart_canvas.pack(fill="x", padx=10, pady=8)
        
        # 网卡信息表格
        table_section = tk.LabelFrame(
            self.detailed_frame, text=" 网卡信息 ", font=self.fonts["label"],
            fg=self.colors["text_primary"], bg=self.colors["bg_dark"]
        )
        table_section.pack(fill="x", padx=12, pady=5)
        
        # 创建表格
        columns = ("网卡", "状态", "下载", "上传", "IP地址")
        self.net_table = ttk.Treeview(
            table_section, columns=columns, show="headings",
            height=3
        )
        
        for col in columns:
            self.net_table.heading(col, text=col)
            self.net_table.column(col, width=80)
        
        self.net_table.column("网卡", width=100)
        self.net_table.column("IP地址", width=120)
        
        # 样式
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background=self.colors["bg_card"],
            foreground=self.colors["text_primary"],
            fieldbackground=self.colors["bg_card"]
        )
        style.configure(
            "Treeview.Heading",
            background=self.colors["bg_dark"],
            foreground=self.colors["text_primary"]
        )
        
        self.net_table.pack(fill="x", padx=10, pady=8)
        
        # 透明度控制区域 - 单独一行
        opacity_section = tk.LabelFrame(
            self.detailed_frame, text=" 透明度调节 ", font=self.fonts["label"],
            fg=self.colors["accent_cyan"], bg=self.colors["bg_dark"]
        )
        opacity_section.pack(fill="x", padx=12, pady=5)
        
        opacity_container = tk.Frame(opacity_section, bg=self.colors["bg_dark"])
        opacity_container.pack(fill="x", padx=10, pady=8)
        
        # 透明度数值标签
        self.opacity_value_label = tk.Label(
            opacity_container, text="90%", font=self.fonts["speed_large"],
            fg=self.colors["accent_cyan"], bg=self.colors["bg_dark"],
            width=5
        )
        self.opacity_value_label.pack(side="left", padx=(0, 10))
        
        # 透明度滑块 - 使用亮色滑块
        self.opacity_slider = tk.Scale(
            opacity_container, from_=30, to=100, orient="horizontal",
            bg=self.colors["bg_dark"], 
            fg=self.colors["accent_blue"],
            activebackground=self.colors["accent_blue"],
            highlightthickness=0,
            highlightbackground=self.colors["accent_cyan"],
            troughcolor="#404040",
            sliderlength=25,
            width=12,
            length=200,
            showvalue=0,
            command=self._on_opacity_change
        )
        self.opacity_slider.pack(side="left", fill="x", expand=True)
        
        # 底部按钮
        btn_frame = tk.Frame(self.detailed_frame, bg=self.colors["bg_dark"])
        btn_frame.pack(fill="x", padx=12, pady=(5, 10))
        
        # 置顶按钮
        self.topmost_btn = tk.Label(
            btn_frame, text="📌 置顶", font=self.fonts["label"],
            fg=self.colors["accent_blue"], bg=self.colors["bg_dark"],
            cursor="hand2"
        )
        self.topmost_btn.pack(side="left", padx=5)
        self.topmost_btn.bind("<Button-1>", lambda e: self._toggle_topmost())
        # 设置初始值
        current_opacity = int(self.root.attributes('-alpha') * 100)
        self.opacity_slider.set(current_opacity)
        
        # 关闭按钮
        close_btn = tk.Label(
            btn_frame, text="❌ 关闭", font=self.fonts["label"],
            fg=self.colors["accent_red"], bg=self.colors["bg_dark"],
            cursor="hand2"
        )
        close_btn.pack(side="right", padx=5)
        close_btn.bind("<Button-1>", lambda e: self._on_close())
        
    def _bind_events(self):
        """绑定事件"""
        self.drag_data = {"x": 0, "y": 0, "dragging": False}
        
        def on_press(event, widget):
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.drag_data["dragging"] = True
            
        def on_drag(event, widget):
            if not self.drag_data["dragging"]:
                return
            deltax = event.x - self.drag_data["x"]
            deltay = event.y - self.drag_data["y"]
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.wm_geometry(f"+{x}+{y}")
            
        def on_release(event, widget):
            self.drag_data["dragging"] = False
            # 保存位置
            self._save_position()
        
        # 绑定到标题栏
        for title_bar in [self.compact_title_bar, self.detailed_title_bar]:
            title_bar.bind("<Button-1>", lambda e, w=title_bar: on_press(e, w))
            title_bar.bind("<B1-Motion>", lambda e, w=title_bar: on_drag(e, w))
            title_bar.bind("<ButtonRelease-1>", lambda e, w=title_bar: on_release(e, w))
            
        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0, bg=self.colors["bg_card"], fg=self.colors["text_primary"])
        self.menu.add_command(label="切换模式", command=self._toggle_mode)
        self.menu.add_command(label="置顶/取消置顶", command=self._toggle_topmost)
        self.menu.add_command(label="调整透明度", command=self._toggle_opacity)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self._on_close)
        
        self.root.bind("<Button-3>", lambda e: self.menu.post(e.x_root, e.y_root))
        
        # 窗口关闭时保存配置
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _toggle_mode(self):
        """切换简洁/详细模式"""
        if self.mode == "compact":
            self._show_detailed()
        else:
            self._show_compact()
        self._save_position()
            
    def _show_compact(self):
        """显示简洁模式"""
        self.mode = "compact"
        self.detailed_frame.pack_forget()
        self.compact_frame.pack(fill="both", expand=True)
        self.root.geometry(f"{self.compact_width}x{self.compact_height}")
        self.expand_btn.config(text="◀")
        
    def _show_detailed(self):
        """显示详细模式"""
        self.mode = "detailed"
        self.compact_frame.pack_forget()
        self.detailed_frame.pack(fill="both", expand=True)
        self.root.geometry(f"{self.detailed_width}x{self.detailed_height}")
        
    def _toggle_topmost(self):
        """切换置顶"""
        current = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not current)
        self._save_position()
        
    def _on_opacity_change(self, value):
        """滑块调整透明度"""
        try:
            opacity = int(value) / 100.0
            self.root.attributes('-alpha', opacity)
            if hasattr(self, 'opacity_value_label'):
                self.opacity_value_label.config(text=f"{int(value)}%")
            self._save_position()
        except:
            pass
        
    def _toggle_opacity(self):
        """切换透明度（右键菜单用）"""
        current = self.root.attributes('-alpha')
        # 在三档之间切换：30% -> 60% -> 90% -> 30%
        if current < 0.5:
            new_opacity = 0.6
        elif current < 0.8:
            new_opacity = 0.9
        else:
            new_opacity = 0.3
        self.root.attributes('-alpha', new_opacity)
        # 同步滑块位置
        if hasattr(self, 'opacity_slider'):
            self.opacity_slider.set(int(new_opacity * 100))
        if hasattr(self, 'opacity_value_label'):
            self.opacity_value_label.config(text=f"{int(new_opacity * 100)}%")
        self._save_position()
        
    def _format_speed(self, bytes_per_sec):
        """格式化速度"""
        if bytes_per_sec >= 1024 * 1024 * 1024:
            return f"{bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s"
        elif bytes_per_sec >= 1024 * 1024:
            return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
        elif bytes_per_sec >= 1024:
            return f"{bytes_per_sec / 1024:.2f} KB/s"
        else:
            return f"{bytes_per_sec:.0f} B/s"
            
    def _format_bytes(self, bytes_val):
        """格式化字节数"""
        if bytes_val >= 1024 * 1024 * 1024 * 1024:
            return f"{bytes_val / (1024 * 1024 * 1024 * 1024):.2f} TB"
        elif bytes_val >= 1024 * 1024 * 1024:
            return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"
        elif bytes_val >= 1024 * 1024:
            return f"{bytes_val / (1024 * 1024):.2f} MB"
        elif bytes_val >= 1024:
            return f"{bytes_val / 1024:.2f} KB"
        else:
            return f"{bytes_val:.0f} B"
            
    def _update_chart(self):
        """更新流量图表"""
        self.chart_canvas.delete("all")
        
        width = self.chart_canvas.winfo_width()
        height = self.chart_canvas.winfo_height()
        
        if width < 10 or height < 10:
            return
            
        padding = 5
        chart_width = width - padding * 2
        chart_height = height - padding * 2
        
        max_val = 1
        for dl, ul in zip(self.download_history, self.upload_history):
            max_val = max(max_val, dl, ul * 2)
            
        for i in range(5):
            y = padding + chart_height * i / 4
            self.chart_canvas.create_line(
                padding, y, width - padding, y,
                fill="#21262d", width=1
            )
            
        if len(self.download_history) > 1:
            points = []
            for i, val in enumerate(self.download_history):
                x = padding + chart_width * i / 60
                y = padding + chart_height * (1 - val / max_val)
                points.extend([x, y])
            if points:
                self.chart_canvas.create_line(
                    points, fill=self.colors["accent_green"], width=2
                )
                
        if len(self.upload_history) > 1:
            points = []
            for i, val in enumerate(self.upload_history):
                x = padding + chart_width * i / 60
                y = padding + chart_height * (1 - val / max_val)
                points.extend([x, y])
            if points:
                self.chart_canvas.create_line(
                    points, fill=self.colors["accent_red"], width=2
                )
                
        self.chart_canvas.create_text(
            width - 60, padding + 10, text="● 下载",
            fill=self.colors["accent_green"], anchor="w", font=self.fonts["tiny"]
        )
        self.chart_canvas.create_text(
            width - 60, padding + 25, text="● 上传",
            fill=self.colors["accent_red"], anchor="w", font=self.fonts["tiny"]
        )
        
    def _update_table(self):
        """更新网卡表格"""
        for item in self.net_table.get_children():
            self.net_table.delete(item)
            
        io_counters = psutil.net_io_counters(pernic=True)
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for iface, addr_list in addrs.items():
            if iface in io_counters:
                io = io_counters[iface]
                stat = stats.get(iface)
                
                status = "✓ 已连接" if stat and stat.isup else "✗ 断开"
                ip = "-"
                for addr in addr_list:
                    if addr.family == 2:
                        ip = addr.address
                        break
                        
                self.net_table.insert("", "end", values=(
                    iface, status,
                    self._format_bytes(io.bytes_recv),
                    self._format_bytes(io.bytes_sent),
                    ip
                ))
                
    def _update_loop(self):
        """主更新循环"""
        while self.running:
            try:
                current_io = psutil.net_io_counters()
                current_time = time.time()
                time_delta = current_time - self.last_time
                
                if time_delta > 0:
                    download_speed = (current_io.bytes_recv - self.last_io.bytes_recv) / time_delta
                    upload_speed = (current_io.bytes_sent - self.last_io.bytes_sent) / time_delta
                    
                    self.download_history.append(download_speed)
                    self.upload_history.append(upload_speed)
                    
                    # 更新峰值
                    self.peak_download = max(self.peak_download, download_speed)
                    self.peak_upload = max(self.peak_upload, upload_speed)
                    
                    connections = len(psutil.net_connections())
                    
                    self.root.after(0, self._update_ui,
                                  download_speed, upload_speed, connections)
                    
                self.last_io = current_io
                self.last_time = current_time
                
                time.sleep(1)
            except Exception as e:
                time.sleep(1)
                
    def _update_ui(self, dl_speed, ul_speed, connections):
        """更新UI显示"""
        try:
            # 简洁模式
            self.download_value.config(text=self._format_speed(dl_speed))
            self.upload_value.config(text=self._format_speed(ul_speed))
            self.download_peak.config(text=f"峰值: {self._format_speed(self.peak_download)}")
            self.upload_peak.config(text=f"峰值: {self._format_speed(self.peak_upload)}")
            
            total_dl = self._format_bytes(self.last_io.bytes_recv)
            total_ul = self._format_bytes(self.last_io.bytes_sent)
            self.total_data_label.config(text=f"总计: ↓{total_dl} ↑{total_ul}")
            
            # 详细模式
            if self.mode == "detailed":
                self.dl_detailed.config(text=self._format_speed(dl_speed))
                self.ul_detailed.config(text=self._format_speed(ul_speed))
                
                self.stat_labels["total_dl"].config(text=self._format_bytes(self.last_io.bytes_recv))
                self.stat_labels["total_ul"].config(text=self._format_bytes(self.last_io.bytes_sent))
                self.stat_labels["connections"].config(text=str(connections))
                self.stat_labels["peak_dl"].config(text=self._format_speed(self.peak_download))
                self.stat_labels["peak_ul"].config(text=self._format_speed(self.peak_upload))
                
                self._update_chart()
                self._update_table()
                
        except tk.TclError:
            pass
            
    def _on_close(self):
        """关闭程序"""
        self._save_position()
        self.running = False
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        """运行"""
        self.root.mainloop()


def main():
    """主函数"""
    # 隐藏控制台窗口（Windows）- 当sys.stdout为None时（打包成exe无控制台）
    if IS_WINDOWS and (sys.stdout is None or not sys.stdout.isatty()):
        try:
            hide_console()
        except:
            pass
    
    # 检查单实例
    lock_socket = check_single_instance()
    if lock_socket is None:
        # 已有一个实例在运行
        tk.Tk().withdraw()
        tk.messagebox.showinfo("提示", "网速监控已经在运行中！")
        return
    
    # 启动应用
    app = NetworkSpeedMonitor()
    app.run()


if __name__ == "__main__":
    main()
