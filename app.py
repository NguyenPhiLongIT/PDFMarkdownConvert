import streamlit as st
import tempfile
import os
import shutil
import zipfile
from utils import extract_pdf_to_markdown_with_ids, build_final_markdown, parse_markdown_with_images

st.set_page_config(page_title="PDF Markdown Convert", layout="wide")
st.title("📄 PDF to Markdown Converter & Translator Assembler")

# Tạo thư mục tạm nếu chưa có
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pdf_markdown_temp")
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Tạo tabs cho 3 chức năng
tab1, tab2, tab3 = st.tabs(["🔍 Bóc tách PDF → Markdown", "🔗 Lắp ráp bản dịch", "📖 MD Reader"])

# ============== TAB 1: BÓC TÁCH PDF ==============
with tab1:
    st.header("Bóc tách PDF sang Markdown với ID")
    st.write("Tải file PDF và tự động trích xuất nội dung, hình ảnh với định danh ID")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 Upload File")
        pdf_file = st.file_uploader("Chọn file PDF", type=["pdf"], key="pdf_upload")
        
        if pdf_file is not None:
            st.success(f"✅ File được chọn: {pdf_file.name}")
    
    with col2:
        st.subheader("⚙️ Cấu hình")
        st.info("Ứng dụng sẽ trích xuất nội dung sang Markdown và ảnh")
    
    if st.button("🚀 Bắt đầu bóc tách", key="extract_btn"):
        if pdf_file is not None:
            with st.spinner("⏳ Đang xử lý..."):
                try:
                    # Lưu PDF tạm vào thư mục tạm
                    session_id = hash(pdf_file.name) % 10000
                    session_dir = os.path.join(TEMP_DIR, f"extract_{session_id}")
                    if not os.path.exists(session_dir):
                        os.makedirs(session_dir)
                    
                    pdf_path = os.path.join(session_dir, "temp_input.pdf")
                    with open(pdf_path, "wb") as f:
                        f.write(pdf_file.getbuffer())
                    
                    md_path = os.path.join(session_dir, "document.md")
                    img_dir = os.path.join(session_dir, "images")
                    
                    # Gọi hàm bóc tách
                    extract_pdf_to_markdown_with_ids(pdf_path, md_path, img_dir)
                    
                    st.success("✅ Bóc tách thành công!")
                    
                    # Tạo file ZIP chứa MD + Images
                    zip_path = os.path.join(session_dir, "output.zip")
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        # Thêm file MD vào ZIP
                        zipf.write(md_path, arcname="document.md")
                        
                        # Thêm thư mục ảnh vào ZIP
                        if os.path.exists(img_dir):
                            for img_file in os.listdir(img_dir):
                                img_full_path = os.path.join(img_dir, img_file)
                                zipf.write(img_full_path, arcname=f"images/{img_file}")
                    
                    # Download nút duy nhất
                    with open(zip_path, "rb") as f:
                        zip_content = f.read()
                    
                    st.download_button(
                        label="📦 Tải file ZIP (Markdown + Ảnh)",
                        data=zip_content,
                        file_name=f"{os.path.splitext(pdf_file.name)[0]}_output.zip",
                        mime="application/zip",
                        key="download_zip_extract"
                    )
                    
                    # Xem trước nội dung Markdown
                    with st.expander("👀 Xem trước nội dung"):
                        with open(md_path, "r", encoding="utf-8") as f:
                            md_content = f.read()
                        st.markdown(md_content[:2000] + "..." if len(md_content) > 2000 else md_content)
                    
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        else:
            st.warning("⚠️ Vui lòng chọn file PDF trước")

# ============== TAB 2: LẮP RÁP BẢN DỊCH ==============
with tab2:
    st.header("Lắp ráp bản dịch Markdown")
    st.write("Trộn nội dung tiếng Việt vào khung tiếng Anh gốc với bảo vệ link hình ảnh")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 File Markdown gốc (English)")
        original_file = st.file_uploader("Chọn file Markdown gốc", type=["md"], key="original_md")
        if original_file is not None:
            st.success(f"✅ {original_file.name}")
    
    with col2:
        st.subheader("📤 File Markdown dịch (Vietnamese)")
        translated_file = st.file_uploader("Chọn file Markdown dịch", type=["md"], key="translated_md")
        if translated_file is not None:
            st.success(f"✅ {translated_file.name}")
    
    st.subheader("⚙️ Cấu hình")
    remove_ids = st.checkbox("Xoá ID sau khi lắp ráp", value=True, help="Nếu chọn, file cuối cùng sẽ không chứa **[ID: xxxx]**")
    
    if st.button("🔗 Bắt đầu lắp ráp", key="build_btn"):
        if original_file is not None and translated_file is not None:
            with st.spinner("⏳ Đang xử lý..."):
                try:
                    # Lưu 2 file tạm
                    original_path = os.path.join(TEMP_DIR, "original_temp.md")
                    translated_path = os.path.join(TEMP_DIR, "translated_temp.md")
                    
                    with open(original_path, "wb") as f:
                        f.write(original_file.getbuffer())
                    with open(translated_path, "wb") as f:
                        f.write(translated_file.getbuffer())
                    
                    # Tạo thư mục kết quả
                    session_id = hash(original_file.name + translated_file.name) % 10000
                    output_dir = os.path.join(TEMP_DIR, f"build_{session_id}")
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    
                    final_path = os.path.join(output_dir, "final.md")
                    
                    # Gọi hàm lắp ráp
                    build_final_markdown(original_path, translated_path, final_path, remove_ids=remove_ids)
                    
                    st.success("✅ Lắp ráp thành công!")
                    
                    # Download file hoàn chỉnh
                    with open(final_path, "r", encoding="utf-8") as f:
                        final_content = f.read()
                    
                    st.download_button(
                        label="📥 Tải file Markdown hoàn chỉnh",
                        data=final_content,
                        file_name="final_document.md",
                        mime="text/markdown"
                    )
                    
                    # Xem trước
                    with st.expander("👀 Xem trước nội dung"):
                        st.markdown(final_content[:2000] + "..." if len(final_content) > 2000 else final_content)
                    
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
        else:
            st.warning("⚠️ Vui lòng chọn cả 2 file Markdown trước")

# ============== TAB 3: MD READER ==============
with tab3:
    st.header("📖 Markdown Reader")
    st.write("Tải file Markdown và thư mục chứa hình ảnh để xem nội dung hoàn chỉnh")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 Upload File Markdown")
        md_reader_file = st.file_uploader("Chọn file .md", type=["md"], key="md_reader_upload")
        if md_reader_file is not None:
            st.success(f"✅ {md_reader_file.name}")
    
    with col2:
        st.subheader("🖼️ Upload Thư mục ảnh (ZIP)")
        img_zip_file = st.file_uploader("Chọn file ZIP chứa ảnh", type=["zip"], key="md_reader_images")
        if img_zip_file is not None:
            st.success(f"✅ {img_zip_file.name}")
    
    if st.button("🔄 Load & Render", key="render_btn"):
        if md_reader_file is not None:
            with st.spinner("⏳ Đang xử lý..."):
                try:
                    # Tạo thư mục session riêng cho reader
                    reader_session_id = hash(md_reader_file.name) % 10000
                    reader_dir = os.path.join(TEMP_DIR, f"reader_{reader_session_id}")
                    if not os.path.exists(reader_dir):
                        os.makedirs(reader_dir)
                    
                    # Lưu file Markdown
                    md_reader_path = os.path.join(reader_dir, md_reader_file.name)
                    with open(md_reader_path, "wb") as f:
                        f.write(md_reader_file.getbuffer())
                    
                    # Xử lý thư mục ảnh nếu có
                    img_reader_dir = os.path.join(reader_dir, "images")
                    if img_zip_file is not None:
                        os.makedirs(img_reader_dir, exist_ok=True)
                        zip_path = os.path.join(reader_dir, "temp.zip")
                        with open(zip_path, "wb") as f:
                            f.write(img_zip_file.getbuffer())
                        
                        # Giải nén
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(reader_dir)
                        
                        # Di chuyển ảnh từ images/ subfolder (nếu có) vào img_reader_dir
                        for root, dirs, files in os.walk(reader_dir):
                            if root != img_reader_dir:
                                for file in files:
                                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                                        src = os.path.join(root, file)
                                        dst = os.path.join(img_reader_dir, file)
                                        if src != dst:
                                            shutil.copy2(src, dst)
                        
                        # Xóa file zip tạm
                        if os.path.exists(zip_path):
                            os.remove(zip_path)
                    
                    # Đọc file Markdown
                    with open(md_reader_path, "r", encoding="utf-8") as f:
                        md_content = f.read()
                    
                    # Parse và render
                    html_content = parse_markdown_with_images(md_content, img_reader_dir)
                    
                    st.success("✅ Render thành công!")
                    st.divider()
                    
                    # Hiển thị nội dung
                    st.markdown(html_content, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        else:
            st.warning("⚠️ Vui lòng chọn file Markdown trước")

# ============== FOOTER ==============
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px; margin-top: 30px;'>
    <p>📝 PDF Markdown Converter v2.0 | Powered by Streamlit & PyMuPDF</p>
</div>
""", unsafe_allow_html=True)
