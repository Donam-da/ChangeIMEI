import sys
from core.browser_engine import BrowserEngine

def main():
    print("=========================================")
    print("   CÔNG CỤ ANTI-DETECT: CHANGE IMEI      ")
    print("=========================================")
    
    engine = BrowserEngine()
    
    while True:
        print("\nMenu:")
        print("1. Mở Trình duyệt ẩn danh (CÓ dùng Proxy trong proxies.txt)")
        print("2. Mở Trình duyệt ẩn danh (KHÔNG dùng Proxy - Dùng IP Thật để vượt link)")
        print("3. Thoát")
        
        choice = input("Chọn chức năng (1-3): ")
        
        if choice == '1' or choice == '2':
            use_proxy = (choice == '1')
            target = input("Nhập link URL muốn mở (Nhấn Enter để mở trang check IP mặc định): ")
            if not target.strip():
                engine.launch_session(use_proxy=use_proxy)
            else:
                engine.launch_session(target_url=target.strip(), use_proxy=use_proxy)
        elif choice == '3':
            print("Cảm ơn bạn đã sử dụng. Tạm biệt!")
            sys.exit(0)
        else:
            print("Lựa chọn không hợp lệ, vui lòng chọn lại.")

if __name__ == "__main__":
    main()
