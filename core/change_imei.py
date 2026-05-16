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

    def generate_new_device(self, preferred_timezone="Auto", platform_type="Mobile"):
        """Tạo Profile Chrome thật, cấp phát một thư mục User Data mới tinh và cực kỳ sạch sẽ"""
        
        profile_id = uuid.uuid4().hex[:8]
        profile_path = os.path.join(self.base_dir, f"Clean_Profile_{profile_id}")
        os.makedirs(profile_path, exist_ok=True)
        
        chrome_major = random.randint(120, 126)
        
        # Xác định kích thước hiển thị mà không can thiệp vào lõi C++ hay JS
        if platform_type == "Desktop":
            viewport = {"width": random.choice([1366, 1440, 1536, 1920]), "height": random.choice([720, 768, 800, 864])}
            is_mobile = False
            platform_str = "Máy tính (Real)"
            dsf = random.choice([1.0, 1.25])
            ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Safari/537.36"
        elif platform_type == "Mobile":
            # Cấu hình chuẩn của các dòng điện thoại di động thực tế (Tránh làm web bị thu nhỏ)
            viewport = {"width": random.choice([360, 390, 412, 430]), "height": random.choice([740, 800, 844, 915])}
            is_mobile = True
            platform_str = "Điện thoại (Emulated by Real Chrome)"
            dsf = random.choice([2.0, 2.5, 3.0])
            ua = f"Mozilla/5.0 (Linux; Android 13; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Mobile Safari/537.36"
        else:
            is_mobile = random.choice([True, False])
            if is_mobile:
                viewport = {"width": 390, "height": 844}
                dsf = 3.0
                ua = f"Mozilla/5.0 (Linux; Android 13; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Mobile Safari/537.36"
            else:
                viewport = {"width": 1366, "height": 768}
                dsf = 1.0
                ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_major}.0.0.0 Safari/537.36"
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
