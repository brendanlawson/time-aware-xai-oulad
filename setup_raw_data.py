import os
import hashlib
import pandas as pd
from datetime import datetime

# Cấu hình đường dẫn
RAW_DIR = './data/raw'
MANIFEST_PATH = os.path.join(RAW_DIR, 'data_manifest.txt')
EXPECTED_FILES = [
    'assessments.csv', 'courses.csv', 'studentAssessment.csv',
    'studentInfo.csv', 'studentRegistration.csv', 'studentVle.csv', 'vle.csv'
]

def calculate_md5(file_path):
    """Tính toán mã băm MD5 cho tệp để kiểm tra tính toàn vẹn."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        # Đọc theo chunk để tránh tràn RAM với tệp lớn
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_size_mb(file_path):
    """Lấy dung lượng tệp tính bằng MB."""
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)

def main():
    print("Bắt đầu quy trình thu thập và lưu trữ bất biến...")
    manifest_lines = []
    manifest_lines.append(f"OULAD Data Manifest - Created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    manifest_lines.append("-" * 60)
    manifest_lines.append(f"{'Tên tệp':<25} | {'Dung lượng (MB)':<15} | {'MD5 Hash'}")
    manifest_lines.append("-" * 60)

    all_passed = True

    for file_name in EXPECTED_FILES:
        file_path = os.path.join(RAW_DIR, file_name)
        
        if not os.path.exists(file_path):
            print(f"LỖI: Không tìm thấy tệp {file_name} trong {RAW_DIR}")
            all_passed = False
            continue

        try:
            # 1. Tính toán siêu dữ liệu
            md5_hash = calculate_md5(file_path)
            size_mb = get_file_size_mb(file_path)
            
            # 2. Kiểm tra khả năng đọc bằng pandas
            # Chỉ đọc 5 dòng đầu để tiết kiệm thời gian và bộ nhớ
            df = pd.read_csv(file_path, nrows=5)
            
            # 3. Chuyển tệp sang chế độ Chỉ-đọc (Read-only)
            # 0o444: Quyền read-only cho Owner, Group, và Others
            os.chmod(file_path, 0o444)
            
            # Ghi nhận vào manifest
            manifest_lines.append(f"{file_name:<25} | {size_mb:<15} | {md5_hash}")
            print(f"Đã xử lý thành công: {file_name}")

        except Exception as e:
            print(f"LỖI khi xử lý {file_name}: {e}")
            all_passed = False

    # Ghi xuất tệp Manifest
    # Nếu file manifest đã tồn tại và là read-only, cần mở quyền ghi trước
    if os.path.exists(MANIFEST_PATH):       
        try:
            with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
                f.write('\n'.join(manifest_lines))
        except PermissionError as e:
            print(f"LỖI: Không thể ghi manifest tại {MANIFEST_PATH}: {e}")
            all_passed = False
        return
    
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(manifest_lines))
    
    # Đặt quyền chỉ đọc cho chính tệp manifest
    os.chmod(MANIFEST_PATH, 0o444)
    print("-" * 40)
    print(f"Đã tạo tệp kê khai tại: {MANIFEST_PATH}")

    if all_passed:
        print("QUY TRÌNH HOÀN TẤT: 7 tệp đã được kiểm tra, khóa quyền và ghi nhận manifest thành công!")
    else:
        print("CẢNH BÁO: Quá trình có lỗi xảy ra, vui lòng kiểm tra lại log.")

if __name__ == "__main__":
    main()