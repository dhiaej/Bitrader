"""
PDF Processing Service
Service for extracting text and processing PDF training files
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import io

logger = logging.getLogger(__name__)

# Try to import PDF libraries
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("PyPDF2 is not installed. Install with: pip install PyPDF2")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber is not installed. Install with: pip install pdfplumber")


class PDFService:
    """Service for PDF processing"""
    
    def __init__(self):
        """Initialize PDF service"""
        if not PYPDF2_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            logger.error("No PDF library available. Install PyPDF2 or pdfplumber")
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF bytes
        
        Args:
            pdf_bytes: PDF file as bytes
            
        Returns:
            Extracted text content
        """
        if not pdf_bytes:
            raise ValueError("PDF bytes are empty")
        
        text_content = []
        
        # Try pdfplumber first (better text extraction)
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                return "\n\n".join(text_content)
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {e}, trying PyPDF2")
        
        # Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                pdf_file = io.BytesIO(pdf_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                
                return "\n\n".join(text_content)
            except Exception as e:
                logger.error(f"PyPDF2 extraction failed: {e}")
                raise ValueError(f"Failed to extract text from PDF: {e}")
        
        raise ImportError("No PDF library available. Install PyPDF2 or pdfplumber")
    
    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text from PDF file path
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()
        return self.extract_text_from_pdf(pdf_bytes)
    
    def get_pdf_metadata(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Get PDF metadata (title, author, pages, etc.)
        
        Args:
            pdf_bytes: PDF file as bytes
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            "title": None,
            "author": None,
            "pages": 0,
            "subject": None
        }
        
        try:
            if PDFPLUMBER_AVAILABLE:
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    metadata["pages"] = len(pdf.pages)
                    if pdf.metadata:
                        metadata["title"] = pdf.metadata.get("Title")
                        metadata["author"] = pdf.metadata.get("Author")
                        metadata["subject"] = pdf.metadata.get("Subject")
            elif PYPDF2_AVAILABLE:
                pdf_file = io.BytesIO(pdf_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                metadata["pages"] = len(pdf_reader.pages)
                if pdf_reader.metadata:
                    metadata["title"] = pdf_reader.metadata.get("/Title")
                    metadata["author"] = pdf_reader.metadata.get("/Author")
                    metadata["subject"] = pdf_reader.metadata.get("/Subject")
        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata: {e}")
        
        return metadata


# Singleton instance
pdf_service = PDFService()

