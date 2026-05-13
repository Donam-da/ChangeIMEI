import os
import random
from playwright.sync_api import sync_playwright

try:
    from playwright_stealth import stealth_sync
except ImportError:
    try:
        from playwright_stealth import stealth as stealth_sync
    except ImportError:
        def stealth_sync(page):
            pass

from core.change_imei import DeviceFaker

class BrowserEngine:
    def __init__(self):
        self.device_faker = DeviceFaker()
        self.proxies = self._load_proxies()

    def _load_proxies(self):
        """Đọc danh sách proxy từ file txt"""
        proxy_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'proxies.txt')
        if not os.path.exists(proxy_path):
            return []
        with open(proxy_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    def launch_session(self, target_url="https://bot.sannysoft.com/", use_proxy=True):
        """Khởi chạy một phiên làm việc (Session) hoàn toàn mới"""
        
        # 1. Lấy thông số thiết bị mới (Change IMEI/Fingerprint)
        device_profile = self.device_faker.generate_new_device()
        print(f"[*] ChangeIMEI Thành công. Đang giả lập thiết bị: \n    {device_profile['user_agent'][:60]}...")
        print(f"    Màn hình: {device_profile['viewport']['width']}x{device_profile['viewport']['height']}")

        # 2. Chọn ngẫu nhiên Proxy (nếu có và được yêu cầu)
        proxy_settings = None
        if use_proxy and self.proxies:
            selected_proxy = random.choice(self.proxies)
            proxy_settings = {"server": selected_proxy}
            print(f"[*] Đã đổi IP sang Proxy: {selected_proxy}")
        elif not use_proxy:
            print("[!] Yêu cầu dùng IP thật (Bypass Link). Bỏ qua Proxy.")
        else:
            print("[!] Không tìm thấy Proxy, đang dùng IP thật của máy.")

        # 3. Khởi chạy Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-webrtc-hw-encoding"
                ]
            )

            # Tạo Context sạch sẽ (Không lưu cookie, không chung chạ với phiên trước)
            context = browser.new_context(
                user_agent=device_profile["user_agent"],
                viewport=device_profile["viewport"],
                timezone_id=device_profile["timezone_id"],
                locale=device_profile["locale"],
                is_mobile=device_profile["is_mobile"],
                proxy=proxy_settings
            )

            # Mở tab mới và gắn Stealth để chống Anti-bot
            page = context.new_page()
            stealth_sync(page)
            
            print(f"[*] Đang mở trang web: {target_url}")
            page.goto(target_url)

            print("=====================================================")
            print("Trình duyệt đang mở! Bạn có thể thao tác tay.")
            print("Đóng cửa sổ trình duyệt để kết thúc và XÓA SẠCH session.")
            print("=====================================================")
            
            # Đợi người dùng đóng trình duyệt thủ công
            page.wait_for_event("close", timeout=0)
            
            context.close()
            browser.close()
            print("[*] Đã đóng trình duyệt và dọn dẹp sạch sẽ Cookie/Cache.")
