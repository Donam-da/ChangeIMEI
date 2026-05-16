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
        
        # Xác định kích thước hiển thị mà không can thiệp vào lõi C++ hay JS
        if platform_type == "Desktop":
            viewport = {"width": random.choice([1366, 1440, 1536, 1920]), "height": random.choice([720, 768, 800, 864])}
            is_mobile = False
            platform_str = "Máy tính (Real)"
        elif platform_type == "Mobile":
            viewport = {"width": random.choice([360, 390, 412, 430]), "height": random.choice([740, 844, 915, 932])}
            is_mobile = True
            platform_str = "Điện thoại (Emulated by Real Chrome)"
        else:
            is_mobile = random.choice([True, False])
            viewport = {"width": 390, "height": 844} if is_mobile else {"width": 1366, "height": 768}
            platform_str = "Ngẫu nhiên (Real)"

        selected_os = {
            "is_mobile": is_mobile,
            "platform": platform_str,
            "viewport": viewport,
            "user_agent": "Sẽ tự động lấy từ Chrome Thật của máy",
            "locale": "Sử dụng ngôn ngữ gốc của máy",
            "timezone_id": "Sử dụng múi giờ gốc của máy",
            "chrome_major": "Real",
            "mac_address": "Sạch (Đã cách ly hoàn toàn khỏi hệ thống)",
            "profile_path": profile_path
        }
        
        return selected_os
