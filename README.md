# PDFMarkdownConvert

### Setup
```sh
pip install -r requirements.txt
```
### Run
```sh
streamlit run app.py
```
### Prompt
```sh
TÀI LIỆU ĐẦU VÀO: 
Tôi đã cung cấp cho bạn tài liệu `contract.md` (Software Requirements Specification). Đây là thiết kế kiến trúc và yêu cầu nghiệp vụ cho dự án "PDFMarkdownConvert".

VAI TRÒ CỦA BẠN:
Bạn là một Senior Software Engineer và Python/Streamlit Architect.

NHIỆM VỤ CỦA BẠN:
Hãy đọc kỹ file `contract.md`, đặc biệt chú ý đến Biểu đồ Lớp (Class Diagram), Biểu đồ Tuần tự (Sequence Diagram), và Các quy tắc Regex. Dựa vào đó, hãy lập trình toàn bộ hệ thống này bằng Python.

YÊU CẦU KỸ THUẬT & CẤU TRÚC CODE:
1. Tech Stack: Sử dụng `streamlit` cho UI, `marker-pdf` cho AI OCR, và các thư viện chuẩn của Python (`re`, `os`, `shutil`, `tempfile`, `subprocess`, `zipfile`).
2. Architecture: BẮT BUỘC phải viết code theo mô hình Hướng đối tượng (OOP) và tuân thủ chính xác các Class đã định nghĩa trong Class Diagram của contract. 
   - Không viết code một cục (spaghetti code). 
   - Hãy chia thành các module rõ ràng hoặc cấu trúc các class rõ ràng trong cùng một file `app.py` (hoặc tách ra `services.py`, `utils.py` tùy bạn thấy hợp lý để dễ bảo trì).
3. Core Logic (Rất quan trọng):
   - Chú ý hàm `IDInjector`: Viết đúng logic nối chuỗi và Regex để tiêm `**[ID: xxxx]**` vào file Markdown. Phải xử lý phân biệt được khối Hình ảnh (ID đứng trước) và khối Text/Heading (ID đứng sau tiền tố).
   - Chú ý hàm `AssemblyService`: Viết đúng thuật toán tạo Dictionary từ file Dịch, và đắp Text vào file Gốc. Giữ nguyên link ảnh của file Gốc.
   - Chú ý hàm `MarkdownCleaner`: Quét sạch ID bằng Regex `r'\*\*\[ID:\s*\d+\]\*\*\s*'`.
4. Quản lý tài nguyên: Implement `TempFileManager` cẩn thận để tạo workspace cách ly cho mỗi phiên, nén ZIP đúng cấu trúc, và BẮT BUỘC phải dọn dẹp thư mục tạm sau khi xử lý xong hoặc khi có lỗi xảy ra.
5. Xử lý ngoại lệ: Sử dụng `try...except` khi gọi `subprocess.run()` cho Marker, hiển thị lỗi thân thiện trên Streamlit UI bằng `st.error()`.

KẾT QUẢ BÀN GIAO MONG ĐỢI:
1. Cấu trúc thư mục dự kiến.
2. File `requirements.txt`.
3. Toàn bộ mã nguồn hoàn chỉnh (ví dụ `app.py` và các file liên quan). Hãy code đầy đủ, không sử dụng placeholder kiểu "# TODO: implement this".
4. Hướng dẫn ngắn gọn cách chạy ứng dụng trên local.

Hãy bắt đầu bằng việc xác nhận bạn đã hiểu kiến trúc, sau đó cung cấp code.
```