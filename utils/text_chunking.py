# ============================================================================
# utils/text_chunking.py - Text Chunking Utilities
# ============================================================================

from typing import List, Tuple
from io import BytesIO
import PyPDF2

def chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
    """Split text into chunks of approximately chunk_size words"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


def chunk_pdf_by_pages(file_bytes: bytes) -> List[tuple]:
    """Extract text from PDF and return list of (page_number, text) tuples"""
    pdf_file = BytesIO(file_bytes)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    chunks = []
    
    for page_num, page in enumerate(pdf_reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            chunks.append((f"Page {page_num}", text))
    
    return chunks