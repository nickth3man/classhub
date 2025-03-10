"""
Text extraction and pattern recognition implementations.
"""
import re
from typing import Dict, Any
import pytesseract
from PIL import Image
from pathlib import Path
import pdf2image
import spacy

class OCRExtractor:
    def __init__(self):
        # Load spaCy model for text processing
        self.nlp = spacy.load("en_core_web_sm")

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from various file formats using OCR when necessary.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            str: Extracted text content
        """
        path = Path(file_path)
        
        if path.suffix.lower() == '.pdf':
            return self._process_pdf(path)
        elif path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            return self._process_image(path)
        elif path.suffix.lower() in ['.txt', '.doc', '.docx']:
            return self._process_document(path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

    def _process_pdf(self, path: Path) -> str:
        """Convert PDF to images and extract text."""
        pages = pdf2image.convert_from_path(path)
        text = []
        for page in pages:
            text.append(pytesseract.image_to_string(page))
        return '\n'.join(text)

    def _process_image(self, path: Path) -> str:
        """Extract text from image."""
        image = Image.open(path)
        return pytesseract.image_to_string(image)

    def _process_document(self, path: Path) -> str:
        """Read text from document files."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

class TextPatternExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for information extraction."""
        self.patterns = {
            'course_code': re.compile(r'([A-Z]{2,4}\s*\d{3,4}[A-Z]?)'),
            'email': re.compile(r'[\w\.-]+@[\w\.-]+\.\w+'),
            'time': re.compile(r'(\d{1,2}):(\d{2})\s*(?:AM|PM|am|pm)?'),
            'days': re.compile(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',
                             re.IGNORECASE)
        }

    def extract_course_info(self, text: str) -> Dict[str, Any]:
        """
        Extract course information from text using NLP and pattern matching.
        
        Args:
            text: Raw text content
            
        Returns:
            dict: Extracted course information
        """
        doc = self.nlp(text)
        
        # Extract course code
        course_code = self._extract_course_code(text)
        
        # Extract course name using NLP
        course_name = self._extract_course_name(doc)
        
        # Extract instructor information
        instructor = self._extract_instructor(doc, text)
        
        # Extract schedule
        schedule = self._extract_schedule(doc, text)
        
        return {
            'code': course_code,
            'name': course_name,
            'instructor': instructor,
            'schedule': schedule
        }

    def _extract_course_code(self, text: str) -> str:
        """Extract course code using regex pattern."""
        match = self.patterns['course_code'].search(text)
        return match.group(1) if match else ""

    def _extract_course_name(self, doc) -> str:
        """Extract course name using NLP patterns."""
        # Look for course name patterns like "Introduction to..."
        for sent in doc.sents:
            if any(token.text.lower() in ['course', 'class'] for token in sent):
                return sent.text.strip()
        return ""

    def _extract_instructor(self, doc, text: str) -> Dict[str, str]:
        """Extract instructor information."""
        name = ""
        email = ""
        
        # Find instructor name using NLP
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text
                break
        
        # Find email using regex
        email_match = self.patterns['email'].search(text)
        if email_match:
            email = email_match.group(0)
            
        return {
            'name': name,
            'email': email
        }

    def _extract_schedule(self, doc, text: str) -> Dict[str, Any]:
        """Extract schedule information."""
        days = []
        start_time = None
        end_time = None
        location = ""
        
        # Extract days
        day_matches = self.patterns['days'].finditer(text)
        days = [match.group(1) for match in day_matches]
        
        # Extract times
        time_matches = self.patterns['time'].finditer(text)
        times = [match.group(0) for match in time_matches]
        if len(times) >= 2:
            start_time = times[0]
            end_time = times[1]
            
        # Extract location using NLP
        for ent in doc.ents:
            if ent.label_ == "FAC" or ent.label_ == "GPE":
                location = ent.text
                break
                
        return {
            'days': days,
            'start_time': start_time,
            'end_time': end_time,
            'location': location
        }