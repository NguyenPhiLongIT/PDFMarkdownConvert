import streamlit as st
import os
import shutil
import zipfile
from utils import TempFileManager, parse_markdown_with_images
from services import ExtractionService, AssemblyService

# Cấu hình trang
st.set_page_config(page_title="PDF Markdown Convert", layout="wide")
st.title("📄 PDF to Markdown Converter & Translator Assembler")

# Khởi tạo các Service và File Manager trong Session State để dùng chung
if 'temp_manager' not in st.session_state:
    st.session_state.temp_manager = TempFileManager()
    st.session_state.extraction_service = ExtractionService(st.session_state.temp_manager)
    st.session_state.assembly_service = AssemblyService(st.session_state.temp_manager)

temp_manager = st.session_state.temp_manager
extraction_service = st.session_state.extraction_service
assembly_service = st.session_state.assembly_service

# Nút dọn dẹp hệ thống ở Sidebar
with st.sidebar:
    st.header("🛠️ Quản lý hệ thống")
    if st.button("🗑️ Dọn dẹp File Tạm"):
        temp_manager.cleanup_workspace()
        st.success("Đã dọn dẹp sạch sẽ bộ nhớ tạm!")

# Tạo tabs cho 3 chức năng
tab1, tab2, tab3 = st.tabs(["🔍 1. Bóc tách PDF (Marker AI)", "🔗 2. Lắp ráp bản dịch", "📖 3. MD Reader"])

# ============== TAB 1: BÓC TÁCH PDF ==============
with tab1:
    st.header("Bóc tách PDF sang Markdown với ID")
    st.write("Sử dụng Marker AI Engine để phân tích bố cục chuyên sâu.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 Upload File")
        pdf_file = st.file_uploader("Chọn file PDF", type=["pdf"], key="pdf_upload")
        if pdf_file is not None:
            st.success(f"✅ File được chọn: {pdf_file.name}")
    
    with col2:
        st.subheader("⚙️ Cấu hình")
        st.info("Hệ thống sẽ chạy `marker-pdf` ngầm. Tốc độ phụ thuộc vào cấu hình GPU/CPU.")
    
    if st.button("🚀 Bắt đầu bóc tách", key="extract_btn"):
        if pdf_file is not None:
            with st.spinner("⏳ Đang chạy AI Marker để phân tích bố cục. Quá trình này có thể mất vài phút..."):
                try:
                    # Tạo thư mục tạm lưu input
                    input_dir = temp_manager.create_workspace_subdir("input")
                    pdf_path = os.path.join(input_dir, "document.pdf")
                    
                    with open(pdf_path, "wb") as f:
                        f.write(pdf_file.getbuffer())
                    
                    # Chạy luồng trích xuất từ Service
                    zip_path = extraction_service.process_pdf(pdf_path)
                    
                    st.success("✅ Bóc tách và gắn ID thành công!")
                    
                    # Cung cấp nút Download
                    with open(zip_path, "rb") as f:
                        zip_content = f.read()
                    
                    st.download_button(
                        label="📦 Tải file ZIP (Markdown đã gắn ID + Thư mục Ảnh)",
                        data=zip_content,
                        file_name=f"{os.path.splitext(pdf_file.name)[0]}_extracted.zip",
                        mime="application/zip",
                        key="download_zip_extract"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
        else:
            st.warning("⚠️ Vui lòng chọn file PDF trước")

# ============== TAB 2: LẮP RÁP BẢN DỊCH ==============
with tab2:
    st.header("Lắp ráp bản dịch Markdown")
    st.write("Đắp mộng văn bản tiếng Việt vào bộ khung tiếng Anh (bảo toàn 100% vị trí ảnh).")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 File Gốc (English)")
        original_file = st.file_uploader("Chọn file GỐC có ID", type=["md"], key="original_md")
    
    with col2:
        st.subheader("📤 File Dịch (Vietnamese)")
        translated_file = st.file_uploader("Chọn file DỊCH có ID", type=["md"], key="translated_md")
    
    if st.button("🔗 Bắt đầu lắp ráp & Xuất bản", key="build_btn"):
        if original_file is not None and translated_file is not None:
            with st.spinner("⏳ Đang xử lý đối chiếu Dictionary..."):
                try:
                    # Lưu 2 file tạm
                    assembly_dir = temp_manager.create_workspace_subdir("assembly_input")
                    original_path = os.path.join(assembly_dir, "original.md")
                    translated_path = os.path.join(assembly_dir, "translated.md")
                    
                    with open(original_path, "wb") as f:
                        f.write(original_file.getbuffer())
                    with open(translated_path, "wb") as f:
                        f.write(translated_file.getbuffer())
                    
                    # Gọi Service lắp ráp (đã tự động clean sạch ID theo logic của class)
                    final_path = assembly_service.assemble_translated_book(
                        original_md_path=original_path, 
                        translated_md_path=translated_path
                    )
                    
                    st.success("✅ Lắp ráp hoàn hảo! Đã gọt sạch các mã ID rác.")
                    
                    # Tải file hoàn chỉnh
                    with open(final_path, "r", encoding="utf-8") as f:
                        final_content = f.read()
                    
                    st.download_button(
                        label="📥 Tải file Markdown Sách (Hoàn chỉnh)",
                        data=final_content,
                        file_name="final_translated_book.md",
                        mime="text/markdown"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Lỗi trong quá trình lắp ráp: {str(e)}")
        else:
            st.warning("⚠️ Vui lòng tải lên ĐẦY ĐỦ cả 2 file Markdown.")

# ============== TAB 3: MD READER ==============
with tab3:
    st.header("📖 Markdown Reader")
    st.write("Dùng để đọc thử file Markdown thành phẩm có chèn ảnh trực quan.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 Upload File Markdown")
        md_reader_file = st.file_uploader("Chọn file .md", type=["md"], key="md_reader_upload")
    
    with col2:
        st.subheader("🖼️ Upload Thư mục ảnh (ZIP)")
        img_zip_file = st.file_uploader("Chọn file ZIP chứa ảnh", type=["zip"], key="md_reader_images")
    
    if st.button("🔄 Render Hiển thị", key="render_btn"):
        if md_reader_file is not None:
            with st.spinner("⏳ Đang nhúng ảnh vào Markdown..."):
                try:
                    reader_dir = temp_manager.create_workspace_subdir("reader")
                    
                    md_reader_path = os.path.join(reader_dir, md_reader_file.name)
                    with open(md_reader_path, "wb") as f:
                        f.write(md_reader_file.getbuffer())
                    
                    img_reader_dir = os.path.join(reader_dir, "images")
                    os.makedirs(img_reader_dir, exist_ok=True)
                    
                    if img_zip_file is not None:
                        zip_path = os.path.join(reader_dir, "temp.zip")
                        with open(zip_path, "wb") as f:
                            f.write(img_zip_file.getbuffer())
                        
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(reader_dir)
                        
                        for root, _, files in os.walk(reader_dir):
                            if root != img_reader_dir:
                                for file in files:
                                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                                        shutil.copy2(os.path.join(root, file), os.path.join(img_reader_dir, file))
                    
                    with open(md_reader_path, "r", encoding="utf-8") as f:
                        md_content = f.read()
                    
                    html_content = parse_markdown_with_images(md_content, img_reader_dir)
                    
                    st.success("✅ Render thành công!")
                    st.divider()
                    st.markdown(html_content, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
        else:
            st.warning("⚠️ Vui lòng tải file Markdown lên để đọc.")

# ============== FOOTER ==============
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px; margin-top: 30px;'>
    <p>📝 PDF Translation Workflow Assistant | Kiến trúc OOP Module</p>
</div>
""", unsafe_allow_html=True)