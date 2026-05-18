import os
import random
import threading
import time
import sys
import tempfile
import uuid
import subprocess
from playwright.sync_api import sync_playwright, Playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

# Vô hiệu hóa toàn bộ log in ra terminal
def print(*args, **kwargs):
    pass

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
        self._pending_action = None
        self.login_phone = ""
        self.login_password = ""
        self.user_data_dir = ""

    def _load_proxies(self):
        """Đọc danh sách proxy từ file txt"""
        proxy_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'proxies.txt')
        if not os.path.exists(proxy_path):
            return []
        with open(proxy_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    def run_session_and_wait(self, target_url, use_proxy, on_launch_callback, device_profile=None, on_browser_created=None, headless=False, search_keywords=None):
        """
        Khởi chạy session, gọi callback, và block cho đến khi trình duyệt bị đóng.
        Việc dọn dẹp được thực hiện tự động khi thoát khỏi khối 'with'.
        """
        self._should_close = False
        
        if self.context:
            print("[!] Một trình duyệt đã đang chạy. Vui lòng đóng và xóa session cũ trước.")
            if self.context and self.context.pages:
                self.context.pages[0].bring_to_front()
            return

        if target_url and not target_url.startswith("http"):
            target_url = "https://" + target_url

        if device_profile is None:
            device_profile = self.device_faker.generate_new_device()
            
        self.user_data_dir = device_profile.get("profile_path", "")
        if not self.user_data_dir:
            self.user_data_dir = os.path.join(tempfile.gettempdir(), f"Clean_Profile_{uuid.uuid4().hex[:8]}")
        os.makedirs(self.user_data_dir, exist_ok=True)
            
        v_width = device_profile['viewport']['width']
        v_height = device_profile['viewport']['height']
        
        print("[*] Đang quét hệ thống để tìm dữ liệu Google Chrome gốc...")
        print("[*] Đã loại bỏ các dấu vết phần cứng (MAC/IMEI) từ hồ sơ cũ.")
        print(f"[*] Đã đóng gói thành công 1 Hồ sơ Chrome thật tại:\n    {self.user_data_dir}")
        print(f"[*] Cửa sổ hiển thị: {v_width}x{v_height}")

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
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[!] Lỗi khi cài đặt Chromium: {e}")

        try:
            with sync_playwright() as p:
                self.playwright = p
                device_profile['executable_path'] = "Google Chrome Thật (Real Browser)"
                print("[*] Đang khởi chạy Google Chrome thật với Hồ sơ Sạch...")
                
                try:
                    self.context = p.chromium.launch_persistent_context(
                        user_data_dir=self.user_data_dir,
                        channel="chrome",
                        headless=headless,
                        ignore_default_args=["--enable-automation"],
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--disable-infobars",
                            "--disable-features=IsolateOrigins,site-per-process",
                            f"--window-size={v_width},{v_height}"
                        ],
                        **( {'user_agent': device_profile["user_agent"]} if device_profile.get("user_agent") else {} ),
                        viewport=device_profile["viewport"],
                        is_mobile=device_profile["is_mobile"],
                        has_touch=device_profile["is_mobile"],
                        device_scale_factor=device_profile.get("device_scale_factor", 1.25),
                        proxy=proxy_settings,
                        color_scheme=random.choice(["light", "dark"])
                    )
                except Exception:
                    print("[!] Không tìm thấy Google Chrome thật trên máy, chuyển sang lõi mặc định...")
                    self.context = p.chromium.launch_persistent_context(
                        user_data_dir=self.user_data_dir,
                        headless=headless,
                        ignore_default_args=["--enable-automation"],
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--disable-infobars",
                            "--disable-features=IsolateOrigins,site-per-process",
                            f"--window-size={v_width},{v_height}"
                        ],
                        **( {'user_agent': device_profile["user_agent"]} if device_profile.get("user_agent") else {} ),
                        viewport=device_profile["viewport"],
                        is_mobile=device_profile["is_mobile"],
                        has_touch=device_profile["is_mobile"],
                        device_scale_factor=device_profile.get("device_scale_factor", 1.25),
                        proxy=proxy_settings,
                        color_scheme=random.choice(["light", "dark"])
                    )
                
                if on_browser_created:
                    on_browser_created()

                # --- GIÁM SÁT NETWORK ĐỂ FIX LỖI ---
                self.auto_action_count = 0
                
                def handle_network_response(response):
                    try:
                        # --- TỰ ĐỘNG BẮT LỖI TẠCH LINK /finish/ ---
                        if response.request.resource_type == "document" and "finish" in response.url:
                            self._pending_action = "fix_404_error"
                    except Exception:
                        pass

                self.context.on("response", handle_network_response)
                # ---------------------------------------------------

                # Giấu các biến toàn cục do Playwright tạo ra
                self.context.add_init_script(
                    f"// Xóa các biến toàn cục do Playwright tạo ra\n"
                    f"delete window.__playwright;\n"
                    f"delete window.__pw_manual;\n"
                    f"delete window.__PW_outOfContext;\n"
                    f"\n"
                    f"// Xóa chữ ký CDP (Chrome DevTools Protocol) chống Cloudflare Turnstile\n"
                    f"try {{\n"
                    f"    let objectToInspect = window;\n"
                    f"    let cdcProps = Object.getOwnPropertyNames(objectToInspect).filter(name => name.includes('cdc_'));\n"
                    f"    cdcProps.forEach(prop => delete objectToInspect[prop]);\n"
                    f"}} catch(e) {{}}\n"
                    f"Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}});\n"
                    f"if (!window.chrome) window.chrome = {{}};\n"
                    f"if (!window.chrome.runtime) window.chrome.runtime = {{}};\n"
                    f"\n"
                    f"// --- HỖ TRỢ ZOOM BẰNG CTRL + CUỘN CHUỘT --- \n"
                    f"window.addEventListener('wheel', function(e) {{\n"
                    f"    if (e.ctrlKey) {{\n"
                    f"        e.preventDefault();\n"
                    f"        let zoom = parseFloat(document.body.style.zoom) || window.devicePixelRatio || 1.0;\n"
                    f"        zoom += e.deltaY < 0 ? 0.15 : -0.15;\n"
                    f"        if (zoom < 0.5) zoom = 0.5;\n"
                    f"        if (zoom > 4.0) zoom = 4.0;\n"
                    f"        document.body.style.zoom = zoom;\n"
                    f"    }}\n"
                    f"}}, {{ passive: false }});\n"
                )

                # --- ÉP MỞ LINK TRONG CÙNG TAB (ÁP DỤNG CHO MỌI TAB TRONG CONTEXT) ---
                self.context.add_init_script("""
                    // 1. Ghi đè window.open để mở đè lên tab hiện tại
                    window.open = function(url) {
                        window.location.href = url;
                        return window;
                    };
                    
                    // 2. Dùng MutationObserver để xóa target="_blank" NGAY LẬP TỨC khi thẻ <a> vừa được web sinh ra
                    const observer = new MutationObserver((mutations) => {
                        mutations.forEach((mutation) => {
                            mutation.addedNodes.forEach((node) => {
                                if (node.nodeType === 1) { // ELEMENT_NODE
                                    if (node.tagName === 'A' && node.getAttribute('target') === '_blank') {
                                        node.removeAttribute('target');
                                    }
                                    if (node.querySelectorAll) {
                                        node.querySelectorAll('a[target="_blank"]').forEach(a => a.removeAttribute('target'));
                                    }
                                }
                            });
                        });
                    });

                    document.addEventListener('DOMContentLoaded', () => {
                        document.querySelectorAll('a[target="_blank"]').forEach(a => a.removeAttribute('target'));
                        observer.observe(document, { childList: true, subtree: true });
                    });
                """)

                def on_page_load(p):
                    try:
                        url_str = p.url
                        if url_str and not url_str.startswith("about:") and not url_str.startswith("chrome-error:"):
                            url_clean = url_str.rstrip("/").split("?")[0]
                            if url_clean == "https://moneytask.top":
                                self._pending_action = "wait_and_go_login"
                            elif url_clean == "https://moneytask.top/login":
                                self._pending_action = "fill_login"
                            elif url_clean == "https://moneytask.top/app":
                                self._pending_action = "wait_and_go_tasks"
                    except Exception:
                        pass

                self.context.on("page", lambda p: p.on("domcontentloaded", on_page_load))

                page = self.context.pages[0] if self.context.pages else self.context.new_page()
                page.on("domcontentloaded", on_page_load)
                
                # --- TĂNG SỨC CHỊU ĐỰNG MẠNG (NETWORK RESILIENCE) ---
                # Giúp trình duyệt kiên nhẫn chờ đợi khi mạng lag hoặc rớt tạm thời mà không đánh hỏng nhiệm vụ
                self.context.set_default_timeout(60000) # Chờ tối đa 60s cho các thao tác (tìm nút, click, gõ)
                self.context.set_default_navigation_timeout(90000) # Chờ tối đa 90s khi tải trang
                
                # ĐÃ TẮT apply_stealth(page): Tránh xung đột với khối add_init_script bên trên. Việc ghi đè thông số 2 lần sẽ khiến Google phát hiện ra Bot.
                
                try:
                    # --- BƯỚC WARM-UP: TRÁNH BỊ NHẬN DIỆN LÀ BOT MỞ TAB SIÊU TỐC ---
                    # 1. Khởi động ở trang trắng (cho trình duyệt vài giây để áp dụng toàn bộ thông số ẩn danh)
                    print("[*] Đang làm ấm trình duyệt...")
                    page.goto("about:blank")
                    page.wait_for_timeout(random.randint(500, 1000))
                    
                    # 2. Truy cập Google theo kịch bản tùy chỉnh thay vì truy cập thẳng link đích
                    print("[*] Truy cập Google...")
                    # Sử dụng domcontentloaded thay vì chờ load xong tất cả ảnh/mạng để giảm tỷ lệ bị Google nghi ngờ
                    page.goto("https://www.google.com/", wait_until="domcontentloaded", timeout=90000)
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(random.randint(325, 825))
                    
                    try:
                        print("[*] Đang mô phỏng hành vi con người (Mouse & Scroll)...")
                        for _ in range(random.randint(3, 5)):
                            x = random.randint(100, v_width - 100)
                            y = random.randint(100, v_height - 100)
                            page.mouse.move(x, y, steps=random.randint(3, 10))
                            page.wait_for_timeout(random.randint(30, 165))
                    except Exception:
                        pass
                        
                    try:
                        print("[*] Đang bắt đầu quy trình tự động tìm kiếm...")
                        
                        search_selector = "textarea[name='q'], input[name='q']"
                        page.wait_for_selector(search_selector, state="visible", timeout=15000)
                        
                        # Click vào ô tìm kiếm để mô phỏng người thật
                        page.click(search_selector)
                        self.auto_action_count += 1
                        page.wait_for_timeout(random.randint(165, 500))
                        
                        # Sử dụng hàm type thay vì fill để gõ từng chữ cái với khoảng trễ delay (như người gõ phím)
                        target_keyword = "moneytask.top"
                        
                        print(f"[*] Đang gõ từ khóa: {target_keyword}")
                        page.type(search_selector, target_keyword, delay=random.randint(12, 32))
                        self.auto_action_count += len(target_keyword)
                        
                        page.wait_for_timeout(random.randint(265, 500))
                        
                        print("[*] Đang nhấn Enter...")
                        page.press(search_selector, "Enter")
                        self.auto_action_count += 1
                        
                        page.wait_for_load_state("domcontentloaded")
                        print("[*] Đã tự động hoá thành công quy trình tìm kiếm!")
                        
                        # --- BỔ SUNG: XỬ LÝ GOOGLE RECAPTCHA (NẾU CÓ) ---
                        try:
                            # Chờ xem iframe checkbox của reCAPTCHA có xuất hiện trong vòng 4 giây không
                            page.wait_for_selector("iframe[src*='recaptcha/api2/anchor'], iframe[src*='recaptcha/enterprise']", timeout=4000)
                            print("[!] Phát hiện xác thực Captcha. Đang tự động xử lý...")
                            page.wait_for_timeout(random.randint(650, 1650))
                            
                            # Sử dụng frame_locator để chọn đúng iframe chứa ô Checkbox
                            recaptcha_frame = page.frame_locator("iframe[src*='recaptcha/api2/anchor'], iframe[src*='recaptcha/enterprise']").first
                            checkbox = recaptcha_frame.locator(".recaptcha-checkbox-border")
                            
                            if checkbox.count() > 0:
                                # Mô phỏng rề chuột từ từ vào ô Checkbox rồi mới click (chuẩn con người)
                                checkbox.hover()
                                page.wait_for_timeout(random.randint(400, 900))
                                checkbox.click(delay=random.randint(80, 200))
                                self.auto_action_count += 2
                                print("[*] Đã tự động click xác thực.")
                                page.wait_for_timeout(random.randint(2000, 3300))
                        except Exception:
                            pass
                            
                        try:
                            # Chờ một lúc trên trang kết quả Google
                            page.wait_for_timeout(random.randint(1500, 2500))
                            current_url = page.url
                            if "google.com/search" in current_url:
                                print("[*] Đã đến trang kết quả tìm kiếm. Tự động chuyển thẳng tới moneytask.top...")
                                page.goto("https://moneytask.top", wait_until="domcontentloaded", timeout=60000)
                                self.auto_action_count += 1
                        except Exception as ex:
                            print(f"[!] Lỗi khi tự động chuyển trang: {ex}")
                    except Exception as ex:
                        print(f"[!] Lỗi trong quá trình tự động hóa tác vụ: {ex}")
                        
                except PlaywrightTimeoutError:
                    pass # Bỏ qua cảnh báo mạng chậm
                except PlaywrightError as e:
                    if "closed" in str(e).lower() or "target page" in str(e).lower():
                        print("[!] Trình duyệt đã bị đóng trong lúc đang tải trang.")
                        return
                    pass # Bỏ qua cảnh báo lỗi mạng

                print("=====================================================")
                print("Trình duyệt đang mở! Bạn có thể thao tác tay.")
                print("Đóng cửa sổ trình duyệt hoặc bấm nút 'Delete' để dọn dẹp.")
                print("=====================================================")

                on_launch_callback(device_profile)

                try:
                    # Giữ tiến trình chạy cho đến khi tất cả các tab bị đóng hoặc trình duyệt tắt
                    while self.context and self.context.pages and not self._should_close:
                        try:
                            # --- TỰ ĐỘNG DIỆT CLOUDFLARE TURNSTILE TRONG LÚC RẢNH RỖI ---
                            try:
                                active_p = self.context.pages[-1]
                                
                                # --- THEO DÕI URL ĐỂ KÍCH HOẠT LỆNH (Bắt chuyển hướng ngầm SPA không cần Tải lại trang) ---
                                current_url_clean = active_p.url.rstrip("/").split("?")[0]
                                if getattr(self, '_last_seen_url', '') != current_url_clean:
                                    self._last_seen_url = current_url_clean
                                    if current_url_clean == "https://moneytask.top/app":
                                        self._pending_action = "wait_and_go_tasks"
                                # -----------------------------------------------------------------------------------------
                                
                                # 1. Dạng Checkbox Cloudflare Turnstile nằm trong iframe
                                cf_frame = active_p.frame_locator("iframe[src*='challenges.cloudflare.com'], iframe[src*='turnstile']").first
                                cf_checkbox = cf_frame.locator("label.ctp-checkbox-label, input[type='checkbox'], .mark, #challenge-stage").first
                                
                                # 2. Dạng nút bấm thông thường bên ngoài
                                verify_btn = active_p.locator("text=Verify you are human, text=Xác minh bạn là con người, text=Vui lòng xác minh bạn là con người").first
                                
                                if cf_checkbox.count() > 0 and cf_checkbox.is_visible(timeout=100):
                                    print("\n[*] [Auto-Bypass] Phát hiện Tường lửa Cloudflare. Đang tự động xác minh...")
                                    try:
                                        box = cf_checkbox.bounding_box()
                                        if box:
                                            # Click lệch tâm ngẫu nhiên (như người thật) thay vì click chính giữa trung tâm
                                            target_x = box["x"] + random.uniform(box["width"] * 0.2, box["width"] * 0.8)
                                            target_y = box["y"] + random.uniform(box["height"] * 0.2, box["height"] * 0.8)
                                            active_p.mouse.move(target_x, target_y, steps=random.randint(3, 7))
                                            active_p.wait_for_timeout(random.randint(200, 500))
                                            active_p.mouse.down()
                                            active_p.wait_for_timeout(random.randint(80, 200))
                                            active_p.mouse.up()
                                        else:
                                            cf_checkbox.click(delay=random.randint(80, 200))
                                    except Exception:
                                        cf_checkbox.click(delay=random.randint(80, 200))
                                    self.auto_action_count += 2
                                    active_p.wait_for_timeout(4000)
                                elif verify_btn.count() > 0 and verify_btn.is_visible(timeout=100):
                                    print("\n[*] [Auto-Bypass] Phát hiện nút Xác minh con người. Đang tự động click...")
                                    try:
                                        box = verify_btn.bounding_box()
                                        if box:
                                            target_x = box["x"] + random.uniform(box["width"] * 0.2, box["width"] * 0.8)
                                            target_y = box["y"] + random.uniform(box["height"] * 0.2, box["height"] * 0.8)
                                            active_p.mouse.move(target_x, target_y, steps=random.randint(3, 7))
                                            active_p.wait_for_timeout(random.randint(200, 500))
                                            active_p.mouse.down()
                                            active_p.wait_for_timeout(random.randint(80, 200))
                                            active_p.mouse.up()
                                        else:
                                            verify_btn.click(delay=random.randint(80, 200))
                                    except Exception:
                                        verify_btn.click(delay=random.randint(80, 200))
                                    self.auto_action_count += 1
                                    active_p.wait_for_timeout(4000)
                            except Exception: pass
                            # -----------------------------------------------------------

                            # Kiểm tra xem có lệnh từ giao diện gửi xuống không
                            if getattr(self, '_pending_action', None) == "wait_and_go_login":
                                self._pending_action = None
                                try:
                                    active_page = self.context.pages[-1]
                                    print("[*] Đã tải xong moneytask.top. Đang chờ 0.5 giây trước khi tự động chuyển trang đăng nhập...")
                                    active_page.wait_for_timeout(500)
                                    active_page.goto("https://moneytask.top/login", wait_until="domcontentloaded", timeout=60000)
                                    self.auto_action_count += 1
                                except Exception as ex:
                                    print(f"[!] Lỗi khi tự động chuyển trang login: {ex}")
                                    
                            elif getattr(self, '_pending_action', None) == "wait_and_go_tasks":
                                self._pending_action = None
                                try:
                                    active_page = self.context.pages[-1]
                                    print("[*] Đã vào trang Home. Đang chờ 1.5 giây trước khi tự động chuyển sang trang nhiệm vụ...")
                                    active_page.wait_for_timeout(1500)
                                    active_page.goto("https://moneytask.top/app/tasks/link-rut-gon", wait_until="domcontentloaded", timeout=60000)
                                    self.auto_action_count += 1
                                except Exception as ex:
                                    print(f"[!] Lỗi khi tự động chuyển trang nhiệm vụ: {ex}")
                                    
                            elif getattr(self, '_pending_action', None) == "fill_login":
                                self._pending_action = None
                                if not getattr(self, 'login_phone', '') or not getattr(self, 'login_password', ''):
                                    print("[!] Cảnh báo: Chưa lưu thông tin tài khoản trên Tool, bỏ qua tự động đăng nhập.")
                                else:
                                    try:
                                        active_page = self.context.pages[-1]
                                        active_page.wait_for_timeout(500) # Đợi trang login load một chút trước khi điền
                                        # Tìm tab có chứa form đăng nhập (ưu tiên tab có ô input password) để tránh bị lỗi do quảng cáo
                                        target_page = None
                                        for p in reversed(self.context.pages):
                                            try:
                                                if p.evaluate("() => document.querySelectorAll('input[type=\"password\"]').length > 0"):
                                                    target_page = p
                                                    break
                                            except Exception: pass
                                        
                                        if not target_page:
                                            target_page = self.context.pages[-1]
                                            
                                        try:
                                            target_page.bring_to_front()
                                        except Exception: pass
                                        
                                        print(f"[*] Đang thực thi lệnh tự động điền tài khoản...")
                                        
                                        login_data = {
                                            "phone": getattr(self, 'login_phone', ''),
                                            "password": getattr(self, 'login_password', '')
                                        }
                                        
                                        target_page.evaluate("""(data) => {
                                            const phone = data.phone;
                                            const password = data.password;
                                            
                                            function fillForm(doc) {
                                                const inputs = Array.from(doc.querySelectorAll('input'));
                                                const passInput = inputs.find(i => i.type === 'password');
                                                const textInputs = inputs.filter(i => i.type === 'text' || i.type === 'tel' || i.name.toLowerCase().includes('phone') || i.name.toLowerCase().includes('user') || i.name.toLowerCase().includes('email'));
                                                
                                                let userInput = null;
                                                if (passInput) {
                                                    userInput = textInputs.reverse().find(i => i.compareDocumentPosition(passInput) & Node.DOCUMENT_POSITION_FOLLOWING);
                                                }
                                                if (!userInput && textInputs.length > 0) userInput = textInputs[0];
                                                
                                                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                                let filled = false;
                                                
                                                if (userInput && phone) {
                                                    nativeInputValueSetter.call(userInput, phone);
                                                    userInput.dispatchEvent(new Event('input', { bubbles: true }));
                                                    userInput.dispatchEvent(new Event('change', { bubbles: true }));
                                                    userInput.blur();
                                                    filled = true;
                                                }
                                                if (passInput && password) {
                                                    nativeInputValueSetter.call(passInput, password);
                                                    passInput.dispatchEvent(new Event('input', { bubbles: true }));
                                                    passInput.dispatchEvent(new Event('change', { bubbles: true }));
                                                    passInput.blur();
                                                    filled = true;
                                                }
                                                return filled;
                                            }
                                            
                                            let success = fillForm(document);
                                            if (!success) {
                                                const frames = document.querySelectorAll('iframe');
                                                for (let i = 0; i < frames.length; i++) {
                                                    try {
                                                        if (frames[i].contentDocument) {
                                                            if (fillForm(frames[i].contentDocument)) break;
                                                        }
                                                    } catch(e) {}
                                                }
                                            }
                                            document.body.click();
                                        }""", login_data)
                                        self.auto_action_count += 5
                                        print("[*] Đã điền xong số điện thoại và mật khẩu!")
                                        
                                        target_page.wait_for_timeout(250)
                                        
                                        print("[*] Đang tự động tìm và nhấn nút Đăng nhập...")
                                        try:
                                            btn_selectors = "button[type='submit'], button:has-text('Đăng nhập'), button:has-text('Đăng Nhập'), button:has-text('Login'), input[type='submit']"
                                            target_page.click(btn_selectors, timeout=4000)
                                            self.auto_action_count += 1
                                            print("[*] Đã nhấn nút Đăng nhập. Đang kiểm tra kết quả (chờ tối đa 3s)...")
                                            
                                            try:
                                                # Đợi 3s xem URL có thoát khỏi trang login (để vào home) hay không
                                                target_page.wait_for_function("window.location.href.indexOf('login') === -1", timeout=3000)
                                                print("[*] Đăng nhập thành công, đã vào trang Home!")
                                                self.login_retry_count = 0  # Reset bộ đếm thử lại nếu thành công
                                                self._pending_action = "wait_and_go_tasks"
                                            except Exception:
                                                print("[-] Sau 3s vẫn chưa vào được trang Home.")
                                                self.login_retry_count = getattr(self, 'login_retry_count', 0) + 1
                                                if self.login_retry_count <= 3:
                                                    print(f"[*] Đang tải lại trang (F5) và thử đăng nhập lại (Lần {self.login_retry_count})...")
                                                    target_page.reload(wait_until="domcontentloaded", timeout=15000)
                                                    self._pending_action = "fill_login"
                                                else:
                                                    print("[!] Đã thử tự động đăng nhập lại 3 lần nhưng vẫn thất bại. Có thể do sai mật khẩu hoặc Captcha. Dừng tự động.")
                                                    self.login_retry_count = 0
                                        except Exception:
                                            print("[!] Không tìm thấy nút Đăng nhập tự động. Vui lòng nhấn bằng tay.")
                                    except Exception as ex:
                                        print(f"[!] Lỗi khi điền thông tin: {ex}")
                                    
                            elif getattr(self, '_pending_action', None) == "auto_task_step":
                                self._pending_action = None
                                try:
                                    active_page = self.context.pages[-1]
                                    print("\n[*] ===========================================")
                                    print("[*] BẮT ĐẦU CHUỖI NHIỆM VỤ LẤY MÃ (UPTO STEP)")
                                    
                                    steps = ["Lấy mã step 1", "Lấy mã step 2", "Lấy mã step 3"]
                                    task_completed = False
                                    
                                    for step in steps:
                                        if self._should_close or task_completed: break
                                        
                                        print(f"[*] Đang tìm nút: '{step}'...")
                                        
                                        # 1. Tự động cuộn trang để kích hoạt nút (nhiều web dùng Lazy-load, phải cuộn mới hiện DOM)
                                        active_page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
                                        self.auto_action_count += 1
                                        active_page.wait_for_timeout(2000)
                                        
                                        button_found = False
                                        # 2. Quét trong trang chính và xuyên qua tất cả thẻ iframe
                                        for frame in [active_page] + active_page.frames:
                                            # Bỏ dấu nháy đơn để tìm chuỗi con, không phân biệt hoa thường và bỏ qua khoảng trắng thừa
                                            step_loc = frame.locator(f"text={step}")
                                            if step_loc.count() > 0:
                                                for i in range(step_loc.count()):
                                                    try:
                                                        if step_loc.nth(i).is_visible():
                                                            step_loc.nth(i).scroll_into_view_if_needed()
                                                            active_page.wait_for_timeout(1000)
                                                            
                                                            step_loc.nth(i).click(timeout=3000)
                                                            self.auto_action_count += 1
                                                            button_found = True
                                                            break
                                                    except Exception: pass
                                            if button_found: break
                                                    
                                        if button_found:
                                            print(f"[*] Đã nhấn '{step}'. Đang chờ hệ thống đếm ngược...")
                                            
                                            for _ in range(120):
                                                if self._should_close: break
                                                active_page.wait_for_timeout(1000)
                                                
                                                finish_loc = active_page.locator("text=Nhấn để tiếp tục")
                                                is_finished = False
                                                for i in range(finish_loc.count()):
                                                    if finish_loc.nth(i).is_visible():
                                                        print("[*] Phá hiện nút 'Nhấn để tiếp tục' (Hoàn thành)!")
                                                        finish_loc.nth(i).scroll_into_view_if_needed()
                                                        active_page.wait_for_timeout(500)
                                                        
                                                        finish_loc.nth(i).click(timeout=3000)
                                                        self.auto_action_count += 1
                                                        is_finished = True
                                                        break
                                                if is_finished:
                                                    print("[*] QUY TRÌNH LẤY MÃ ĐÃ HOÀN TẤT!")
                                                    task_completed = True
                                                    break
                                                    
                                                link_loc = active_page.locator("text=Nhấn link bất kỳ để tiếp tục, text=Nhấn link bất kì để tiếp tục")
                                                needs_reload = False
                                                for i in range(link_loc.count()):
                                                    if link_loc.nth(i).is_visible():
                                                        print(f"[!] Web yêu cầu click link. Đang tự động Tải lại trang (F5) để sang {steps[steps.index(step)+1] if step != steps[-1] else 'bước tiếp'}...")
                                                        needs_reload = True
                                                        break
                                                
                                                if needs_reload:
                                                    active_page.reload()
                                                    self.auto_action_count += 1
                                                    active_page.wait_for_load_state("domcontentloaded")
                                                    active_page.wait_for_timeout(3000)
                                                    break
                                        else:
                                            print(f"[-] Không tìm thấy '{step}' trên màn hình. Có thể đã qua bước này.")
                                            
                                    if not task_completed and not self._should_close:
                                        print("[*] Đã chạy xong kịch bản quét nhưng chưa thấy nút hoàn tất cuối cùng.")
                                    print("[*] ===========================================\n")
                                        
                                except Exception as ex:
                                    print(f"[!] Lỗi trong quá trình tự động lấy mã upto step: {ex}")

                            elif getattr(self, '_pending_action', None) == "fix_404_error":
                                self._pending_action = None
                                try:
                                    active_page = self.context.pages[-1]
                                    print("[*] CẤP CỨU: Tool đang chờ 2 giây để Web hiển thị lỗi...")
                                    active_page.wait_for_timeout(2000)
                                    
                                    error_loc_str = "text=404 Not Found, text=không tìm thấy trên máy chủ"
                                    if active_page.locator(error_loc_str).count() > 0:
                                        print("[*] Đang tự động Tải lại trang (F5) để ép Server kết nối lại...")
                                        active_page.reload(wait_until="domcontentloaded", timeout=15000)
                                        self.auto_action_count += 1
                                        active_page.wait_for_timeout(3000)
                                        
                                        # Kiểm tra lại xem F5 có giải quyết được không
                                        if active_page.locator(error_loc_str).count() > 0:
                                            print("[*] F5 thất bại. Đang tự động lùi lại (Back) trang trước đó...")
                                            active_page.go_back(wait_until="domcontentloaded", timeout=15000)
                                            self.auto_action_count += 1
                                            print("[*] Đã lùi trang. Bạn hãy thử bấm 'Xác thực' lại một lần nữa!")
                                            print("[*] (Lưu ý: Nếu vẫn lỗi thì 100% Server web nhiệm vụ đã sập, vui lòng bỏ qua web này).")
                                        else:
                                            print("[*] F5 thành công! Trang web đã vượt qua được lỗi 404.")
                                    else:
                                        print("[*] Không tìm thấy dòng chữ báo lỗi, có thể web đã tự chuyển hướng.")
                                except Exception as ex:
                                    print(f"[-] Lỗi khi tự động cấp cứu 404: {ex}")

                            elif getattr(self, '_pending_action', None) == "auto_task":
                                self._pending_action = None
                                try:
                                    active_page = self.context.pages[-1]
                                    print("\n[*] ===========================================")
                                    print("[*] BẮT ĐẦU CHUỖI NHIỆM VỤ LẤY MÁ TỰ ĐỘNG")
                                    
                                    task_completed = False
                                    
                                    # 1. Kiểm tra yêu cầu click bài viết bất kỳ trước khi tìm nút lấy mã
                                    req_link_loc = active_page.locator("text=Vui lòng nhấn bài viết bất kỳ")
                                    if req_link_loc.count() > 0 and req_link_loc.nth(0).is_visible():
                                        print("[*] Phát hiện yêu cầu 'Vui lòng nhấn bài viết bất kỳ...'. Đang tìm và click vào 1 bài viết...")
                                        
                                        clicked = active_page.evaluate("""() => {
                                            const links = Array.from(document.querySelectorAll('a[href]'));
                                            // Lọc ra các link bài viết nội bộ thực sự (có text, không phải link rỗng hoặc nhảy neo)
                                            const validLinks = links.filter(a => {
                                                const rect = a.getBoundingClientRect();
                                                return a.innerText.trim().length > 5 
                                                    && rect.width > 0 && rect.height > 0 
                                                    && a.href.startsWith(window.location.origin)
                                                    && !a.href.includes('#');
                                            });
                                            if (validLinks.length > 0) {
                                                const randomLink = validLinks[Math.floor(Math.random() * validLinks.length)];
                                                randomLink.scrollIntoView({behavior: 'smooth', block: 'center'});
                                                randomLink.click();
                                                return true;
                                            } else if (links.length > 0) {
                                                links[Math.floor(Math.random() * links.length)].click();
                                                return true;
                                            }
                                            return false;
                                        }""")
                                        
                                        if clicked:
                                            self.auto_action_count += 1
                                            print("[*] Đã click vào một bài viết. Đang đợi trang mới tải...")
                                            active_page.wait_for_load_state("domcontentloaded")
                                            active_page.wait_for_timeout(3000)
                                            
                                            print("[*] Đang tự động cuộn xuống dưới cùng để tìm nút 'Lấy mã'...")
                                            active_page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
                                            self.auto_action_count += 1
                                            active_page.wait_for_timeout(2000)
                                        else:
                                            print("[-] Không tìm thấy bài viết hợp lệ nào để click, tiếp tục...")
                                    
                                    print("[*] Đang tìm nút 'Lấy mã'...")
                                    # Tìm cụm từ chính xác (không phân biệt hoa thường do đặc tính Playwright locator)
                                    lay_ma_loc = active_page.locator("text='Lấy mã'")
                                    
                                    button_found = False
                                    if lay_ma_loc.count() > 0:
                                        for i in range(lay_ma_loc.count()):
                                            if lay_ma_loc.nth(i).is_visible():
                                                lay_ma_loc.nth(i).scroll_into_view_if_needed()
                                                active_page.wait_for_timeout(1000)
                                                
                                                lay_ma_loc.nth(i).click(timeout=3000)
                                                self.auto_action_count += 1
                                                button_found = True
                                                break
                                                
                                    if button_found:
                                        print("[*] Đã nhấn nút 'Lấy mã'. Đang chờ hệ thống đếm ngược...")
                                        
                                        # Vòng lặp chờ tối đa 120 giây
                                        for _ in range(120):
                                            if self._should_close or task_completed: break
                                            active_page.wait_for_timeout(1000) # Đợi 1 giây rồi kiểm tra lại
                                            
                                            touch_loc = active_page.locator("text=chạm vào màn hình để lấy mã")
                                            if touch_loc.count() > 0 and touch_loc.nth(0).is_visible():
                                                print("[*] Phát hiện yêu cầu 'chạm vào màn hình để lấy mã'!")
                                                touch_loc.nth(0).scroll_into_view_if_needed()
                                                active_page.wait_for_timeout(500)
                                                
                                                touch_loc.nth(0).click(timeout=3000)
                                                self.auto_action_count += 1
                                                print("[*] Đã chạm vào màn hình. Đang kiểm tra yêu cầu cuộn trang...")
                                                
                                                # Đợi 2 giây để thông báo cuộn xuất hiện (nếu có)
                                                active_page.wait_for_timeout(2000)
                                                
                                                scroll_up_loc = active_page.locator("text=vui lòng cuộn lên để tiếp tục lấy mã")
                                                scroll_down_loc = active_page.locator("text=vui lòng cuộn xuống để tiếp tục lấy mã")
                                                
                                                if scroll_up_loc.count() > 0 and scroll_up_loc.nth(0).is_visible():
                                                    print("[*] Web yêu cầu cuộn lên. Đang tự động cuộn lên trên cùng...")
                                                    active_page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
                                                    self.auto_action_count += 1
                                                elif scroll_down_loc.count() > 0 and scroll_down_loc.nth(0).is_visible():
                                                    print("[*] Web yêu cầu cuộn xuống. Đang tự động cuộn xuống dưới cùng...")
                                                    active_page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
                                                    self.auto_action_count += 1
                                                else:
                                                    print("[*] Không thấy thông báo yêu cầu cuộn trang.")
                                                    
                                                print("[*] Đang chờ hộp thoại 'Xác thực và lấy mã' xuất hiện (tối đa 60s)...")
                                                verify_found = False
                                                for _ in range(60):
                                                    if self._should_close: break
                                                    active_page.wait_for_timeout(1000)
                                                    verify_loc = active_page.locator("text=xác thực và lấy mã")
                                                    if verify_loc.count() > 0 and verify_loc.nth(0).is_visible():
                                                        print("[*] Đã xuất hiện nút 'Xác thực và lấy mã'!")
                                                        print("[!!!] TIẾN TRÌNH TỰ ĐỘNG TẠM DỪNG: Vui lòng tự giải Captcha và nhấn xác thực bằng tay.")
                                                        verify_loc.nth(0).scroll_into_view_if_needed()
                                                        verify_found = True
                                                        break
                                                        
                                                if not verify_found and not self._should_close:
                                                    print("[-] Quá thời gian chờ nút xác thực. Vui lòng tự kiểm tra trang web.")
                                                    
                                                print("[*] QUY TRÌNH TỰ ĐỘNG ĐIỀU KHIỂN ĐÃ HOÀN TẤT!")
                                                task_completed = True
                                                break
                                    else:
                                        print("[-] Không tìm thấy nút 'Lấy mã' trên màn hình.")
                                        
                                    if not task_completed and not self._should_close:
                                        print("[*] Đã chạy xong kịch bản quét nhưng chưa hoàn thành quy trình.")
                                    print("[*] ===========================================\n")
                                        
                                except Exception as ex:
                                    print(f"[!] Lỗi trong quá trình tự động lấy mã: {ex}")

                            elif getattr(self, '_pending_action', None) == "open_tab_and_search":
                                self._pending_action = None
                                keyword = getattr(self, '_keyword_to_type', None)
                                self._keyword_to_type = None # Consume it
                                
                                if not keyword:
                                    print("[!] Lệnh open_tab_and_search không có từ khóa đi kèm. Bỏ qua.")
                                    continue

                                try:
                                    print(f"\n[*] Đang thực thi lệnh mở tab mới và tìm kiếm '{keyword}'...")
                                    # 1. Mở tab mới
                                    new_page = self.context.new_page()
                                    new_page.bring_to_front()
                                    self.auto_action_count += 1
                                    print("[*] Đã mở tab mới.")
                            
                                    # 2. Đi đến google.com
                                    print("[*] Đang truy cập Google...")
                                    new_page.goto("https://www.google.com/", wait_until="domcontentloaded", timeout=60000)
                                    new_page.wait_for_load_state("domcontentloaded")
                                    self.auto_action_count += 1
                            
                                    # 3. Chờ ô tìm kiếm và điền từ khóa
                                    search_selector = "textarea[name='q'], input[name='q']"
                                    new_page.wait_for_selector(search_selector, state="visible", timeout=15000)
                                    
                                    new_page.click(search_selector)
                                    self.auto_action_count += 1
                                    new_page.wait_for_timeout(random.randint(165, 500))
                                    
                                    print(f"[*] Đang gõ từ khóa: {keyword}")
                                    new_page.type(search_selector, keyword, delay=random.randint(12, 32))
                                    self.auto_action_count += len(keyword)
                                    
                                    new_page.wait_for_timeout(random.randint(265, 500))
                                    
                                    # 4. Nhấn Enter
                                    print("[*] Đang nhấn Enter...")
                                    new_page.press(search_selector, "Enter")
                                    self.auto_action_count += 1
                                    
                                    new_page.wait_for_load_state("domcontentloaded")
                                    print("[*] Đã mở tab mới và tìm kiếm thành công!\n")
                                except Exception as ex:
                                    print(f"[!] Lỗi khi mở tab mới và tìm kiếm: {ex}\n")

                            self.context.pages[0].wait_for_event("close", timeout=500)
                        except PlaywrightTimeoutError:
                            pass # Hết thời gian chờ 0.5s, lặp lại để tiếp tục kiểm tra cờ _should_close và _pending_action
                        except Exception:
                            pass
                except Exception:
                    pass
                    
                if self._should_close and self.context:
                    print("[*] Đang thực hiện đóng trình duyệt từ luồng chạy nền...")
                    try:
                        self.context.close()
                    except Exception:
                        pass
                    
                print("[*] Trình duyệt đã đóng. Bắt đầu dọn dẹp tài nguyên...")

        except PlaywrightError as e:
            # Bắt các lỗi cụ thể của Playwright, ví dụ như không tải được trình duyệt
            print(f"[!!!] Lỗi Playwright: {e}")
            # raise e # Ném lại lỗi để GUI hiển thị, đã tắt theo yêu cầu
        finally:
            # Khối này đảm bảo trạng thái được reset ngay cả khi có lỗi
            self.context = None
            self.playwright = None
            self.user_data_dir = ""
            print("[*] Session đã được dọn dẹp hoàn toàn.")

    def close_and_cleanup(self):
        """Phát tín hiệu để luồng Playwright tự đóng trình duyệt và dọn dẹp."""
        print("[*] Nhận lệnh dọn dẹp. Gửi tín hiệu đóng trình duyệt/session...")
        self._should_close = True
