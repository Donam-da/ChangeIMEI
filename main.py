import os
import sys
import threading
import random
import tkinter as tk
import shutil
import tempfile
from tkinter import messagebox
from tkinter import ttk
from core.browser_engine import BrowserEngine

class AntiDetectGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ChangeIMEI Anti-Detect Browser")
        self.root.geometry("600x450")
        
        self.engine = BrowserEngine()
        
        # Thiết kế các thành phần Giao diện (UI)
        tk.Label(root, text="CÔNG CỤ ANTI-DETECT: CHANGE IMEI", font=("Arial", 14, "bold"), fg="#333").pack(pady=15)
        
        tk.Label(root, text="Nhập link URL muốn mở:", font=("Arial", 10)).pack()
        self.url_entry = tk.Entry(root, width=60, font=("Arial", 10))
        self.url_entry.pack(pady=5)
        self.url_entry.insert(0, "https://www.google.com/search?q=moneytask.top&sca_esv=3d73e6268d6609d9&sxsrf=ANbL-n5OwmW4jJHMCw_P-MHSjJYYql4e-Q%3A1778737875726&source=hp&ei=02IFas2XKteO2roP_vuQwQE&iflsig=AFdpzrgAAAAAagVw4whkttcjBBee1Pj39b_eAIp1hlot&oq=money&gs_lp=Egdnd3Mtd2l6IgVtb25leSoCCAAyBBAjGCcyChAAGIAEGIoFGEMyCxAAGIAEGLEDGIMBMgsQABiABBixAxiDATINEAAYgAQYigUYQxixAzILEAAYgAQYigUYkgMyFhAuGIAEGIoFGEMYsQMYyQMYxwEY0QMyChAAGIAEGIoFGEMyEBAuGIAEGIoFGEMYsQMYgwEyChAuGIAEGIoFGENImjRQyh5YqCRwAXgAkAEAmAHGB6AB4BaqAQkzLTIuMS4wLjK4AQHIAQD4AQGYAgagArsXqAIKwgIHECMY6gIYJ8ICDBAjGIAEGIoFGBMYJ8ICCxAuGIAEGLEDGIMBwgIIEC4YgAQYsQPCAg4QLhiABBiKBRixAxiDAcICCBAAGIAEGLEDwgIREC4YgAQYsQMYgwEYxwEY0QPCAhAQABiABBiKBRhDGLEDGIMBmAMN8QXuyFYW96YaBJIHCzEuMy0yLjEuMS4xoAepNLIHCTMtMi4xLjEuMbgHrhfCBwUyLTIuNMgHNoAIAQ&sclient=gws-wiz")
        
        # Các nút bấm
        self.btn_ip_that = tk.Button(root, text="🚀 Mở Trình Duyệt (IP Thật - Vượt Link)", 
                                     command=self.launch_ip_that, bg="#d9edf7", font=("Arial", 10, "bold"), width=35)
        self.btn_ip_that.pack(pady=5)
        
        self.btn_proxy = tk.Button(root, text="🌐 Mở Trình Duyệt (Có Dùng Proxy)", 
                                   command=self.launch_proxy, bg="#dff0d8", font=("Arial", 10), width=35)
        self.btn_proxy.pack(pady=5)

        self.btn_delete = tk.Button(root, text="🗑️ Xóa Session & Dọn Dẹp",
                                    command=self.delete_session, bg="#f2dede", font=("Arial", 10, "bold"), width=35,
                                    state=tk.DISABLED)
        self.btn_delete.pack(pady=5)

        # --- Hiển thị đường dẫn dữ liệu ---
        info_frame = tk.Frame(root)
        info_frame.pack(pady=(10, 0), fill=tk.X, padx=20)

        tk.Label(info_frame, 
                 text="Nơi lưu trữ trình duyệt (máy ảo):", 
                 font=("Arial", 9, "italic"),
                 justify=tk.LEFT).pack(anchor='w')
        
        browser_path = self.get_playwright_browser_path()
        self.path_entry = tk.Entry(info_frame, font=("Courier", 8))
        self.path_entry.insert(0, browser_path)
        self.path_entry.config(state='readonly')
        self.path_entry.pack(fill=tk.X, expand=True)

        tk.Label(info_frame, 
                 text="*Đây là nơi Playwright cài đặt các trình duyệt (Chromium, Firefox,...).\n*Dữ liệu phiên (cookie, cache) của mỗi lần chạy là tạm thời và sẽ bị xóa sạch.",
                 font=("Arial", 8), fg="darkblue", justify=tk.LEFT).pack(anchor='w', pady=(2,0))
        # --- Kết thúc ---

        # --- Hiển thị thông số cấu hình giả lập ---
        self.device_info_frame = tk.LabelFrame(root, text="Chi tiết trình duyệt ẩn danh vừa tạo:", font=("Arial", 9, "bold"))
        self.device_info_frame.pack(pady=(10, 0), fill=tk.BOTH, expand=False, padx=20)
        
        self.device_info_text = tk.Text(self.device_info_frame, height=5, font=("Courier", 8), bg="#f9f9f9", state=tk.DISABLED, wrap=tk.WORD)
        self.device_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.status_label = tk.Label(root, text="Trạng thái: Sẵn sàng", fg="gray", font=("Arial", 9))
        self.status_label.pack(side=tk.BOTTOM, pady=10)

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

    def show_initialization(self):
        """Hiển thị tiến trình khởi tạo thiết bị giả lập mới khi mở tool hoặc sau khi dọn dẹp."""
        self.btn_ip_that.config(state=tk.DISABLED)
        self.btn_proxy.config(state=tk.DISABLED)
        
        prog_win = tk.Toplevel(self.root)
        prog_win.title("Đang nạp môi trường...")
        prog_win.geometry("420x150")
        prog_win.transient(self.root)
        prog_win.grab_set()
        prog_win.protocol("WM_DELETE_WINDOW", lambda: None)
        
        tk.Label(prog_win, text="Đang khởi tạo cấu hình ẩn danh hoàn toàn mới...", font=("Arial", 10, "bold"), fg="#333").pack(pady=10)
        
        progress = ttk.Progressbar(prog_win, orient=tk.HORIZONTAL, length=380, mode='determinate')
        progress.pack(pady=5)
        
        step_label = tk.Label(prog_win, text="Bắt đầu...", font=("Courier", 9), fg="blue")
        step_label.pack(pady=5)
        
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
                self.profiles_queue = [self.engine.device_faker.generate_new_device() for _ in range(5)]
                self.root.after(400, prog_win.destroy)
                self.load_next_profile()
                
        do_step(0)

    def load_next_profile(self):
        """Lấy profile tiếp theo trong hàng đợi ra để sử dụng."""
        if self.profiles_queue:
            self.current_profile = self.profiles_queue.pop(0)
            self.profiles_used += 1
            self.device_info_frame.config(text=f"Chi tiết trình duyệt ẩn danh (Đang dùng: {self.profiles_used}/5):")
            self.update_device_info_display(self.current_profile)
            self.btn_ip_that.config(state=tk.NORMAL)
            self.btn_proxy.config(state=tk.NORMAL)
            self.btn_delete.config(state=tk.DISABLED)
            self.status_label.config(text=f"Trạng thái: Sẵn sàng (Thiết bị {self.profiles_used}/5)", fg="green")
        else:
            self.current_profile = None
            self.device_info_frame.config(text="Chi tiết trình duyệt ẩn danh (Hết lượt):")
            self.update_device_info_display(None, exhausted=True)
            self.btn_ip_that.config(state=tk.DISABLED)
            self.btn_proxy.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)
            self.status_label.config(text="Trạng thái: Hết thiết bị. Vui lòng tắt phần mềm và mở lại.", fg="red")

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
        dialog.title("Cảnh báo thoát")
        dialog.geometry("380x160")
        dialog.transient(self.root) # Nổi trên cửa sổ chính
        dialog.grab_set() # Khóa cửa sổ chính cho đến khi xử lý xong hộp thoại
        
        tk.Label(dialog, text="Một phiên làm việc ẩn danh đang tồn tại!\nBạn hãy dọn dẹp hoặc hệ thống sẽ tự động dọn dẹp sau:", font=("Arial", 10)).pack(pady=10)
        
        countdown_label = tk.Label(dialog, text="3", font=("Arial", 18, "bold"), fg="red")
        countdown_label.pack()
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        countdown_active = [True] # Dùng list để dễ dàng thay đổi state trong local function
        
        def do_cleanup_and_exit():
            countdown_active[0] = False
            self.engine.close_and_cleanup()
            
            def final_wipe_and_exit():
                if self.engine.playwright is not None:
                    self.root.after(200, final_wipe_and_exit) # Chờ engine tắt hẳn
                    return
                
                try:
                    # Chỉ xóa dữ liệu rác/cookie tạm thời của Playwright, giữ lại lõi trình duyệt
                    temp_dir = tempfile.gettempdir()
                    for item in os.listdir(temp_dir):
                        if item.startswith("playwright_"):
                            shutil.rmtree(os.path.join(temp_dir, item), ignore_errors=True)
                except: pass
                
                self.root.destroy()
            final_wipe_and_exit()
            
        def cancel():
            countdown_active[0] = False
            dialog.destroy()
            
        tk.Button(btn_frame, text="Dọn dẹp & Thoát ngay", command=do_cleanup_and_exit, bg="#f2dede", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Hủy (Quay lại)", command=cancel).pack(side=tk.LEFT, padx=10)
        
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

    def get_playwright_browser_path(self):
        """Lấy đường dẫn thư mục cài đặt trình duyệt của Playwright."""
        try:
            if sys.platform == "win32":
                # Trên Windows, nó nằm trong LOCALAPPDATA
                path = os.path.join(os.environ["LOCALAPPDATA"], "ms-playwright")
            elif sys.platform == "darwin":
                # Trên macOS
                path = os.path.join(os.path.expanduser("~"), "Library", "Caches", "ms-playwright")
            else: 
                # Trên Linux và các hệ thống tương tự Unix
                path = os.path.join(os.path.expanduser("~"), ".cache", "ms-playwright")
            
            return path if os.path.exists(path) else "Chưa tìm thấy (Cần chạy trình duyệt lần đầu để cài đặt)"
        except Exception as e:
            print(f"Lỗi khi lấy đường dẫn Playwright: {e}")
            return "Không thể xác định đường dẫn."

    def set_ui_for_browser_state(self, is_running):
        """Cập nhật trạng thái các nút bấm và label trên giao diện."""
        if is_running:
            self.btn_ip_that.config(state=tk.DISABLED)
            self.btn_proxy.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.NORMAL)
            self.status_label.config(text="Trạng thái: Trình duyệt đang chạy. Đóng trình duyệt và bấm 'Xóa' để dọn dẹp.", fg="blue")
        else:
            pass # Không tự động mở lại nút chạy, bắt buộc phải qua bước Xóa Session để dọn dẹp chuyển qua profile mới

    def run_browser_thread(self, target_url, use_proxy):
        """Chạy việc mở trình duyệt trong một thread riêng để không làm treo giao diện."""
        # Cập nhật giao diện ngay lập tức
        self.set_ui_for_browser_state(is_running=True)
        self.status_label.config(text="Trạng thái: Đang khởi chạy trình duyệt...", fg="orange")
        
        try:
            # Callback này sẽ được gọi từ worker thread khi trình duyệt đã mở thành công
            def on_launch_success(device_profile):
                def update_ui():
                    self.status_label.config(text="Trạng thái: Trình duyệt đang chạy. Đóng trình duyệt và bấm 'Xóa' để dọn dẹp.", fg="blue")
                    self.update_device_info_display(device_profile)
                self.root.after(0, update_ui)

            # Lệnh này sẽ block cho đến khi trình duyệt được đóng và dọn dẹp xong
            self.engine.run_session_and_wait(
                target_url=target_url, 
                use_proxy=use_proxy,
                on_launch_callback=on_launch_success,
                device_profile=self.current_profile
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
                    self.status_label.config(text="Trạng thái: Trình duyệt đã đóng. Vui lòng bấm 'Xóa Session' để dọn dẹp.", fg="red")
            self.root.after(0, on_browser_thread_exit)

    def launch_ip_that(self):
        url = self.url_entry.get().strip()
        threading.Thread(target=self.run_browser_thread, args=(url, False), daemon=True).start()

    def launch_proxy(self):
        url = self.url_entry.get().strip()
        threading.Thread(target=self.run_browser_thread, args=(url, True), daemon=True).start()

    def delete_session(self):
        """Thực hiện dọn dẹp session với thanh tiến trình trực quan."""
        self.btn_delete.config(state=tk.DISABLED) # Tránh click đúp
        self.status_label.config(text="Trạng thái: Đang tiêu hủy dữ liệu...", fg="orange")
        self._is_wiping = True
        
        # Tạo cửa sổ hiển thị tiến trình
        prog_win = tk.Toplevel(self.root)
        prog_win.title("Đang dọn dẹp...")
        prog_win.geometry("420x150")
        prog_win.transient(self.root)
        prog_win.grab_set() # Khóa màn hình chính
        prog_win.protocol("WM_DELETE_WINDOW", lambda: None) # Vô hiệu hóa nút X để tránh làm gián đoạn

        tk.Label(prog_win, text="Đang tiêu hủy dấu vết, Cookie, Lịch sử...", font=("Arial", 10, "bold")).pack(pady=10)

        progress = ttk.Progressbar(prog_win, orient=tk.HORIZONTAL, length=380, mode='determinate')
        progress.pack(pady=5)

        file_label = tk.Label(prog_win, text="Khởi tạo...", font=("Courier", 8), fg="gray")
        file_label.pack(pady=5)

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
                        temp_dir = tempfile.gettempdir()
                        for item in os.listdir(temp_dir):
                            if item.startswith("playwright_"):
                                shutil.rmtree(os.path.join(temp_dir, item), ignore_errors=True)
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
