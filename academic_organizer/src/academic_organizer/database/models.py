"""
SQLAlchemy models for the Academic Organizer.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CourseModel(Base):
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    syllabus_path = Column(String)
    
    instructor_id = Column(Integer, ForeignKey('instructors.id'))
    instructor = relationship("InstructorModel", back_populates="courses")
    schedules = relationship("ScheduleModel", back_populates="course")

class InstructorModel(Base):
    __tablename__ = 'instructors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String)
    office_hours = Column(String)
    office_location = Column(String)
    contact_info = Column(String)
    
    courses = relationship("CourseModel", back_populates="instructor")

class ScheduleModel(Base):
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'))
    day = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String)
    
    course = relationship("CourseModel", back_populates="schedules")