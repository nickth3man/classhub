"""
Integration tests for Course Manager module.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from academic_organizer.database.models import Base
from academic_organizer.modules.course_manager.repository import CourseRepository
from academic_organizer.modules.course_manager.service import CourseService

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def course_service(db_session):
    repository = CourseRepository(db_session)
    return CourseService(repository)

class TestCourseManagerIntegration:
    def test_course_lifecycle(self, course_service, sample_course):
        # Test course import
        import_result = course_service.import_course("tests/data/sample_syllabus.pdf")
        assert import_result.success
        
        # Test course retrieval
        course = course_service.get_course(sample_course.code)
        assert course is not None
        assert course.code == sample_course.code
        
        # Test course update
        sample_course.name = "Updated Course Name"
        assert course_service.update_course(sample_course)
        
        # Test course deletion
        assert course_service.delete_course(sample_course.code)
        assert course_service.get_course(sample_course.code) is None