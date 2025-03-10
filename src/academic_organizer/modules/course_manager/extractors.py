"""
Text extraction and pattern recognition for course materials.
"""
import re
from typing import Dict, Any
import pytesseract
from PIL import Image
import pdf2image
from datetime import datetime
from .models import Instructor, Schedule
from ...utils.logger import get_logger

logger = get_logger(__name__)

class OCRExtractor:
    """Handles OCR-based text extraction from images and PDFs."""
    
    def __init__(self):
        self.supported_formats = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff'}

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a file using OCR if necessary.
        """
        try:
            file_ext = file_path.lower()[-4:]
            
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_ext}")

            if file_ext == '.pdf':
                return self._extract_from_pdf(file_path)
            else:
                return self._extract_from_image(file_path)

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise

    def _extract_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR."""
        pages = pdf2image.convert_from_path(pdf_path)
        text = []
        
        for page in pages:
            text.append(pytesseract.image_to_string(page))
        
        return '\n'.join(text)

    def _extract_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR."""
        with Image.open(image_path) as img:
            return pytesseract.image_to_string(img)


class TextPatternExtractor:
    """Extracts structured information from text using pattern matching."""
    
    def __init__(self):
        self.patterns = {
            'course_code': r'([A-Z]{2,4}\s*\d{3,4}[A-Z]?)',
            'email': r'[\w\.-]+@[\w\.-]+\.\w+',
            'time': r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)',
            'days': r'(Monday|Tuesday|Wednesday|Thursday|Friday|M|T|W|Th|F)',
        }

    def extract_course_info(self, text: str) -> Dict[str, Any]:
        """
        Extract course information from text.
        
        Returns:
            Dict containing course code, name, instructor, and schedule information
        """
        try:
            # Extract course code
            code_match = re.search(self.patterns['course_code'], text)
            code = code_match.group(1) if code_match else None

            # Extract course name (usually follows the course code)
            name = self._extract_course_name(text, code)

            # Extract instructor information
            instructor = self._extract_instructor_info(text)

            # Extract schedule information
            schedule = self._extract_schedule(text)

            return {
                'code': code,
                'name': name,
                'instructor': instructor,
                'schedule': schedule
            }

        except Exception as e:
            logger.error(f"Failed to extract course info: {e}")
            raise

    def _extract_course_name(self, text: str, code: str) -> str:
        """Extract course name from text."""
        if not code:
            return None
            
        # Look for text after the course code
        code_index = text.find(code)
        if code_index == -1:
            return None

        # Get the text after the course code until the next newline
        text_after = text[code_index + len(code):].strip()
        name_match = text_after.split('\n')[0].strip()
        
        # Clean up common prefixes/suffixes
        name = re.sub(r'^[-:]\s*', '', name_match)
        return name[:100]  # Limit length

    def _extract_instructor_info(self, text: str) -> Instructor:
        """Extract instructor information from text."""
        # Look for common instructor indicators
        patterns = [
            r'Instructor:\s*([^\n]+)',
            r'Professor:\s*([^\n]+)',
            r'Teacher:\s*([^\n]+)'
        ]

        name = None
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                break

        # Extract email
        email_match = re.search(self.patterns['email'], text)
        email = email_match.group(0) if email_match else None

        # Extract office hours
        office_hours_match = re.search(r'Office Hours?:\s*([^\n]+)', text)
        office_hours = office_hours_match.group(1) if office_hours_match else None

        return Instructor(
            name=name or "Unknown",
            email=email,
            office_hours=office_hours
        )

    def _extract_schedule(self, text: str) -> Schedule:
        """Extract schedule information from text."""
        days = []
        for day_match in re.finditer(self.patterns['days'], text):
            day = day_match.group(1)
            # Normalize day format
            day_map = {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday',
                      'Th': 'Thursday', 'F': 'Friday'}
            days.append(day_map.get(day, day))

        # Extract times
        time_matches = re.finditer(self.patterns['time'], text)
        times = []
        for match in time_matches:
            hour = int(match.group(1))
            minute = int(match.group(2))
            meridian = match.group(3).upper()
            
            if meridian == 'PM' and hour != 12:
                hour += 12
            elif meridian == 'AM' and hour == 12:
                hour = 0

            times.append(datetime.now().replace(hour=hour, minute=minute))

        if len(times) >= 2:
            start_time, end_time = times[:2]
        else:
            start_time = end_time = None

        return Schedule(
            days=list(set(days)),  # Remove duplicates
            start_time=start_time,
            end_time=end_time
        )