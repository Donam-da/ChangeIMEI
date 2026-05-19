import os
import shutil
import time

def deep_clean():
    print("==================================================")
    print(" CÔNG CỤ DỌN DẸP SÂU - DEEP CLEAN PROFILES")
    print("==================================================")
    print("[!] CẢNH BÁO: Công cụ này sẽ quét TOÀN BỘ ổ đĩa C:\\")
    print("    để tìm và xóa tận gốc mọi thư mục bắt đầu bằng")
    print("    'Clean_Profile_'. Quá trình có thể mất vài phút.")
    print("==================================================")
    
    confirm = input("Bạn có chắc chắn muốn bắt đầu quét? (y/n): ")
    if confirm.lower() != 'y':
        print("Đã hủy thao tác.")
        input("Nhấn Enter để thoát...")
        return

    target_prefix = "Clean_Profile_"
    root_dir = "C:\\"
    
    deleted_count = 0
    error_count = 0
    
    start_time = time.time()
    print(f"\n[*] Đang quét toàn bộ ổ {root_dir}... (vui lòng kiên nhẫn chờ đợi)")
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Tạo danh sách copy để có thể thay đổi dirnames an toàn trong vòng lặp
        for dirname in list(dirnames):
            if dirname.startswith(target_prefix):
                full_path = os.path.join(dirpath, dirname)
                print(f"[*] Phát hiện thư mục rác: {full_path}")
                try:
                    shutil.rmtree(full_path, ignore_errors=True)
                    if not os.path.exists(full_path):
                        print("    -> Đã xóa thành công.")
                        deleted_count += 1
                    else:
                        print("    -> Lỗi: Không thể xóa hết (có thể Profile đang chạy ngầm).")
                        error_count += 1
                except Exception as e:
                    print(f"    -> Lỗi: {e}")
                    error_count += 1
                
                # Bỏ qua thư mục này để os.walk không quét sâu vào bên trong thư mục vừa bị xóa
                dirnames.remove(dirname)

    elapsed_time = time.time() - start_time
    print("\n==================================================")
    print(" BÁO CÁO KẾT QUẢ DỌN DẸP SÂU")
    print("==================================================")
    print(f"Thời gian quét: {elapsed_time:.2f} giây")
    print(f"Số thư mục rác đã xóa thành công: {deleted_count}")
    if error_count > 0:
        print(f"Số thư mục bị lỗi không thể xóa: {error_count}")
    print("==================================================")
    input("Nhấn Enter để kết thúc...")

if __name__ == "__main__":
    deep_clean()