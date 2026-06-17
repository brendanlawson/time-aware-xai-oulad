import pandas as pd
import os

def load_data(file_name):
    """
    Hàm hỗ trợ tải một file CSV từ thư mục data/raw/
    """
    file_path = os.path.join('data', 'raw', file_name)
    if not os.path.exists(file_path):
        print(f"Không tìm thấy file: {file_path}. Vui lòng đảm bảo bạn đã tải dữ liệu vào thư mục data/raw/")
        return None
    
    print(f"Đang tải {file_name}...")
    return pd.read_csv(file_path)

def main():
    # 1. Tải một số file CSV ví dụ (bạn có thể đổi tên file theo nhu cầu)
    # Các file có sẵn theo OULAD: 'studentInfo.csv', 'courses.csv', 'assessments.csv', 'studentAssessment.csv', v.v.
    df_student = load_data('studentInfo.csv')
    
    if df_student is None:
        return

    print("\n--- XEM TRƯỚC DỮ LIỆU ---")
    print(df_student.head())

    print("\n--- VÍ DỤ QUERY (LỌC DỮ LIỆU) ---")
    
    # Ví dụ 1: Tìm tất cả sinh viên nữ (gender == 'F') có kết quả cuối cùng (final_result) là 'Pass'
    query_1 = df_student[(df_student['gender'] == 'F') & (df_student['final_result'] == 'Pass')]
    print(f"\n1. Số lượng sinh viên nữ đậu (Pass): {len(query_1)}")
    print(query_1[['id_student', 'gender', 'region', 'final_result']].head())

    # Ví dụ 2: Tìm sinh viên học ngành 'AAA' vào kỳ '2013J'
    query_2 = df_student[(df_student['code_module'] == 'AAA') & (df_student['code_presentation'] == '2013J')]
    print(f"\n2. Số lượng sinh viên ngành AAA, kỳ 2013J: {len(query_2)}")
    print(query_2.head())

    # ---------------------------------------------------------
    # VIẾT QUERY CỦA BẠN DƯỚI ĐÂY:
    # ---------------------------------------------------------
    # df_custom_query = df_student[df_student['cột_nào_đó'] == 'giá_trị']
    # print(df_custom_query)

if __name__ == "__main__":
    main()
