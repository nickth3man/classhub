"""
Course Manager Module
Handles course-related operations including creation, updates, and organization.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from academic_organizer.database.repositories.course_repository import CourseRepository
from academic_organizer.database.models.course import Course, Instructor
from academic_organizer.utils.exceptions import CourseManagerError
from academic_organizer.utils.validators import validate_course_data, validate_instructor_data

logger = logging.getLogger(__name__)

class CourseManager:
    """Manages course-related operations and organization."""

    def __init__(self, course_repository: CourseRepository):
        """Initialize CourseManager with required dependencies."""
        self.course_repository = course_repository
        logger.info("CourseManager initialized")

    def create_course(
        self, 
        course_data: Dict[str, Any], 
        instructor_data: Dict[str, Any]
    ) -> Course:
        """
        Create a new course with instructor information.
        
        Args:
            course_data: Dictionary containing course information
            instructor_data: Dictionary containing instructor information
        
        Returns:
            Created Course instance
        
        Raises:
            CourseManagerError: If validation fails or creation fails
        """
        try:
            # Validate input data
            validate_course_data(course_data)
            validate_instructor_data(instructor_data)

            # Create course with instructor
            course = self.course_repository.create_with_instructor(
                course_data=course_data,
                instructor_data=instructor_data
            )
            
            logger.info(f"Created course: {course.code} - {course.name}")
            return course

        except Exception as e:
            error_msg = f"Failed to create course: {str(e)}"
            logger.error(error_msg)
            raise CourseManagerError(error_msg)

    def get_course_details(self, course_id: int) -> Optional[Course]:
        """
        Retrieve complete course details including relationships.
        
        Args:
            course_id: ID of the course to retrieve
            
        Returns:
            Course instance with loaded relationships or None if not found
        """
        try:
            course = self.course_repository.get_with_relationships(course_id)
            if course:
                logger.info(f"Retrieved course details for: {course.code}")
            else:
                logger.warning(f"Course not found with ID: {course_id}")
            return course

        except Exception as e:
            error_msg = f"Failed to retrieve course details: {str(e)}"
            logger.error(error_msg)
            raise CourseManagerError(error_msg)

    def get_active_courses(self) -> List[Course]:
        """
        Get all currently active courses.
        
        Returns:
            List of active Course instances
        """
        try:
            courses = self.course_repository.get_active_courses()
            logger.info(f"Retrieved {len(courses)} active courses")
            return courses

        except Exception as e:
            error_msg = f"Failed to retrieve active courses: {str(e)}"
            logger.error(error_msg)
            raise CourseManagerError(error_msg)

    def update_course(
        self, 
        course_id: int, 
        course_data: Dict[str, Any]
    ) -> Course:
        """
        Update course information.
        
        Args:
            course_id: ID of the course to update
            course_data: Dictionary containing updated course information
            
        Returns:
            Updated Course instance
        """
        try:
            validate_course_data(course_data)
            course = self.course_repository.update(course_id, course_data)
            logger.info(f"Updated course: {course.code}")
            return course

        except Exception as e:
            error_msg = f"Failed to update course: {str(e)}"
            logger.error(error_msg)
            raise CourseManagerError(error_msg)

    def search_courses(self, query: str) -> List[Course]:
        """
        Search for courses by code or name.
        
        Args:
            query: Search string
            
        Returns:
            List of matching Course instances
        """
        try:
            courses = self.course_repository.search_courses(query)
            logger.info(f"Found {len(courses)} courses matching query: {query}")
            return courses

        except Exception as e:
            error_msg = f"Failed to search courses: {str(e)}"
            logger.error(error_msg)
            raise CourseManagerError(error_msg)

    def get_courses_by_semester(
        self, 
        semester: str, 
        year: int
    ) -> List[Course]:
        """
        Get all courses for a specific semester.
        
        Args:
            semester: Semester name
            year: Academic year
            
        Returns:
            List of Course instances for the specified semester
        """
        try:
            courses = self.course_repository.get_by_semester(semester, year)
            logger.info(f"Retrieved {len(courses)} courses for {semester} {year}")
            return courses

        except Exception as e:
            error_msg = f"Failed to retrieve courses by semester: {str(e)}"
            logger.error(error_msg)
            raise CourseManagerError(error_msg)
