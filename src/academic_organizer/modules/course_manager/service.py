"""
Service layer for Course Manager module.
"""
from typing import List, Optional
from .repository import CourseRepository
from .extractors import OCRExtractor, TextPatternExtractor
from .models import Course, ImportResult
from ...utils.logger import get_logger

logger = get_logger(__name__)

class CourseService:
    def __init__(self, repository: CourseRepository):
        self.repository = repository
        self.ocr_extractor = OCRExtractor()
        self.pattern_extractor = TextPatternExtractor()

    def import_course(self, file_path: str) -> ImportResult:
        """
        Import a course from a file (syllabus, schedule, etc.).
        """
        try:
            # Extract text from file
            text = self.ocr_extractor.extract_text(file_path)
            
            # Extract course information
            course_info = self.pattern_extractor.extract_course_info(text)
            
            if not course_info['code'] or not course_info['name']:
                return ImportResult(
                    success=False,
                    error_message="Failed to extract required course information"
                )

            # Create course object
            course = Course(
                code=course_info['code'],
                name=course_info['name'],
                instructor=course_info['instructor'],
                schedule=course_info['schedule'],
                syllabus_path=file_path
            )

            # Save to database
            if self.repository.add(course):
                return ImportResult(success=True, course=course)
            else:
                return ImportResult(
                    success=False,
                    error_message="Failed to save course to database"
                )

        except Exception as e:
            logger.error(f"Failed to import course: {e}")
            return ImportResult(
                success=False,
                error_message=f"Error during import: {str(e)}"
            )

    def get_course(self, code: str) -> Optional[Course]:
        """Retrieve a course by its code."""
        return self.repository.get_by_code(code)

    def get_all_courses(self) -> List[Course]:
        """Retrieve all courses."""
        return self.repository.get_all()

    def update_course(self, course: Course) -> bool:
        """Update an existing course."""
        return self.repository.update(course)

    def delete_course(self, code: str) -> bool:
        """Delete a course by its code."""
        return self.repository.delete(code)