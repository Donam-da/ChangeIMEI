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
        self._pending_action = None

    def _load_proxies(self):
        """Đọc danh sách proxy từ file txt"""
        proxy_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'proxies.txt')
        if not os.path.exists(proxy_path):
            return []
        with open(proxy_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    def run_session_and_wait(self, target_url, use_proxy, on_launch_callback, device_profile=None):
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

        if device_profile is None:
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
                            "--disable-infobars",
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
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
                            "--disable-infobars",
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
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
                    f"// --- CHỐNG NHẬN DIỆN BOT NÂNG CAO ---\n"
                    f"// 1. Xóa hoàn toàn dấu vết Webdriver\n"
                    f"Object.defineProperty(Object.getPrototypeOf(navigator), 'webdriver', {{ get: () => undefined, set: () => {{}} }});\n"
                    f"// 2. Xóa các biến toàn cục do Playwright tạo ra\n"
                    f"delete window.__playwright;\n"
                    f"delete window.__pw_manual;\n"
                    f"delete window.__PW_outOfContext;\n"
                    f"// 3. Giả mạo đối tượng Chrome (Rất nhiều hệ thống Anti-Bot check thuộc tính này)\n"
                    f"if (!window.chrome) window.chrome = {{}};\n"
                    f"window.chrome.app = {{ isInstalled: false, InstallState: {{ DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }}, RunningState: {{ CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }} }};\n"
                    f"window.chrome.runtime = {{ OnInstalledReason: {{ CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' }}, OnRestartRequiredReason: {{ APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' }} }};\n"
                    f"window.chrome.csi = function() {{ return {{ onloadT: Date.now(), startE: Date.now(), pageT: Date.now(), tran: 15 }}; }};\n"
                    f"// 4. Giả mạo số lượng Plugins (Bot thường có 0 plugin)\n"
                    f"Object.defineProperty(navigator, 'plugins', {{ get: () => [1, 2, 3, 4, 5] }});\n"
                    f"Object.defineProperty(navigator, 'mimeTypes', {{ get: () => [1, 2, 3, 4] }});\n"
                    f"// 5. Fake trạng thái Permission (Tránh trả về lỗi bị từ chối mặc định của trình duyệt tự động)\n"
                    f"const originalQuery = window.navigator.permissions.query;\n"
                    f"window.navigator.permissions.query = (parameters) => (parameters.name === 'notifications' ? Promise.resolve({{ state: Notification.permission }}) : originalQuery(parameters));\n"
                    f"// --- Chống nhận diện: Đổi mã băm Canvas Fingerprint thành Độc Nhất ---\n"
                    f"const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;\n"
                    f"HTMLCanvasElement.prototype.toDataURL = function() {{\n"
                    f"    const ctx = this.getContext('2d', {{willReadFrequently: true}});\n"
                    f"    if (ctx) {{ ctx.fillStyle = 'rgba({device_profile['canvas_noise_r']}, {device_profile['canvas_noise_g']}, {device_profile['canvas_noise_b']}, 0.01)'; ctx.fillRect(0, 0, 1, 1); }}\n"
                    f"    return originalToDataURL.apply(this, arguments);\n"
                    f"}};\n"
                    f"// --- Chống nhận diện: Trộn thông số WebGL Fingerprint ---\n"
                    f"const getParameterProxy = new Proxy(WebGLRenderingContext.prototype.getParameter, {{\n"
                    f"    apply: function(target, thisArg, args) {{\n"
                    f"        if (args[0] === 37445) return '{device_profile['webgl_vendor']}';\n"
                    f"        if (args[0] === 37446) return '{device_profile['webgl_renderer']}';\n"
                    f"        return Reflect.apply(target, thisArg, args);\n"
                    f"    }}\n"
                    f"}});\n"
                    f"WebGLRenderingContext.prototype.getParameter = getParameterProxy;\n"
                )

                page = self.context.new_page()
                
                # ĐÃ TẮT apply_stealth(page): Tránh xung đột với khối add_init_script bên trên. Việc ghi đè thông số 2 lần sẽ khiến Google phát hiện ra Bot.
                
                # --- LỚP BẢO VỆ 1: CHẶN POPUP MỚI TẠI CẤP ĐỘ LÕI TRÌNH DUYỆT (PLAYWRIGHT) ---
                def block_new_tabs(new_page):
                    # Nếu trang mới mở ra không phải là tab gốc đang làm nhiệm vụ -> lập tức đóng lại
                    if new_page != page:
                        try:
                            new_page.close()
                            print("[Anti-Detect] Đã tự động đóng một Popup/Tab quảng cáo cố tình mở ra.")
                        except Exception:
                            pass
                self.context.on("page", block_new_tabs)

                # --- ÉP BUỘC TẤT CẢ CHẠY TRÊN 1 TAB DUY NHẤT ---
                page.add_init_script("""
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
                # ---------------------------------------------

                try:
                    # --- BƯỚC WARM-UP: TRÁNH BỊ NHẬN DIỆN LÀ BOT MỞ TAB SIÊU TỐC ---
                    # 1. Khởi động ở trang trắng (cho trình duyệt vài giây để áp dụng toàn bộ thông số ẩn danh)
                    print("[*] Đang làm ấm trình duyệt...")
                    page.goto("about:blank")
                    page.wait_for_timeout(random.randint(1500, 3000))
                    
                    # 2. Truy cập Google theo kịch bản tùy chỉnh thay vì truy cập thẳng link đích
                    print("[*] Truy cập Google...")
                    # Sử dụng domcontentloaded thay vì chờ load xong tất cả ảnh/mạng để giảm tỷ lệ bị Google nghi ngờ
                    page.goto("https://www.google.com/", wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(random.randint(1000, 2500))
                    
                    try:
                        print("[*] Đang mô phỏng hành vi con người (Mouse & Scroll)...")
                        for _ in range(random.randint(3, 5)):
                            x = random.randint(100, v_width - 100)
                            y = random.randint(100, v_height - 100)
                            page.mouse.move(x, y, steps=random.randint(5, 15))
                            page.wait_for_timeout(random.randint(100, 500))
                    except Exception:
                        pass
                        
                    try:
                        print("[*] Đang bắt đầu quy trình tự động tìm kiếm...")
                        
                        search_selector = "textarea[name='q'], input[name='q']"
                        page.wait_for_selector(search_selector, state="visible", timeout=15000)
                        
                        # Click vào ô tìm kiếm để mô phỏng người thật
                        page.click(search_selector)
                        page.wait_for_timeout(random.randint(500, 1500))
                        
                        # Sử dụng hàm type thay vì fill để gõ từng chữ cái với khoảng trễ delay (như người gõ phím)
                        print("[*] Đang gõ từ khóa: moneytask.top")
                        page.type(search_selector, "moneytask.top", delay=random.randint(150, 400))
                        
                        page.wait_for_timeout(random.randint(800, 1500))
                        
                        print("[*] Đang nhấn Enter...")
                        page.press(search_selector, "Enter")
                        
                        page.wait_for_load_state("domcontentloaded")
                        print("[*] Đã tự động hoá thành công quy trình tìm kiếm!")
                        
                        # --- BỔ SUNG: XỬ LÝ GOOGLE RECAPTCHA (NẾU CÓ) ---
                        try:
                            # Chờ xem iframe checkbox của reCAPTCHA có xuất hiện trong vòng 4 giây không
                            page.wait_for_selector("iframe[src*='recaptcha/api2/anchor']", timeout=4000)
                            print("[!] Phát hiện Google reCAPTCHA chặn. Đang thử click tự động...")
                            page.wait_for_timeout(random.randint(1000, 2500))
                            
                            # Sử dụng frame_locator để chọn đúng iframe chứa ô Checkbox
                            recaptcha_frame = page.frame_locator("iframe[src*='recaptcha/api2/anchor']")
                            checkbox = recaptcha_frame.locator(".recaptcha-checkbox-border")
                            
                            if checkbox.count() > 0:
                                checkbox.click()
                                print("[*] Đã tự động click vào ô 'Tôi không phải là người máy'.")
                                page.wait_for_timeout(random.randint(3000, 5000))
                                
                                # Kiểm tra xem bảng chọn hình ảnh (bframe) có hiển thị không
                                challenge_iframe = page.locator("iframe[src*='recaptcha/api2/bframe']")
                                if challenge_iframe.count() > 0 and challenge_iframe.is_visible():
                                    print("[!!!] CẢNH BÁO: Google yêu cầu giải CAPTCHA hình ảnh.")
                                    print("[!!!] Bạn vui lòng chọn hình thủ công (việc tự động giải hình ảnh cần tích hợp API như 2Captcha/Anti-captcha).")
                        except Exception:
                            print("[*] Trạng thái: An toàn (Không bị Google hỏi reCAPTCHA).")
                    except Exception as ex:
                        print(f"[!] Lỗi trong quá trình tự động hóa tác vụ: {ex}")
                        
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
                            # Kiểm tra xem có lệnh từ giao diện gửi xuống không
                            if getattr(self, '_pending_action', None) == "fill_login":
                                self._pending_action = None
                                try:
                                    active_page = self.context.pages[-1]
                                    if "moneytask.top" in active_page.url:
                                        print("[*] Đang thực thi lệnh tự động điền tài khoản...")
                                        # Dùng JavaScript để điền dữ liệu (vượt qua cơ chế chống Bot của React/Vue)
                                        active_page.evaluate("""() => {
                                            const inputs = Array.from(document.querySelectorAll('input'));
                                            const passInput = inputs.find(i => i.type === 'password');
                                            const textInputs = inputs.filter(i => i.type === 'text' || i.type === 'tel' || i.name.includes('phone'));
                                            
                                            let userInput = null;
                                            if (passInput) {
                                                // Tìm ô tài khoản nằm trước ô mật khẩu trong cấu trúc HTML
                                                userInput = textInputs.reverse().find(i => i.compareDocumentPosition(passInput) & Node.DOCUMENT_POSITION_FOLLOWING);
                                            }
                                            if (!userInput && textInputs.length > 0) userInput = textInputs[0];
                                            
                                            // Thủ thuật vượt qua cơ chế State của React/Vue để trang web ghi nhận dữ liệu thật
                                            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                            
                                            if (userInput) {
                                                nativeInputValueSetter.call(userInput, '0855361500');
                                                userInput.dispatchEvent(new Event('input', { bubbles: true }));
                                                userInput.dispatchEvent(new Event('change', { bubbles: true }));
                                                userInput.blur(); // Bỏ focus khỏi ô nhập để làm mất gợi ý
                                            }
                                            if (passInput) {
                                                nativeInputValueSetter.call(passInput, 'Nam523181@');
                                                passInput.dispatchEvent(new Event('input', { bubbles: true }));
                                                passInput.dispatchEvent(new Event('change', { bubbles: true }));
                                                passInput.blur(); // Bỏ focus khỏi ô nhập để làm mất gợi ý
                                            }
                                            
                                            // Giả lập thao tác "click vào khoảng trống" trên màn hình
                                            document.body.click();
                                        }""")
                                        print("[*] Đã điền xong số điện thoại và mật khẩu!")
                                        
                                        # Đợi 0.5s để trang web nhận diện sự thay đổi dữ liệu của các ô input
                                        active_page.wait_for_timeout(500)
                                        
                                        print("[*] Đang tự động tìm và nhấn nút Đăng nhập...")
                                        try:
                                            btn_selectors = "button[type='submit'], button:has-text('Đăng nhập'), button:has-text('Đăng Nhập'), button:has-text('Login'), input[type='submit']"
                                            active_page.click(btn_selectors, timeout=3000)
                                            print("[*] Đã nhấn nút Đăng nhập. Hoàn tất lệnh tự động!")
                                        except Exception:
                                            print("[!] Không tìm thấy nút Đăng nhập tự động. Vui lòng nhấn bằng tay.")
                                    else:
                                        print("[!] Bạn chưa mở trang moneytask.top. Vui lòng vào trang đăng nhập trước khi bấm.")
                                except Exception as ex:
                                    print(f"[!] Lỗi khi điền thông tin: {ex}")
                                    
                            elif getattr(self, '_pending_action', None) == "auto_task":
                                self._pending_action = None
                                try:
                                    active_page = self.context.pages[-1]
                                    print("\n[*] ===========================================")
                                    print("[*] BẮT ĐẦU CHUỖI NHIỆM VỤ LẤY MÁ TỰ ĐỘNG")
                                    
                                    steps = ["Lấy mã step 1", "Lấy mã step 2", "Lấy mã step 3"]
                                    task_completed = False
                                    
                                    for step in steps:
                                        if self._should_close or task_completed: break
                                        
                                        print(f"[*] Đang tìm nút: '{step}'...")
                                        # Tìm nút chứa text tương ứng
                                        step_loc = active_page.locator(f"text='{step}'")
                                        
                                        button_found = False
                                        if step_loc.count() > 0:
                                            for i in range(step_loc.count()):
                                                if step_loc.nth(i).is_visible():
                                                    step_loc.nth(i).scroll_into_view_if_needed()
                                                    active_page.wait_for_timeout(1000)
                                                    step_loc.nth(i).click(timeout=3000)
                                                    button_found = True
                                                    break
                                                    
                                        if button_found:
                                            print(f"[*] Đã nhấn '{step}'. Đang chờ hệ thống đếm ngược...")
                                            
                                            # Vòng lặp chờ tối đa 120 giây cho mỗi step
                                            for _ in range(120):
                                                if self._should_close: break
                                                active_page.wait_for_timeout(1000) # Đợi 1 giây rồi kiểm tra lại
                                                
                                                # 1. Kiểm tra xem có nút "Nhấn để tiếp tục" (Nút Hoàn Thành) chưa
                                                finish_loc = active_page.locator("text='Nhấn để tiếp tục', text='Nhấn Để Tiếp Tục'")
                                                is_finished = False
                                                for i in range(finish_loc.count()):
                                                    if finish_loc.nth(i).is_visible():
                                                        print("[*] Phá hiện nút 'Nhấn để tiếp tục' (Hoàn thành)!")
                                                        finish_loc.nth(i).scroll_into_view_if_needed()
                                                        active_page.wait_for_timeout(500)
                                                        finish_loc.nth(i).click(timeout=3000)
                                                        is_finished = True
                                                        break
                                                if is_finished:
                                                    print("[*] QUY TRÌNH LẤY MÃ ĐÃ HOÀN TẤT!")
                                                    task_completed = True
                                                    break
                                                    
                                                # 2. Nếu chưa hoàn thành, kiểm tra xem có bắt nhấn Link bất kỳ không
                                                link_loc = active_page.locator("text='Nhấn link bất kỳ để tiếp tục', text='Nhấn link bất kì để tiếp tục'")
                                                needs_reload = False
                                                for i in range(link_loc.count()):
                                                    if link_loc.nth(i).is_visible():
                                                        print(f"[!] Web yêu cầu click link. Đang tự động Tải lại trang (F5) để sang {steps[steps.index(step)+1] if step != steps[-1] else 'bước tiếp'}...")
                                                        needs_reload = True
                                                        break
                                                
                                                if needs_reload:
                                                    active_page.reload()
                                                    active_page.wait_for_load_state("domcontentloaded")
                                                    active_page.wait_for_timeout(3000)
                                                    break # Thoát vòng lặp chờ đếm ngược, chuyển sang xử lý step tiếp theo
                                        else:
                                            print(f"[-] Không tìm thấy '{step}' trên màn hình. Có thể đã qua bước này.")
                                            
                                    if not task_completed and not self._should_close:
                                        print("[*] Đã chạy xong kịch bản quét nhưng chưa thấy nút hoàn tất cuối cùng.")
                                    print("[*] ===========================================\n")
                                        
                                except Exception as ex:
                                    print(f"[!] Lỗi trong quá trình tự động lấy mã: {ex}")

                            self.context.pages[0].wait_for_event("close", timeout=500)
                        except PlaywrightTimeoutError:
                            pass # Hết thời gian chờ 0.5s, lặp lại để tiếp tục kiểm tra cờ _should_close và _pending_action
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
