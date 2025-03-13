from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from academic_organizer.database.models.course import Course
from academic_organizer.database.repositories.course_repository import CourseRepository
from academic_organizer.database.repositories.instructor_repository import InstructorRepository

class BaseCourseManager(ABC):
    """Abstract base class for course managers."""

    def __init__(
        self,
        course_repository: CourseRepository,
        instructor_repository: InstructorRepository
    ):
        """Initialize the course manager."""
        self.course_repository = course_repository
        self.instructor_repository = instructor_repository

    @abstractmethod
    def create_course(self, course_data: Dict[str, Any], instructor_data: Dict[str, Any]) -> Course:
        """Create a new course."""
        pass

    @abstractmethod
    def update_course(self, course_id: int, course_data: Dict[str, Any]) -> Course:
        """Update an existing course."""
        pass

    @abstractmethod
    def delete_course(self, course_id: int) -> None:
        """Delete a course."""
        pass

    @abstractmethod
    def get_course_by_code(self, code: str) -> Optional[Course]:
        """Get a course by its code."""
        pass

    def get_active_courses(self) -> List[Course]:
        """Get all active courses."""
        return self.course_repository.get_active_courses()