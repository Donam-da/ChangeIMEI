import os
import sys
import threading
import time
import random
import tkinter as tk
import shutil
import tempfile
import uuid
import json
from tkinter import messagebox
from tkinter import ttk
import urllib.request
from core.browser_engine import BrowserEngine

class AntiDetectGUI:
    def __init__(self, root):
        self.root = root

        self.window_index = 0
        self.is_hidden = False

        self.auto_launch_hidden = False
        for arg in sys.argv:
            if arg.startswith("--window-index="):
                try: self.window_index = int(arg.split("=")[1])
                except: pass
            elif arg == "--hidden":
                self.is_hidden = True
            elif arg == "--auto-launch-hidden":
                self.auto_launch_hidden = True

        if self.window_index > 0:
            self.root.title(f"ChangeIMEI Anti-Detect Browser - Cửa sổ {self.window_index}")
        else:
            self.root.title("ChangeIMEI Anti-Detect Browser")
        
        self.current_scale = 0.8
        # Căn giữa cửa sổ phần mềm chính trên màn hình lúc mới bật
        window_w = int(400 * self.current_scale)
        window_h = int(560 * self.current_scale)
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()

        # Tự động ném các cửa sổ mới vào 4 góc màn hình để không bị rối
        if self.window_index == 1: pos_x, pos_y = 10, 10
        elif self.window_index == 2: pos_x, pos_y = screen_w - window_w - 10, 10
        elif self.window_index == 3: pos_x, pos_y = 10, screen_h - window_h - 50
        elif self.window_index == 4: pos_x, pos_y = screen_w - window_w - 10, screen_h - window_h - 50
        else:
            pos_x = (screen_w // 2) - (window_w // 2)
            pos_y = (screen_h // 2) - (window_h // 2)
        self.root.geometry(f"{window_w}x{window_h}+{pos_x}+{pos_y}")
        
        if self.is_hidden:
            self.root.withdraw() # Ẩn cửa sổ khởi chạy ngầm, không hiện ra Desktop và Taskbar

        self.root.aspect(40, 27, 40, 27) # Khóa tỷ lệ khung hình cố định, chỉ cho kéo đường chéo
        self.root.configure(bg="#121212")
        
        # --- Cấu hình Style cho các ô chọn (Combobox/Filter) ---
        style = ttk.Style(root)
        style.theme_use('clam') # Đổi engine giao diện sang clam để cho phép đổi màu
        
        # Đổi màu nền, chữ và mũi tên của ô Filter
        style.configure("TCombobox", fieldbackground="#f5f5f5", background="#cccccc", foreground="black", arrowcolor="black", bordercolor="#121212")
        # Đổi màu danh sách xổ xuống (Listbox) của Filter
        root.option_add('*TCombobox*Listbox.background', '#f5f5f5')
        root.option_add('*TCombobox*Listbox.foreground', 'black')
        root.option_add('*TCombobox*Listbox.selectBackground', '#333333')
        root.option_add('*TCombobox*Listbox.selectForeground', '#00e676')
        # Đồng bộ màu xanh cho các thanh tiến trình (Progressbar)
        style.configure("Horizontal.TProgressbar", troughcolor="#1e1e1e", background="#00bcd4", bordercolor="#121212", lightcolor="#00bcd4", darkcolor="#00bcd4")
        # -------------------------------------------------------

        self.engine = BrowserEngine()
        self.is_optimized = False
        
        self.credentials_file = os.path.join(os.path.dirname(__file__), 'data', 'credentials.json')
        self.keywords_file = os.path.join(os.path.dirname(__file__), 'data', 'keywords.json')
        self.keywords = self.load_keywords()
        
        self.is_pinned = False
        self.btn_pin = tk.Button(root, text="📌 Ghim", font=("Arial", 7, "bold"), bg="#1e1e1e", fg="#a0a0a0", relief=tk.FLAT, command=self.toggle_pin, activebackground="#333333", activeforeground="#00e676")
        self.btn_pin.place(relx=1.0, x=-85, y=15, width=70)

        self.is_dark_mode = True
        self.btn_theme = tk.Button(root, text="🌙 Dark", font=("Arial", 7, "bold"), bg="#1e1e1e", fg="#a0a0a0", relief=tk.FLAT, command=self.toggle_theme, activebackground="#333333", activeforeground="#00ffff")
        self.btn_theme.place(relx=1.0, x=-150, y=15, width=60)

        self.is_bottommost = False
        self.btn_bottom = tk.Button(root, text="⬇️ Dưới", font=("Arial", 7, "bold"), bg="#1e1e1e", fg="#a0a0a0", relief=tk.FLAT, command=self.toggle_bottom, activebackground="#333333", activeforeground="#b388ff")
        self.btn_bottom.place(relx=1.0, x=-215, y=15, width=60)

        middle_container = tk.Frame(root, bg="#121212")
        middle_container.pack(fill=tk.X, padx=15, pady=(45, 0))
        
        tk.Label(middle_container, text="Nhập link URL muốn mở:", font=("Arial", 8), fg="#e0e0e0", bg="#121212", justify=tk.LEFT).pack(anchor="w")
        
        url_frame = tk.Frame(middle_container, bg="#121212")
        url_frame.pack(anchor="w", pady=4)
        
        self.url_entry = tk.Entry(url_frame, width=25, font=("Arial", 8), bg="#1e1e1e", fg="#00ffff", insertbackground="#00ffff", relief=tk.FLAT)
        self.url_entry.pack(side=tk.LEFT, ipady=2)
        self.url_entry.insert(0, "https://www.google.com/search?q=moneytask.top&sca_esv=3d73e6268d6609d9&sxsrf=ANbL-n5OwmW4jJHMCw_P-MHSjJYYql4e-Q%3A1778737875726&source=hp&ei=02IFas2XKteO2roP_vuQwQE&iflsig=AFdpzrgAAAAAagVw4whkttcjBBee1Pj39b_eAIp1hlot&oq=money&gs_lp=Egdnd3Mtd2l6IgVtb25leSoCCAAyBBAjGCcyChAAGIAEGIoFGEMyCxAAGIAEGLEDGIMBMgsQABiABBixAxiDATINEAAYgAQYigUYQxixAzILEAAYgAQYigUYkgMyFhAuGIAEGIoFGEMYsQMYyQMYxwEY0QMyChAAGIAEGIoFGEMyEBAuGIAEGIoFGEMYsQMYgwEyChAuGIAEGIoFGENImjRQyh5YqCRwAXgAkAEAmAHGB6AB4BaqAQkzLTIuMS4wLjK4AQHIAQD4AQGYAgagArsXqAIKwgIHECMY6gIYJ8ICDBAjGIAEGIoFGBMYJ8ICCxAuGIAEGLEDGIMBwgIIEC4YgAQYsQPCAg4QLhiABBiKBRixAxiDAcICCBAAGIAEGLEDwgIREC4YgAQYsQMYgwEYxwEY0QPCAhAQABiABBiKBRhDGLEDGIMBmAMN8QXuyFYW96YaBJIHCzEuMy0yLjEuMS4xoAepNLIHCTMtMi4xLjEuMbgHrhfCBwUyLTIuNMgHNoAIAQ&sclient=gws-wiz")
        
        self.btn_toggle_url = tk.Button(url_frame, text="👁️", bg="#1e1e1e", fg="#00ffff", relief=tk.FLAT, font=("Arial", 8), width=2, command=self.toggle_url_visibility, activebackground="#333333", activeforeground="#00ffff")
        self.btn_toggle_url.pack(side=tk.LEFT, padx=(4, 0), ipady=0)

        # Các nút bấm
        btn_frame = tk.Frame(root, bg="#121212")
        btn_frame.pack(pady=(15, 4))

        btn_style = {"font": ("Arial", 8, "bold"), "relief": tk.FLAT, "activebackground": "#00e5ff", "activeforeground": "black"}

        self.btn_ip_that = tk.Button(btn_frame, text="Mở Trình Duyệt", 
                                     command=self.launch_ip_that, bg="#00bcd4", fg="black", width=15, **btn_style)
        self.btn_ip_that.grid(row=0, column=1, padx=2, pady=4)
        
        self.btn_proxy = tk.Button(btn_frame, text="Proxy nếu có", 
                                   command=self.launch_proxy, bg="#a52a2a", fg="white", width=15, **btn_style)
        self.btn_proxy.grid(row=0, column=0, padx=2, pady=4)

        self.btn_auto_login = tk.Button(btn_frame, text="🔑 Auto Login", 
                                        command=self.trigger_auto_login, bg="#81c784", fg="black", width=15,
                                        state=tk.DISABLED, **btn_style)
        self.btn_auto_login.grid(row=0, column=2, padx=2, pady=4)
        self.btn_auto_login.bind("<Double-1>", self.show_credentials_dialog)

        self.btn_auto_task_step = tk.Button(btn_frame, text="Upto step (chưa có)", 
                                        command=self.trigger_auto_task_step, bg="#263238", fg="#00bcd4", width=15,
                                        state=tk.DISABLED, **btn_style)
        self.btn_auto_task_step.grid(row=1, column=0, padx=2, pady=4)

        self.btn_auto_task = tk.Button(btn_frame, text="Lấy mã (chưa có)", 
                                        command=self.trigger_auto_task, bg="#263238", fg="#00bcd4", width=15,
                                        state=tk.DISABLED, **btn_style)
        self.btn_auto_task.grid(row=1, column=1, padx=2, pady=4)

        self.btn_delete = tk.Button(btn_frame, text="🗑️ Delete",
                                    command=self.delete_session, bg="#b71c1c", fg="white", width=15,
                                    state=tk.NORMAL, font=("Arial", 8, "bold"), relief=tk.FLAT, activebackground="#f44336", activeforeground="white", disabledforeground="#ffcdd2")
        self.btn_delete.grid(row=1, column=2, padx=2, pady=4)

        self.btn_refresh = tk.Button(btn_frame, text="🔄 F5/Refresh", 
                                        command=self.trigger_refresh, bg="#ffb74d", fg="black", width=15,
                                        state=tk.DISABLED, **btn_style)
        self.btn_refresh.grid(row=2, column=1, padx=2, pady=4)

        self.btn_optimize = tk.Button(btn_frame, text="⚡ Giảm Lag", 
                                        command=self.toggle_optimize, bg="#673ab7", fg="white", width=15,
                                        state=tk.NORMAL, font=("Arial", 8, "bold"), relief=tk.FLAT, activebackground="#9575cd", activeforeground="white")
        self.btn_optimize.grid(row=2, column=0, padx=2, pady=4)

        self.btn_deep_clean = tk.Button(btn_frame, text="🧹 Deep Clean", 
                                        command=self.trigger_deep_clean, bg="#880e4f", fg="white", width=15,
                                        state=tk.NORMAL, font=("Arial", 8, "bold"), relief=tk.FLAT, activebackground="#c2185b", activeforeground="white")
        self.btn_deep_clean.grid(row=2, column=2, padx=2, pady=4)

        # --- BỘ LỌC CẤU HÌNH (KÍCH THƯỚC) ---
        filter_frame = tk.Frame(root, bg="#121212")
        filter_frame.pack(pady=(0, 6))
        
        tk.Label(filter_frame, text="Thiết bị:", font=("Arial", 8, "bold"), fg="#e0e0e0", bg="#121212").pack(side=tk.LEFT, padx=2)
        
        device_list = self.engine.device_faker.get_device_list()
        self.platform_var = tk.StringVar(value="Điện thoại (Ngẫu nhiên)")
        self.platform_cb = ttk.Combobox(filter_frame, textvariable=self.platform_var, values=device_list, state="readonly", font=("Arial", 8), width=22, height=6)
        self.platform_cb.pack(side=tk.LEFT, padx=(0, 2))
        self.platform_cb.bind("<<ComboboxSelected>>", lambda e: self.regenerate_profiles())
        
        tk.Label(filter_frame, text="Giao diện:", font=("Arial", 8, "bold"), fg="#e0e0e0", bg="#121212").pack(side=tk.LEFT, padx=2)
        self.scale_var = tk.StringVar(value="Size: x0.8")
        self.scale_cb = ttk.Combobox(filter_frame, textvariable=self.scale_var, values=["Size: x0.8", "Size: x1.0", "Size: x1.2", "Size: x1.4", "Size: x1.6"], state="readonly", font=("Arial", 8), width=9)
        self.scale_cb.pack(side=tk.LEFT)
        self.scale_cb.bind("<<ComboboxSelected>>", self.apply_scale)
        # ---------------------------------

        # --- Container cho khung Thiết bị ---
        bottom_container = tk.Frame(root, bg="#121212")
        bottom_container.pack(pady=(8, 0), fill=tk.BOTH, expand=True, padx=15)
        
        bottom_container.columnconfigure(0, weight=1)
        bottom_container.rowconfigure(0, weight=1)

        self.keyword_frame = tk.LabelFrame(bottom_container, text="Từ khóa tự động tìm kiếm Google:", font=("Arial", 7, "bold"), bg="#121212", fg="#00bcd4")
        self.keyword_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(4, 0))
        
        kw_top_frame = tk.Frame(self.keyword_frame, bg="#121212")
        kw_top_frame.pack(fill=tk.X, padx=5, pady=(5, 2))
        
        self.placeholder_text = "nhập text vào đây"
        self.kw_entry = tk.Entry(kw_top_frame, font=("Arial", 8), bg="#1e1e1e", fg="#ffffff", insertbackground="#ffffff", relief=tk.FLAT)
        self.kw_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)
        
        self.kw_entry.insert(0, self.placeholder_text)
        self.kw_entry.config(fg="#a0a0a0")
        
        self.kw_entry.bind("<FocusIn>", self.clear_placeholder)
        self.kw_entry.bind("<FocusOut>", self.add_placeholder)
        
        self.btn_add_kw = tk.Button(kw_top_frame, text="Thêm", command=self.add_keyword, bg="#00bcd4", fg="black", font=("Arial", 7, "bold"), relief=tk.FLAT, activebackground="#00e5ff")
        self.btn_add_kw.pack(side=tk.LEFT, padx=(5, 0))
        
        self.btn_update_kw = tk.Button(kw_top_frame, text="Sửa", command=self.update_keyword, bg="#ffb74d", fg="black", font=("Arial", 7, "bold"), relief=tk.FLAT, activebackground="#ff9800")
        self.btn_update_kw.pack(side=tk.LEFT, padx=(5, 0))
        
        self.btn_delete_kw = tk.Button(kw_top_frame, text="Xóa", command=self.delete_keyword, bg="#ff5252", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT, activebackground="#f44336")
        self.btn_delete_kw.pack(side=tk.LEFT, padx=(5, 0))
        
        list_container = tk.Frame(self.keyword_frame, bg="#1e1e1e")
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        self.kw_canvas = tk.Canvas(list_container, bg="#1e1e1e", highlightthickness=0, height=50)
        self.kw_scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.kw_canvas.yview)
        self.kw_list_inner_frame = tk.Frame(self.kw_canvas, bg="#1e1e1e")
        
        self.kw_canvas.configure(yscrollcommand=self.kw_scrollbar.set)
        self.kw_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.kw_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.kw_canvas_window = self.kw_canvas.create_window((0, 0), window=self.kw_list_inner_frame, anchor="nw")
        self.kw_list_inner_frame.bind("<Configure>", self._on_list_configure)
        self.kw_canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Lắng nghe sự kiện cuộn chuột trên Canvas và Frame chứa
        self.kw_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.kw_canvas.bind("<Button-4>", self._on_mousewheel)
        self.kw_canvas.bind("<Button-5>", self._on_mousewheel)
        self.kw_list_inner_frame.bind("<MouseWheel>", self._on_mousewheel)
        self.kw_list_inner_frame.bind("<Button-4>", self._on_mousewheel)
        self.kw_list_inner_frame.bind("<Button-5>", self._on_mousewheel)
        
        self.selected_kw_idx = None
        self.refresh_keyword_list()

        self.status_label = tk.Label(root, text="Trạng thái: Sẵn sàng", fg="#a0a0a0", bg="#121212", font=("Arial", 7))
        self.status_label.pack(side=tk.BOTTOM, pady=8)

        # Đảm bảo dọn dẹp session khi người dùng đóng cửa sổ chính
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self._is_wiping = False
        self.current_profile = None
        
        # Thiết lập trạng thái ban đầu
        self.status_label.config(text="Trạng thái: Sẵn sàng tạo trình duyệt mới", fg=self.get_color("#a0a0a0"))
        self.set_ui_for_browser_state(is_running=False)

        # Lắng nghe sự kiện phím Space để Refresh trang
        self.root.bind("<space>", self.handle_space_refresh)

        # Cập nhật cỡ chữ và giao diện theo scale hiện tại ngay khi phần mềm khởi động xong
        self.root.after(50, self.apply_scale)

    def clear_placeholder(self, event=None):
        if self.kw_entry.get() == self.placeholder_text:
            self.kw_entry.delete(0, tk.END)
            self.kw_entry.config(fg=self.get_color("#ffffff"))

    def add_placeholder(self, event=None):
        if not self.kw_entry.get():
            self.kw_entry.insert(0, self.placeholder_text)
            self.kw_entry.config(fg=self.get_color("#a0a0a0"))

    def update_clock(self):
        current_time = time.strftime("%H:%M:%S | %d/%m/%Y")
        self.clock_label.config(text=current_time)
        self.root.after(1000, self.update_clock)

    def apply_scale(self, event=None):
        """Áp dụng bộ lọc tỷ lệ phóng to giao diện"""
        scale_str = self.scale_var.get()
        if "0.8" in scale_str: self.current_scale = 0.8
        elif "1.2" in scale_str: self.current_scale = 1.2
        elif "1.4" in scale_str: self.current_scale = 1.4
        elif "1.6" in scale_str: self.current_scale = 1.6
        else: self.current_scale = 1.0

        new_w = int(400 * self.current_scale)
        new_h = int(560 * self.current_scale)
        self.root.geometry(f"{new_w}x{new_h}")

        # Tính toán lại tọa độ cho các thành phần neo cố định (Ghim, Theme, Dưới, Đồng hồ)
        self.btn_pin.place(relx=1.0, x=int(-85 * self.current_scale), y=int(15 * self.current_scale), width=int(70 * self.current_scale))
        self.btn_theme.place(relx=1.0, x=int(-150 * self.current_scale), y=int(15 * self.current_scale), width=int(60 * self.current_scale))
        self.btn_bottom.place(relx=1.0, x=int(-215 * self.current_scale), y=int(15 * self.current_scale), width=int(60 * self.current_scale))

        self._scale_widget_tree(self.root, self.current_scale)

    def _on_list_configure(self, event=None):
        self.kw_canvas.configure(scrollregion=self.kw_canvas.bbox("all"))
        # Ép dính lên trên cùng nếu nội dung ngắn hơn khung
        if self.kw_list_inner_frame.winfo_height() <= self.kw_canvas.winfo_height():
            self.kw_canvas.yview_moveto(0)

    def _on_canvas_configure(self, event):
        self.kw_canvas.itemconfig(self.kw_canvas_window, width=event.width)
        if self.kw_list_inner_frame.winfo_height() <= event.height:
            self.kw_canvas.yview_moveto(0)

    def _on_mousewheel(self, event):
        """Hàm xử lý cuộn chuột cho danh sách từ khóa"""
        try:
            # Nếu nội dung ngắn hơn khung thì chặn cuộn hoàn toàn
            if self.kw_list_inner_frame.winfo_height() <= self.kw_canvas.winfo_height():
                self.kw_canvas.yview_moveto(0)
                return
                
            yview = self.kw_canvas.yview()
            if getattr(event, 'num', None) == 5 or event.delta < 0:
                if yview[1] < 1.0: # Chưa đến đáy
                    self.kw_canvas.yview_scroll(1, "units")
            elif getattr(event, 'num', None) == 4 or event.delta > 0:
                if yview[0] > 0.0: # Chưa chạm đỉnh (tránh tạo khoảng trống phía trên)
                    self.kw_canvas.yview_scroll(-1, "units")
        except Exception: pass

    def _scale_widget_tree(self, widget, f):
        """Đệ quy quét toàn bộ giao diện và cập nhật kích thước Font chữ"""
        if not hasattr(self, '_original_fonts'):
            self._original_fonts = {}
            
        if widget not in self._original_fonts:
            try:
                self._original_fonts[widget] = widget.cget('font')
            except Exception:
                self._original_fonts[widget] = None

        orig_font = self._original_fonts[widget]
        if orig_font:
            try:
                if isinstance(orig_font, tuple) or isinstance(orig_font, list):
                    new_size = max(1, int(orig_font[1] * f))
                    new_font = (orig_font[0], new_size) + tuple(orig_font[2:])
                    widget.config(font=new_font)
                elif isinstance(orig_font, str):
                    parts = orig_font.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        new_size = max(1, int(int(parts[1]) * f))
                        new_font = f"{parts[0]} {new_size} {' '.join(parts[2:])}"
                        widget.config(font=new_font)
            except Exception:
                pass

        for child in widget.winfo_children():
            self._scale_widget_tree(child, f)

    def get_theme_maps(self, to_light=True):
        bg_map = {
            "#121212": "#f5f5f5", "#1e1e1e": "#ffffff",
            "#263238": "#b3e5fc", "#333333": "#e0e0e0", "#555555": "#cccccc"
        }
        fg_map = {
            "#00ffff": "#00509e", "#e0e0e0": "#333333", "#b388ff": "#5e35b1",
            "#00e676": "#2e7d32", "#ffb74d": "#ef6c00", "#4dd0e1": "#00838f",
            "#f48fb1": "#ad1457", "#a0a0a0": "#666666", "#00bcd4": "#1565c0",
            "#ff5252": "#d32f2f", "#ffff00": "#f57f17", "#d2b48c": "#8b4513",
            "#ffffff": "#000000"
        }
        if not to_light:
            bg_map = {v: k for k, v in bg_map.items()}
            fg_map = {v: k for k, v in fg_map.items()}
        return bg_map, fg_map

    def get_color(self, hex_color):
        if getattr(self, 'is_dark_mode', True):
            return hex_color
        _, fg_map = self.get_theme_maps(to_light=True)
        return fg_map.get(hex_color.lower(), hex_color)

    def _apply_theme_to_widget(self, widget, bg_map, fg_map):
        try:
            bg = str(widget.cget("bg")).lower()
            if bg in bg_map: widget.config(bg=bg_map[bg])
        except: pass
        try:
            fg = str(widget.cget("fg")).lower()
            if fg in fg_map: widget.config(fg=fg_map[fg])
        except: pass
        try:
            abg = str(widget.cget("activebackground")).lower()
            if abg in bg_map: widget.config(activebackground=bg_map[abg])
        except: pass
        try:
            afg = str(widget.cget("activeforeground")).lower()
            if afg in fg_map: widget.config(activeforeground=fg_map[afg])
        except: pass
        try:
            ibg = str(widget.cget("insertbackground")).lower()
            if ibg in fg_map: widget.config(insertbackground=fg_map[ibg])
        except: pass
        try:
            rbg = str(widget.cget("readonlybackground")).lower()
            if rbg in bg_map: widget.config(readonlybackground=bg_map[rbg])
        except: pass
        for child in widget.winfo_children():
            self._apply_theme_to_widget(child, bg_map, fg_map)

    def apply_current_theme(self, widget):
        if not getattr(self, 'is_dark_mode', True):
            bg_map, fg_map = self.get_theme_maps(to_light=True)
            self._apply_theme_to_widget(widget, bg_map, fg_map)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.btn_theme.config(text="🌙 Dark" if self.is_dark_mode else "☀️ Light")
        bg_map, fg_map = self.get_theme_maps(to_light=not self.is_dark_mode)
        self._apply_theme_to_widget(self.root, bg_map, fg_map)

    def load_credentials(self):
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"phone": "", "password": ""}

    def save_credentials(self, phone, password):
        try:
            os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump({"phone": phone, "password": password}, f)
        except Exception as e:
            print(f"Lỗi lưu tài khoản: {e}")

    def load_keywords(self):
        try:
            if os.path.exists(self.keywords_file):
                with open(self.keywords_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return ["moneytask.top"]
        
    def save_keywords(self):
        try:
            os.makedirs(os.path.dirname(self.keywords_file), exist_ok=True)
            with open(self.keywords_file, 'w', encoding='utf-8') as f:
                json.dump(self.keywords, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Lỗi lưu từ khóa: {e}")

    def refresh_keyword_list(self):
        for widget in self.kw_list_inner_frame.winfo_children():
            widget.destroy()

        for idx, kw in enumerate(self.keywords):
            row = tk.Frame(self.kw_list_inner_frame, bg="#1e1e1e")
            row.pack(fill=tk.X, pady=1)

            lbl = tk.Label(row, text=kw, font=("Arial", 8), bg="#1e1e1e", fg="#00e676", anchor="w", cursor="hand2")

            delete_btn = tk.Label(row, text="🗑️", font=("Arial", 8), bg="#1e1e1e", fg="#ff5252", cursor="hand2")
            delete_btn.pack(side=tk.RIGHT, padx=(0, 5))
            delete_btn.bind("<Button-1>", lambda e, i=idx: self.delete_keyword_by_index(i))

            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            # Bắt sự kiện click để chọn và kéo thả
            lbl.bind("<ButtonPress-1>", lambda e, i=idx: self.on_drag_start(e, i))
            lbl.bind("<B1-Motion>", self.on_drag_motion)
            lbl.bind("<ButtonRelease-1>", self.on_drag_release)
            
            row.bind("<ButtonPress-1>", lambda e, i=idx: self.on_drag_start(e, i))
            row.bind("<B1-Motion>", self.on_drag_motion)
            row.bind("<ButtonRelease-1>", self.on_drag_release)

            # Double-click (nháy đúp) để tự động mở tab mới và tìm kiếm
            lbl.bind("<Double-1>", lambda e, k=kw: self.trigger_type_keyword(k))
            row.bind("<Double-1>", lambda e, k=kw: self.trigger_type_keyword(k))

            # Kế thừa sự kiện cuộn chuột cho từng nút, nhãn trong danh sách (Tránh bị chặn khi trỏ trúng chữ)
            for w in (row, lbl, delete_btn):
                w.bind("<MouseWheel>", self._on_mousewheel)
                w.bind("<Button-4>", self._on_mousewheel)
                w.bind("<Button-5>", self._on_mousewheel)
            
        if hasattr(self, 'current_scale') and self.current_scale != 1.0:
            self._scale_widget_tree(self.kw_list_inner_frame, self.current_scale)
        if hasattr(self, 'apply_current_theme'):
            self.apply_current_theme(self.kw_list_inner_frame)

    def add_keyword(self):
        kw = self.kw_entry.get().strip()
        if kw and kw != self.placeholder_text and kw not in self.keywords:
            self.keywords.insert(0, kw)
            self.save_keywords()
            self.refresh_keyword_list()
            self.kw_entry.delete(0, tk.END)
            self.root.focus()
            self.add_placeholder()

    def update_keyword(self):
        if getattr(self, 'selected_kw_idx', None) is None: return
        idx = self.selected_kw_idx
        if idx >= len(self.keywords): return
        new_kw = self.kw_entry.get().strip()
        if new_kw and new_kw != self.placeholder_text:
            self.keywords[idx] = new_kw
            self.save_keywords()
            self.refresh_keyword_list()
            self.on_keyword_select(new_kw, idx)

    def delete_keyword(self):
        if getattr(self, 'selected_kw_idx', None) is None: return
        idx = self.selected_kw_idx
        if idx >= len(self.keywords): return
        del self.keywords[idx]
        self.selected_kw_idx = None
        self.save_keywords()
        self.refresh_keyword_list()
        self.kw_entry.delete(0, tk.END)
        self.root.focus()
        self.add_placeholder()

    def delete_keyword_by_index(self, index_to_delete):
        if index_to_delete >= len(self.keywords): return

        current_selected_idx = getattr(self, 'selected_kw_idx', None)

        del self.keywords[index_to_delete]

        if current_selected_idx is not None:
            if current_selected_idx == index_to_delete:
                # The selected item was deleted, so clear the entry and selection
                self.selected_kw_idx = None
                self.kw_entry.delete(0, tk.END)
                self.add_placeholder()
            elif current_selected_idx > index_to_delete:
                # An item before the selected one was deleted, so the index shifts down
                self.selected_kw_idx -= 1

        self.save_keywords()
        self.refresh_keyword_list()

        # Re-highlight the selected item if it still exists
        if self.selected_kw_idx is not None and self.selected_kw_idx < len(self.keywords):
            # This will re-apply highlight and text in entry
            self.on_keyword_select(self.keywords[self.selected_kw_idx], self.selected_kw_idx)

    def on_keyword_select(self, kw, idx):
        self.selected_kw_idx = idx
        self.kw_entry.delete(0, tk.END)
        self.kw_entry.config(fg=self.get_color("#ffffff"))
        self.kw_entry.insert(0, kw)

        for i, row_widget in enumerate(self.kw_list_inner_frame.winfo_children()):
            bg_color = "#333333" if i == idx else "#1e1e1e"
            row_widget.config(bg=bg_color)
            for child in row_widget.winfo_children():
                child.config(bg=bg_color)

    def toggle_optimize(self):
        """Bật/tắt chế độ tối ưu hóa giảm lag (CPU/RAM)"""
        self.is_optimized = not getattr(self, 'is_optimized', False)
        if self.is_optimized:
            self.btn_optimize.config(bg="#00e676", fg="black", text="⚡ Đã Giảm Lag")
            self.engine.optimize_performance = True
            messagebox.showinfo("Tối ưu", "Đã BẬT chế độ giảm lag.\n\nTrình duyệt sẽ được cấu hình giới hạn dung lượng lưu trữ và tự động dọn dẹp bộ nhớ đệm (Cache) mỗi 60 giây để hoạt động mượt mà hơn, mà không bị tắt hình ảnh hay quảng cáo.", parent=self.root)
        else:
            self.btn_optimize.config(bg="#673ab7", fg="white", text="⚡ Giảm Lag")
            self.engine.optimize_performance = False
            messagebox.showinfo("Tối ưu", "Đã TẮT chế độ giảm lag.\n\nTrình duyệt sẽ lưu bộ nhớ đệm đầy đủ bình thường.", parent=self.root)

    def on_drag_start(self, event, index):
        self._drag_start_y = event.y_root
        self._drag_index = index
        self._drag_threshold_met = False
        
        # Chọn từ khóa khi click
        if index < len(self.keywords):
            self.on_keyword_select(self.keywords[index], index)

    def on_drag_motion(self, event):
        if getattr(self, '_drag_index', None) is None:
            return
            
        y_diff = event.y_root - self._drag_start_y
        if abs(y_diff) > 5: # Ngưỡng kéo 5 pixel
            self._drag_threshold_met = True
            
        if self._drag_threshold_met:
            self.kw_canvas.config(cursor="fleur")
            target_index = self._get_drag_target_index(event.y_root)
            
            # Đổi màu hiển thị nháp dòng mục tiêu
            for i, child in enumerate(self.kw_list_inner_frame.winfo_children()):
                if i == target_index and i != self._drag_index:
                    bg_color = "#555555" # Màu xám sáng cho dòng sắp thả xuống
                elif i == self._drag_index:
                    bg_color = "#333333" # Dòng đang được kéo
                else:
                    bg_color = "#1e1e1e" # Màu mặc định
                    
                child.config(bg=bg_color)
                for sub in child.winfo_children():
                    sub.config(bg=bg_color)

    def _get_drag_target_index(self, y_root):
        children = self.kw_list_inner_frame.winfo_children()
        if not children:
            return 0
            
        for i, child in enumerate(children):
            child_y = child.winfo_rooty()
            child_h = child.winfo_height()
            # Trả về index nếu chuột nằm ở nửa trên của dòng này
            if y_root < child_y + child_h // 2:
                return i
        return len(children) - 1

    def on_drag_release(self, event):
        if getattr(self, '_drag_index', None) is None:
            return
            
        self.kw_canvas.config(cursor="")
        
        if getattr(self, '_drag_threshold_met', False):
            target_index = self._get_drag_target_index(event.y_root)
            if target_index != self._drag_index:
                # Đổi vị trí từ khóa
                kw = self.keywords.pop(self._drag_index)
                self.keywords.insert(target_index, kw)
                self.save_keywords()
                self.selected_kw_idx = target_index
                
                self._drag_index = None
                self._drag_threshold_met = False
                
                self.refresh_keyword_list()
                if self.selected_kw_idx is not None and self.selected_kw_idx < len(self.keywords):
                    self.on_keyword_select(self.keywords[self.selected_kw_idx], self.selected_kw_idx)
                return
            else:
                # Khôi phục màu hiển thị nếu người dùng kéo nhưng thả lại đúng vị trí cũ
                if self.selected_kw_idx is not None and self.selected_kw_idx < len(self.keywords):
                    self.on_keyword_select(self.keywords[self.selected_kw_idx], self.selected_kw_idx)
        
        self._drag_index = None
        self._drag_threshold_met = False

    def trigger_type_keyword(self, keyword):
        if self.engine.playwright is None:
            return

        # Tự động gửi lệnh mở tab mới và tìm kiếm luôn
        self.engine._pending_action = "open_tab_and_search"
        self.engine._keyword_to_type = keyword
        self.status_label.config(text=f"Trạng thái: Tự động mở tab mới và tìm '{keyword}'...", fg=self.get_color("#b388ff"))
        
        self.root.after(3000, lambda: self.status_label.config(text="Trạng thái: Trình duyệt đang chạy. Đóng trình duyệt và bấm 'Delete' để dọn dẹp.", fg=self.get_color("#00bcd4")))

    def show_credentials_dialog(self, event=None):
        if hasattr(self, 'cred_dialog') and self.cred_dialog.winfo_exists():
            self.cred_dialog.lift()
            return
            
        self.cred_dialog = tk.Toplevel(self.root)
        self.cred_dialog.withdraw() # Ẩn cửa sổ tạm thời để chống chớp trắng
        self.cred_dialog.title("Cài đặt Tài Khoản")
        
        # Tính toán để hộp thoại luôn nằm ngay giữa phần mềm, dù phần mềm đang bị kéo đi đâu
        dialog_w = int(300 * self.current_scale)
        dialog_h = int(230 * self.current_scale)
        self.root.update_idletasks()
        main_x = self.root.winfo_rootx()
        main_y = self.root.winfo_rooty()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        
        pos_x = main_x + (main_w // 2) - (dialog_w // 2)
        pos_y = main_y + (main_h // 2) - (dialog_h // 2)
        self.cred_dialog.geometry(f"{dialog_w}x{dialog_h}+{pos_x}+{pos_y}")
        
        self.cred_dialog.configure(bg="#121212")
        self.cred_dialog.transient(self.root)
        self.cred_dialog.grab_set()
        
        creds = self.load_credentials()
        
        tk.Label(self.cred_dialog, text="Số điện thoại:", font=("Arial", 9), fg="#e0e0e0", bg="#121212").pack(pady=(15, 2))
        phone_entry = tk.Entry(self.cred_dialog, font=("Arial", 10), bg="#1e1e1e", fg="#b388ff", insertbackground="#b388ff", relief=tk.FLAT)
        phone_entry.pack(pady=2, ipady=3, padx=20, fill=tk.X)
        phone_entry.insert(0, creds.get("phone", ""))
        
        tk.Label(self.cred_dialog, text="Mật khẩu:", font=("Arial", 9), fg="#e0e0e0", bg="#121212").pack(pady=(10, 2))
        
        pwd_frame = tk.Frame(self.cred_dialog, bg="#121212")
        pwd_frame.pack(pady=2, padx=20, fill=tk.X)
        
        pwd_entry = tk.Entry(pwd_frame, font=("Arial", 10), bg="#1e1e1e", fg="#b388ff", insertbackground="#b388ff", relief=tk.FLAT, show="*")
        pwd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        pwd_entry.insert(0, creds.get("password", ""))
        
        def toggle_pwd():
            if pwd_entry.cget('show') == '':
                pwd_entry.config(show='*')
                btn_toggle_pwd.config(text="👁️")
            else:
                pwd_entry.config(show='')
                btn_toggle_pwd.config(text="🙈")
                
        btn_toggle_pwd = tk.Button(pwd_frame, text="👁️", bg="#1e1e1e", fg="#b388ff", relief=tk.FLAT, font=("Arial", 10), width=3, command=toggle_pwd, activebackground="#333333", activeforeground="#b388ff")
        btn_toggle_pwd.pack(side=tk.LEFT, padx=(5, 0), ipady=1)
        
        def save():
            phone = phone_entry.get().strip()
            pwd = pwd_entry.get().strip()
            if not phone or not pwd:
                messagebox.showwarning("Lỗi", "Vui lòng nhập đầy đủ Số điện thoại và Mật khẩu!", parent=self.cred_dialog)
                return
            self.save_credentials(phone, pwd)
            self.cred_dialog.destroy()
            messagebox.showinfo("Thành công", "Đã lưu thông tin tài khoản!", parent=self.root)
            
        tk.Button(self.cred_dialog, text="💾 Lưu và Đóng", command=save, bg="#00e676", fg="black", font=("Arial", 9, "bold"), relief=tk.FLAT, activebackground="#2e7d32").pack(pady=15, ipadx=20)
        
        self._scale_widget_tree(self.cred_dialog, self.current_scale)
        self.apply_current_theme(self.cred_dialog)
        self.cred_dialog.deiconify() # Hiển thị ra sau khi đã dàn trang xong

    def toggle_url_visibility(self):
        """Hiện/ẩn nội dung ô nhập URL"""
        if self.url_entry.cget('show') == '':
            self.url_entry.config(show='*')
            self.btn_toggle_url.config(text="🙈")
        else:
            self.url_entry.config(show='')
            self.btn_toggle_url.config(text="👁️")

    def toggle_pin(self):
        """Bật/tắt chế độ luôn nổi trên cùng (Topmost) của cửa sổ"""
        self.is_pinned = not self.is_pinned
        self.root.attributes("-topmost", self.is_pinned)
        if self.is_pinned:
            if getattr(self, 'is_bottommost', False):
                self.is_bottommost = False
                self.btn_bottom.config(text="⬇️ Dưới", fg=self.get_color("#a0a0a0"))
            self.btn_pin.config(text="📍 Đã Ghim", fg=self.get_color("#00e676"))
        else:
            self.btn_pin.config(text="📌 Ghim", fg=self.get_color("#a0a0a0"))
            
    def toggle_bottom(self):
        """Bật/tắt chế độ luôn nằm dưới cùng của cửa sổ"""
        self.is_bottommost = not getattr(self, 'is_bottommost', False)
        if self.is_bottommost:
            if getattr(self, 'is_pinned', False):
                self.is_pinned = False
                self.root.attributes("-topmost", False)
                self.btn_pin.config(text="📌 Ghim", fg=self.get_color("#a0a0a0"))
            self.btn_bottom.config(text="⏬ Chìm", fg=self.get_color("#b388ff"))
            
            # Bắt sự kiện click hoặc focus để lập tức ép phần mềm xuống đáy
            if not hasattr(self, '_focus_lower_bound'):
                self.root.bind("<FocusIn>", self._force_lower, add="+")
                self.root.bind_all("<Button-1>", self._force_lower, add="+")
                self._focus_lower_bound = True
                
            self.root.lower()
            self._keep_bottommost()
        else:
            self.btn_bottom.config(text="⬇️ Dưới", fg=self.get_color("#a0a0a0"))

    def _force_lower(self, event=None):
        if getattr(self, 'is_bottommost', False):
            self.root.lower()

    def _keep_bottommost(self):
        if getattr(self, 'is_bottommost', False):
            self.root.lower()
            self.root.after(150, self._keep_bottommost)
            
    def regenerate_profiles(self):
        if self.engine.playwright is not None or (hasattr(self, '_is_wiping') and self._is_wiping):
            dialog = tk.Toplevel(self.root)
            dialog.withdraw()
            dialog.title("Cảnh báo")
            
            dialog_w = int(350 * self.current_scale)
            dialog_h = int(120 * self.current_scale)
            self.root.update_idletasks()
            
            main_x = self.root.winfo_rootx()
            main_y = self.root.winfo_rooty()
            main_w = self.root.winfo_width()
            main_h = self.root.winfo_height()
            pos_x = main_x + (main_w // 2) - (dialog_w // 2)
            pos_y = main_y + (main_h // 2) - (dialog_h // 2)
            
            dialog.geometry(f"{dialog_w}x{dialog_h}+{pos_x}+{pos_y}")
            dialog.configure(bg="#121212")
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.attributes("-topmost", True) # Nổi lên trên cùng
            
            tk.Label(dialog, text="Hãy đóng trình duyệt đang chạy để tiếp tục!", font=("Arial", 9, "bold"), fg="#ffb74d", bg="#121212").pack(expand=True, pady=(20, 10))
            tk.Button(dialog, text="Đóng", command=dialog.destroy, bg="#333333", fg="white", font=("Arial", 8, "bold"), relief=tk.FLAT, activebackground="#555555", activeforeground="white", width=10).pack(pady=(0, 20))
            
            self._scale_widget_tree(dialog, self.current_scale)
            self.apply_current_theme(dialog)
            dialog.deiconify()
            return
        self.current_profile = None
        self.status_label.config(text="Trạng thái: Sẵn sàng tạo trình duyệt mới", fg=self.get_color("#a0a0a0"))

    def reset_to_ready_state(self):
        """Reset giao diện về trạng thái sẵn sàng tạo trình duyệt mới."""
        self.btn_ip_that.config(state=tk.NORMAL)
        self.btn_proxy.config(state=tk.NORMAL)
        self.btn_delete.config(state=tk.NORMAL)
        self.btn_auto_task.config(state=tk.DISABLED)
        self.btn_auto_task_step.config(state=tk.DISABLED)
        self.btn_refresh.config(state=tk.DISABLED)
        self.btn_deep_clean.config(state=tk.NORMAL)
        self.btn_optimize.config(state=tk.NORMAL)
        self.status_label.config(text="Trạng thái: Sẵn sàng tạo trình duyệt mới", fg=self.get_color("#a0a0a0"))
        self.current_profile = None
        
        if getattr(self, 'auto_launch_hidden', False):
            self.auto_launch_hidden = False # Chỉ chạy tự động ở lần nạp cấu hình đầu tiên
            self.root.after(500, lambda: self.launch_ip_that(headless=True))
            
    def _wipe_all_residual_data(self):
        """Hàm dùng chung để quét và xóa triệt để toàn bộ dữ liệu Profile ẩn danh"""
        # 1. Xóa thư mục Profile đang dùng hiện tại (nếu có)
        try:
            current_path = getattr(self.engine, 'user_data_dir', None)
            if current_path and os.path.exists(current_path) and ("Clean_Profile_" in current_path or "playwright_" in current_path or "pyright-" in current_path):
                shutil.rmtree(current_path, ignore_errors=True)
        except Exception: pass
        
        # 2. Xóa tất cả các thư mục Profile cũ còn sót lại trong thư mục gốc
        try:
            base_dir = self.engine.device_faker.base_dir
            if os.path.exists(base_dir):
                for item in os.listdir(base_dir):
                    item_path = os.path.join(base_dir, item)
                    if os.path.isdir(item_path) and "Clean_Profile_" in item:
                        shutil.rmtree(item_path, ignore_errors=True)
        except Exception: pass
        
        # 3. Dọn rác trong thư mục Temp của hệ điều hành (Chỉ xóa file do Tool tạo ra)
        try:
            temp_dir = tempfile.gettempdir()
            if os.path.exists(temp_dir):
                for item in os.listdir(temp_dir):
                    if item.startswith("Clean_Profile_"):
                        item_path = os.path.join(temp_dir, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
        except Exception: pass

    def on_closing(self):
        """Xử lý sự kiện đóng cửa sổ chính của ứng dụng."""
        self.show_auto_close_dialog()

    def show_auto_close_dialog(self):
        """Hiển thị hộp thoại đếm ngược 3s trước khi tự động dọn dẹp và thoát."""
        dialog = tk.Toplevel(self.root)
        dialog.withdraw()
        dialog.title("Cảnh báo thoát")
        
        dialog_w = int(380 * self.current_scale)
        dialog_h = int(160 * self.current_scale)
        self.root.update_idletasks()
        pos_x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - (dialog_w // 2)
        pos_y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - (dialog_h // 2)
        dialog.geometry(f"{dialog_w}x{dialog_h}+{pos_x}+{pos_y}")
        
        dialog.configure(bg="#121212")
        dialog.transient(self.root) # Nổi trên cửa sổ chính
        dialog.grab_set() # Khóa cửa sổ chính cho đến khi xử lý xong hộp thoại
        
        tk.Label(dialog, text="Đang chuẩn bị đóng chương trình!\nHệ thống sẽ dọn sạch toàn bộ Profile ẩn danh sau:", font=("Arial", 8), fg="#e0e0e0", bg="#121212").pack(pady=8)
        
        countdown_label = tk.Label(dialog, text="3", font=("Arial", 14, "bold"), fg="#ff5252", bg="#121212")
        countdown_label.pack()
        
        btn_frame = tk.Frame(dialog, bg="#121212")
        btn_frame.pack(pady=8)
        
        countdown_active = [True] # Dùng list để dễ dàng thay đổi state trong local function
        
        def do_cleanup_and_exit():
            countdown_active[0] = False
            self.engine.close_and_cleanup()
            
            def final_wipe_and_exit():
                if self.engine.playwright is not None:
                    self.root.after(200, final_wipe_and_exit) # Chờ engine tắt hẳn
                    return
                
                self._wipe_all_residual_data()
                
                self.root.destroy()
            final_wipe_and_exit()
            
        def cancel():
            countdown_active[0] = False
            dialog.destroy()
            
        tk.Button(btn_frame, text="Dọn dẹp & Thoát ngay", command=do_cleanup_and_exit, bg="#b71c1c", fg="white", font=("Arial", 7, "bold"), relief=tk.FLAT, activebackground="#f44336", activeforeground="white").pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="Hủy (Quay lại)", command=cancel, bg="#333333", fg="#e0e0e0", font=("Arial", 7), relief=tk.FLAT, activebackground="#555555", activeforeground="#e0e0e0").pack(side=tk.LEFT, padx=8)
        
        self._scale_widget_tree(dialog, self.current_scale)
        self.apply_current_theme(dialog)
        dialog.deiconify()

        def tick(time_left):
            if not countdown_active[0] or not dialog.winfo_exists():
                return
            if time_left > 0:
                countdown_label.config(text=str(time_left))
                self.root.after(1000, tick, time_left - 1)
            else:
                do_cleanup_and_exit()
                
        # Bắt đầu đếm ngược từ 3 giây
        tick(3)
        # Nếu người dùng bấm X trên hộp thoại đếm ngược -> xem như Hủy
        dialog.protocol("WM_DELETE_WINDOW", cancel)

    def set_ui_for_browser_state(self, is_running):
        """Cập nhật trạng thái các nút bấm và label trên giao diện."""
        if is_running:
            self.btn_ip_that.config(state=tk.DISABLED)
            self.btn_proxy.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.NORMAL)
            self.btn_auto_login.config(state=tk.NORMAL)
            self.btn_auto_task.config(state=tk.NORMAL)
            self.btn_auto_task_step.config(state=tk.NORMAL)
            self.btn_refresh.config(state=tk.NORMAL)
            self.btn_deep_clean.config(state=tk.DISABLED)
            self.btn_optimize.config(state=tk.DISABLED)
            self.status_label.config(text="Trạng thái: Trình duyệt đang chạy. Đóng trình duyệt và bấm 'Delete' để dọn dẹp.", fg=self.get_color("#00bcd4"))
        else:
            self.btn_ip_that.config(state=tk.NORMAL)
            self.btn_proxy.config(state=tk.NORMAL)
            self.btn_auto_login.config(state=tk.DISABLED)
            self.btn_auto_task.config(state=tk.DISABLED)
            self.btn_auto_task_step.config(state=tk.DISABLED)
            self.btn_refresh.config(state=tk.DISABLED)
            self.btn_deep_clean.config(state=tk.NORMAL)
            self.btn_optimize.config(state=tk.NORMAL)

    def trigger_auto_login(self):
        """Gửi lệnh điền tài khoản đến luồng duyệt web"""
        creds = self.load_credentials()
        if not creds.get("phone") or not creds.get("password"):
            self.show_credentials_dialog()
            return
            
        if self.engine.playwright is not None:
            self.engine.login_phone = creds.get("phone")
            self.engine.login_password = creds.get("password")
            self.engine._pending_action = "fill_login"
            self.status_label.config(text="Trạng thái: Đang tự động điền tài khoản...", fg=self.get_color("#00bcd4"))
            self.root.after(2000, lambda: self.status_label.config(text="Trạng thái: Trình duyệt đang chạy. Đóng trình duyệt và bấm 'Delete' để dọn dẹp.", fg=self.get_color("#00bcd4")))
            
    def trigger_auto_task(self):
        """Gửi lệnh thực hiện nhiệm vụ lấy mã đến luồng duyệt web"""
        if self.engine.playwright is not None:
            self.engine._pending_action = "auto_task"
            self.status_label.config(text="Trạng thái: Đang chạy tiến trình lấy mã tự động...", fg=self.get_color("#b388ff"))
            self.root.after(3000, lambda: self.status_label.config(text="Trạng thái: Đang theo dõi tiến trình lấy mã...", fg=self.get_color("#b388ff")))

    def trigger_auto_task_step(self):
        """Gửi lệnh thực hiện nhiệm vụ lấy mã theo step đến luồng duyệt web"""
        if self.engine.playwright is not None:
            self.engine._pending_action = "auto_task_step"
            self.status_label.config(text="Trạng thái: Đang chạy tiến trình lấy mã upto step...", fg=self.get_color("#b388ff"))
            self.root.after(3000, lambda: self.status_label.config(text="Trạng thái: Đang theo dõi tiến trình lấy mã...", fg=self.get_color("#b388ff")))

    def trigger_refresh(self):
        """Gửi lệnh tải lại trang (F5) đến luồng duyệt web"""
        if self.engine.playwright is not None:
            self.engine._pending_action = "reload_page"
            self.status_label.config(text="Trạng thái: Đang tải lại trang...", fg=self.get_color("#ffb74d"))
            self.root.after(2000, lambda: self.status_label.config(text="Trạng thái: Trình duyệt đang chạy. Đóng trình duyệt và bấm 'Delete' để dọn dẹp.", fg=self.get_color("#00bcd4")))

    def handle_space_refresh(self, event=None):
        """Xử lý sự kiện nhấn phím Space để tải lại trang"""
        # Bỏ qua nếu người dùng đang gõ văn bản trong ô tìm kiếm hoặc URL (Tránh bị dính phím Cách)
        if event and event.widget.winfo_class() in ('Entry', 'Text', 'TCombobox'):
            return
            
        self.trigger_refresh()

    def run_browser_thread(self, target_url, use_proxy, headless=False):
        """Chạy việc mở trình duyệt trong một thread riêng để không làm treo giao diện."""
        # Cập nhật giao diện ngay lập tức
        self.set_ui_for_browser_state(is_running=True)
        self.status_label.config(text="Trạng thái: Đang khởi chạy trình duyệt...", fg=self.get_color("#ffb74d"))
        
        # Chỉ tạo profile mới khi thực sự cần (khi bấm nút Mở trình duyệt)
        if self.current_profile is None:
            self.status_label.config(text="Trạng thái: Đang tạo profile trình duyệt...", fg=self.get_color("#ffb74d"))
            preferred_platform = self.platform_var.get()
            self.current_profile = self.engine.device_faker.generate_new_device(platform_type=preferred_platform)
            self.status_label.config(text="Trạng thái: Đang khởi chạy trình duyệt...", fg=self.get_color("#ffb74d"))
        
        # Nạp sẵn tài khoản trước để sẵn sàng cho tự động đăng nhập
        creds = self.load_credentials()
        self.engine.login_phone = creds.get("phone", "")
        self.engine.login_password = creds.get("password", "")

        try:
            # Callback này sẽ được gọi từ worker thread khi trình duyệt đã mở thành công
            def on_launch_success(device_profile):
                def update_ui():
                    self.status_label.config(text="Trạng thái: Trình duyệt đang chạy. Đóng trình duyệt và bấm 'Delete' để dọn dẹp.", fg=self.get_color("#00bcd4"))
                self.root.after(0, update_ui)

            # Lệnh này sẽ block cho đến khi trình duyệt được đóng và dọn dẹp xong
            self.engine.run_session_and_wait(
                target_url=target_url, 
                use_proxy=use_proxy,
                on_launch_callback=on_launch_success,
                device_profile=self.current_profile,
                on_browser_created=None,
                headless=headless,
                search_keywords=self.keywords
            )
        except Exception as e:
            print(f"Lỗi: {e}")
            messagebox.showerror("Lỗi Mở Trình Duyệt", f"Không thể mở trình duyệt.\n\nChi tiết lỗi:\n{e}")
        finally:
            def on_browser_thread_exit():
                self.set_ui_for_browser_state(False)
                # Tự động dọn dẹp khi trình duyệt tắt để dọn temp & chuyển sang thiết bị tiếp theo
                if hasattr(self, '_is_wiping') and not self._is_wiping:
                    self.btn_ip_that.config(state=tk.DISABLED)
                    self.btn_proxy.config(state=tk.DISABLED)
                    self.btn_delete.config(state=tk.NORMAL)
                    self.status_label.config(text="Trạng thái: Trình duyệt đã đóng. Đang tự động dọn dẹp...", fg=self.get_color("#ffb74d"))
                    self.delete_session()
            self.root.after(0, on_browser_thread_exit)

    def launch_ip_that(self, headless=False):
        url = self.url_entry.get().strip()
        threading.Thread(target=self.run_browser_thread, args=(url, False, headless), daemon=True).start()

    def launch_proxy(self, headless=False):
        url = self.url_entry.get().strip()
        threading.Thread(target=self.run_browser_thread, args=(url, True, headless), daemon=True).start()

    def delete_session(self):
        """Thực hiện dọn dẹp session với thanh tiến trình trực quan."""
        self.btn_delete.config(state=tk.DISABLED) # Tránh click đúp
        self.status_label.config(text="Trạng thái: Đang tiêu hủy dữ liệu...", fg=self.get_color("#ffb74d"))
        self._is_wiping = True
        
        # Tạo cửa sổ hiển thị tiến trình
        prog_win = tk.Toplevel(self.root)
        prog_win.withdraw()
        prog_win.title("Đang dọn dẹp...")
        
        dialog_w = int(380 * self.current_scale)
        dialog_h = int(150 * self.current_scale)
        self.root.update_idletasks()
        
        main_x = self.root.winfo_rootx()
        main_y = self.root.winfo_rooty()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        pos_x = main_x + (main_w // 2) - (dialog_w // 2)
        pos_y = main_y + (main_h // 2) - (dialog_h // 2)
        
        prog_win.geometry(f"{dialog_w}x{dialog_h}+{pos_x}+{pos_y}")
        prog_win.configure(bg="#121212")
        prog_win.transient(self.root)
        prog_win.grab_set() # Khóa màn hình chính
        prog_win.attributes("-topmost", True) # Ép hộp thoại nổi lên trên cùng (xuyên qua trình duyệt nếu có)
        prog_win.protocol("WM_DELETE_WINDOW", lambda: None) # Vô hiệu hóa nút X để tránh làm gián đoạn

        tk.Label(prog_win, text="Đang tiêu hủy dấu vết, Cookie, Lịch sử...", font=("Arial", 10, "bold"), fg="#ff5252", bg="#121212").pack(pady=10)

        progress = ttk.Progressbar(prog_win, orient=tk.HORIZONTAL, length=int(340*self.current_scale), mode='determinate')
        progress.pack(pady=5)

        file_label = tk.Label(prog_win, text="Khởi tạo...", font=("Courier", 8), fg="#ffb74d", bg="#121212")
        file_label.pack(pady=5)
        
        self._scale_widget_tree(prog_win, self.current_scale)
        self.apply_current_theme(prog_win)
        prog_win.deiconify()

        items_to_wipe = [
            "Đang đóng kết nối trình duyệt (nếu có)...",
            "Xác định thư mục gốc 'ChangeIMEI_Real_Profiles'...",
            "Bắt đầu quét và xóa các thư mục con...",
            "Đang xóa Profile...",
            "Đang xóa Profile...",
            "Hoàn tất xóa thư mục...",
            "Dọn dẹp các file rác còn sót lại...",
            "Giải phóng bộ nhớ RAM...",
            "Đã xóa sạch toàn bộ các Profile."
        ]
        total_items = len(items_to_wipe)

        def update_progress(index):
            if index < total_items:
                progress['value'] = (index / (total_items - 1)) * 100
                file_label.config(text=items_to_wipe[index])
                # Delay ngẫu nhiên để tạo cảm giác xử lý file chân thực
                self.root.after(random.randint(50, 250), update_progress, index + 1)
            else:
                self.engine.close_and_cleanup()
                
                # Chờ Playwright tắt hẳn rồi mới thực hiện xóa vật lý thư mục
                def wipe_browser_folder():
                    if self.engine.playwright is not None:
                        self.root.after(200, wipe_browser_folder)
                        return
                    
                    def do_actual_wipe():
                        file_label.config(text="Đang quét và xóa TOÀN BỘ các Profile đã tạo...")
                        
                        self._wipe_all_residual_data()
                        
                        def finish_wipe():
                            self._is_wiping = False
                            prog_win.destroy()
                            self.reset_to_ready_state()
                            
                        self.root.after(300, finish_wipe)

                    # Thêm một khoảng chờ ngắn để đảm bảo tiến trình trình duyệt đã được HĐH dọn dẹp hoàn toàn
                    # và giải phóng khóa file trước khi xóa, giúp việc xóa profile triệt để hơn.
                    self.root.after(500, do_actual_wipe)
                wipe_browser_folder()

        update_progress(0)

    def trigger_deep_clean(self):
        confirm = messagebox.askyesno("Xác nhận Deep Clean", 
                                      "CẢNH BÁO: Chức năng này sẽ quét TOÀN BỘ ổ đĩa C:\\ để tìm và xóa tận gốc mọi thư mục bắt đầu bằng 'Clean_Profile_'.\n\nQuá trình có thể mất từ vài phút đến chục phút. Bạn có chắc chắn muốn bắt đầu?", 
                                      parent=self.root)
        if confirm:
            self.run_deep_clean_thread()

    def run_deep_clean_thread(self):
        prog_win = tk.Toplevel(self.root)
        prog_win.title("Deep Clean đang chạy...")
        
        dialog_w = int(400 * self.current_scale)
        dialog_h = int(180 * self.current_scale)
        self.root.update_idletasks()
        
        main_x = self.root.winfo_rootx()
        main_y = self.root.winfo_rooty()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        pos_x = main_x + (main_w // 2) - (dialog_w // 2)
        pos_y = main_y + (main_h // 2) - (dialog_h // 2)
        
        prog_win.geometry(f"{dialog_w}x{dialog_h}+{pos_x}+{pos_y}")
        prog_win.configure(bg="#121212")
        prog_win.transient(self.root)
        prog_win.grab_set() 
        prog_win.attributes("-topmost", True)
        
        tk.Label(prog_win, text="Đang quét toàn bộ ổ C:\\ ...\nVui lòng kiên nhẫn chờ đợi (có thể mất vài phút).", font=("Arial", 9, "bold"), fg="#ffb74d", bg="#121212").pack(pady=10)
        
        status_label = tk.Label(prog_win, text="Đang chuẩn bị...", font=("Courier", 8), fg="#00e676", bg="#121212", wraplength=int(360*self.current_scale))
        status_label.pack(pady=5)
        
        stats_label = tk.Label(prog_win, text="Đã xóa: 0 | Lỗi: 0", font=("Arial", 9), fg="#ffffff", bg="#121212")
        stats_label.pack(pady=5)

        stop_flag = [False]

        def on_close_deep_clean():
            stop_flag[0] = True
            if prog_win.winfo_exists():
                status_label.config(text="Đang dừng quá trình quét...", fg="#ff5252")
                # Vô hiệu hóa nút X sau khi bấm 1 lần để tránh lỗi click nhiều lần
                prog_win.protocol("WM_DELETE_WINDOW", lambda: None)
        prog_win.protocol("WM_DELETE_WINDOW", on_close_deep_clean)

        self._scale_widget_tree(prog_win, self.current_scale)
        self.apply_current_theme(prog_win)
        
        def worker():
            target_prefix = "Clean_Profile_"
            root_dir = "C:\\"
            deleted_count = 0
            error_count = 0
            
            last_update_time = time.time()
            
            for dirpath, dirnames, filenames in os.walk(root_dir):
                if stop_flag[0]:
                    break
                current_time = time.time()
                if current_time - last_update_time > 0.5:
                    def update_scanning(path=dirpath):
                        if prog_win.winfo_exists():
                            display_path = path if len(path) <= 55 else "..." + path[-52:]
                            status_label.config(text=f"Đang quét: {display_path}")
                    self.root.after(0, update_scanning)
                    last_update_time = current_time

                for dirname in list(dirnames):
                    if stop_flag[0]:
                        break
                    if dirname.startswith(target_prefix):
                        full_path = os.path.join(dirpath, dirname)
                        try:
                            shutil.rmtree(full_path, ignore_errors=True)
                            if not os.path.exists(full_path):
                                deleted_count += 1
                            else:
                                error_count += 1
                        except Exception:
                            error_count += 1
                        
                        def update_stats(path=full_path, d=deleted_count, e=error_count):
                            if prog_win.winfo_exists():
                                display_path = path if len(path) <= 55 else "..." + path[-52:]
                                status_label.config(text=f"Phát hiện & xóa: {display_path}")
                                stats_label.config(text=f"Đã xóa: {d} | Lỗi: {e}")
                        self.root.after(0, update_stats)
                        
                        dirnames.remove(dirname)
            
            def finish(d=deleted_count, e=error_count, stopped=stop_flag[0]):
                if prog_win.winfo_exists():
                    prog_win.destroy()
                if stopped:
                    messagebox.showinfo("Deep Clean Đã Dừng", f"Quá trình dọn dẹp đã bị người dùng dừng lại giữa chừng.\n\nSố thư mục đã xóa: {d}\nSố thư mục bị lỗi: {e}", parent=self.root)
                else:
                    messagebox.showinfo("Deep Clean Hoàn Tất", f"Quá trình dọn dẹp sâu đã hoàn tất!\n\nSố thư mục đã xóa thành công: {d}\nSố thư mục bị lỗi (có thể do đang mở): {e}", parent=self.root)
            self.root.after(0, finish)
            
        threading.Thread(target=worker, daemon=True).start()

def main():
    # Bịt hoàn toàn cổng đầu ra, ngăn 100% log và lỗi in ra Terminal (Cửa sổ đen)
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

    root = tk.Tk()
    app = AntiDetectGUI(root)
    # Chạy vòng lặp giao diện
    root.mainloop()

if __name__ == "__main__":
    main()
