# ============================================================================
# services/document_processor.py - Document Parsing and Text Extraction
# ============================================================================

from io import BytesIO
import PyPDF2
import docx
from typing import List, Tuple

class DocumentProcessor:
    """Handle document parsing and text extraction"""
    
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        """Extract all text from PDF (for knowledge base storage)"""
        pdf_file = BytesIO(file_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text() + '\n'
        return text
    
    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Extract text from DOCX file"""
        doc_file = BytesIO(file_bytes)
        doc = docx.Document(doc_file)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        return text
    
    @staticmethod
    def extract_text_from_txt(file_bytes: bytes, encoding: str = 'utf-8') -> str:
        """Extract text from TXT file"""
        return file_bytes.decode(encoding)


def chunk_pdf_by_pages(file_bytes: bytes) -> List[Tuple[str, str]] :
    """Extract text from PDF and return list of (page_number, text) tuples"""
    pdf_file = BytesIO(file_bytes)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    chunks = []
    
    for page_num, page in enumerate(pdf_reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            chunks.append((f"Page {page_num}", text))
    
    return chunks