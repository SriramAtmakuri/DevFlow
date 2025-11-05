import PyPDF2
import docx
import io
from typing import Tuple

class FileProcessor:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error reading DOCX: {str(e)}")
    
    @staticmethod
    def extract_text_from_txt(file_bytes: bytes) -> str:
        """Extract text from TXT file"""
        try:
            return file_bytes.decode('utf-8').strip()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                return file_bytes.decode('latin-1').strip()
            except Exception as e:
                raise ValueError(f"Error reading TXT: {str(e)}")
    
    @staticmethod
    def process_file(filename: str, file_bytes: bytes) -> Tuple[str, str]:
        """
        Process uploaded file and extract text
        Returns: (extracted_text, file_type)
        """
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.pdf'):
            text = FileProcessor.extract_text_from_pdf(file_bytes)
            return text, "PDF"
        
        elif filename_lower.endswith('.docx'):
            text = FileProcessor.extract_text_from_docx(file_bytes)
            return text, "DOCX"
        
        elif filename_lower.endswith('.txt'):
            text = FileProcessor.extract_text_from_txt(file_bytes)
            return text, "TXT"
        
        else:
            raise ValueError(f"Unsupported file type. Please upload PDF, DOCX, or TXT files.")