"""Course repository implementation."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from academic_organizer.database.models.course import Course, Instructor
from academic_organizer.database.repositories.base import BaseRepository
from academic_organizer.utils.exceptions import DatabaseError

class CourseRepository(BaseRepository[Course]):
    """Repository for managing course-related database operations."""

    def __init__(self, db_manager: 'DatabaseManager'):
        super().__init__(db_manager, Course)

    def get_with_relationships(self, course_id: int) -> Optional[Course]:
        """Get course with all relationships loaded."""
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
        """Get all courses for a specific semester."""
        try:
            with self.db.session() as session:
                return session.query(Course)\
                    .filter(Course.semester == semester, Course.year == year)\
                    .all()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve courses by semester: {e}")

    def search_courses(self, query: str) -> List[Course]:
        """Search courses by code or name."""
        try:
            with self.db.session() as session:
                return session.query(Course)\
                    .filter(
                        or_(
                            Course.code.ilike(f"%{query}%"),
                            Course.name.ilike(f"%{query}%")
                        )
                    )\
                    .all()
        except Exception as e:
            raise DatabaseError(f"Failed to search courses: {e}")

    def create_with_instructor(
        self, 
        course_data: Dict[str, Any], 
        instructor_data: Dict[str, Any]
    ) -> Course:
        """Create a course with its instructor."""
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
        """Get currently active courses based on semester dates."""
        current_date = datetime.utcnow()
        # This is a simplified version - you might want to add proper semester date ranges
        try:
            with self.db.session() as session:
                return session.query(Course)\
                    .filter(Course.year == current_date.year)\
                    .all()
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve active courses: {e}")