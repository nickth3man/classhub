"""
Syllabus Parser Module
Handles extraction and parsing of information from course syllabi.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache
import hashlib
from concurrent.futures import ThreadPoolExecutor

class ParseError(Exception):
    """Base exception for parsing errors"""
    pass

class FileTypeError(ParseError):
    """Raised when file type is unsupported"""
    pass

class ExtractionError(ParseError):
    """Raised when text extraction fails"""
    pass

class ValidationError(ParseError):
    """Raised when extracted data is invalid"""
    pass

@dataclass
class SyllabusInfo:
    course_code: str
    course_name: str
    instructor_name: str
    instructor_email: Optional[str] = None
    office_hours: Optional[str] = None
    semester: str = ""
    year: int = field(default_factory=lambda: datetime.now().year)
    course_description: Optional[str] = None
    textbooks: List[str] = field(default_factory=list)
    grading_scheme: Dict[str, float] = field(default_factory=dict)
    important_dates: Dict[str, datetime] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate extracted information"""
        if not self.course_code or not re.match(r'^[A-Z]{2,4}\s*\d{3,4}$', self.course_code):
            raise ValidationError(f"Invalid course code: {self.course_code}")
        if not self.course_name:
            raise ValidationError("Course name is required")
        if not self.instructor_name:
            raise ValidationError("Instructor name is required")
        if self.instructor_email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', self.instructor_email):
            raise ValidationError(f"Invalid email: {self.instructor_email}")
        if sum(self.grading_scheme.values()) != 100:
            raise ValidationError("Grading scheme percentages must sum to 100")

class SyllabusParser:
    """Handles parsing of syllabus documents."""

    def __init__(self):
        """Initialize the syllabus parser."""
        self.text_patterns = {
            'course_code': r'(?:Course|Class)\s+(?:Code|Number):\s*([A-Z]{2,4}\s*\d{3,4})',
            'course_name': r'(?:Course|Class)\s+(?:Title|Name):\s*(.+?)(?:\n|$)',
            'instructor': r'(?:Instructor|Professor|Teacher):\s*(.+?)(?:\n|$)',
            'email': r'[\w\.-]+@[\w\.-]+\.\w+',
            'office_hours': r'(?:Office\s+Hours):\s*(.+?)(?:\n|$)',
            'semester': r'(?:Term|Semester):\s*((?:Fall|Spring|Summer|Winter)\s*\d{4})',
            'textbook': r'(?:Required\s+)?(?:Text|Textbook)(?:s)?:\s*(.+?)(?:\n|$)',
            'grading': r'(\d{1,3})%\s*[-–]\s*([A-Za-z\s]+)',
        }
        self._pdf_cache = {}
        
    @lru_cache(maxsize=128)
    def _get_file_hash(self, file_path: Path) -> str:
        """Generate hash of file content for caching"""
        return hashlib.md5(file_path.read_bytes()).hexdigest()

    def parse_file(self, file_path: Path) -> SyllabusInfo:
        """
        Parse a syllabus file and extract relevant information.
        
        Args:
            file_path: Path to the syllabus file
            
        Returns:
            SyllabusInfo containing extracted information
            
        Raises:
            ValueError: If file format is unsupported
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        text = self._extract_text(file_path)
        return self._parse_text(text)

    def batch_parse(self, file_paths: List[Path], max_workers: int = 4) -> Iterator[SyllabusInfo]:
        """
        Parse multiple syllabus files concurrently.
        
        Args:
            file_paths: List of paths to syllabus files
            max_workers: Maximum number of concurrent workers
            
        Returns:
            Iterator of SyllabusInfo objects
        """
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            yield from executor.map(self.parse_file, file_paths)

    def _extract_text(self, file_path: Path) -> str:
        """Extract text from various file formats."""
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            return self._extract_from_pdf(file_path)
        elif ext in ('.png', '.jpg', '.jpeg', '.tiff'):
            return self._extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF with caching"""
        file_hash = self._get_file_hash(file_path)
        
        if file_hash in self._pdf_cache:
            return self._pdf_cache[file_hash]
            
        text = ""
        doc = fitz.open(file_path)
        
        # Process pages in chunks for memory efficiency
        chunk_size = 5
        for i in range(0, len(doc), chunk_size):
            chunk = doc.pages(i, min(i + chunk_size, len(doc)))
            for page in chunk:
                text += self._process_page(page)
                
        self._pdf_cache[file_hash] = text
        return text
        
    def _process_page(self, page) -> str:
        """Process a single PDF page with optimized OCR decision"""
        text = page.get_text()
        
        # Only use OCR if necessary
        if len(text.strip()) < 100:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Increase resolution for better OCR
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, config='--psm 1')
            
        return text + "\n"

    def _extract_from_image(self, file_path: Path) -> str:
        """Extract text from image files using OCR."""
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)

    def _parse_text(self, text: str) -> SyllabusInfo:
        """Parse extracted text into structured information."""
        info = {
            'course_code': '',
            'course_name': '',
            'instructor_name': '',
            'instructor_email': None,
            'office_hours': None,
            'semester': '',
            'year': datetime.now().year,
            'course_description': None,
            'textbooks': [],
            'grading_scheme': {},
            'important_dates': {}
        }
        
        # Extract basic information using regex patterns
        for key, pattern in self.text_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if key == 'grading':
                    for percentage, category in matches:
                        info['grading_scheme'][category.strip()] = float(percentage)
                elif key == 'textbook':
                    info['textbooks'].extend(match.strip() for match in matches)
                else:
                    info[key] = matches[0].strip()

        # Extract semester and year
        if 'semester' in info:
            semester_match = re.match(r'(Fall|Spring|Summer|Winter)\s*(\d{4})', info['semester'])
            if semester_match:
                info['semester'] = semester_match.group(1)
                info['year'] = int(semester_match.group(2))

        # Extract important dates
        date_pattern = r'(\w+\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?)\s*[-–]\s*(.+?)(?:\n|$)'
        dates = re.findall(date_pattern, text)
        for date_str, description in dates:
            try:
                date = datetime.strptime(date_str, '%B %d, %Y')
                info['important_dates'][description.strip()] = date
            except ValueError:
                continue

        return SyllabusInfo(**info)
