import random

class DeviceFaker:
    """
    Module ChangeIMEI: Chịu trách nhiệm tạo ra các thông số giả mạo 
    để đánh lừa các trang web rằng đây là một thiết bị hoàn toàn mới.
    """
    def __init__(self):
        # Mở rộng Múi giờ và Ngôn ngữ đồng nhất để tạo hàng trăm tổ hợp Geo
        self.geo_profiles = [
            {"timezone_id": "America/New_York", "locale": "en-US"},
            {"timezone_id": "America/Chicago", "locale": "en-US"},
            {"timezone_id": "America/Los_Angeles", "locale": "en-US"},
            {"timezone_id": "America/Toronto", "locale": "en-CA"},
            {"timezone_id": "America/Sao_Paulo", "locale": "pt-BR"},
            {"timezone_id": "Europe/London", "locale": "en-GB"},
            {"timezone_id": "Europe/Berlin", "locale": "de-DE"},
            {"timezone_id": "Europe/Paris", "locale": "fr-FR"},
            {"timezone_id": "Europe/Madrid", "locale": "es-ES"},
            {"timezone_id": "Europe/Rome", "locale": "it-IT"},
            {"timezone_id": "Asia/Tokyo", "locale": "ja-JP"},
            {"timezone_id": "Asia/Ho_Chi_Minh", "locale": "vi-VN"},
            {"timezone_id": "Asia/Bangkok", "locale": "th-TH"},
            {"timezone_id": "Asia/Kolkata", "locale": "en-IN"},
            {"timezone_id": "Australia/Sydney", "locale": "en-AU"},
            {"timezone_id": "Australia/Melbourne", "locale": "en-AU"}
        ]
        
        # Các cặp Card đồ họa (WebGL Vendor & Renderer) thực tế trên Mobile
        self.webgl_combos = [
            ("Qualcomm", "Adreno (TM) 610"), ("Qualcomm", "Adreno (TM) 640"),
            ("Qualcomm", "Adreno (TM) 650"), ("Qualcomm", "Adreno (TM) 730"), 
            ("Qualcomm", "Adreno (TM) 740"), ("ARM", "Mali-G52 MC2"), 
            ("ARM", "Mali-G72 MP3"), ("ARM", "Mali-G77 MC9"), 
            ("ARM", "Mali-G710 MC10"), ("Imagination Technologies", "PowerVR Rogue GE8320"),
            ("Apple Inc.", "Apple GPU"), ("Apple Inc.", "Apple A14 GPU"),
            ("Apple Inc.", "Apple A15 GPU"), ("Apple Inc.", "Apple A16 GPU")
        ]

    def generate_new_device(self):
        """Sinh trực tiếp (On-the-fly) một cấu hình thiết bị hoàn toàn mới mỗi lần gọi"""
        
        # 1. Sinh ngẫu nhiên dải rộng phiên bản trình duyệt Chrome (VD: Từ 100 đến 126)
        chrome_major = random.randint(100, 126)
        chrome_version = f"{chrome_major}.0.{random.randint(4000, 6400)}.{random.randint(50, 200)}"

        # Hàng nghìn tổ hợp mã điện thoại Android bằng cách trộn chuỗi
        android_models = [
            # Google Pixel (Ví dụ: Pixel 6, Pixel 7 Pro, Pixel 5a)
            f"Pixel {random.randint(4, 8)}", f"Pixel {random.randint(6, 8)} Pro", f"Pixel {random.randint(4, 7)}a",
            # Samsung Galaxy S & Note (Ví dụ: SM-G998B, SM-S901U)
            f"SM-G9{random.randint(70, 99)}{random.choice(['B', 'F', 'N', 'U'])}", 
            f"SM-S9{random.randint(0, 2)}{random.randint(1, 8)}{random.choice(['B', 'U', 'N'])}", 
            # Samsung Galaxy A (Ví dụ: SM-A536E)
            f"SM-A{random.randint(10, 73)}{random.choice(['F', 'G', 'M', '0', 'E'])}", 
            # Xiaomi / Redmi (Ví dụ: Redmi Note 12, 2201117TG)
            f"Redmi Note {random.randint(10, 13)}", f"Redmi {random.randint(9, 12)}{random.choice(['A', 'C'])}", 
            f"Xiaomi {random.randint(11, 14)}", f"22{random.randint(0,12)}{random.randint(1111,9999)}{random.choice(['G', 'I', 'C'])}",
            # Oppo / OnePlus / Vivo (Ví dụ: CPH2399, V2130)
            f"CPH{random.randint(2000, 2600)}", f"NE{random.randint(2210, 2215)}", f"V{random.randint(2000, 2300)}"
        ]
        
        ios_versions = [
            f"{random.randint(14, 17)}_{random.randint(0, 6)}",
            f"{random.randint(14, 17)}_{random.randint(0, 5)}_{random.randint(1, 3)}"
        ]
        ios_major_version = random.randint(14, 17)

        # 2. Sinh ngẫu nhiên Hệ điều hành (OS) và thông số màn hình phù hợp
        os_choices = [
            # --- Mobile OS (Theo yêu cầu, chỉ giả lập điện thoại) ---
            {
                "os_str": f"Linux; Android {random.randint(10, 14)}; {random.choice(android_models)}",
                "platform": "Linux aarch64",
                "is_mobile": True,
                "viewport": {"width": random.choice([360, 384, 390, 393, 412, 428, 432]), 
                             "height": random.choice([740, 800, 824, 844, 850, 892, 915, 932])}
            },
            {
                "os_str": f"iPhone; CPU iPhone OS {random.choice(ios_versions)} like Mac OS X",
                "platform": "iPhone",
                "is_mobile": True,
                "viewport": {"width": random.choice([375, 390, 414, 428, 430]), 
                             "height": random.choice([667, 812, 844, 852, 896, 926, 932])}
            }
        ]
        # Ghi chú: Các cấu hình máy tính/desktop đã được loại bỏ để chỉ tập trung vào điện thoại.

        selected_os = random.choice(os_choices)

        # 3. Lắp ráp User-Agent dựa trên OS và Phiên bản vừa sinh
        if selected_os["is_mobile"] and "iPhone" in selected_os["platform"]:
            user_agent = f"Mozilla/5.0 ({selected_os['os_str']}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{ios_major_version}.0 Mobile/15E148 Safari/604.1"
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
        selected_os["device_memory"] = random.choice([4, 6, 8, 12])
        
        # Thông số Card Đồ Họa Độc nhất
        webgl = random.choice(self.webgl_combos)
        selected_os["webgl_vendor"] = webgl[0]
        selected_os["webgl_renderer"] = webgl[1]
        
        # Tọa độ nhiễu màu sắc Canvas Độc nhất cho Profile này
        selected_os["canvas_noise_r"] = random.randint(0, 255)
        selected_os["canvas_noise_g"] = random.randint(0, 255)
        selected_os["canvas_noise_b"] = random.randint(0, 255)

        return selected_os
