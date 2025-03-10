from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from ..base import Base

class Assignment(Base):
    """Database model for assignments."""
    __tablename__ = 'assignments'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(50), default='Not Started')
    priority = Column(String(50), default='Low')
    estimated_time = Column(Float, default=1.0)
    description = Column(Text)
    
    # Relationship to course
    course = relationship("Course", back_populates="assignments")

    def to_dict(self):
        """Convert assignment to dictionary for UI."""
        return {
            'id': self.id,
            'title': self.title,
            'course': self.course.name if self.course else None,
            'due_date': self.due_date.strftime('%Y-%m-%d'),
            'status': self.status,
            'priority': self.priority,
            'estimated_time': self.estimated_time,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data, session):
        """Create assignment from dictionary."""
        from ..models.course import Course
        
        # Find course by name
        course = session.query(Course).filter(Course.name == data['course']).first()
        if not course:
            raise ValueError(f"Course not found: {data['course']}")

        return cls(
            title=data['title'],
            course_id=course.id,
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
            status=data['status'],
            priority=data['priority'],
            estimated_time=data['estimated_time'],
            description=data.get('description', '')
        )