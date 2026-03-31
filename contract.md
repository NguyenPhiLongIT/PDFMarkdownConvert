# PDFMarkdownConvert
## Tổng quan Dự án (Project Overview)

Mục tiêu: Xây dựng một ứng dụng web hỗ trợ khâu tiền xử lý và hậu xử lý cho quy trình dịch thuật tài liệu PDF phức tạp (chứa biểu đồ, bảng biểu, trích dẫn) sang định dạng Markdown.

Quy trình hoạt động: Hệ thống chia làm 2 giai đoạn độc lập:

- Tiền xử lý (Pre-processing): Dùng AI phân tích PDF, trích xuất văn bản và hình ảnh, sau đó tự động tiêm mã định danh (ID) vào từng khối văn bản tạo thành "khung chuẩn" (template).

- Khâu trung gian (Bên ngoài hệ thống): Người dùng sử dụng template này đem đi dịch thủ công hoặc dùng công cụ bên ngoài (giữ nguyên các mã ID).

- Hậu xử lý (Post-processing): Hệ thống nhận lại bản dịch, tự động đối chiếu mã ID để ráp văn bản tiếng Việt vào khung gốc, giữ nguyên vị trí hình ảnh và cấu trúc, cuối cùng gọt sạch mã ID để xuất bản.
## Use case
![image](/public/images/usecase.png)
```sh
UC-01: Bóc tách PDF và Gắn ID (Extract PDF & Inject IDs)
- Actor: Người dùng (User), AI Marker Engine (Hệ thống phụ trợ).
- Goal: Chuyển đổi tệp PDF thô thành một tệp Markdown có cấu trúc hoàn chỉnh, trích xuất hình ảnh và tự động gắn các mã định danh **[ID: xxxx]** để chuẩn bị cho việc dịch thuật bên ngoài.

Main Flow:
- Người dùng điều hướng đến chức năng "Phân tích & Bóc tách PDF" trên ứng dụng.

- Người dùng tải lên một tệp PDF cần xử lý.

- Người dùng nhấn nút "Bắt đầu bóc tách".

- Hệ thống lưu tệp PDF vào thư mục tạm (temp workspace).

- Hệ thống gọi AI Marker Engine để phân tích bố cục và tạo ra tệp Markdown "sạch" cùng thư mục chứa hình ảnh.

- Hệ thống quét tệp Markdown sạch, sử dụng Regex để tự động tiêm mã **[ID: xxxx]** vào trước mỗi Tiêu đề, Đoạn văn, Trích dẫn, Bảng biểu và Link ảnh.

- Hệ thống đóng gói tệp Markdown (đã gắn ID) và thư mục hình ảnh thành một tệp nén .zip.

- Hệ thống hiển thị thông báo thành công và cung cấp nút tải xuống (Download) tệp .zip.
(Người dùng sau đó sẽ giải nén, lấy file Markdown này mang đi dịch thủ công hoặc nạp vào các phần mềm dịch thuật khác, miễn là giữ nguyên mã ID).
```
```sh
UC-02: Lắp ráp Bản dịch và Dọn dẹp (Assemble Translation & Clean)
- Actor: Người dùng (User).
- Goal: Nhận tệp Markdown đã được người dùng dịch (từ bên ngoài), ráp nội dung tiếng Việt vào khung của tệp gốc để bảo toàn chính xác vị trí hình ảnh và cấu trúc, cuối cùng xóa bỏ các mã ID kỹ thuật.

Main Flow:

- Người dùng điều hướng đến chức năng "Lắp ráp Bản dịch" trên ứng dụng.

- Người dùng tải lên 2 tệp: File Gốc (Markdown tiếng Anh, có ID) và File Bản dịch (Markdown tiếng Việt, có ID, do người dùng tự dịch bên ngoài).

- Người dùng nhấn nút "Lắp ráp".

- Hệ thống quét File Bản dịch và tạo một từ điển (Dictionary) ánh xạ giữa các mã ID và văn bản tiếng Việt tương ứng.

- Hệ thống đọc từng dòng của File Gốc để làm khung chuẩn.

- Hệ thống phân tích từng khối của File Gốc:

- Nếu là khối Hình ảnh: Hệ thống giữ nguyên đường dẫn ảnh của File Gốc.

- Nếu là khối Văn bản: Hệ thống tra cứu ID trong từ điển và thay thế nội dung tiếng Anh bằng nội dung tiếng Việt.

- Hệ thống sử dụng Regex để làm sạch toàn bộ văn bản vừa ráp, loại bỏ hoàn toàn các chuỗi **[ID: xxxx]**.

- Hệ thống tạo ra tệp .md hoàn chỉnh (chỉ chứa nội dung tiếng Việt đã căn chỉnh ảnh), hiển thị thông báo thành công và cung cấp nút tải xuống cho Người dùng.
```

## Sequence diagram
![image](/public/images/sequence1.jpg)
### Chi tiết luồng UC-01
```sh
User → StreamlitUI: uploads PDF file and clicks "Bắt đầu bóc tách"
StreamlitUI → TempFileManager.saveFile(pdfFile)
StreamlitUI → ExtractionService.processPDF(pdfFilePath)
ExtractionService → MarkerEngine.runMarkerCLI(pdfFilePath)
MarkerEngine: AI analyzes layout, extracts text, and crops images
MarkerEngine returns CleanMarkdownFile and ImageFolder
ExtractionService → IDInjector.inject(CleanMarkdownFile)
IDInjector: parses markdown blocks (headings, quotes, lists, images)
IDInjector: prepends **[ID: xxxx]** to each block using Regex
IDInjector returns MarkdownWithIDsFile
ExtractionService → TempFileManager.createZip(MarkdownWithIDsFile, ImageFolder)
TempFileManager returns ZipFilePath
ExtractionService returns ProcessingResult(success, ZipFilePath)
StreamlitUI displays success message
StreamlitUI → User: provides Download button for ZIP file
```
![image](/public/images/sequence2.jpg)
### Chi tiết luồng UC-02
```sh
User → StreamlitUI: uploads OriginalMD, TranslatedMD and clicks "Lắp ráp"
StreamlitUI → TempFileManager.saveFiles(OriginalMD, TranslatedMD)
StreamlitUI → AssemblyService.assembleBook(OriginalMD, TranslatedMD)
AssemblyService: reads TranslatedMD and creates dictionary {ID: VietnameseText}
AssemblyService: iterates through blocks in OriginalMD
AssemblyService: identifies block type (Image vs Text) via Regex prefix
AssemblyService: keeps Original Image links intact
AssemblyService: replaces Original Text with mapped VietnameseText from dictionary
AssemblyService returns AssembledContent (with IDs)
AssemblyService → MarkdownCleaner.stripIDs(AssembledContent)
MarkdownCleaner: applies Regex substitution to remove all **[ID: xxxx]** tags
MarkdownCleaner returns FinalCleanContent
AssemblyService → TempFileManager.saveFile(FinalCleanContent)
TempFileManager returns FinalFilePath
AssemblyService returns AssemblyResult(success, FinalFilePath)
StreamlitUI displays success message
StreamlitUI → User: provides Download button for Final Vietnamese MD file
```

## Class diagram

```sh
classDiagram
    %% Giao dien & Controller chinh
    class StreamlitApp {
        +run()
        +render_extraction_tab()
        +render_assembly_tab()
        -show_success_message(msg: String)
        -show_error_message(msg: String)
    }

    %% Quan ly File & Tai nguyen
    class TempFileManager {
        -workspace_dir: String
        +save_uploaded_file(uploaded_file, filename: String): String
        +read_file(filepath: String): String
        +write_file(filepath: String, content: String)
        +create_zip_archive(source_dir: String, zip_filename: String): String
        +cleanup_workspace()
    }

    %% Cac Service xu ly nghiep vu cho Use Case 01
    class ExtractionService {
        +process_pdf(pdf_filepath: String, output_dir: String): String
    }

    class MarkerEngine {
        -cli_command: String
        +run_layout_analysis(pdf_filepath: String, output_dir: String): String
    }

    class IDInjector {
        -regex_pattern: String
        +inject_ids_to_markdown(clean_md_path: String, output_path: String): int
    }

    %% Cac Service xu ly nghiep vu cho Use Case 02
    class AssemblyService {
        +assemble_translated_book(original_md: String, translated_md: String, final_md: String): boolean
        -build_translation_dictionary(translated_content: String): Map
    }

    class MarkdownCleaner {
        -id_regex_pattern: String
        +strip_all_ids(assembled_content: String): String
    }

    %% Dinh nghia cac moi quan he (Relationships)
    StreamlitApp --> TempFileManager : uses
    StreamlitApp --> ExtractionService : calls
    StreamlitApp --> AssemblyService : calls

    ExtractionService --> MarkerEngine : uses
    ExtractionService --> IDInjector : uses
    ExtractionService --> TempFileManager : uses

    AssemblyService --> MarkdownCleaner : uses
    AssemblyService --> TempFileManager : uses
```

## Định dạng dữ liệu & Quy tắc
1. Cú pháp ID & Tiêm định dạng

- Cú pháp: **[ID: xxxx]** (xxxx là 4 chữ số, bắt đầu từ 0001).

- Vị trí với Hình ảnh: ID đứng trước thẻ ảnh
``` **[ID: 0001]** ![img...](...).```

- Vị trí với Văn bản: Tiền tố định dạng (###, >, -) đứng trước, tiếp theo là ID, cuối cùng là nội dung: ### **[ID: 0005]** Tiêu đề.

2. Biểu thức Chính quy (Regex Patterns)

- Tách khối để lắp ráp: r'^(.*?)\*\*\[ID:\s*(\d+)\]\*\*\s*(.*)' (Lấy được Tiền tố, ID, Nội dung).

- Làm sạch file cuối: r'\*\*\[ID:\s*\d+\]\*\*\s*' (Tìm và thay thế bằng chuỗi rỗng).

## Yêu cầu Phi chức năng (NFRs)
- Khả năng mở rộng: Hệ thống xử lý tệp PDF lên tới 50MB hoặc tối đa 1000 trang.

- Phần cứng: Quá trình Bóc tách (UC-01) yêu cầu máy chủ có GPU (CUDA) để chạy tối ưu model marker-pdf. Quá trình Lắp ráp (UC-02) chỉ thao tác text, tốn chưa tới 1 giây xử lý kể cả trên CPU cấu hình thấp.

- Quản lý phiên bản: Hệ thống phải xóa sạch tệp tạm (temp files) trên server sau khi người dùng tải tệp xuống để tránh đầy ổ cứng.
## Xử lý Ngoại lệ (Exceptions & Edge Cases)
- Thiếu sót ID trong bản dịch: Ở UC-02, nếu người dùng lỡ tay xóa mất một ID (VD: 0015) trong file dịch, hệ thống sẽ kích hoạt Fallback Mode: Lấy nguyên văn đoạn tiếng Anh của ID 0015 từ file gốc điền vào, đảm bảo không bị gãy cấu trúc dòng.

- Lỗi PDF đầu vào: Bắt lỗi subprocess.CalledProcessError nếu file PDF bị khóa mật khẩu hoặc định dạng hỏng, trả thông báo lỗi trực tiếp trên giao diện.
## Giả định & Ràng buộc (Assumptions & Dependencies)
- Trách nhiệm của Người dịch: Để UC-02 hoạt động đúng, file bản dịch đầu vào bắt buộc không được thay đổi, xóa bỏ hay làm biến dạng cú pháp chuỗi **[ID: xxxx]**.

- Quản lý Hình ảnh: Ở bước lắp ráp, hệ thống lấy link ảnh 100% từ file gốc, do đó người dùng có thể thoải mái xóa hoặc làm hỏng dòng chứa link ảnh bên file dịch mà không bị ảnh hưởng.

- Đường dẫn tương đối: Người dùng cần giữ tệp .md thành phẩm nằm cùng cấp với thư mục images/ đã giải nén ở bước 1 để hiển thị ảnh.