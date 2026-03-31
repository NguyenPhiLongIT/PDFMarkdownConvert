import os
import shutil
import tempfile
import zipfile
import base64
import re
import uuid
from typing import List

class TempFileManager:
    """Class quản lý file tạm thời, dọn dẹp không gian lưu trữ (Workspace)"""
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            self.workspace_dir = os.path.join(tempfile.gettempdir(), "pdf_translation_workspace")
        else:
            self.workspace_dir = base_dir
        os.makedirs(self.workspace_dir, exist_ok=True)

    def create_workspace_subdir(self, prefix: str) -> str:
        """Tạo một thư mục con ngẫu nhiên cho mỗi phiên làm việc"""
        session_id = uuid.uuid4().hex[:8]
        subdir = os.path.join(self.workspace_dir, f"{prefix}_{session_id}")
        os.makedirs(subdir, exist_ok=True)
        return subdir

    def create_zip_archive(self, output_dir: str, zip_filename: str, include_files: List[str] = None, include_dirs: List[str] = None) -> str:
        """Đóng gói file và thư mục thành 1 file ZIP"""
        zip_path = os.path.join(output_dir, zip_filename)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Thêm các file đơn lẻ
            if include_files:
                for fpath in include_files:
                    if os.path.exists(fpath):
                        zipf.write(fpath, arcname=os.path.basename(fpath))
            
            # Thêm toàn bộ thư mục (ví dụ: thư mục images)
            if include_dirs:
                for dpath in include_dirs:
                    if os.path.exists(dpath):
                        for root, _, files in os.walk(dpath):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # Giữ nguyên cấu trúc thư mục con (VD: images/img_001.jpg)
                                arcname = os.path.relpath(file_path, os.path.dirname(dpath))
                                zipf.write(file_path, arcname=arcname)
        return zip_path
        
    def cleanup_workspace(self):
        """Xóa toàn bộ thư mục làm việc tạm thời"""
        if os.path.exists(self.workspace_dir):
            shutil.rmtree(self.workspace_dir)
            os.makedirs(self.workspace_dir, exist_ok=True)


def parse_markdown_with_images(md_content: str, img_dir: str) -> str:
    """
    Parse Markdown content và thay thế đường dẫn ảnh bằng base64 embedded images
    để hiển thị đầy đủ trên giao diện Streamlit (Dành riêng cho Tab 3)
    """
    lines = md_content.split('\n')
    processed_lines = []
    
    img_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    
    def replace_img(match):
        alt_text = match.group(1)
        img_path = match.group(2)
        img_filename = os.path.basename(img_path)
        
        full_img_path = None
        if os.path.exists(img_path):
            full_img_path = img_path
        else:
            potential_path = os.path.join(img_dir, img_filename)
            if os.path.exists(potential_path):
                full_img_path = potential_path
            else:
                for root, _, files in os.walk(img_dir):
                    if img_filename in files:
                        full_img_path = os.path.join(root, img_filename)
                        break
        
        if full_img_path and os.path.exists(full_img_path):
            try:
                with open(full_img_path, 'rb') as f:
                    img_data = f.read()
                b64_img = base64.b64encode(img_data).decode('utf-8')
                
                ext = os.path.splitext(full_img_path)[1].lower()
                mime_type = {
                    '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif', '.bmp': 'image/bmp', '.webp': 'image/webp'
                }.get(ext, 'image/png')
                
                return f'<img src="data:{mime_type};base64,{b64_img}" alt="{alt_text}" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0;">'
            except Exception as e:
                print(f"Lỗi xử lý ảnh {full_img_path}: {str(e)}")
                return match.group(0)
        else:
            return match.group(0)
            
    for line in lines:
        processed_line = re.sub(img_pattern, replace_img, line)
        processed_lines.append(processed_line)
        
    return '\n'.join(processed_lines)