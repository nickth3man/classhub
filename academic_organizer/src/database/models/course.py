"""Course-related database models."""

from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from academic_organizer.database.models.base import Base

# Many-to-many relationship table for course materials
course_materials = Table(
    'course_materials',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('material_id', Integer, ForeignKey('materials.id'), primary_key=True)
)

class Course(Base):
    """Course model representing academic courses."""
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    semester = Column(String(20), nullable=False)
    year = Column(Integer, nullable=False)
    syllabus_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    instructor_id = Column(Integer, ForeignKey('instructors.id'))
    instructor = relationship("Instructor", back_populates="courses")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    materials = relationship("Material", secondary=course_materials, back_populates="courses")
    notes = relationship("Note", back_populates="course", cascade="all, delete-orphan")

    @hybrid_property
    def full_name(self) -> str:
        """Return the full course name including code."""
        return f"{self.code} - {self.name}"

    @hybrid_property
    def term(self) -> str:
        """Return the full term (semester and year)."""
        return f"{self.semester} {self.year}"

    def __repr__(self) -> str:
        return f"<Course {self.code} {self.name} ({self.term})>"

class Instructor(Base):
    """Instructor model for course teachers and professors."""
    __tablename__ = 'instructors'

    id = Column(Integer, primary_key=True)
    title = Column(String(20))
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100))
    office_location = Column(String(100))
    office_hours = Column(Text)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    courses = relationship("Course", back_populates="instructor")

    @hybrid_property
    def full_name(self) -> str:
        """Return the full name with title if available."""
        if self.title:
            return f"{self.title} {self.first_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Instructor {self.full_name}>"