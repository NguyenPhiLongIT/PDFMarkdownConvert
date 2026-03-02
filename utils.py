import fitz  # PyMuPDF
import os
import re
import base64
from pathlib import Path

def extract_pdf_to_markdown_with_ids(input_pdf, output_md, img_dir):
    """
    Bóc tách PDF sang Markdown với ID và trích xuất hình ảnh
    """
    # Tạo thư mục chứa ảnh nếu chưa có
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    doc = fitz.open(input_pdf)
    md_lines = []
    element_id = 1  # Bộ đếm ID bắt đầu từ 1

    print(f"🚀 Bắt đầu bóc tách {len(doc)} trang...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Dùng get_text("dict") để lấy thông tin cực chi tiết bao gồm cả font size và hình ảnh
        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            # 1. NẾU LÀ KHỐI VĂN BẢN (Text)
            if b["type"] == 0:  
                text_content = ""
                max_fontsize = 0
                
                # Gom chữ trong block và tìm font size lớn nhất để đoán tiêu đề
                for line in b["lines"]:
                    for span in line["spans"]:
                        text_content += span["text"] + " "
                        if span["size"] > max_fontsize:
                            max_fontsize = span["size"]
                
                text_content = text_content.strip()
                
                if text_content: # Bỏ qua các khối rỗng
                    # Logic đơn giản đoán Heading dựa trên Font Size (Bạn có thể tinh chỉnh)
                    prefix = ""
                    if max_fontsize > 14:
                        prefix = "## "  # Tiêu đề lớn
                    elif max_fontsize > 12:
                        prefix = "### " # Tiêu đề phụ
                    
                    # Gán ID và định dạng Markdown
                    formatted_block = f"**[ID: {element_id:04d}]** {prefix}{text_content}\n\n"
                    md_lines.append(formatted_block)
                    element_id += 1

            # 2. NẾU LÀ KHỐI HÌNH ẢNH (Image)
            elif b["type"] == 1: 
                image_bytes = b["image"]
                img_extension = b["ext"]
                img_filename = f"img_{element_id:04d}.{img_extension}"
                img_filepath = os.path.join(img_dir, img_filename)
                
                # Lưu ảnh ra thư mục
                with open(img_filepath, "wb") as img_file:
                    img_file.write(image_bytes)
                
                # Tạo thẻ chèn ảnh trong Markdown
                formatted_block = f"**[ID: {element_id:04d}]** ![{img_filename}]({img_dir}/{img_filename})\n\n"
                md_lines.append(formatted_block)
                element_id += 1

    # Ghi toàn bộ nội dung ra file Markdown
    with open(output_md, "w", encoding="utf-8") as f:
        f.writelines(md_lines)

    doc.close()
    print(f"✅ Hoàn tất! File Markdown lưu tại: {output_md}")
    print(f"🖼️ Toàn bộ hình ảnh đã được trích xuất vào thư mục: {img_dir}/")

def build_final_markdown(original_md, translated_md, final_md, remove_ids=True):
    """
    Lắp ráp bản dịch tiếng Việt vào khung tiếng Anh gốc, bảo vệ link ảnh
    """
    # 1. Đọc file bản dịch tiếng Việt và đưa vào Từ điển (Dictionary) map theo ID
    translation_dict = {}
    with open(translated_md, 'r', encoding='utf-8') as f:
        translated_content = f.read()

    # Tách các khối bằng dấu xuống dòng kép
    translated_blocks = translated_content.split('\n\n')
    for block in translated_blocks:
        # Lọc ID và phần chữ tiếng Việt
        match = re.match(r'\*\*\[ID:\s*(\d+)\]\*\*\s*(.*)', block.strip(), flags=re.DOTALL)
        if match:
            block_id = match.group(1)
            text_content = match.group(2).strip()
            translation_dict[block_id] = text_content

    # 2. Đọc file Markdown gốc (bản chuẩn chứa toàn bộ link ảnh)
    with open(original_md, 'r', encoding='utf-8') as f:
        original_content = f.read()

    original_blocks = original_content.split('\n\n')
    final_blocks = []

    print(f"🚀 Bắt đầu quá trình lắp ráp file Markdown hoàn chỉnh...")

    # 3. Lắp ráp: Trộn chữ tiếng Việt vào khung ảnh gốc
    for block in original_blocks:
        block = block.strip()
        if not block:
            continue

        match = re.match(r'\*\*\[ID:\s*(\d+)\]\*\*\s*(.*)', block, flags=re.DOTALL)
        if match:
            block_id = match.group(1)
            original_text = match.group(2).strip()

            # Xử lý khối Hình Ảnh: Bảo vệ tuyệt đối link ảnh gốc
            if original_text.startswith('!['):
                if remove_ids:
                    final_blocks.append(original_text)
                else:
                    final_blocks.append(block)
            
            # Xử lý khối Văn Bản: Bốc chữ tiếng Việt đắp vào
            else:
                if block_id in translation_dict:
                    vietnamese_text = translation_dict[block_id]
                    if remove_ids:
                        final_blocks.append(vietnamese_text)
                    else:
                        final_blocks.append(f"**[ID: {block_id}]** {vietnamese_text}")
                else:
                    # Fallback dự phòng: Nếu đoạn nào bị rớt mạng sót bản dịch, giữ nguyên tiếng Anh
                    if remove_ids:
                        final_blocks.append(original_text)
                    else:
                        final_blocks.append(block)
        else:
            # Các khối bị lỗi hoặc không có ID (nếu có)
            final_blocks.append(block)

    # 4. Lưu ra file Markdown cuối cùng, sạch sẽ
    with open(final_md, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(final_blocks) + '\n')

    print(f"✅ Lắp ráp thành công! File sách hoàn chỉnh đã được lưu tại: {final_md}")

def parse_markdown_with_images(md_content, img_dir):
    """
    Parse Markdown content và thay thế đường dẫn ảnh bằng base64 embedded images
    để hiển thị đầy đủ trên Streamlit
    """
    lines = md_content.split('\n')
    processed_lines = []
    
    for line in lines:
        # Tìm các pattern ảnh trong Markdown: ![alt text](path/to/image)
        # Pattern: ![...](...)
        img_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
        
        def replace_img(match):
            alt_text = match.group(1)
            img_path = match.group(2)
            
            # Lấy tên file từ đường dẫn
            img_filename = os.path.basename(img_path)
            
            # Tìm ảnh trong thư mục
            full_img_path = None
            if os.path.exists(img_path):
                full_img_path = img_path
            else:
                # Tìm trong img_dir
                potential_path = os.path.join(img_dir, img_filename)
                if os.path.exists(potential_path):
                    full_img_path = potential_path
                else:
                    # Tìm trong thư mục con
                    for root, dirs, files in os.walk(img_dir):
                        if img_filename in files:
                            full_img_path = os.path.join(root, img_filename)
                            break
            
            # Nếu tìm được ảnh, chuyển thành base64
            if full_img_path and os.path.exists(full_img_path):
                try:
                    with open(full_img_path, 'rb') as f:
                        img_data = f.read()
                    b64_img = base64.b64encode(img_data).decode('utf-8')
                    
                    # Xác định loại ảnh
                    ext = os.path.splitext(full_img_path)[1].lower()
                    mime_type = {
                        '.png': 'image/png',
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.gif': 'image/gif',
                        '.bmp': 'image/bmp',
                        '.webp': 'image/webp'
                    }.get(ext, 'image/png')
                    
                    # Trả về HTML img tag với base64 data
                    return f'<img src="data:{mime_type};base64,{b64_img}" alt="{alt_text}" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0;">'
                except Exception as e:
                    print(f"Lỗi xử lý ảnh {full_img_path}: {str(e)}")
                    return match.group(0)
            else:
                # Nếu không tìm được ảnh, giữ nguyên link
                return match.group(0)
        
        # Replace tất cả ảnh trong dòng
        processed_line = re.sub(img_pattern, replace_img, line)
        processed_lines.append(processed_line)
    
    result = '\n'.join(processed_lines)
    return result
