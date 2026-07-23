# Kịch bản demo Dashboard — ~90 giây (khớp slide 9–10)

Người trình: **Người B** · App: `dashboard/app.py` (mô hình vận hành: XGBoost)

Format: **[BẤM]** = thao tác · **[NÓI]** = lời thoại.

---

## Chuẩn bị TRƯỚC khi lên sân khấu (bắt buộc)

```
C:/Users/phank/anaconda3/python.exe -m streamlit run dashboard/app.py
```

- Để sẵn: **mốc 40%** · **lọc "còn đang học" đang BẬT** · đã **bấm 1 sinh viên** một lần cho nạp cache.
- Mở đúng trạng thái đó rồi để yên. Lên demo là bấm tiếp, **không chờ load**.
- Lý do: lần chấm đầu tính SHAP cho >6.000 em nên chậm vài chục giây — không để chết máy trên sân khấu.

---

## Màn 1 — Danh sách hành động (nối từ slide 9) · ~25s

**[BẤM]** Chỉ tay vào sidebar (không đổi gì).
**[NÓI]** "Đây là công cụ cho giảng viên. Mô hình đã chốt là XGBoost — bản thắng
benchmark có kiểm định, không phải để người dùng tự chọn. Đang xem tại mốc 40% khóa học."

**[BẤM]** Chỉ vào panel **"Độ tin cậy tại mốc này"**.
**[NÓI]** "Đây chính là slide 9 chạy thật: nhóm còn-đang-học recall **0.678**, kèm khoảng
tin cậy 95% — gắn dấu ⚠️ vì **chưa đạt** chuẩn 0.80. Trong khi toàn bộ ghi danh là
**0.811**, dấu ✅. Cùng một mô hình, khác nhau ở chỗ chấm trên ai."

---

## Màn 2 — Vì sao em này bị gắn cờ (slide 10) · ~25s

**[BẤM]** Bên phải, chọn 1 sinh viên trong danh sách.
**[NÓI]** "App không bắt giảng viên đọc biểu đồ kỹ thuật — nó giải thích bằng câu chữ:
'Số ngày im lặng cao hơn trung vị lớp → tăng nguy cơ'. Đây là SHAP tính riêng cho em này,
chỉ dùng dữ liệu tới mốc 40%."

**[NÓI thêm]** "Và để ý: các lý do đều là **hành vi học tập**, không có giới tính hay
hoàn cảnh — cảnh báo công bằng theo thiết kế."

---

## Màn 3 — Khoảnh khắc "wow": hiệu ứng dân số · ~25s

**[BẤM]** Sidebar → **TẮT** nút "Chỉ hiện SV còn đang học".
**[NÓI]** "Giờ tôi bật cả những em đã rút môn." *(Cảnh báo vàng "X em đã rút môn" hiện ra.)*
"Những em này quá dễ đoán vì đã ngồi im — chính họ làm điểm bị phồng lên. Bật/tắt một nút là
thấy đúng phần chênh lệch ở slide 9. Bọn em để mặc định BẬT lọc, để không bao giờ dẫn giảng
viên đi liên hệ người đã rời lớp."

---

## Màn 4 — Chốt: trung thực + hành động được · ~15s

**[BẤM]** Kéo thanh **"Tiến độ khóa học" → 100%**.
**[NÓI]** "Đến cuối khóa, nhóm còn-học mới đạt **0.841** ✅ — đó là con số trung thực bọn em
báo cáo."

**[BẤM]** Bấm **⬇️ Tải danh sách ưu tiên (CSV)**.
**[NÓI]** "Và giảng viên tải được danh sách để hành động ngay. Đó là toàn bộ: nghiên cứu chặt,
mà dùng được thật."

---

## Câu cứu nguy nếu máy lag

> "Lần chấm đầu hơi lâu vì nó đang tính SHAP cho hơn 6.000 em — trong lúc chờ, con số các
> anh/chị sẽ thấy là…" *(rồi đọc số ở Màn 1).*

## Số phải thuộc (phòng khi không đọc kịp màn hình)

| Mốc | Nhóm còn học | Toàn bộ ghi danh | Gap |
|-----|--------------|------------------|-----|
| t = 40%  | **0.678** ⚠️ | **0.811** ✅ | **0.133** |
| t = 100% | **0.841** ✅ | **0.930** ✅ | **0.089** |

Chuẩn đáng tin cậy: recall ≥ 0.80 **và** PR-AUC ≥ 0.80.
