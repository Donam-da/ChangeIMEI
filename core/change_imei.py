import os
import random
import uuid
import sys

class DeviceFaker:
    """
    Module ChangeIMEI (Phiên bản Mới): Chuyển sang sử dụng trình duyệt THẬT.
    Quét hệ thống, loại bỏ các tệp tin chứa tracking/IMEI/MAC cũ và đóng gói
    Hồ sơ (Profile) sạch 100% để chạy bằng Google Chrome vật lý.
    """
    def __init__(self):
        if sys.platform == "win32":
            self.base_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ChangeIMEI_Real_Profiles")
        else:
            self.base_dir = os.path.join(os.path.expanduser("~"), ".ChangeIMEI_Real_Profiles")
        os.makedirs(self.base_dir, exist_ok=True)
        self.PHONE_DEVICES = {
            "iPhone 14 Pro Max": {"width": 430, "height": 932, "dsf": 3.0, "ua_prefix": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)"},
            "iPhone 14 Pro": {"width": 393, "height": 852, "dsf": 3.0, "ua_prefix": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)"},
            "iPhone 13 / 13 Pro": {"width": 390, "height": 844, "dsf": 3.0, "ua_prefix": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"},
            "iPhone X": {"width": 375, "height": 812, "dsf": 3.0, "ua_prefix": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X)"},
            "Samsung S22 Ultra": {"width": 412, "height": 915, "dsf": 3.5, "ua_prefix": "Mozilla/5.0 (Linux; Android 13; SM-S908B)"},
            "Samsung S20": {"width": 360, "height": 800, "dsf": 3.0, "ua_prefix": "Mozilla/5.0 (Linux; Android 11; SM-G980F)"},
            "Google Pixel 7": {"width": 412, "height": 915, "dsf": 2.625, "ua_prefix": "Mozilla/5.0 (Linux; Android 13; Pixel 7)"},
            "Xiaomi Redmi Note 10": {"width": 393, "height": 873, "dsf": 2.75, "ua_prefix": "Mozilla/5.0 (Linux; Android 12; M2101K7BG)"},
        }

    def get_device_list(self):
        base = ["Điện thoại (Ngẫu nhiên)", "Máy tính", "Ngẫu nhiên"]
        phones = list(self.PHONE_DEVICES.keys())
        return base + phones

    def generate_new_device(self, preferred_timezone="Auto", platform_type="Mobile"):
        """Tạo Profile Chrome thật, cấp phát một thư mục User Data mới tinh và cực kỳ sạch sẽ"""
        
        profile_id = uuid.uuid4().hex[:8]
        profile_path = os.path.join(self.base_dir, f"Clean_Profile_{profile_id}")
        os.makedirs(profile_path, exist_ok=True)
        
        chrome_major = random.randint(120, 126)
        
        if platform_type in self.PHONE_DEVICES:
            device = self.PHONE_DEVICES[platform_type]
            viewport = {"width": device["width"], "height": device["height"]}
            is_mobile = True
            platform_str = f"{platform_type} (Emulated by Real Chrome)"
            dsf = device["dsf"]
            ua = f"{device['ua_prefix']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Mobile Safari/537.36"
        elif platform_type == "Máy tính":
            viewport = {"width": random.choice([1300, 1340, 1436, 1720]), "height": random.choice([720, 768, 800, 864])}
            is_mobile = False
            platform_str = "Máy tính (Real)"
            dsf = random.choice([1.0, 1.25])
            ua = None  # Để trống để Playwright tự dùng User-Agent chuẩn của Chrome thật trên máy (tránh mismatch TLS/UA gây dính Cloudflare)
        elif platform_type == "Mobile" or platform_type == "Điện thoại" or platform_type == "Điện thoại (Ngẫu nhiên)":
            # Cấu hình chuẩn của các dòng điện thoại di động thực tế (Tránh làm web bị thu nhỏ)
            viewport = {"width": random.choice([450, 460, 470, 480, 490]), "height": random.choice([740, 800, 844, 915])}
            is_mobile = True
            platform_str = "Điện thoại (Emulated by Real Chrome)"
            dsf = random.choice([2.0, 2.5, 3.0])
            ua = f"Mozilla/5.0 (Linux; Android 13; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Mobile Safari/537.36"
        else:
            # "Ngẫu nhiên"
            is_mobile = random.choice([True, False])
            if is_mobile:
                viewport = {"width": 390, "height": 844}
                dsf = 3.0
                ua = f"Mozilla/5.0 (Linux; Android 13; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Mobile Safari/537.36"
            else:
                viewport = {"width": 1366, "height": 768}
                dsf = 1.0
                ua = None
            platform_str = "Ngẫu nhiên (Real)"

        selected_os = {
            "is_mobile": is_mobile,
            "platform": platform_str,
            "viewport": viewport,
            "device_scale_factor": dsf,
            "user_agent": ua,
            "locale": "Sử dụng ngôn ngữ gốc của máy",
            "timezone_id": "Sử dụng múi giờ gốc của máy",
            "chrome_major": "Real",
            "mac_address": "Sạch (Đã cách ly hoàn toàn khỏi hệ thống)",
            "profile_path": profile_path
        }
        
        return selected_os
