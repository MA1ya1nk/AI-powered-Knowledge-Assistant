# utils/chunker.py
import re
from config import config

def chunk_text(text, chunk_size=None, overlap=None):
    """Split text into overlapping chunks by word count."""
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP
    
    # Clean text
    text = re.sub(r'\s+', ' ', text).strip()
    
    if not text:
        return []
    
    words = text.split()
    chunks = []
    start = 0
    
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_text = ' '.join(chunk_words)
        
        if chunk_text.strip():
            chunks.append(chunk_text.strip())
        
        if end >= len(words):
            break
        
        start = end - overlap
    
    return chunks

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    try:
        import PyPDF2
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n[Page {page_num + 1}]\n{page_text}"
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF extraction failed: {str(e)}")

def extract_text_from_txt(file_path):
    """Extract text from a TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().strip()
    except Exception as e:
        raise Exception(f"TXT extraction failed: {str(e)}")

def extract_text(file_path, file_type):
    """Extract text based on file type."""
    if file_type == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type == 'txt':
        return extract_text_from_txt(file_path)
    else:
        raise Exception(f"Unsupported file type: {file_type}")