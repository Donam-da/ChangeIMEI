import os
import random
import threading
import time
import sys
import subprocess
from playwright.sync_api import sync_playwright, Playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

def apply_stealth(page):
    """Hàm bọc an toàn để gọi thư viện stealth mà không gây lỗi phần mềm"""
    try:
        import playwright_stealth
        if hasattr(playwright_stealth, 'stealth_sync'):
            playwright_stealth.stealth_sync(page)
        elif hasattr(playwright_stealth, 'stealth') and callable(playwright_stealth.stealth):
            playwright_stealth.stealth(page)
    except Exception as e:
        print(f"[!] Bỏ qua stealth do cấu trúc thư viện thay đổi: {e}")

from core.change_imei import DeviceFaker

class BrowserEngine:
    def __init__(self):
        self.device_faker = DeviceFaker()
        self.proxies = self._load_proxies()
        self.playwright: Playwright | None = None
        self.browser = None
        self.context = None
        self._should_close = False

    def _load_proxies(self):
        """Đọc danh sách proxy từ file txt"""
        proxy_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'proxies.txt')
        if not os.path.exists(proxy_path):
            return []
        with open(proxy_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    def run_session_and_wait(self, target_url, use_proxy, on_launch_callback):
        """
        Khởi chạy session, gọi callback, và block cho đến khi trình duyệt bị đóng.
        Việc dọn dẹp được thực hiện tự động khi thoát khỏi khối 'with'.
        """
        self._should_close = False
        
        if self.browser and self.browser.is_connected():
            print("[!] Một trình duyệt đã đang chạy. Vui lòng đóng và xóa session cũ trước.")
            if self.context and self.context.pages:
                self.context.pages[0].bring_to_front()
            return

        if target_url and not target_url.startswith("http"):
            target_url = "https://" + target_url

        device_profile = self.device_faker.generate_new_device()
        v_width = device_profile['viewport']['width']
        v_height = device_profile['viewport']['height']
        print(f"[*] ChangeIMEI Thành công. Đang giả lập thiết bị: \n    {device_profile['user_agent'][:60]}...")
        print(f"    Màn hình (Cửa sổ): {v_width}x{v_height}")

        proxy_settings = None
        if use_proxy and self.proxies:
            selected_proxy = random.choice(self.proxies)
            proxy_settings = {"server": selected_proxy}
            print(f"[*] Đã đổi IP sang Proxy: {selected_proxy}")
        elif not use_proxy:
            print("[!] Yêu cầu dùng IP thật. Bỏ qua Proxy.")
        else:
            print("[!] Không tìm thấy Proxy, đang dùng IP thật của máy.")

        print("[*] Đang kiểm tra lõi Chromium...")
        try:
            # Khắc phục lỗi nếu người dùng chỉ xóa thủ công thư mục con chrome-win64 mà không xóa thư mục cha
            pw_dir = ""
            if sys.platform == "win32":
                pw_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ms-playwright")
            elif sys.platform == "darwin":
                pw_dir = os.path.join(os.path.expanduser("~"), "Library", "Caches", "ms-playwright")
            else:
                pw_dir = os.path.join(os.path.expanduser("~"), ".cache", "ms-playwright")

            needs_install = True
            if os.path.exists(pw_dir):
                import shutil
                for item in os.listdir(pw_dir):
                    if item.startswith("chromium"):
                        c_dir = os.path.join(pw_dir, item)
                        # Các đường dẫn thực thi phổ biến của Chromium Playwright
                        exes = [os.path.join(c_dir, "chrome-win", "chrome.exe"), os.path.join(c_dir, "chrome-win64", "chrome.exe"), os.path.join(c_dir, "chrome-mac", "Chromium.app", "Contents", "MacOS", "Chromium"), os.path.join(c_dir, "chrome-linux", "chrome")]
                        if any(os.path.exists(exe) for exe in exes):
                            needs_install = False
                            break
                        else:
                            print(f"[!] Phát hiện lõi {item} bị lỗi do xóa thủ công. Đang dọn dẹp để ép tải lại...")
                            shutil.rmtree(c_dir, ignore_errors=True)

            if needs_install:
                print("[*] Không tìm thấy bản cài đặt chuẩn, đang tải lõi Chromium mới...")
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        except Exception as e:
            print(f"[!] Lỗi khi cài đặt Chromium: {e}")

        try:
            with sync_playwright() as p:
                self.playwright = p
                device_profile['executable_path'] = p.chromium.executable_path
                print("[*] Đang khởi chạy trình duyệt Chromium sạch...")
                
                try:
                    # Ưu tiên sử dụng Google Chrome thật cài sẵn trên máy tính để tăng độ uy tín (Bypass reCAPTCHA)
                    self.browser = p.chromium.launch(
                        channel="chrome",
                        headless=False,
                        ignore_default_args=["--enable-automation"], # Xóa thanh cảnh báo màu vàng
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--disable-webrtc-hw-encoding",
                            f"--window-size={v_width},{v_height}",
                            "--incognito"
                        ]
                    )
                except Exception:
                    print("[!] Không tìm thấy Google Chrome, quay lại dùng lõi Chromium mặc định...")
                    self.browser = p.chromium.launch(
                        headless=False,
                        ignore_default_args=["--enable-automation"],
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--disable-webrtc-hw-encoding",
                            "--disable-features=IsolateOrigins,site-per-process",
                            "--disable-site-isolation-trials",
                            f"--window-size={v_width},{v_height}",
                            "--incognito"
                        ]
                    )
                
                # Phân tích nền tảng để tạo Client-Hints Header chuẩn xác
                sec_ch_platform = "Windows" if "Win" in device_profile["platform"] else "macOS" if "Mac" in device_profile["platform"] else "Android" if "aarch" in device_profile["platform"] else "Linux"
                if "iPhone" in device_profile["platform"]:
                    sec_ch_platform = "iOS"

                self.context = self.browser.new_context(
                    viewport=device_profile["viewport"],
                    user_agent=device_profile["user_agent"],
                    is_mobile=device_profile.get("is_mobile", False),
                    locale=device_profile["locale"],
                    timezone_id=device_profile["timezone_id"],
                    proxy=proxy_settings,
                    color_scheme=random.choice(["light", "dark"]),
                    extra_http_headers={
                        "Accept-Language": f"{device_profile['locale']},en;q=0.9",
                        "sec-ch-ua": f'"Chromium";v="{device_profile["chrome_major"]}", "Not A(Brand";v="99", "Google Chrome";v="{device_profile["chrome_major"]}"',
                        "sec-ch-ua-mobile": "?1" if device_profile.get("is_mobile") else "?0",
                        "sec-ch-ua-platform": f'"{sec_ch_platform}"'
                    }
                )

                # Ghi đè thông số navigator.platform và phần cứng bằng Javascript để giả mạo thiết bị sâu hơn
                self.context.add_init_script(
                    f"Object.defineProperty(navigator, 'platform', {{get: () => '{device_profile['platform']}'}});\n"
                    f"Object.defineProperty(navigator, 'hardwareConcurrency', {{get: () => {device_profile['hardware_concurrency']}}});\n"
                    f"Object.defineProperty(navigator, 'deviceMemory', {{get: () => {device_profile['device_memory']}}});\n"
                    f"Object.defineProperty(navigator, 'languages', {{get: () => ['{device_profile['locale']}', 'en-US', 'en']}});\n"
                    f"// Ghi đè webdriver an toàn hơn dựa trên nguyên mẫu (prototype) để tránh bị phát hiện\n"
                    f"if (navigator.webdriver !== undefined) {{\n"
                    f"    Object.defineProperty(Object.getPrototypeOf(navigator), 'webdriver', {{ get: () => false }});\n"
                    f"}}"
                    f"}}\n"
                    f"// --- Chống nhận diện: Đổi mã băm Canvas Fingerprint thành Độc Nhất ---\n"
                    f"const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;\n"
                    f"HTMLCanvasElement.prototype.toDataURL = function() {{\n"
                    f"    const ctx = this.getContext('2d');\n"
                    f"    if (ctx) {{ ctx.fillStyle = 'rgba({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)}, 0.01)'; ctx.fillRect(0, 0, 1, 1); }}\n"
                    f"    return originalToDataURL.apply(this, arguments);\n"
                    f"}};\n"
                    f"// --- Chống nhận diện: Trộn thông số WebGL Fingerprint ---\n"
                    f"const getParameterProxy = new Proxy(WebGLRenderingContext.prototype.getParameter, {{\n"
                    f"    apply: function(target, thisArg, args) {{\n"
                    f"        if (args[0] === 37445) return '{random.choice(['Intel Inc.', 'Apple Inc.', 'NVIDIA Corporation', 'AMD', 'Qualcomm'])}';\n"
                    f"        if (args[0] === 37446) return '{random.choice(['Intel Iris OpenGL Engine', 'Apple GPU', 'Adreno (TM) 640', 'Mali-G77 MC9', 'Adreno (TM) 730'])}';\n"
                    f"        return Reflect.apply(target, thisArg, args);\n"
                    f"    }}\n"
                    f"}});\n"
                    f"WebGLRenderingContext.prototype.getParameter = getParameterProxy;\n"
                )

                page = self.context.new_page()
                apply_stealth(page)
                
                try:
                    print(f"[*] Đang mở trang web: {target_url}")
                    # Thiết lập Timeout 45 giây để kiểm tra Proxy chậm/bất ổn
                    page.goto(target_url, timeout=45000)
                    
                    # Tự động mô phỏng hành vi người dùng (Di chuột & Cuộn trang ngẫu nhiên) 
                    # ngay sau khi load trang để tăng Trust Score, đánh lừa hệ thống phát hiện Bot.
                    try:
                        print("[*] Đang mô phỏng hành vi con người (Mouse & Scroll)...")
                        # Di chuyển chuột ngẫu nhiên 3-5 lần (steps tạo độ mượt cho trỏ chuột)
                        for _ in range(random.randint(3, 5)):
                            x = random.randint(100, v_width - 100)
                            y = random.randint(100, v_height - 100)
                            page.mouse.move(x, y, steps=random.randint(5, 15))
                            page.wait_for_timeout(random.randint(100, 500))
                            
                        # Cuộn trang xuống ngẫu nhiên 1-3 lần
                        for _ in range(random.randint(1, 3)):
                            page.mouse.wheel(0, random.randint(100, 600))
                            page.wait_for_timeout(random.randint(300, 1000))
                            
                        # Cuộn ngược lên một chút để tạo sự tự nhiên
                        page.mouse.wheel(0, -random.randint(50, 200))
                        page.wait_for_timeout(random.randint(300, 800))
                    except Exception:
                        pass # Bỏ qua nếu có lỗi trong quá trình mô phỏng (ví dụ trang bị đóng đột ngột)
                        
                except PlaywrightTimeoutError:
                    print("[!!!] CẢNH BÁO: Mạng quá chậm hoặc Proxy đã chết (Timeout 45s).")
                    print("[!!!] Vui lòng kiểm tra lại chất lượng Proxy (Ping cao hoặc mất kết nối)!")
                    return
                except PlaywrightError as e:
                    if "closed" in str(e).lower() or "target page" in str(e).lower():
                        print("[!] Trình duyệt đã bị đóng trong lúc đang tải trang.")
                        return
                    raise e

                print("=====================================================")
                print("Trình duyệt đang mở! Bạn có thể thao tác tay.")
                print("Đóng cửa sổ trình duyệt hoặc bấm nút 'Xóa Session' để dọn dẹp.")
                print("=====================================================")

                on_launch_callback(device_profile)

                try:
                    # Giữ tiến trình chạy cho đến khi tất cả các tab bị đóng hoặc trình duyệt tắt
                    while self.context and self.context.pages and not self._should_close:
                        try:
                            self.context.pages[0].wait_for_event("close", timeout=1000)
                        except PlaywrightTimeoutError:
                            pass # Hết thời gian chờ 1s, lặp lại để tiếp tục kiểm tra cờ _should_close
                        except Exception:
                            pass
                except Exception:
                    pass
                    
                if self._should_close and self.browser and self.browser.is_connected():
                    print("[*] Đang thực hiện đóng trình duyệt từ luồng chạy nền...")
                    try:
                        self.browser.close()
                    except Exception:
                        pass
                    
                print("[*] Trình duyệt đã đóng. Bắt đầu dọn dẹp tài nguyên...")

        except PlaywrightError as e:
            # Bắt các lỗi cụ thể của Playwright, ví dụ như không tải được trình duyệt
            print(f"[!!!] Lỗi Playwright: {e}")
            raise e # Ném lại lỗi để GUI hiển thị
        finally:
            # Khối này đảm bảo trạng thái được reset ngay cả khi có lỗi
            self.context = None
            self.browser = None
            self.playwright = None
            print("[*] Session đã được dọn dẹp hoàn toàn.")

    def close_and_cleanup(self):
        """Phát tín hiệu để luồng Playwright tự đóng trình duyệt và dọn dẹp."""
        print("[*] Nhận lệnh dọn dẹp. Gửi tín hiệu đóng trình duyệt/session...")
        self._should_close = True
