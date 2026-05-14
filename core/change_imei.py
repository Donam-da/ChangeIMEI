import random

class DeviceFaker:
    """
    Module ChangeIMEI: Chịu trách nhiệm tạo ra các thông số giả mạo 
    để đánh lừa các trang web rằng đây là một thiết bị hoàn toàn mới.
    """
    def __init__(self):
        # Kết hợp Múi giờ và Ngôn ngữ đồng nhất để tăng độ Trust (Vượt reCAPTCHA)
        self.geo_profiles = [
            {"timezone_id": "America/New_York", "locale": "en-US"},
            {"timezone_id": "America/Chicago", "locale": "en-US"},
            {"timezone_id": "America/Los_Angeles", "locale": "en-US"},
            {"timezone_id": "Europe/London", "locale": "en-GB"},
            {"timezone_id": "Europe/Berlin", "locale": "de-DE"},
            {"timezone_id": "Europe/Paris", "locale": "fr-FR"},
            {"timezone_id": "Asia/Tokyo", "locale": "ja-JP"},
            {"timezone_id": "Australia/Sydney", "locale": "en-AU"}
        ]

    def generate_new_device(self):
        """Sinh trực tiếp (On-the-fly) một cấu hình thiết bị hoàn toàn mới mỗi lần gọi"""
        
        # 1. Sinh ngẫu nhiên phiên bản trình duyệt Chrome (VD: Từ Chrome 115 đến 122)
        chrome_major = random.randint(115, 124)
        chrome_version = f"{chrome_major}.0.{random.randint(1000, 9999)}.{random.randint(10, 150)}"

        # Đa dạng hóa các dòng điện thoại để mỗi lần tạo là một thiết bị độc nhất
        android_models = [
            f"Pixel {random.randint(4, 8)}", f"Pixel {random.randint(6, 8)} Pro",
            f"SM-G9{random.randint(70, 99)}B", f"SM-S9{random.randint(0, 2)}8B", # Dòng Samsung Galaxy S
            f"SM-A{random.randint(10, 73)}F", # Dòng Samsung Galaxy A
            "Redmi Note 10", "Redmi Note 11", "Redmi Note 12", "Xiaomi 12", "Xiaomi 13", "OnePlus 9", "OnePlus 10 Pro"
        ]
        ios_versions = [
            f"{random.randint(14, 17)}_{random.randint(0, 6)}",
            f"{random.randint(15, 17)}_{random.randint(0, 5)}_{random.randint(1, 3)}"
        ]

        # 2. Sinh ngẫu nhiên Hệ điều hành (OS) và thông số màn hình phù hợp
        os_choices = [
            # --- Mobile OS (Theo yêu cầu, chỉ giả lập điện thoại) ---
            {
                "os_str": f"Linux; Android {random.randint(10, 14)}; {random.choice(android_models)}",
                "platform": "Linux aarch64",
                "is_mobile": True,
                "viewport": {"width": random.choice([360, 384, 390, 393, 412, 428, 432]), 
                             "height": random.choice([800, 824, 844, 850, 892, 915])}
            },
            {
                "os_str": f"iPhone; CPU iPhone OS {random.choice(ios_versions)} like Mac OS X",
                "platform": "iPhone",
                "is_mobile": True,
                "viewport": {"width": random.choice([375, 390, 414, 428]), 
                             "height": random.choice([812, 844, 896, 926])}
            }
        ]
        # Ghi chú: Các cấu hình máy tính/desktop đã được loại bỏ để chỉ tập trung vào điện thoại.

        selected_os = random.choice(os_choices)

        # 3. Lắp ráp User-Agent dựa trên OS và Phiên bản vừa sinh
        if selected_os["is_mobile"] and "iPhone" in selected_os["platform"]:
            user_agent = f"Mozilla/5.0 ({selected_os['os_str']}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{random.randint(15, 17)}.0 Mobile/15E148 Safari/604.1"
        elif selected_os["is_mobile"]: # Android
            user_agent = f"Mozilla/5.0 ({selected_os['os_str']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Mobile Safari/537.36"
        else: # Desktop
            user_agent = f"Mozilla/5.0 ({selected_os['os_str']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"

        # 4. Trả về cấu hình hoàn chỉnh
        geo = random.choice(self.geo_profiles)
        selected_os["user_agent"] = user_agent
        selected_os["locale"] = geo["locale"]
        selected_os["timezone_id"] = geo["timezone_id"]
        selected_os["chrome_major"] = chrome_major
        selected_os["hardware_concurrency"] = random.choice([4, 8, 12, 16])
        selected_os["device_memory"] = random.choice([4, 8])

        return selected_os
