"""Course-related database models with validation."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from ...utils.error_handler import ValidationError, handle_errors
from ...utils.validators import validate_email, validate_phone, sanitize_input

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

    @validates('code')
    def validate_code(self, key: str, code: str) -> str:
        """Validate course code format."""
        code = sanitize_input(code)
        if not code or len(code) > 20:
            raise ValidationError("Invalid course code")
        return code
    
    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        """Validate course name."""
        name = sanitize_input(name)
        if not name or len(name) > 100:
            raise ValidationError("Invalid course name")
        return name
    
    @validates('year')
    def validate_year(self, key: str, year: int) -> int:
        """Validate course year."""
        current_year = datetime.now().year
        if not (current_year - 1 <= year <= current_year + 1):
            raise ValidationError("Invalid course year")
        return year
    
    @validates('semester')
    def validate_semester(self, key: str, semester: str) -> str:
        """Validate semester value."""
        valid_semesters = {'Fall', 'Spring', 'Summer', 'Winter'}
        semester = sanitize_input(semester)
        if semester not in valid_semesters:
            raise ValidationError("Invalid semester")
        return semester

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
