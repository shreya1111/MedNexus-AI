"""
Text extraction module for MedNexus-AI Knowledge Ingestion Framework.

Extracts text from various document formats (PDF, TXT, Markdown, XML, HTML).
"""

from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import time

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

logger = get_logger(__name__)


class ExtractionStatus(Enum):
    """Status of text extraction."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    EMPTY = "empty"
    UNSUPPORTED = "unsupported"


@dataclass
class ExtractionResult:
    """Result of text extraction operation."""
    status: ExtractionStatus
    text: str = ""
    page_count: Optional[int] = None
    char_count: int = 0
    word_count: int = 0
    extraction_time_seconds: float = 0.0
    method: str = ""
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        
        # Calculate counts if not provided
        if self.text:
            self.char_count = len(self.text)
            self.word_count = len(self.text.split())


class TextExtractor:
    """Extracts text from various document formats."""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.md', '.xml', '.html', '.htm'}
    
    def __init__(self, fallback_to_pdfplumber: bool = True):
        """
        Initialize text extractor.
        
        Args:
            fallback_to_pdfplumber: Use pdfplumber if pypdf fails
        """
        self.fallback_to_pdfplumber = fallback_to_pdfplumber
        self.logger = get_logger(__name__)
    
    def extract(self, file_path: Path) -> ExtractionResult:
        """
        Extract text from a document.
        
        Args:
            file_path: Path to document
            
        Returns:
            ExtractionResult
        """
        start_time = time.time()
        
        if not file_path.exists():
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message=f"File not found: {file_path}",
                extraction_time_seconds=time.time() - start_time
            )
        
        extension = file_path.suffix.lower()
        
        if extension not in self.SUPPORTED_EXTENSIONS:
            return ExtractionResult(
                status=ExtractionStatus.UNSUPPORTED,
                error_message=f"Unsupported file type: {extension}",
                extraction_time_seconds=time.time() - start_time
            )
        
        try:
            if extension == '.pdf':
                result = self._extract_pdf(file_path)
            elif extension == '.txt':
                result = self._extract_text(file_path)
            elif extension == '.md':
                result = self._extract_markdown(file_path)
            elif extension in {'.xml', '.html', '.htm'}:
                result = self._extract_xml_html(file_path)
            else:
                result = ExtractionResult(
                    status=ExtractionStatus.UNSUPPORTED,
                    error_message=f"No extractor for: {extension}"
                )
            
            result.extraction_time_seconds = time.time() - start_time
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting text from {file_path}: {e}")
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message=str(e),
                extraction_time_seconds=time.time() - start_time
            )
    
    def _extract_pdf(self, file_path: Path) -> ExtractionResult:
        """Extract text from PDF."""
        if not PDF_AVAILABLE:
            if PDFPLUMBER_AVAILABLE and self.fallback_to_pdfplumber:
                return self._extract_pdf_pdfplumber(file_path)
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message="pypdf not installed"
            )
        
        try:
            reader = PdfReader(str(file_path))
            page_count = len(reader.pages)
            
            text_parts = []
            empty_pages = 0
            
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_parts.append(page_text)
                    else:
                        empty_pages += 1
                except Exception as e:
                    self.logger.warning(f"Error extracting page {page_num}: {e}")
                    empty_pages += 1
            
            text = "\n\n".join(text_parts)
            
            if not text.strip():
                # Try pdfplumber as fallback
                if PDFPLUMBER_AVAILABLE and self.fallback_to_pdfplumber:
                    self.logger.info("pypdf extracted no text, trying pdfplumber")
                    return self._extract_pdf_pdfplumber(file_path)
                
                return ExtractionResult(
                    status=ExtractionStatus.EMPTY,
                    text=text,
                    page_count=page_count,
                    method="pypdf",
                    metadata={'empty_pages': empty_pages}
                )
            
            status = ExtractionStatus.PARTIAL if empty_pages > 0 else ExtractionStatus.SUCCESS
            
            return ExtractionResult(
                status=status,
                text=text,
                page_count=page_count,
                method="pypdf",
                metadata={'empty_pages': empty_pages}
            )
            
        except Exception as e:
            # Try pdfplumber as fallback
            if PDFPLUMBER_AVAILABLE and self.fallback_to_pdfplumber:
                self.logger.info(f"pypdf failed ({e}), trying pdfplumber")
                return self._extract_pdf_pdfplumber(file_path)
            
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message=f"PDF extraction failed: {str(e)}",
                method="pypdf"
            )
    
    def _extract_pdf_pdfplumber(self, file_path: Path) -> ExtractionResult:
        """Extract text from PDF using pdfplumber."""
        if not PDFPLUMBER_AVAILABLE:
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message="pdfplumber not installed"
            )
        
        try:
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                text_parts = []
                empty_pages = 0
                
                for page in pdf.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_parts.append(page_text)
                        else:
                            empty_pages += 1
                    except Exception as e:
                        self.logger.warning(f"Error extracting page: {e}")
                        empty_pages += 1
                
                text = "\n\n".join(text_parts)
                
                if not text.strip():
                    return ExtractionResult(
                        status=ExtractionStatus.EMPTY,
                        text=text,
                        page_count=page_count,
                        method="pdfplumber",
                        metadata={'empty_pages': empty_pages}
                    )
                
                status = ExtractionStatus.PARTIAL if empty_pages > 0 else ExtractionStatus.SUCCESS
                
                return ExtractionResult(
                    status=status,
                    text=text,
                    page_count=page_count,
                    method="pdfplumber",
                    metadata={'empty_pages': empty_pages}
                )
                
        except Exception as e:
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message=f"pdfplumber extraction failed: {str(e)}",
                method="pdfplumber"
            )
    
    def _extract_text(self, file_path: Path) -> ExtractionResult:
        """Extract text from plain text file."""
        try:
            # Try UTF-8 first
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                encoding = 'utf-8'
            except UnicodeDecodeError:
                # Try with chardet if available
                try:
                    import chardet
                    with open(file_path, 'rb') as f:
                        raw_data = f.read()
                    detected = chardet.detect(raw_data)
                    encoding = detected['encoding'] or 'latin-1'
                    text = raw_data.decode(encoding, errors='replace')
                except ImportError:
                    # Fallback to latin-1
                    with open(file_path, 'r', encoding='latin-1', errors='replace') as f:
                        text = f.read()
                    encoding = 'latin-1'
            
            if not text.strip():
                return ExtractionResult(
                    status=ExtractionStatus.EMPTY,
                    text=text,
                    method="text",
                    metadata={'encoding': encoding}
                )
            
            return ExtractionResult(
                status=ExtractionStatus.SUCCESS,
                text=text,
                method="text",
                metadata={'encoding': encoding}
            )
            
        except Exception as e:
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message=f"Text extraction failed: {str(e)}",
                method="text"
            )
    
    def _extract_markdown(self, file_path: Path) -> ExtractionResult:
        """Extract text from Markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if not text.strip():
                return ExtractionResult(
                    status=ExtractionStatus.EMPTY,
                    text=text,
                    method="markdown"
                )
            
            # Keep original markdown text (don't convert to HTML)
            return ExtractionResult(
                status=ExtractionStatus.SUCCESS,
                text=text,
                method="markdown"
            )
            
        except Exception as e:
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message=f"Markdown extraction failed: {str(e)}",
                method="markdown"
            )
    
    def _extract_xml_html(self, file_path: Path) -> ExtractionResult:
        """Extract text from XML/HTML file."""
        if not BS4_AVAILABLE:
            # Fallback to plain text extraction
            return self._extract_text(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'lxml' if file_path.suffix.lower() == '.xml' else 'html.parser')
            
            # Remove script and style tags
            for tag in soup(['script', 'style', 'meta', 'link']):
                tag.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            
            if not text.strip():
                return ExtractionResult(
                    status=ExtractionStatus.EMPTY,
                    text=text,
                    method="beautifulsoup"
                )
            
            return ExtractionResult(
                status=ExtractionStatus.SUCCESS,
                text=text,
                method="beautifulsoup"
            )
            
        except Exception as e:
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message=f"XML/HTML extraction failed: {str(e)}",
                method="beautifulsoup"
            )
