"""
Course Manager Module
Handles course-related operations and syllabus parsing.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from academic_organizer.database.models.course import Course
from academic_organizer.database.models.instructor import Instructor
from academic_organizer.database.repositories.course_repository import CourseRepository
from academic_organizer.database.repositories.instructor_repository import InstructorRepository
from academic_organizer.modules.course_manager.syllabus_parser import SyllabusInfo
from academic_organizer.utils.exceptions import ValidationError
from .base import BaseCourseManager

class CourseManager(BaseCourseManager):
    """Manages course-related operations."""

    def __init__(
        self,
        course_repository: CourseRepository,
        instructor_repository: InstructorRepository
    ):
        """Initialize the course manager."""
        super().__init__(course_repository, instructor_repository)

    def create_course_from_syllabus(self, syllabus_info: SyllabusInfo) -> Course:
        """
        Create a new course from parsed syllabus information.
        
        Args:
            syllabus_info: Parsed syllabus information
            
        Returns:
            Created Course instance
            
        Raises:
            ValidationError: If required information is missing
        """
        # Validate required information
        if not syllabus_info.course_code or not syllabus_info.course_name:
            raise ValidationError("Course code and name are required")

        # Create or update instructor
        instructor_data = {
            'first_name': syllabus_info.instructor_name.split()[0],
            'last_name': " ".join(syllabus_info.instructor_name.split()[1:]),
            'email': syllabus_info.instructor_email
        }
        
        instructor = self.instructor_repository.get_by_email(syllabus_info.instructor_email)
        if instructor:
            instructor = self.instructor_repository.update(instructor.id, instructor_data)
        else:
            instructor = self.instructor_repository.create(instructor_data)

        # Create course
        course_data = {
            'code': syllabus_info.course_code,
            'name': syllabus_info.course_name,
            'semester': syllabus_info.semester,
            'year': syllabus_info.year,
            'description': syllabus_info.course_description,
            'instructor_id': instructor.id,
            'textbooks': syllabus_info.textbooks,
            'grading_scheme': syllabus_info.grading_scheme,
            'important_dates': syllabus_info.important_dates
        }
        
        return self.course_repository.create(course_data)


    def create_course(self, course_data: Dict[str, Any], instructor_data: Dict[str, Any]) -> Course:
        """Create a new course with instructor."""
        instructor = self.instructor_repository.create(instructor_data)
        course_data['instructor_id'] = instructor.id
        return self.course_repository.create(course_data)

    def update_course(self, course_id: int, course_data: Dict[str, Any]) -> Course:
        """Update an existing course."""
        return self.course_repository.update(course_id, course_data)

    def delete_course(self, course_id: int) -> None:
        """Delete a course."""
        self.course_repository.delete(course_id)

    def get_course_by_code(self, code: str) -> Optional[Course]:
        """Get a course by its code."""
        return self.course_repository.get_by_code(code)