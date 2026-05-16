import random

class DeviceFaker:
    """
    Module ChangeIMEI: Chịu trách nhiệm tạo ra các thông số giả mạo 
    để đánh lừa các trang web rằng đây là một thiết bị hoàn toàn mới.
    """
    def __init__(self):
        # Danh sách 195 quốc gia và ngôn ngữ bản địa tương ứng (Locale)
        self.geo_profiles = [
            # Châu Á
            {"timezone_id": "Asia/Tokyo", "locale": "ja-JP"},
            {"timezone_id": "Asia/Ho_Chi_Minh", "locale": "vi-VN"},
            {"timezone_id": "Asia/Bangkok", "locale": "th-TH"},
            {"timezone_id": "Asia/Seoul", "locale": "ko-KR"},
            {"timezone_id": "Asia/Shanghai", "locale": "zh-CN"},
            {"timezone_id": "Asia/Taipei", "locale": "zh-TW"},
            {"timezone_id": "Asia/Hong_Kong", "locale": "zh-HK"},
            {"timezone_id": "Asia/Singapore", "locale": "en-SG"},
            {"timezone_id": "Asia/Kuala_Lumpur", "locale": "ms-MY"},
            {"timezone_id": "Asia/Jakarta", "locale": "id-ID"},
            {"timezone_id": "Asia/Manila", "locale": "en-PH"},
            {"timezone_id": "Asia/Kolkata", "locale": "en-IN"},
            {"timezone_id": "Asia/Karachi", "locale": "ur-PK"},
            {"timezone_id": "Asia/Dhaka", "locale": "bn-BD"},
            {"timezone_id": "Asia/Colombo", "locale": "si-LK"},
            {"timezone_id": "Asia/Phnom_Penh", "locale": "km-KH"},
            {"timezone_id": "Asia/Vientiane", "locale": "lo-LA"},
            {"timezone_id": "Asia/Yangon", "locale": "my-MM"},
            {"timezone_id": "Asia/Kathmandu", "locale": "ne-NP"},
            {"timezone_id": "Asia/Tehran", "locale": "fa-IR"},
            {"timezone_id": "Asia/Baghdad", "locale": "ar-IQ"},
            {"timezone_id": "Asia/Jerusalem", "locale": "he-IL"},
            {"timezone_id": "Asia/Amman", "locale": "ar-JO"},
            {"timezone_id": "Asia/Kuwait", "locale": "ar-KW"},
            {"timezone_id": "Asia/Beirut", "locale": "ar-LB"},
            {"timezone_id": "Asia/Muscat", "locale": "ar-OM"},
            {"timezone_id": "Asia/Damascus", "locale": "ar-SY"},
            {"timezone_id": "Asia/Aden", "locale": "ar-YE"},
            {"timezone_id": "Asia/Almaty", "locale": "kk-KZ"},
            {"timezone_id": "Asia/Tashkent", "locale": "uz-UZ"},
            {"timezone_id": "Asia/Ulaanbaatar", "locale": "mn-MN"},
            {"timezone_id": "Asia/Dubai", "locale": "ar-AE"},
            {"timezone_id": "Asia/Riyadh", "locale": "ar-SA"},
            {"timezone_id": "Asia/Qatar", "locale": "ar-QA"},
            {"timezone_id": "Asia/Yerevan", "locale": "hy-AM"},
            {"timezone_id": "Asia/Baku", "locale": "az-AZ"},
            {"timezone_id": "Asia/Bahrain", "locale": "ar-BH"},
            {"timezone_id": "Asia/Thimphu", "locale": "dz-BT"},
            {"timezone_id": "Asia/Brunei", "locale": "ms-BN"},
            {"timezone_id": "Asia/Pyongyang", "locale": "ko-KP"},
            {"timezone_id": "Asia/Nicosia", "locale": "el-CY"},
            {"timezone_id": "Asia/Dili", "locale": "pt-TL"},
            {"timezone_id": "Asia/Tbilisi", "locale": "ka-GE"},
            {"timezone_id": "Asia/Bishkek", "locale": "ky-KG"},
            {"timezone_id": "Indian/Maldives", "locale": "dv-MV"},
            {"timezone_id": "Asia/Gaza", "locale": "ar-PS"},
            {"timezone_id": "Asia/Dushanbe", "locale": "tg-TJ"},
            {"timezone_id": "Asia/Ashgabat", "locale": "tk-TM"},
            # Châu Âu
            {"timezone_id": "Europe/London", "locale": "en-GB"},
            {"timezone_id": "Europe/Berlin", "locale": "de-DE"},
            {"timezone_id": "Europe/Paris", "locale": "fr-FR"},
            {"timezone_id": "Europe/Rome", "locale": "it-IT"},
            {"timezone_id": "Europe/Madrid", "locale": "es-ES"},
            {"timezone_id": "Europe/Lisbon", "locale": "pt-PT"},
            {"timezone_id": "Europe/Amsterdam", "locale": "nl-NL"},
            {"timezone_id": "Europe/Zurich", "locale": "de-CH"},
            {"timezone_id": "Europe/Brussels", "locale": "fr-BE"},
            {"timezone_id": "Europe/Vienna", "locale": "de-AT"},
            {"timezone_id": "Europe/Stockholm", "locale": "sv-SE"},
            {"timezone_id": "Europe/Oslo", "locale": "nb-NO"},
            {"timezone_id": "Europe/Copenhagen", "locale": "da-DK"},
            {"timezone_id": "Europe/Helsinki", "locale": "fi-FI"},
            {"timezone_id": "Europe/Dublin", "locale": "en-IE"},
            {"timezone_id": "Europe/Athens", "locale": "el-GR"},
            {"timezone_id": "Europe/Warsaw", "locale": "pl-PL"},
            {"timezone_id": "Europe/Prague", "locale": "cs-CZ"},
            {"timezone_id": "Europe/Budapest", "locale": "hu-HU"},
            {"timezone_id": "Europe/Bucharest", "locale": "ro-RO"},
            {"timezone_id": "Europe/Sofia", "locale": "bg-BG"},
            {"timezone_id": "Europe/Moscow", "locale": "ru-RU"},
            {"timezone_id": "Europe/Kiev", "locale": "uk-UA"},
            {"timezone_id": "Europe/Istanbul", "locale": "tr-TR"},
            {"timezone_id": "Europe/Belgrade", "locale": "sr-RS"},
            {"timezone_id": "Europe/Bratislava", "locale": "sk-SK"},
            {"timezone_id": "Europe/Riga", "locale": "lv-LV"},
            {"timezone_id": "Europe/Vilnius", "locale": "lt-LT"},
            {"timezone_id": "Europe/Tallinn", "locale": "et-EE"},
            {"timezone_id": "Europe/Tirane", "locale": "sq-AL"},
            {"timezone_id": "Europe/Andorra", "locale": "ca-AD"},
            {"timezone_id": "Europe/Skopje", "locale": "mk-MK"},
            {"timezone_id": "Europe/Minsk", "locale": "be-BY"},
            {"timezone_id": "Europe/Sarajevo", "locale": "bs-BA"},
            {"timezone_id": "Europe/Zagreb", "locale": "hr-HR"},
            {"timezone_id": "Atlantic/Reykjavik", "locale": "is-IS"},
            {"timezone_id": "Europe/Vaduz", "locale": "de-LI"},
            {"timezone_id": "Europe/Luxembourg", "locale": "fr-LU"},
            {"timezone_id": "Europe/Malta", "locale": "mt-MT"},
            {"timezone_id": "Europe/Chisinau", "locale": "ro-MD"},
            {"timezone_id": "Europe/Monaco", "locale": "fr-MC"},
            {"timezone_id": "Europe/Podgorica", "locale": "sr-ME"},
            {"timezone_id": "Europe/San_Marino", "locale": "it-SM"},
            {"timezone_id": "Europe/Ljubljana", "locale": "sl-SI"},
            {"timezone_id": "Europe/Vatican", "locale": "it-VA"},
            # Châu Phi
            {"timezone_id": "Africa/Cairo", "locale": "ar-EG"},
            {"timezone_id": "Africa/Johannesburg", "locale": "en-ZA"},
            {"timezone_id": "Africa/Lagos", "locale": "en-NG"},
            {"timezone_id": "Africa/Nairobi", "locale": "sw-KE"},
            {"timezone_id": "Africa/Casablanca", "locale": "ar-MA"},
            {"timezone_id": "Africa/Accra", "locale": "en-GH"},
            {"timezone_id": "Africa/Addis_Ababa", "locale": "am-ET"},
            {"timezone_id": "Africa/Algiers", "locale": "ar-DZ"},
            {"timezone_id": "Africa/Abidjan", "locale": "fr-CI"},
            {"timezone_id": "Africa/Tunis", "locale": "ar-TN"},
            {"timezone_id": "Africa/Luanda", "locale": "pt-AO"},
            {"timezone_id": "Africa/Porto-Novo", "locale": "fr-BJ"},
            {"timezone_id": "Africa/Gaborone", "locale": "en-BW"},
            {"timezone_id": "Africa/Ouagadougou", "locale": "fr-BF"},
            {"timezone_id": "Africa/Bujumbura", "locale": "fr-BI"},
            {"timezone_id": "Atlantic/Cape_Verde", "locale": "pt-CV"},
            {"timezone_id": "Africa/Douala", "locale": "fr-CM"},
            {"timezone_id": "Africa/Ndjamena", "locale": "fr-TD"},
            {"timezone_id": "Indian/Comoro", "locale": "ar-KM"},
            {"timezone_id": "Africa/Brazzaville", "locale": "fr-CG"},
            {"timezone_id": "Africa/Kinshasa", "locale": "fr-CD"},
            {"timezone_id": "Africa/Bangui", "locale": "fr-CF"},
            {"timezone_id": "Africa/Djibouti", "locale": "fr-DJ"},
            {"timezone_id": "Africa/Asmara", "locale": "ti-ER"},
            {"timezone_id": "Africa/Mbabane", "locale": "en-SZ"},
            {"timezone_id": "Africa/Libreville", "locale": "fr-GA"},
            {"timezone_id": "Africa/Banjul", "locale": "en-GM"},
            {"timezone_id": "Africa/Conakry", "locale": "fr-GN"},
            {"timezone_id": "Africa/Malabo", "locale": "es-GQ"},
            {"timezone_id": "Africa/Bissau", "locale": "pt-GW"},
            {"timezone_id": "Africa/Maseru", "locale": "en-LS"},
            {"timezone_id": "Africa/Monrovia", "locale": "en-LR"},
            {"timezone_id": "Africa/Tripoli", "locale": "ar-LY"},
            {"timezone_id": "Indian/Antananarivo", "locale": "mg-MG"},
            {"timezone_id": "Africa/Blantyre", "locale": "en-MW"},
            {"timezone_id": "Africa/Bamako", "locale": "fr-ML"},
            {"timezone_id": "Africa/Nouakchott", "locale": "ar-MR"},
            {"timezone_id": "Indian/Mauritius", "locale": "en-MU"},
            {"timezone_id": "Africa/Maputo", "locale": "pt-MZ"},
            {"timezone_id": "Africa/Windhoek", "locale": "en-NA"},
            {"timezone_id": "Africa/Juba", "locale": "en-SS"},
            {"timezone_id": "Africa/Niamey", "locale": "fr-NE"},
            {"timezone_id": "Africa/Kigali", "locale": "rw-RW"},
            {"timezone_id": "Africa/Sao_Tome", "locale": "pt-ST"},
            {"timezone_id": "Africa/Dakar", "locale": "fr-SN"},
            {"timezone_id": "Indian/Mahe", "locale": "en-SC"},
            {"timezone_id": "Africa/Freetown", "locale": "en-SL"},
            {"timezone_id": "Africa/Mogadishu", "locale": "so-SO"},
            {"timezone_id": "Africa/Khartoum", "locale": "ar-SD"},
            {"timezone_id": "Africa/Dar_es_Salaam", "locale": "sw-TZ"},
            {"timezone_id": "Africa/Lome", "locale": "fr-TG"},
            {"timezone_id": "Africa/Kampala", "locale": "en-UG"},
            {"timezone_id": "Africa/Lusaka", "locale": "en-ZM"},
            {"timezone_id": "Africa/Harare", "locale": "en-ZW"},
            # Châu Mỹ
            {"timezone_id": "America/New_York", "locale": "en-US"},
            {"timezone_id": "America/Toronto", "locale": "en-CA"},
            {"timezone_id": "America/Mexico_City", "locale": "es-MX"},
            {"timezone_id": "America/Sao_Paulo", "locale": "pt-BR"},
            {"timezone_id": "America/Argentina/Buenos_Aires", "locale": "es-AR"},
            {"timezone_id": "America/Bogota", "locale": "es-CO"},
            {"timezone_id": "America/Lima", "locale": "es-PE"},
            {"timezone_id": "America/Santiago", "locale": "es-CL"},
            {"timezone_id": "America/Caracas", "locale": "es-VE"},
            {"timezone_id": "America/Havana", "locale": "es-CU"},
            {"timezone_id": "America/Costa_Rica", "locale": "es-CR"},
            {"timezone_id": "America/Guayaquil", "locale": "es-EC"},
            {"timezone_id": "America/La_Paz", "locale": "es-BO"},
            {"timezone_id": "America/Antigua", "locale": "en-AG"},
            {"timezone_id": "America/Nassau", "locale": "en-BS"},
            {"timezone_id": "America/Barbados", "locale": "en-BB"},
            {"timezone_id": "America/Belize", "locale": "en-BZ"},
            {"timezone_id": "America/Dominica", "locale": "en-DM"},
            {"timezone_id": "America/Santo_Domingo", "locale": "es-DO"},
            {"timezone_id": "America/El_Salvador", "locale": "es-SV"},
            {"timezone_id": "America/Grenada", "locale": "en-GD"},
            {"timezone_id": "America/Guatemala", "locale": "es-GT"},
            {"timezone_id": "America/Guyana", "locale": "en-GY"},
            {"timezone_id": "America/Port-au-Prince", "locale": "fr-HT"},
            {"timezone_id": "America/Tegucigalpa", "locale": "es-HN"},
            {"timezone_id": "America/Jamaica", "locale": "en-JM"},
            {"timezone_id": "America/Managua", "locale": "es-NI"},
            {"timezone_id": "America/Panama", "locale": "es-PA"},
            {"timezone_id": "America/Asuncion", "locale": "es-PY"},
            {"timezone_id": "America/St_Kitts", "locale": "en-KN"},
            {"timezone_id": "America/St_Lucia", "locale": "en-LC"},
            {"timezone_id": "America/St_Vincent", "locale": "en-VC"},
            {"timezone_id": "America/Paramaribo", "locale": "nl-SR"},
            {"timezone_id": "America/Port_of_Spain", "locale": "en-TT"},
            {"timezone_id": "America/Montevideo", "locale": "es-UY"},
            # Châu Đại Dương
            {"timezone_id": "Australia/Sydney", "locale": "en-AU"},
            {"timezone_id": "Pacific/Auckland", "locale": "en-NZ"},
            {"timezone_id": "Pacific/Fiji", "locale": "en-FJ"},
            {"timezone_id": "Pacific/Port_Moresby", "locale": "en-PG"},
            {"timezone_id": "Pacific/Tarawa", "locale": "en-KI"},
            {"timezone_id": "Pacific/Nauru", "locale": "en-NR"},
            {"timezone_id": "Pacific/Palau", "locale": "en-PW"},
            {"timezone_id": "Pacific/Majuro", "locale": "en-MH"},
            {"timezone_id": "Pacific/Guadalcanal", "locale": "en-SB"},
            {"timezone_id": "Pacific/Apia", "locale": "sm-WS"},
            {"timezone_id": "Pacific/Tongatapu", "locale": "to-TO"},
            {"timezone_id": "Pacific/Funafuti", "locale": "en-TV"},
            {"timezone_id": "Pacific/Efate", "locale": "bi-VU"},
            {"timezone_id": "Pacific/Pohnpei", "locale": "en-FM"}
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

    def generate_new_device(self, preferred_timezone="Auto"):
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
        if preferred_timezone and preferred_timezone != "Auto":
            continent_map = {
                "Asia": ["Asia/", "Indian/Maldives"],
                "Europe": ["Europe/", "Atlantic/Reykjavik"],
                "Africa": ["Africa/", "Atlantic/Cape_Verde", "Indian/Comoro", "Indian/Antananarivo", "Indian/Mauritius", "Indian/Mahe"],
                "America": ["America/"],
                "Oceania": ["Australia/", "Pacific/"]
            }
            allowed_prefixes = continent_map.get(preferred_timezone)
            if allowed_prefixes:
                matching_geos = [g for g in self.geo_profiles if any(g["timezone_id"].startswith(p) for p in allowed_prefixes)]
            else:
                matching_geos = [g for g in self.geo_profiles if g["timezone_id"] == preferred_timezone]
                
            if matching_geos:
                geo = random.choice(matching_geos)
            else:
                geo = random.choice(self.geo_profiles)
        else:
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

        # Tạo MAC address ngẫu nhiên (chỉ mang tính chất định danh nội bộ, Web không đọc được MAC qua trình duyệt)
        mac = [0x02, random.randint(0x00, 0xff), random.randint(0x00, 0xff), random.randint(0x00, 0xff), random.randint(0x00, 0xff), random.randint(0x00, 0xff)]
        selected_os["mac_address"] = ':'.join(f"{b:02x}" for b in mac).upper()

        return selected_os
