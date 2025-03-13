"""Course repository implementation."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from academic_organizer.database.models.course import Course, Instructor
from academic_organizer.database.repositories.base import BaseRepository
from academic_organizer.utils.exceptions import DatabaseError

class CourseRepository(BaseRepository[Course]):
    """Repository for managing course-related database operations.
    
    This repository handles all database operations related to courses, including
    creation, retrieval, and search functionality. It extends the BaseRepository
    with Course-specific operations.
    """

    def __init__(self, db_manager: 'DatabaseManager'):
        """Initialize the course repository.
        
        Args:
            db_manager: Database manager instance for handling connections
        """
        super().__init__(db_manager, Course)

    def get_with_relationships(self, course_id: int) -> Optional[Course]:
        """Get course with all relationships loaded.
        
        Retrieves a course by ID with its instructor, assignments, materials,
        and notes relationships eagerly loaded.
        
        Args:
            course_id: ID of the course to retrieve
            
        Returns:
            Course object with loaded relationships or None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            with self.db.session() as session:
                return session.query(Course)\
                    .options(
                        joinedload(Course.instructor),
                        joinedload(Course.assignments),
                        joinedload(Course.materials),
                        joinedload(Course.notes)
                    )\
                    .filter(Course.id == course_id)\
                    .first()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve course with relationships: {e}")

    def get_by_semester(self, semester: str, year: int) -> List[Course]:
        """Get all courses for a specific semester.
        
        Args:
            semester: Semester identifier (e.g., 'Fall', 'Spring')
            year: Academic year
            
        Returns:
            List of courses for the specified semester
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            with self.db.session() as session:
                return session.query(Course)\
                    .filter(Course.semester == semester, Course.year == year)\
                    .all()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve courses by semester: {e}")

    def search_courses(self, query: str) -> List[Course]:
        """Search courses by code or name.
        
        Performs a case-insensitive search on course codes and names.
        
        Args:
            query: Search string to match against course codes and names
            
        Returns:
            List of matching courses
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            with self.db.session() as session:
                search_pattern = "%" + query + "%"
                course_table = Course.__table__
                stmt = select(Course).where(
                    or_(
                        course_table.c.course_code.ilike(bindparam('search_pattern')),
                        course_table.c.course_name.ilike(bindparam('search_pattern'))
                    )
                ).params(search_pattern=search_pattern)
                result = session.execute(stmt)
                courses = [row[0] for row in result.all()] # Extract Course objects
                return courses
        except Exception as e:
            raise DatabaseError(f"Failed to search courses: {e}")

    def create_with_instructor(
        self, 
        course_data: Dict[str, Any], 
        instructor_data: Dict[str, Any]
    ) -> Course:
        """Create a course with its instructor.
        
        Creates a new course and either creates or updates the associated instructor.
        
        Args:
            course_data: Dictionary containing course attributes
            instructor_data: Dictionary containing instructor attributes
            
        Returns:
            Newly created Course object
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            with self.db.session() as session:
                # Create or update instructor
                instructor = session.query(Instructor)\
                    .filter_by(email=instructor_data['email'])\
                    .first()
                
                if not instructor:
                    instructor = Instructor(**instructor_data)
                    session.add(instructor)
                    session.flush()

                # Create course
                course = Course(**course_data, instructor_id=instructor.id)
                session.add(course)
                session.flush()
                
                return course
        except Exception as e:
            raise DatabaseError(f"Failed to create course with instructor: {e}")

    def get_active_courses(self) -> List[Course]:
        """Get currently active courses based on semester dates.
        
        Retrieves courses that are currently active based on the current year.
        Note: This is a simplified implementation that could be enhanced with
        proper semester date ranges.
        
        Returns:
            List of active courses
            
        Raises:
            DatabaseError: If database operation fails
        """
        current_date = datetime.utcnow()
        try:
            with self.db.session() as session:
                return session.query(Course)\
                    .filter(Course.year == current_date.year)\
                    .all()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve active courses: {e}")
