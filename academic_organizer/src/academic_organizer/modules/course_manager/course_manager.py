"""
Main Course Manager implementation with database integration.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from ...database.models import CourseModel, InstructorModel, ScheduleModel
from .models import Course, Instructor, Schedule
from .extractors import OCRExtractor, TextPatternExtractor

class CourseManager:
    def __init__(self, db_session: Session):
        self.ocr_extractor = OCRExtractor()
        self.pattern_extractor = TextPatternExtractor()
        self.db = db_session

    def add_course(self, course: Course) -> None:
        """Add a new course to the database."""
        # Create instructor model
        instructor_model = InstructorModel(
            name=course.instructor.name,
            email=course.instructor.email,
            office_hours=course.instructor.office_hours,
            office_location=course.instructor.office_location,
            contact_info=course.instructor.contact_info
        )
        
        # Create course model
        course_model = CourseModel(
            code=course.code,
            name=course.name,
            description=course.description,
            syllabus_path=course.syllabus_path,
            instructor=instructor_model
        )
        
        # Create schedule models
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
        
        # Add to database
        self.db.add(instructor_model)
        self.db.add(course_model)
        self.db.add_all(schedule_models)
        self.db.commit()

    def get_course(self, code: str) -> Optional[Course]:
        """Retrieve a course by its code."""
        course_model = self.db.query(CourseModel).filter(
            CourseModel.code == code
        ).first()
        
        if not course_model:
            return None
            
        return self._convert_to_course(course_model)

    def _convert_to_course(self, course_model: CourseModel) -> Course:
        """Convert database model to domain model."""
        instructor = Instructor(
            name=course_model.instructor.name,
            email=course_model.instructor.email,
            office_hours=course_model.instructor.office_hours,
            office_location=course_model.instructor.office_location,
            contact_info=course_model.instructor.contact_info
        )
        
        schedule = Schedule(
            days=[s.day for s in course_model.schedules],
            start_time=course_model.schedules[0].start_time,
            end_time=course_model.schedules[0].end_time,
            location=course_model.schedules[0].location
        )
        
        return Course(
            name=course_model.name,
            code=course_model.code,
            instructor=instructor,
            schedule=schedule,
            description=course_model.description,
            syllabus_path=course_model.syllabus_path
        )
