import random

class DeviceFaker:
    """
    Module ChangeIMEI: Chịu trách nhiệm tạo ra các thông số giả mạo 
    để đánh lừa các trang web rằng đây là một thiết bị hoàn toàn mới.
    """
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        ]
        
        self.viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 390, "height": 844} # iPhone 12/13/14
        ]

    def generate_new_device(self):
        """Tạo và trả về một cấu hình thiết bị ngẫu nhiên"""
        viewport = random.choice(self.viewports)
        is_mobile = viewport["width"] < 500
        
        # Lọc User Agent phù hợp với kích thước màn hình (Mobile/PC)
        if is_mobile:
            ua = self.user_agents[3]
        else:
            ua = random.choice(self.user_agents[:3])

        device_profile = {
            "user_agent": ua,
            "viewport": viewport,
            "is_mobile": is_mobile,
            "timezone_id": "America/New_York", # Có thể random hoặc map theo IP proxy
            "locale": "en-US"
        }
        return device_profile
