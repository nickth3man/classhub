"""
Repository layer for Course Manager module.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ...database.models import CourseModel, InstructorModel, ScheduleModel
from .models import Course, Instructor, Schedule
from ...utils.logger import get_logger

logger = get_logger(__name__)

class CourseRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, course: Course) -> bool:
        """
        Add a new course to the database.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            instructor_model = InstructorModel(
                name=course.instructor.name,
                email=course.instructor.email,
                office_hours=course.instructor.office_hours,
                office_location=course.instructor.office_location,
                contact_info=course.instructor.contact_info
            )

            course_model = CourseModel(
                code=course.code,
                name=course.name,
                description=course.description,
                syllabus_path=course.syllabus_path,
                instructor=instructor_model
            )

            schedule_models = [
                ScheduleModel(
                    day=day,
                    start_time=course.schedule.start_time,
                    end_time=course.schedule.end_time,
                    location=course.schedule.location,
                    course=course_model
                )
                for day in course.schedule.days
            ]

            self.session.add(instructor_model)
            self.session.add(course_model)
            self.session.add_all(schedule_models)
            self.session.commit()
            return True

        except SQLAlchemyError as e:
            logger.error(f"Failed to add course: {e}")
            self.session.rollback()
            return False

    def get_by_code(self, code: str) -> Optional[Course]:
        """Retrieve a course by its code."""
        try:
            course_model = self.session.query(CourseModel).filter(
                CourseModel.code == code
            ).first()
            
            return self._to_domain(course_model) if course_model else None

        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve course: {e}")
            return None

    def get_all(self) -> List[Course]:
        """Retrieve all courses."""
        try:
            course_models = self.session.query(CourseModel).all()
            return [self._to_domain(cm) for cm in course_models]

        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve courses: {e}")
            return []

    def update(self, course: Course) -> bool:
        """Update an existing course."""
        try:
            course_model = self.session.query(CourseModel).filter(
                CourseModel.code == course.code
            ).first()
            
            if not course_model:
                return False

            # Update course attributes
            course_model.name = course.name
            course_model.description = course.description
            course_model.syllabus_path = course.syllabus_path

            # Update instructor
            course_model.instructor.name = course.instructor.name
            course_model.instructor.email = course.instructor.email
            course_model.instructor.office_hours = course.instructor.office_hours
            course_model.instructor.office_location = course.instructor.office_location
            course_model.instructor.contact_info = course.instructor.contact_info

            # Update schedules
            self.session.query(ScheduleModel).filter(
                ScheduleModel.course_id == course_model.id
            ).delete()

            new_schedules = [
                ScheduleModel(
                    day=day,
                    start_time=course.schedule.start_time,
                    end_time=course.schedule.end_time,
                    location=course.schedule.location,
                    course=course_model
                )
                for day in course.schedule.days
            ]
            
            self.session.add_all(new_schedules)
            self.session.commit()
            return True

        except SQLAlchemyError as e:
            logger.error(f"Failed to update course: {e}")
            self.session.rollback()
            return False

    def delete(self, code: str) -> bool:
        """Delete a course by its code."""
        try:
            course_model = self.session.query(CourseModel).filter(
                CourseModel.code == code
            ).first()
            
            if not course_model:
                return False

            self.session.delete(course_model)
            self.session.commit()
            return True

        except SQLAlchemyError as e:
            logger.error(f"Failed to delete course: {e}")
            self.session.rollback()
            return False

    def _to_domain(self, model: CourseModel) -> Course:
        """Convert database model to domain model."""
        instructor = Instructor(
            name=model.instructor.name,
            email=model.instructor.email,
            office_hours=model.instructor.office_hours,
            office_location=model.instructor.office_location,
            contact_info=model.instructor.contact_info
        )

        schedule = Schedule(
            days=[s.day for s in model.schedules],
            start_time=model.schedules[0].start_time,
            end_time=model.schedules[0].end_time,
            location=model.schedules[0].location
        )

        return Course(
            code=model.code,
            name=model.name,
            instructor=instructor,
            schedule=schedule,
            description=model.description,
            syllabus_path=model.syllabus_path
        )