import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Optional, List
from utils import TempFileManager


class MarkerEngine:
    """Wrapper for marker CLI tool for PDF layout analysis"""
    
    def __init__(self):
        # Sử dụng marker_single cho việc bóc tách từng file (an toàn và phổ biến nhất)
        self.cli_command = "marker_single"
    
    def run_layout_analysis(self, pdf_filepath: str, output_dir: str) -> str:
        """
        Run marker_single to analyze layout and extract markdown + images.
        Returns the path to the clean markdown file.
        """
        # 1. Khai báo 2 cú pháp lệnh (Mới và Cũ) để dự phòng
        primary_cmd = [
            self.cli_command,
            pdf_filepath,
            "--output_dir",
            output_dir
        ]
        
        fallback_cmd = [
            self.cli_command,
            pdf_filepath,
            output_dir
        ]
        
        # 2. Thực thi lệnh một cách an toàn (Không dùng shell=True)
        try:
            subprocess.run(
                primary_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=1800  # Chờ tối đa 30 phút cho các file nặng
            )
        except subprocess.CalledProcessError as e:
            print(f"🔄 Lệnh mới lỗi, thử lại với cú pháp cũ... Chi tiết lỗi: {e.stderr}")
            try:
                subprocess.run(
                    fallback_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=1800
                )
            except subprocess.CalledProcessError as fallback_e:
                raise RuntimeError(f"Marker-pdf error: {fallback_e.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "Marker CLI not found. Please install: pip install marker-pdf"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Marker-pdf processing timed out (>10 min)")

        # 3. Tìm đúng file Markdown mà Marker vừa tạo ra
        # Marker thường tạo một thư mục con có tên giống tên file PDF
        base_name = os.path.splitext(os.path.basename(pdf_filepath))[0]
        marker_output_dir = os.path.join(output_dir, base_name)
        expected_md_path = os.path.join(marker_output_dir, f"{base_name}.md")
        
        if os.path.exists(expected_md_path):
            return expected_md_path
            
        # Fallback tìm kiếm: Nếu cấu trúc thư mục của Marker thay đổi, 
        # tìm bất kỳ file .md nào có trong thư mục output
        md_files = list(Path(output_dir).rglob("*.md"))
        if md_files:
            return str(md_files[0])
            
        raise FileNotFoundError(f"Marker completed but no markdown file found at: {expected_md_path}")


class IDInjector:
    """Injects [ID: xxxx] markers into markdown blocks"""
    
    def __init__(self):
        self.id_counter = 1
        self.regex_pattern = r'^(.*?)\*\*\[ID:\s*(\d+)\]\*\*\s*(.*)'
    
    def _generate_id(self) -> str:
        """Generate next ID in format [ID: xxxx]"""
        id_str = f"[ID: {self.id_counter:04d}]"
        self.id_counter += 1
        return id_str
    
    def _is_image_line(self, line: str) -> bool:
        """Check if line contains markdown image syntax"""
        return re.search(r'!\[.*?\]\(.*?\)', line) is not None
    
    def _is_heading(self, line: str) -> bool:
        """Check if line is a markdown heading"""
        return re.match(r'^#+\s', line) is not None
    
    def _is_quote(self, line: str) -> bool:
        """Check if line is a blockquote"""
        return re.match(r'^>\s', line) is not None
    
    def _is_list_item(self, line: str) -> bool:
        """Check if line is a list item"""
        return re.match(r'^[\s]*[-*+]\s', line) is not None
    
    def inject_ids_to_markdown(self, clean_md_path: str, output_path: str) -> int:
        """
        Inject IDs into markdown file
        Rules:
        - Images: **[ID: xxxx]** goes BEFORE the image syntax
        - Headings: ### **[ID: xxxx]** Heading Text
        - Quotes: > **[ID: xxxx]** Quote text
        - Lists: - **[ID: xxxx]** Item text
        - Paragraphs: **[ID: xxxx]** Paragraph text
        
        Returns: number of IDs injected
        """
        try:
            with open(clean_md_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            injected_lines = []
            ids_added = 0
            skip_next_empty = False
            
            for i, line in enumerate(lines):
                stripped = line.rstrip('\n')
                
                # Skip empty lines
                if not stripped.strip():
                    injected_lines.append(line)
                    skip_next_empty = False
                    continue
                
                # Process image blocks
                if self._is_image_line(stripped):
                    id_marker = f"**{self._generate_id()}**"
                    injected_line = f"{id_marker} {stripped}\n"
                    injected_lines.append(injected_line)
                    ids_added += 1
                    skip_next_empty = True
                    continue
                
                # Process headings
                if self._is_heading(stripped):
                    match = re.match(r'^(#+\s)(.*)', stripped)
                    if match:
                        prefix, content = match.groups()
                        id_marker = f"**{self._generate_id()}**"
                        injected_line = f"{prefix}{id_marker} {content}\n"
                        injected_lines.append(injected_line)
                        ids_added += 1
                        skip_next_empty = True
                        continue
                
                # Process blockquotes
                if self._is_quote(stripped):
                    match = re.match(r'^(>\s)(.*)', stripped)
                    if match:
                        prefix, content = match.groups()
                        id_marker = f"**{self._generate_id()}**"
                        injected_line = f"{prefix}{id_marker} {content}\n"
                        injected_lines.append(injected_line)
                        ids_added += 1
                        skip_next_empty = True
                        continue
                
                # Process list items
                if self._is_list_item(stripped):
                    match = re.match(r'^([\s]*[-*+]\s)(.*)', stripped)
                    if match:
                        prefix, content = match.groups()
                        id_marker = f"**{self._generate_id()}**"
                        injected_line = f"{prefix}{id_marker} {content}\n"
                        injected_lines.append(injected_line)
                        ids_added += 1
                        skip_next_empty = True
                        continue
                
                # Process regular paragraphs
                id_marker = f"**{self._generate_id()}**"
                injected_line = f"{id_marker} {stripped}\n"
                injected_lines.append(injected_line)
                ids_added += 1
                skip_next_empty = True
            
            # Write to output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines(injected_lines)
            
            return ids_added
            
        except Exception as e:
            raise RuntimeError(f"Error injecting IDs: {str(e)}")


class ExtractionService:
    """Service for UC-01: Extract PDF and Inject IDs"""
    
    def __init__(self, temp_manager: TempFileManager):
        self.temp_manager = temp_manager
        self.marker_engine = MarkerEngine()
        self.id_injector = IDInjector()
    
    def process_pdf(self, pdf_filepath: str) -> Optional[str]:
        """
        Process PDF through extraction pipeline
        Returns: path to generated ZIP file
        """
        extraction_dir = None
        try:
            # Create extraction workspace
            extraction_dir = self.temp_manager.create_workspace_subdir("extraction")
            
            # Run marker-pdf
            clean_md_path = self.marker_engine.run_layout_analysis(
                pdf_filepath,
                extraction_dir
            )
            
            # Inject IDs
            md_with_ids_path = os.path.join(extraction_dir, "with_ids.md")
            ids_count = self.id_injector.inject_ids_to_markdown(
                clean_md_path,
                md_with_ids_path
            )
            
            # Find images folder
            images_dir = os.path.join(extraction_dir, "images")
            if not os.path.exists(images_dir):
                images_dir = None
            
            # Create ZIP archive
            zip_path = self.temp_manager.create_zip_archive(
                extraction_dir,
                "extracted_with_ids.zip",
                include_files=[md_with_ids_path],
                include_dirs=[images_dir] if images_dir else []
            )
            
            return zip_path
            
        except Exception as e:
            raise RuntimeError(f"PDF processing failed: {str(e)}")


class MarkdownCleaner:
    """Cleans ID markers from markdown"""
    
    def __init__(self):
        self.id_regex_pattern = r'\*\*\[ID:\s*\d+\]\*\*\s*'
    
    def strip_all_ids(self, assembled_content: str) -> str:
        """
        Remove all **[ID: xxxx]** markers from content
        Returns: cleaned content
        """
        return re.sub(self.id_regex_pattern, '', assembled_content)


class AssemblyService:
    """Service for UC-02: Assemble Translation and Clean IDs"""
    
    def __init__(self, temp_manager: TempFileManager):
        self.temp_manager = temp_manager
        self.markdown_cleaner = MarkdownCleaner()
        self.regex_pattern = r'^(.*?)\*\*\[ID:\s*(\d+)\]\*\*\s*(.*)'
    
    def _build_translation_dictionary(self, translated_content: str) -> Dict[int, str]:
        """
        Parse translated markdown and build dictionary {ID: Vietnamese Text}
        """
        dictionary = {}
        lines = translated_content.split('\n')
        
        for line in lines:
            match = re.match(self.regex_pattern, line)
            if match:
                prefix, id_str, content = match.groups()
                try:
                    id_num = int(id_str)
                    # Store full line for context (prefix + content)
                    dictionary[id_num] = (prefix, content)
                except ValueError:
                    continue
        
        return dictionary
    
    def _build_original_dictionary(self, original_content: str) -> Dict[int, str]:
        """
        Parse original markdown and build dictionary {ID: English Text}
        For fallback when translation ID is missing
        """
        dictionary = {}
        lines = original_content.split('\n')
        
        for line in lines:
            match = re.match(self.regex_pattern, line)
            if match:
                prefix, id_str, content = match.groups()
                try:
                    id_num = int(id_str)
                    dictionary[id_num] = (prefix, content)
                except ValueError:
                    continue
        
        return dictionary
    
    def _is_image_line(self, line: str) -> bool:
        """Check if line contains markdown image"""
        return re.search(r'!\[.*?\]\(.*?\)', line) is not None
    
    def assemble_translated_book(
        self,
        original_md_path: str,
        translated_md_path: str,
        final_md_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Assemble translated content into original structure
        
        Process:
        1. Read original MD (template)
        2. Read translated MD and build dictionary
        3. Iterate through original blocks
        4. For image blocks: keep original links
        5. For text blocks: replace with translated text (with fallback)
        6. Strip all IDs
        7. Save final MD
        
        Returns: path to final markdown file
        """
        try:
            if final_md_path is None:
                final_md_path = self.temp_manager.create_workspace_subdir("assembly")
                final_md_path = os.path.join(final_md_path, "final.md")
            
            # Read files
            with open(original_md_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            with open(translated_md_path, 'r', encoding='utf-8') as f:
                translated_content = f.read()
            
            # Build dictionaries
            translated_dict = self._build_translation_dictionary(translated_content)
            original_dict = self._build_original_dictionary(original_content)
            
            # Process original lines
            original_lines = original_content.split('\n')
            assembled_lines = []
            
            for line in original_lines:
                # Check if line contains image
                if self._is_image_line(line):
                    # Keep original image line as-is (with ID, will be stripped later)
                    assembled_lines.append(line)
                    continue
                
                # Try to match ID pattern
                match = re.match(self.regex_pattern, line)
                if match:
                    prefix, id_str, original_text = match.groups()
                    try:
                        id_num = int(id_str)
                        
                        # Try to get translated version
                        if id_num in translated_dict:
                            trans_prefix, trans_text = translated_dict[id_num]
                            # Reconstruct line with translated text
                            assembled_line = f"{trans_prefix}**[ID: {id_num:04d}]** {trans_text}"
                        else:
                            # Fallback: use original English text
                            assembled_line = f"{prefix}**[ID: {id_num:04d}]** {original_text}"
                        
                        assembled_lines.append(assembled_line)
                    except ValueError:
                        assembled_lines.append(line)
                else:
                    # Line without ID pattern - keep as-is
                    assembled_lines.append(line)
            
            # Join assembled content
            assembled_content = '\n'.join(assembled_lines)
            
            # Strip all IDs
            final_content = self.markdown_cleaner.strip_all_ids(assembled_content)
            
            # Write final file
            with open(final_md_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            return final_md_path
            
        except Exception as e:
            raise RuntimeError(f"Assembly failed: {str(e)}")
