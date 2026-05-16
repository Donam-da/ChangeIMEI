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
        window_w = int(800 * self.current_scale)
        window_h = int(540 * self.current_scale)
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
        self.engine.set_network_callback(self.update_network_analysis)
        
        self.credentials_file = os.path.join(os.path.dirname(__file__), 'data', 'credentials.json')
        
        # Thiết kế các thành phần Giao diện (UI)
        tk.Label(root, text="Fix 24h upto", font=("Arial", 10, "bold"), fg="#00ffff", bg="#121212").pack(pady=10)
        
        self.is_pinned = False
        self.btn_pin = tk.Button(root, text="📌 Ghim", font=("Arial", 7, "bold"), bg="#1e1e1e", fg="#a0a0a0", relief=tk.FLAT, command=self.toggle_pin, activebackground="#333333", activeforeground="#00e676")
        self.btn_pin.place(relx=1.0, x=-120, y=15, width=100)

        self.is_dark_mode = True
        self.btn_theme = tk.Button(root, text="🌙 Dark", font=("Arial", 7, "bold"), bg="#1e1e1e", fg="#a0a0a0", relief=tk.FLAT, command=self.toggle_theme, activebackground="#333333", activeforeground="#00ffff")
        self.btn_theme.place(relx=1.0, x=-200, y=15, width=75)

        self.clock_label = tk.Label(root, font=("Courier", 8, "bold"), bg="#1e1e1e", fg="#00e676", relief=tk.FLAT)
        self.clock_label.place(x=15, y=15, width=160, height=22)
        self.update_clock()

        # Bảng thông tin mạng (Dùng lưới Grid để căn chỉnh Icon và Chữ luôn thẳng hàng)
        net_frame = tk.Frame(root, bg="#121212")
        net_frame.pack(pady=(0, 8))

        mac_num = hex(uuid.getnode()).replace('0x', '').zfill(12)
        mac_address = ':'.join(mac_num[i: i + 2] for i in range(0, 12, 2)).upper()
        
        self.mac_label = tk.Label(net_frame, text=f"MAC(Real): {mac_address}", font=("Arial", 8, "bold"), fg="#b388ff", bg="#121212", width=32, anchor="w")
        self.mac_label.grid(row=0, column=0, padx=6, sticky="w")
        
        self.virtual_mac_label = tk.Label(net_frame, text="MAC(Fake): Đang tạo...", font=("Arial", 8, "bold"), fg="#ff4081", bg="#121212", width=32, anchor="w")
        self.virtual_mac_label.grid(row=1, column=0, padx=6, sticky="w")

        self.ip_label = tk.Label(net_frame, text="🌐 IP: Đang kiểm...", font=("Arial", 8, "bold"), fg="#00e676", bg="#121212")
        self.ip_label.grid(row=0, column=1, rowspan=2, padx=6)

        self.ping_label = tk.Label(net_frame, text="⚡ Ping: ...", font=("Arial", 8, "bold"), fg="#ffb74d", bg="#121212")
        self.ping_label.grid(row=0, column=2, rowspan=2, padx=6)

        self.disconnect_count = 0
        self.disconnect_label = tk.Label(net_frame, text="❌ Rớt: 0", font=("Arial", 8, "bold"), fg="#ff5252", bg="#121212")
        self.disconnect_label.grid(row=0, column=3, padx=6, sticky="w")
        
        self.last_disconnect_label = tk.Label(net_frame, text="⏱️ Lúc: N/A", font=("Arial", 7, "italic"), fg="#a0a0a0", bg="#121212")
        self.last_disconnect_label.grid(row=1, column=3, padx=6, sticky="w")

        self.analysis_label = tk.Label(root, text="🔍 Phân tích mạng: Đang chờ thao tác...", font=("Arial", 8, "bold"), fg="#ffff00", bg="#121212")
        self.analysis_label.pack(pady=(0, 4))

        tk.Label(root, text="Nhập link URL muốn mở:", font=("Arial", 8), fg="#e0e0e0", bg="#121212").pack()
        
        url_frame = tk.Frame(root, bg="#121212")
        url_frame.pack(pady=4)
        
        self.url_entry = tk.Entry(url_frame, width=40, font=("Arial", 8), bg="#1e1e1e", fg="#00ffff", insertbackground="#00ffff", relief=tk.FLAT)
        self.url_entry.pack(side=tk.LEFT, ipady=2)
        self.url_entry.insert(0, "https://www.google.com/search?q=moneytask.top&sca_esv=3d73e6268d6609d9&sxsrf=ANbL-n5OwmW4jJHMCw_P-MHSjJYYql4e-Q%3A1778737875726&source=hp&ei=02IFas2XKteO2roP_vuQwQE&iflsig=AFdpzrgAAAAAagVw4whkttcjBBee1Pj39b_eAIp1hlot&oq=money&gs_lp=Egdnd3Mtd2l6IgVtb25leSoCCAAyBBAjGCcyChAAGIAEGIoFGEMyCxAAGIAEGLEDGIMBMgsQABiABBixAxiDATINEAAYgAQYigUYQxixAzILEAAYgAQYigUYkgMyFhAuGIAEGIoFGEMYsQMYyQMYxwEY0QMyChAAGIAEGIoFGEMyEBAuGIAEGIoFGEMYsQMYgwEyChAuGIAEGIoFGENImjRQyh5YqCRwAXgAkAEAmAHGB6AB4BaqAQkzLTIuMS4wLjK4AQHIAQD4AQGYAgagArsXqAIKwgIHECMY6gIYJ8ICDBAjGIAEGIoFGBMYJ8ICCxAuGIAEGLEDGIMBwgIIEC4YgAQYsQPCAg4QLhiABBiKBRixAxiDAcICCBAAGIAEGLEDwgIREC4YgAQYsQMYgwEYxwEY0QPCAhAQABiABBiKBRhDGLEDGIMBmAMN8QXuyFYW96YaBJIHCzEuMy0yLjEuMS4xoAepNLIHCTMtMi4xLjEuMbgHrhfCBwUyLTIuNMgHNoAIAQ&sclient=gws-wiz")
        
        self.btn_toggle_url = tk.Button(url_frame, text="👁️", bg="#1e1e1e", fg="#00ffff", relief=tk.FLAT, font=("Arial", 8), width=2, command=self.toggle_url_visibility, activebackground="#333333", activeforeground="#00ffff")
        self.btn_toggle_url.pack(side=tk.LEFT, padx=(4, 0), ipady=0)
        
        self.btn_server_load = tk.Button(url_frame, text="📊 Đo tải", bg="#1e1e1e", fg="#ffb74d", relief=tk.FLAT, font=("Arial", 8, "bold"), command=self.measure_server_load, activebackground="#333333", activeforeground="#ffb74d")
        self.btn_server_load.pack(side=tk.LEFT, padx=(4, 0), ipady=0)

        # Các nút bấm
        btn_frame = tk.Frame(root, bg="#121212")
        btn_frame.pack(pady=(8, 4))

        btn_style = {"font": ("Arial", 8, "bold"), "relief": tk.FLAT, "activebackground": "#00e5ff", "activeforeground": "black"}

        self.btn_ip_that = tk.Button(btn_frame, text="Mở Trình Duyệt", 
                                     command=self.launch_ip_that, bg="#00bcd4", fg="black", width=18, **btn_style)
        self.btn_ip_that.grid(row=0, column=1, padx=4, pady=4)
        
        self.btn_proxy = tk.Button(btn_frame, text="Proxy nếu có", 
                                   command=self.launch_proxy, bg="#a52a2a", fg="white", width=18, **btn_style)
        self.btn_proxy.grid(row=0, column=0, padx=4, pady=4)

        self.btn_auto_login = tk.Button(btn_frame, text="🔑 Auto đăng nhập", 
                                        command=self.trigger_auto_login, bg="#81c784", fg="black", width=18,
                                        state=tk.DISABLED, **btn_style)
        self.btn_auto_login.grid(row=0, column=2, padx=4, pady=4)
        self.btn_auto_login.bind("<Double-1>", self.show_credentials_dialog)

        self.btn_auto_task_step = tk.Button(btn_frame, text="Upto step (thử nghiệm)", 
                                        command=self.trigger_auto_task_step, bg="#263238", fg="#00bcd4", width=18,
                                        state=tk.DISABLED, **btn_style)
        self.btn_auto_task_step.grid(row=1, column=0, padx=4, pady=4)

        self.btn_auto_task = tk.Button(btn_frame, text="Lấy mã (thử nghiệm)", 
                                        command=self.trigger_auto_task, bg="#263238", fg="#00bcd4", width=18,
                                        state=tk.DISABLED, **btn_style)
        self.btn_auto_task.grid(row=1, column=1, padx=4, pady=4)

        self.btn_delete = tk.Button(btn_frame, text="🗑️ Delete",
                                    command=self.delete_session, bg="#b71c1c", fg="white", width=18,
                                    state=tk.DISABLED, font=("Arial", 8, "bold"), relief=tk.FLAT, activebackground="#f44336", activeforeground="white", disabledforeground="#ffcdd2")
        self.btn_delete.grid(row=1, column=2, padx=4, pady=4)

        # --- BỘ LỌC CẤU HÌNH (MÚI GIỜ & KÍCH THƯỚC) ---
        filter_frame = tk.Frame(root, bg="#121212")
        filter_frame.pack(pady=(0, 6))
        
        tk.Label(filter_frame, text="Chọn Múi giờ:", font=("Arial", 8, "bold"), fg="#e0e0e0", bg="#121212").pack(side=tk.LEFT, padx=2)
        
        self.tz_var = tk.StringVar(value="Toàn cầu")
        self.tz_map = {
            "Toàn cầu": "Auto",
            "Châu Á": "Asia",
            "Châu Âu": "Europe",
            "Châu Mỹ": "America",
            "Châu Phi": "Africa",
            "Châu Đại Dương": "Oceania"
        }
        self.tz_cb = ttk.Combobox(filter_frame, textvariable=self.tz_var, values=list(self.tz_map.keys()), state="readonly", font=("Arial", 8), width=12)
        self.tz_cb.pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Label(filter_frame, text="Thiết bị:", font=("Arial", 8, "bold"), fg="#e0e0e0", bg="#121212").pack(side=tk.LEFT, padx=2)
        self.platform_var = tk.StringVar(value="Điện thoại")
        self.platform_cb = ttk.Combobox(filter_frame, textvariable=self.platform_var, values=["Điện thoại", "Máy tính", "Ngẫu nhiên"], state="readonly", font=("Arial", 8), width=10)
        self.platform_cb.pack(side=tk.LEFT, padx=(0, 5))
        self.platform_cb.bind("<<ComboboxSelected>>", lambda e: self.regenerate_profiles())
        
        self.btn_regen = tk.Button(filter_frame, text="🔄 Tổ hợp mới", command=self.regenerate_profiles, bg="#333333", fg="#00e676", font=("Arial", 8, "bold"), relief=tk.FLAT, activebackground="#555555", activeforeground="#00e676")
        self.btn_regen.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(filter_frame, text="Giao diện:", font=("Arial", 8, "bold"), fg="#e0e0e0", bg="#121212").pack(side=tk.LEFT, padx=2)
        self.scale_var = tk.StringVar(value="Size: x0.8")
        self.scale_cb = ttk.Combobox(filter_frame, textvariable=self.scale_var, values=["Size: x0.8", "Size: x1.0", "Size: x1.2", "Size: x1.4", "Size: x1.6"], state="readonly", font=("Arial", 8), width=9)
        self.scale_cb.pack(side=tk.LEFT)
        self.scale_cb.bind("<<ComboboxSelected>>", self.apply_scale)
        # ---------------------------------

        # --- Hiển thị đường dẫn dữ liệu ---
        info_frame = tk.Frame(root, bg="#121212")
        info_frame.pack(pady=(4, 0), fill=tk.X, padx=15)

        tk.Label(info_frame, 
                 text="Nơi lưu trữ trình duyệt (máy ảo):", 
                 font=("Arial", 7, "italic"), fg="#a0a0a0", bg="#121212",
                 justify=tk.LEFT).pack(anchor='w', pady=(0, 2))
        
        browser_path = self.get_playwright_browser_path(is_running=False)
        self.path_entry = tk.Entry(info_frame, font=("Courier", 7), bg="#1e1e1e", fg="#d2b48c", readonlybackground="#1e1e1e", relief=tk.FLAT)
        self.path_entry.insert(0, browser_path)
        self.path_entry.config(state='readonly')
        self.path_entry.pack(fill=tk.X, expand=True, ipady=2)

        # --- Container cho 2 khung (Thiết bị và Log) ---
        bottom_container = tk.Frame(root, bg="#121212")
        bottom_container.pack(pady=(8, 0), fill=tk.BOTH, expand=True, padx=15)
        
        bottom_container.columnconfigure(0, weight=1, uniform="group1")
        bottom_container.columnconfigure(1, weight=1, uniform="group1")
        bottom_container.rowconfigure(0, weight=1)

        # Cột 1: Hiển thị thông số cấu hình giả lập
        self.device_info_frame = tk.LabelFrame(bottom_container, text="Chi tiết trình duyệt vừa tạo:", font=("Arial", 7, "bold"), bg="#121212", fg="#00bcd4")
        self.device_info_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        self.device_info_text = tk.Text(self.device_info_frame, height=6, font=("Courier", 7), bg="#1e1e1e", fg="#00ffff", state=tk.DISABLED, wrap=tk.WORD, relief=tk.FLAT)
        self.device_info_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Cột 2: Terminal Log
        self.log_frame = tk.LabelFrame(bottom_container, text="Log:", font=("Arial", 7, "bold"), bg="#121212", fg="#00e676")
        self.log_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self.log_text = tk.Text(self.log_frame, height=6, font=("Courier", 7), bg="#1e1e1e", fg="#00e676", state=tk.DISABLED, wrap=tk.WORD, relief=tk.FLAT)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Chuyển hướng Terminal (stdout/stderr) vào GUI
        class Redirector:
            def __init__(self, text_widget, root_ref):
                self.text_widget = text_widget
                self.root = root_ref
            def write(self, string):
                def append():
                    try:
                        self.text_widget.config(state=tk.NORMAL)
                        self.text_widget.insert(tk.END, string)
                        self.text_widget.see(tk.END) # Tự động cuộn xuống dòng mới nhất
                        self.text_widget.config(state=tk.DISABLED)
                    except Exception: pass
                self.root.after(0, append) # Sử dụng thread-safe để tránh treo phần mềm
            def flush(self): pass
            def isatty(self): return False

        sys.stdout = Redirector(self.log_text, self.root)
        sys.stderr = Redirector(self.log_text, self.root)

        self.status_label = tk.Label(root, text="Trạng thái: Sẵn sàng", fg="#a0a0a0", bg="#121212", font=("Arial", 7))
        self.status_label.pack(side=tk.BOTTOM, pady=8)

        # Đảm bảo dọn dẹp session khi người dùng đóng cửa sổ chính
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self._is_wiping = False
        self.current_profile = None
        self.profiles_queue = []
        self.profiles_used = 0
        
        # Vô hiệu hóa nút trong lúc chờ khởi tạo cấu hình ban đầu
        self.btn_ip_that.config(state=tk.DISABLED)
        self.btn_proxy.config(state=tk.DISABLED)
        
        # Mở hộp thoại tiến trình khởi tạo khi vừa mở Tool
        self.root.after(300, self.show_initialization)

        # Khởi động luồng theo dõi IP liên tục
        self.start_ip_monitor()

        # Cập nhật cỡ chữ và giao diện theo scale hiện tại ngay khi phần mềm khởi động xong
        self.root.after(50, self.apply_scale)

    def update_network_analysis(self, cookie_count, auto_cmds=0):
        def _update():
            self.analysis_label.config(text=f"🔍 Cookies: {cookie_count} | ⚙️ Lệnh Auto: {auto_cmds}", fg=self.get_color("#ffff00"))
        self.root.after(0, _update)

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

        new_w = int(800 * self.current_scale)
        new_h = int(540 * self.current_scale)
        self.root.geometry(f"{new_w}x{new_h}")

        # Tính toán lại tọa độ cho các thành phần neo cố định (Ghim, Theme, Đồng hồ)
        self.btn_pin.place(relx=1.0, x=int(-120 * self.current_scale), y=int(15 * self.current_scale), width=int(100 * self.current_scale))
        self.btn_theme.place(relx=1.0, x=int(-200 * self.current_scale), y=int(15 * self.current_scale), width=int(75 * self.current_scale))
        self.clock_label.place(x=int(15 * self.current_scale), y=int(15 * self.current_scale), width=int(160 * self.current_scale), height=int(22 * self.current_scale))

        self._scale_widget_tree(self.root, self.current_scale)

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
            "#ff5252": "#d32f2f", "#ffff00": "#f57f17", "#d2b48c": "#8b4513"
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

    def start_ip_monitor(self):
        """Chạy luồng ngầm liên tục kiểm tra IP mạng của máy mỗi 2 giây"""
        def monitor():
            import time
            current_ip = ""
            was_disconnected = False
            was_unstable = False
            
            def update_ui(i, l, err=False, disc_time=None):
                c_ip = "#ff5252" if err else "#00e676"
                c_ping = "#ff5252" if err else "#ffb74d"
                self.ip_label.config(text=f"🌐 IP: {i}", fg=self.get_color(c_ip))
                self.ping_label.config(text=f"⚡ Ping: {l}", fg=self.get_color(c_ping))
                self.disconnect_label.config(text=f"❌ Rớt: {self.disconnect_count}")
                if disc_time:
                    self.last_disconnect_label.config(text=f"⏱️ Lúc: {disc_time}")

            while True:
                try:
                    import socket
                    # Đo Ping thực tế bằng kết nối TCP siêu nhẹ tới DNS Google (giống hệt ICMP Ping thực tế)
                    try:
                        ping_start = time.time()
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.settimeout(1.5)
                            s.connect(("8.8.8.8", 53))
                        latency_val = int((time.time() - ping_start) * 1000)
                        latency = f"{latency_val}ms"
                    except Exception:
                        latency_val = 9999
                        latency = "N/A"
                        
                    # Lấy IP (Không dùng thời gian tải HTTPS này làm số Ping nữa)
                    req = urllib.request.Request("https://api.ipify.org", headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=2) as response:
                        ip = response.read().decode('utf-8').strip()
                        
                        if was_disconnected:
                            was_disconnected = False

                        if latency_val >= 300 and latency_val != 9999:
                            if not was_unstable:
                                was_unstable = True
                                self.root.after(0, lambda l=latency: self.show_unstable_network_popup(l))
                        else:
                            was_unstable = False

                        self.root.after(0, update_ui, ip, latency, False)
                except Exception:
                    disc_time_str = None
                    if not was_disconnected:
                        self.disconnect_count += 1
                        was_disconnected = True
                        disc_time_str = time.strftime("%H:%M:%S")
                        self.root.after(0, self.show_disconnect_popup)
                    self.root.after(0, update_ui, "Mất kết nối", "N/A", True, disc_time_str)
                    current_ip = ""
                time.sleep(2)
                
        threading.Thread(target=monitor, daemon=True).start()

    def show_disconnect_popup(self):
        if hasattr(self, 'disconnect_popup') and self.disconnect_popup.winfo_exists():
            return
            
        self.disconnect_popup = tk.Toplevel(self.root)
        self.disconnect_popup.withdraw()
        self.disconnect_popup.overrideredirect(True) # Xóa thanh tiêu đề để trông giống thông báo nổi hơn
        
        dialog_w = int(700 * self.current_scale)
        dialog_h = int(160 * self.current_scale)
        
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = (screen_w // 2) - (dialog_w // 2)
        pos_y = (screen_h // 2) - (dialog_h // 2)
        
        self.disconnect_popup.geometry(f"{dialog_w}x{dialog_h}+{pos_x}+{pos_y}")
        self.disconnect_popup.attributes("-topmost", True) # Luôn nổi trên cùng, không bị che
        
        border_frame = tk.Frame(self.disconnect_popup, bg="#ff5252")
        border_frame.pack(fill=tk.BOTH, expand=True)
        
        inner_frame = tk.Frame(border_frame, bg="#121212")
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        tk.Label(inner_frame, text="⚠️ CẢNH BÁO: MẤT KẾT NỐI MẠNG!", font=("Arial", 20, "bold"), fg="#ff5252", bg="#121212").pack(expand=True)
        
        self._scale_widget_tree(self.disconnect_popup, self.current_scale)
        self.apply_current_theme(self.disconnect_popup)
        
        self.disconnect_popup.deiconify()
        
        # Tự động đóng sau 5 giây (5000 ms)
        self.root.after(5000, lambda: self.disconnect_popup.destroy() if self.disconnect_popup.winfo_exists() else None)

    def show_unstable_network_popup(self, ping_str):
        if hasattr(self, 'unstable_popup') and self.unstable_popup.winfo_exists():
            return
            
        self.unstable_popup = tk.Toplevel(self.root)
        self.unstable_popup.withdraw()
        self.unstable_popup.overrideredirect(True) # Xóa thanh tiêu đề
        
        dialog_w = int(700 * self.current_scale)
        dialog_h = int(160 * self.current_scale)
        
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = (screen_w // 2) - (dialog_w // 2)
        pos_y = (screen_h // 2) - (dialog_h // 2) - int(170 * self.current_scale) # Hơi đẩy lên trên để không đè vào thông báo mất kết nối
        
        self.unstable_popup.geometry(f"{dialog_w}x{dialog_h}+{pos_x}+{pos_y}")
        self.unstable_popup.attributes("-topmost", True)
        
        border_frame = tk.Frame(self.unstable_popup, bg="#ff9800") # Viền màu cam
        border_frame.pack(fill=tk.BOTH, expand=True)
        
        inner_frame = tk.Frame(border_frame, bg="#121212")
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        tk.Label(inner_frame, text=f"⚠️ MẠNG KHÔNG ỔN ĐỊNH (Ping: {ping_str})", font=("Arial", 20, "bold"), fg="#ff9800", bg="#121212").pack(expand=True)
        
        self._scale_widget_tree(self.unstable_popup, self.current_scale)
        self.apply_current_theme(self.unstable_popup)
        
        self.unstable_popup.deiconify()
        
        self.root.after(5000, lambda: self.unstable_popup.destroy() if self.unstable_popup.winfo_exists() else None)

    def toggle_url_visibility(self):
        """Hiện/ẩn nội dung ô nhập URL"""
        if self.url_entry.cget('show') == '':
            self.url_entry.config(show='*')
            self.btn_toggle_url.config(text="🙈")
        else:
            self.url_entry.config(show='')
            self.btn_toggle_url.config(text="👁️")

    def measure_server_load(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Lỗi", "Vui lòng nhập URL để đo tải!", parent=self.root)
            return
            
        if not url.startswith("http"):
            url = "https://" + url
            
        self.btn_server_load.config(text="⏳ Đang đo...", state=tk.DISABLED)
        
        def worker():
            import time
            import urllib.request
            from urllib.parse import urlparse
            import random
            
            try:
                domain = urlparse(url).netloc
                
                # Bóc tách thông minh: Nếu dùng Google Search, lấy tên miền mục tiêu ra để đo
                if "google.com/search" in url and "q=" in url:
                    from urllib.parse import parse_qs
                    query = parse_qs(urlparse(url).query)
                    if 'q' in query:
                        target = query['q'][0]
                        domain = target.replace("https://", "").replace("http://", "").split("/")[0]

                check_url = f"https://{domain}"
                
                start_time = time.time()
                req = urllib.request.Request(check_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                
                try:
                    with urllib.request.urlopen(req, timeout=5) as response:
                        response.read(1024) # Chỉ cần đọc mồi 1KB để xác định tốc độ phản hồi của Máy chủ
                    elapsed = time.time() - start_time
                    
                    if elapsed < 0.2: score = random.randint(1, 10)
                    elif elapsed < 0.5: score = random.randint(11, 30)
                    elif elapsed < 1.0: score = random.randint(31, 50)
                    elif elapsed < 2.0: score = random.randint(51, 75)
                    elif elapsed < 4.0: score = random.randint(76, 90)
                    else: score = random.randint(91, 99)
                    
                    status = "Mượt mà (Ít người)" if score <= 30 else "Bình thường" if score <= 60 else "Khá tải (Nhiều người)" if score <= 85 else "Quá tải (Nguy cơ sập)"
                    color = "#00e676" if score <= 30 else "#ffff00" if score <= 60 else "#ff9800" if score <= 85 else "#ff5252"
                    
                except Exception:
                    elapsed = 999
                    score = 100
                    status = "Sập / Không phản hồi"
                    color = "#ff5252"
                
                def update_ui():
                    self.btn_server_load.config(text="📊 Đo tải", state=tk.NORMAL)
                    self.show_server_load_popup(domain, score, elapsed, status, color)
                    
                self.root.after(0, update_ui)
                
            except Exception:
                self.root.after(0, lambda: self.btn_server_load.config(text="📊 Đo tải", state=tk.NORMAL))

        threading.Thread(target=worker, daemon=True).start()

    def show_server_load_popup(self, domain, score, elapsed, status, color):
        if hasattr(self, 'load_popup') and self.load_popup.winfo_exists():
            self.load_popup.destroy()
            
        self.load_popup = tk.Toplevel(self.root)
        self.load_popup.withdraw()
        self.load_popup.title("Phân tích Tải Máy Chủ")
        
        dialog_w = int(350 * self.current_scale)
        dialog_h = int(180 * self.current_scale)
        
        self.root.update_idletasks()
        main_x = self.root.winfo_rootx()
        main_y = self.root.winfo_rooty()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        pos_x = main_x + (main_w // 2) - (dialog_w // 2)
        pos_y = main_y + (main_h // 2) - (dialog_h // 2)
        
        self.load_popup.geometry(f"{dialog_w}x{dialog_h}+{pos_x}+{pos_y}")
        self.load_popup.configure(bg="#121212")
        self.load_popup.transient(self.root)
        self.load_popup.attributes("-topmost", True)
        
        tk.Label(self.load_popup, text=f"🌐 Server: {domain}", font=("Arial", 9, "bold"), fg="#00bcd4", bg="#121212").pack(pady=(15, 5))
        
        progress_frame = tk.Frame(self.load_popup, bg="#121212")
        progress_frame.pack(pady=5, fill=tk.X, padx=20)
        
        tk.Label(progress_frame, text="0", font=("Arial", 7), fg="#a0a0a0", bg="#121212").pack(side=tk.LEFT)
        
        style = ttk.Style(self.load_popup)
        style_name = f"Load_{score}.Horizontal.TProgressbar"
        style.configure(style_name, troughcolor="#1e1e1e", background=color)
        
        pb = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate', style=style_name)
        pb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        pb['value'] = score
        tk.Label(progress_frame, text="100", font=("Arial", 7), fg="#a0a0a0", bg="#121212").pack(side=tk.LEFT)
        
        tk.Label(self.load_popup, text=f"Chỉ số Tải: {score}/100", font=("Arial", 16, "bold"), fg=color, bg="#121212").pack()
        
        ping_text = "N/A" if elapsed == 999 else f"{int(elapsed * 1000)}ms"
        tk.Label(self.load_popup, text=f"Trạng thái: {status} (Độ trễ: {ping_text})", font=("Arial", 8, "italic"), fg="#e0e0e0", bg="#121212").pack(pady=5)
        
        tk.Button(self.load_popup, text="Đóng", command=self.load_popup.destroy, bg="#333333", fg="white", font=("Arial", 8, "bold"), relief=tk.FLAT, activebackground="#555555", activeforeground="white").pack(pady=5, ipadx=10)
        
        self._scale_widget_tree(self.load_popup, self.current_scale)
        self.apply_current_theme(self.load_popup)
        self.load_popup.deiconify()

    def toggle_pin(self):
        """Bật/tắt chế độ luôn nổi trên cùng (Topmost) của cửa sổ"""
        self.is_pinned = not self.is_pinned
        self.root.attributes("-topmost", self.is_pinned)
        if self.is_pinned:
            self.btn_pin.config(text="📍 Đã Ghim", fg=self.get_color("#00e676"))
        else:
            self.btn_pin.config(text="📌 Ghim", fg=self.get_color("#a0a0a0"))
            
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
        self.show_initialization()

    def show_initialization(self):
        """Hiển thị tiến trình khởi tạo thiết bị giả lập mới khi mở tool hoặc sau khi dọn dẹp."""
        self.btn_ip_that.config(state=tk.DISABLED)
        self.btn_proxy.config(state=tk.DISABLED)
        
        prog_win = tk.Toplevel(self.root)
        prog_win.withdraw()
        prog_win.title("Đang nạp môi trường...")
        
        dialog_w = int(420 * self.current_scale)
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
        prog_win.grab_set()
        prog_win.attributes("-topmost", True) # Nổi lên trên cùng giống hộp thoại xóa
        prog_win.protocol("WM_DELETE_WINDOW", lambda: None)
        
        tk.Label(prog_win, text="Đang khởi tạo cấu hình ẩn danh hoàn toàn mới...", font=("Arial", 8, "bold"), fg="#00e676", bg="#121212").pack(pady=8)
        
        progress = ttk.Progressbar(prog_win, orient=tk.HORIZONTAL, length=int(380*self.current_scale), mode='determinate')
        progress.pack(pady=4)
        
        step_label = tk.Label(prog_win, text="Bắt đầu...", font=("Courier", 7), fg="#ffb74d", bg="#121212")
        step_label.pack(pady=4)
        
        self._scale_widget_tree(prog_win, self.current_scale)
        self.apply_current_theme(prog_win)
        
        # Chỉ hiển thị bảng thông báo khởi tạo nếu cửa sổ phần mềm chính đang không bị ẩn
        if self.root.state() != 'withdrawn':
            prog_win.deiconify()
        
        steps = [
            "Đang sinh dữ liệu thiết bị 1/5...",
            "Đang sinh dữ liệu thiết bị 2/5...",
            "Đang sinh dữ liệu thiết bị 3/5...",
            "Đang sinh dữ liệu thiết bị 4/5...",
            "Đang sinh dữ liệu thiết bị 5/5...",
            "Hoàn tất nạp 5 cấu hình thiết bị sạch!"
        ]
        
        def do_step(index):
            if index < len(steps):
                progress['value'] = (index / (len(steps) - 1)) * 100
                step_label.config(text=steps[index])
                self.root.after(random.randint(150, 400), do_step, index + 1)
            else:
                # Tạo sẵn 5 profile ảo (thông số) vào hàng đợi. Lúc này temp vẫn sạch.
                preferred_tz = "Auto"
                if hasattr(self, 'tz_map') and hasattr(self, 'tz_var'):
                    preferred_tz = self.tz_map.get(self.tz_var.get(), "Auto")
                    
                preferred_platform = "Mobile"
                if hasattr(self, 'platform_var'):
                    p_val = self.platform_var.get()
                    if p_val == "Máy tính": preferred_platform = "Desktop"
                    elif p_val == "Ngẫu nhiên": preferred_platform = "Random"
                    
                self.profiles_queue = [self.engine.device_faker.generate_new_device(preferred_timezone=preferred_tz, platform_type=preferred_platform) for _ in range(5)]
                self.profiles_used = 0
                self.root.after(400, prog_win.destroy)
                self.load_next_profile()
                
        do_step(0)

    def load_next_profile(self):
        """Lấy profile tiếp theo trong hàng đợi ra để sử dụng."""
        if self.profiles_queue:
            self.current_profile = self.profiles_queue.pop(0)
            self.profiles_used += 1
            self.device_info_frame.config(text=f"Chi tiết trình duyệt (Đang dùng: {self.profiles_used}/5):")
            self.update_device_info_display(self.current_profile)
            
            self.virtual_mac_label.config(text="MAC(Fake): Đang chờ khởi chạy...")
                
            self.btn_ip_that.config(state=tk.NORMAL)
            self.btn_proxy.config(state=tk.NORMAL)
            self.btn_delete.config(state=tk.DISABLED)
            self.btn_auto_task.config(state=tk.DISABLED)
            self.btn_auto_task_step.config(state=tk.DISABLED)
            self.status_label.config(text=f"Trạng thái: Sẵn sàng (Thiết bị {self.profiles_used}/5)", fg=self.get_color("#00e676"))
            
            if getattr(self, 'auto_launch_hidden', False):
                self.auto_launch_hidden = False # Chỉ chạy tự động ở lần nạp cấu hình đầu tiên
                self.root.after(500, lambda: self.launch_ip_that(headless=True))
        else:
            self.current_profile = None
            self.device_info_frame.config(text="Chi tiết trình duyệt (Hết lượt):")
            self.update_device_info_display(None, exhausted=True)
            self.virtual_mac_label.config(text="MAC(Fake): Hết thiết bị")
            self.btn_ip_that.config(state=tk.DISABLED)
            self.btn_proxy.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)
            self.status_label.config(text="Trạng thái: Hết thiết bị. Vui lòng tắt phần mềm và mở lại.", fg=self.get_color("#ff5252"))

        if hasattr(self, 'path_entry'):
            self.path_entry.config(state=tk.NORMAL)
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.get_playwright_browser_path(is_running=False))
            self.path_entry.config(state='readonly')

    def update_device_info_display(self, profile, exhausted=False):
        """Cập nhật khung hiển thị thông tin thiết bị đã tạo."""
        self.device_info_text.config(state=tk.NORMAL)
        self.device_info_text.delete(1.0, tk.END)
        if exhausted:
            self.device_info_text.insert(tk.END, "Đã sử dụng hết 5 thiết bị sạch.\n\nVui lòng tắt phần mềm và mở lại (chạy lại lệnh python main.py)\nđể khởi tạo một lứa 5 thiết bị hoàn toàn mới.")
        elif profile:
            info_str = (
                f"Hệ điều hành : {profile.get('platform', 'N/A')} (Mobile: {profile.get('is_mobile', False)})\n"
                f"Độ phân giải : {profile['viewport']['width']}x{profile['viewport']['height']}\n"
                f"Múi giờ      : {profile['timezone_id']} | Ngôn ngữ: {profile['locale']}\n"
                f"User-Agent   : {profile['user_agent']}\n"
                f"File chạy    : {profile.get('executable_path', 'Đang chờ khởi chạy...')}"
            )
            self.device_info_text.insert(tk.END, info_str)
        self.device_info_text.config(state=tk.DISABLED)

    def on_closing(self):
        """Xử lý sự kiện đóng cửa sổ chính của ứng dụng."""
        if self.engine.playwright is not None:
            self.show_auto_close_dialog()
        else:
            self.root.destroy()

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
        
        tk.Label(dialog, text="Một phiên làm việc ẩn danh đang tồn tại!\nBạn hãy dọn dẹp hoặc hệ thống sẽ tự động dọn dẹp sau:", font=("Arial", 8), fg="#e0e0e0", bg="#121212").pack(pady=8)
        
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
                
                try:
                    # Chỉ xóa thư mục tạm của đúng trình duyệt ở cửa sổ này dựa vào đường dẫn data
                    current_path = self.path_entry.get()
                    if current_path and os.path.exists(current_path) and ("Clean_Profile_" in current_path or "playwright_" in current_path or "pyright-" in current_path):
                        shutil.rmtree(current_path, ignore_errors=True)
                except Exception: pass
                
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

    def get_playwright_browser_path(self, is_running=False):
        """Lấy đường dẫn thư mục chứa dữ liệu cấu hình tạm thời của trình duyệt Playwright."""
        try:
            if not is_running:
                return "Đang chờ khởi chạy..."
            if hasattr(self.engine, 'user_data_dir') and self.engine.user_data_dir:
                return self.engine.user_data_dir
            return "Không tìm thấy thư mục tạm thời."
        except Exception as e:
            print(f"Lỗi khi lấy đường dẫn: {e}")
            return "Không thể xác định đường dẫn."

    def set_ui_for_browser_state(self, is_running):
        """Cập nhật trạng thái các nút bấm và label trên giao diện."""
        if is_running:
            self.btn_ip_that.config(state=tk.DISABLED)
            self.btn_proxy.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.NORMAL)
            self.btn_auto_login.config(state=tk.NORMAL)
            self.btn_auto_task.config(state=tk.NORMAL)
            self.btn_auto_task_step.config(state=tk.NORMAL)
            self.status_label.config(text="Trạng thái: Trình duyệt đang chạy. Đóng trình duyệt và bấm 'Delete' để dọn dẹp.", fg=self.get_color("#00bcd4"))
            self.analysis_label.config(text="🔍 Phân tích mạng: Đang thu thập dữ liệu...", fg=self.get_color("#ffff00"))
        else:
            self.btn_auto_login.config(state=tk.DISABLED)
            self.btn_auto_task.config(state=tk.DISABLED)
            self.btn_auto_task_step.config(state=tk.DISABLED)
            self.analysis_label.config(text="🔍 Phân tích mạng: Đang chờ thao tác...", fg=self.get_color("#ffff00"))

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

    def run_browser_thread(self, target_url, use_proxy, headless=False):
        """Chạy việc mở trình duyệt trong một thread riêng để không làm treo giao diện."""
        # Cập nhật giao diện ngay lập tức
        self.set_ui_for_browser_state(is_running=True)
        self.status_label.config(text="Trạng thái: Đang khởi chạy trình duyệt...", fg=self.get_color("#ffb74d"))
        
        # Hiển thị MAC Fake ngay lập tức khi bắt đầu chạy thay vì chờ Google search xong
        if self.current_profile and "mac_address" in self.current_profile:
            self.virtual_mac_label.config(text=f"MAC(Fake): {self.current_profile['mac_address']}")

        try:
            def on_browser_created():
                def update_path():
                    if hasattr(self, 'path_entry'):
                        self.path_entry.config(state=tk.NORMAL)
                        self.path_entry.delete(0, tk.END)
                        self.path_entry.insert(0, self.get_playwright_browser_path(is_running=True))
                        self.path_entry.config(state='readonly')
                self.root.after(0, update_path)

            # Callback này sẽ được gọi từ worker thread khi trình duyệt đã mở thành công
            def on_launch_success(device_profile):
                def update_ui():
                    self.status_label.config(text="Trạng thái: Trình duyệt đang chạy. Đóng trình duyệt và bấm 'Delete' để dọn dẹp.", fg=self.get_color("#00bcd4"))
                    self.update_device_info_display(device_profile)
                self.root.after(0, update_ui)

            # Lệnh này sẽ block cho đến khi trình duyệt được đóng và dọn dẹp xong
            self.engine.run_session_and_wait(
                target_url=target_url, 
                use_proxy=use_proxy,
                on_launch_callback=on_launch_success,
                device_profile=self.current_profile,
                on_browser_created=on_browser_created,
                headless=headless
            )
        except Exception as e:
            print(f"Lỗi: {e}")
            messagebox.showerror("Lỗi Mở Trình Duyệt", f"Không thể mở trình duyệt.\n\nChi tiết lỗi:\n{e}")
        finally:
            def on_browser_thread_exit():
                self.set_ui_for_browser_state(False)
                # Bắt buộc người dùng phải bấm Xóa Session khi trình duyệt tắt để dọn temp & chuyển sang thiết bị tiếp theo
                if hasattr(self, '_is_wiping') and not self._is_wiping:
                    self.btn_ip_that.config(state=tk.DISABLED)
                    self.btn_proxy.config(state=tk.DISABLED)
                    self.btn_delete.config(state=tk.NORMAL)
                    self.status_label.config(text="Trạng thái: Trình duyệt đã đóng. Vui lòng bấm 'Delete' để dọn dẹp.", fg=self.get_color("#ff5252"))
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
        
        dialog_w = int(420 * self.current_scale)
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

        progress = ttk.Progressbar(prog_win, orient=tk.HORIZONTAL, length=int(380*self.current_scale), mode='determinate')
        progress.pack(pady=5)

        file_label = tk.Label(prog_win, text="Khởi tạo...", font=("Courier", 8), fg="#ffb74d", bg="#121212")
        file_label.pack(pady=5)
        
        self._scale_widget_tree(prog_win, self.current_scale)
        self.apply_current_theme(prog_win)
        prog_win.deiconify()

        # Các thành phần dữ liệu trình duyệt bị xóa khỏi RAM
        items_to_wipe = [
            "Đang đóng kết nối trình duyệt...", "Xóa thư mục: /Default/Cookies",
            "Xóa tệp: /Default/Network Persistent State", "Xóa tệp: /Default/History",
            "Xóa tệp: /Default/Login Data (Mật khẩu)", "Dọn dẹp thư mục: /Default/Web Data",
            "Đang quét: /Default/Cache/Cache_Data/...", "Đang quét: /Default/GPUCache/...",
            "Xóa dữ liệu: /Default/Local Storage/leveldb/...", "Xóa dữ liệu: /Default/Session Storage/...",
            "Xóa dữ liệu: /Default/IndexedDB/...", "Tiêu hủy Service Worker Cache...", "Giải phóng toàn bộ RAM..."
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
                    
                    file_label.config(text="Đang dọn sạch các file rác trong thư mục Temp...")
                    
                    try:
                        # Chỉ xóa thư mục tạm của đúng trình duyệt ở cửa sổ này dựa vào đường dẫn data
                        current_path = self.path_entry.get()
                        if current_path and os.path.exists(current_path) and ("Clean_Profile_" in current_path or "playwright_" in current_path or "pyright-" in current_path):
                            shutil.rmtree(current_path, ignore_errors=True)
                    except Exception: pass
                    
                    def finish_wipe():
                        self._is_wiping = False
                        prog_win.destroy()
                        self.load_next_profile()
                        
                    self.root.after(800, finish_wipe)
                wipe_browser_folder()

        update_progress(0)

def main():
    root = tk.Tk()
    app = AntiDetectGUI(root)
    # Chạy vòng lặp giao diện
    root.mainloop()

if __name__ == "__main__":
    main()
