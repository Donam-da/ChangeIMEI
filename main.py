import threading
import tkinter as tk
from tkinter import messagebox
from core.browser_engine import BrowserEngine

class AntiDetectGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ChangeIMEI Anti-Detect Browser")
        self.root.geometry("550x250")
        
        self.engine = BrowserEngine()
        
        # Thiết kế các thành phần Giao diện (UI)
        tk.Label(root, text="CÔNG CỤ ANTI-DETECT: CHANGE IMEI", font=("Arial", 14, "bold"), fg="#333").pack(pady=15)
        
        tk.Label(root, text="Nhập link URL muốn mở:", font=("Arial", 10)).pack()
        self.url_entry = tk.Entry(root, width=60, font=("Arial", 10))
        self.url_entry.pack(pady=5)
        self.url_entry.insert(0, "https://moneytask.top")
        
        # Các nút bấm
        self.btn_ip_that = tk.Button(root, text="🚀 Mở Trình Duyệt (IP Thật - Vượt Link)", 
                                     command=self.launch_ip_that, bg="#d9edf7", font=("Arial", 10, "bold"), width=35)
        self.btn_ip_that.pack(pady=5)
        
        self.btn_proxy = tk.Button(root, text="🌐 Mở Trình Duyệt (Có Dùng Proxy)", 
                                   command=self.launch_proxy, bg="#dff0d8", font=("Arial", 10), width=35)
        self.btn_proxy.pack(pady=5)
        
        self.status_label = tk.Label(root, text="Trạng thái: Sẵn sàng", fg="gray", font=("Arial", 9))
        self.status_label.pack(side=tk.BOTTOM, pady=10)

    def run_browser_thread(self, target_url, use_proxy):
        # Vô hiệu hóa nút bấm trong khi đang mở trình duyệt để tránh click nhầm nhiều lần
        self.status_label.config(text="Trạng thái: Đang chạy trình duyệt ẩn danh...", fg="blue")
        try:
            self.engine.launch_session(target_url=target_url, use_proxy=use_proxy)
        except Exception as e:
            print(f"Lỗi: {e}")
            # Hiển thị cửa sổ cảnh báo nếu có lỗi thay vì im lặng chớp tắt
            messagebox.showerror("Lỗi Mở Trình Duyệt", f"Không thể mở trình duyệt.\n\nChi tiết lỗi:\n{e}")
        finally:
            self.status_label.config(text="Trạng thái: Sẵn sàng", fg="gray")

    def launch_ip_that(self):
        url = self.url_entry.get().strip()
        threading.Thread(target=self.run_browser_thread, args=(url, False), daemon=True).start()

    def launch_proxy(self):
        url = self.url_entry.get().strip()
        threading.Thread(target=self.run_browser_thread, args=(url, True), daemon=True).start()

def main():
    root = tk.Tk()
    app = AntiDetectGUI(root)
    # Chạy vòng lặp giao diện
    root.mainloop()

if __name__ == "__main__":
    main()
