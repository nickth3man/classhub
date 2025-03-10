"""
Unit tests for Course Manager module.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from academic_organizer.modules.course_manager.models import Course, Instructor, Schedule
from academic_organizer.modules.course_manager.repository import CourseRepository
from academic_organizer.modules.course_manager.service import CourseService
from academic_organizer.modules.course_manager.extractors import OCRExtractor, TextPatternExtractor

@pytest.fixture
def sample_course():
    instructor = Instructor(
        name="Dr. Smith",
        email="smith@university.edu",
        office_hours="Mon/Wed 2-4pm"
    )
    
    schedule = Schedule(
        days=['Monday', 'Wednesday'],
        start_time=datetime.now().replace(hour=14, minute=0),
        end_time=datetime.now().replace(hour=15, minute=30)
    )
    
    return Course(
        code="CS101",
        name="Introduction to Computer Science",
        instructor=instructor,
        schedule=schedule,
        description="Fundamental concepts of programming"
    )

@pytest.fixture
def mock_repository():
    return Mock(spec=CourseRepository)

@pytest.fixture
def course_service(mock_repository):
    return CourseService(mock_repository)

class TestCourseRepository:
    def test_add_course(self, sample_course):
        session_mock = Mock()
        repo = CourseRepository(session_mock)
        
        # Test successful addition
        assert repo.add(sample_course) is True
        session_mock.add.assert_called()
        session_mock.commit.assert_called_once()

        # Test failed addition
        session_mock.commit.side_effect = Exception("DB Error")
        assert repo.add(sample_course) is False

    def test_get_course(self, sample_course):
        session_mock = Mock()
        repo = CourseRepository(session_mock)
        
        # Mock query result
        query_mock = Mock()
        session_mock.query.return_value = query_mock
        query_mock.filter.return_value.first.return_value = None
        
        # Test course not found
        assert repo.get_by_code("CS101") is None
        
        # Test course found
        model_mock = Mock()
        query_mock.filter.return_value.first.return_value = model_mock
        model_mock.code = "CS101"
        assert repo.get_by_code("CS101") is not None

class TestCourseService:
    def test_import_course(self, course_service, sample_course):
        with patch('academic_organizer.modules.course_manager.extractors.OCRExtractor') as mock_ocr:
            mock_ocr.return_value.extract_text.return_value = "Sample syllabus text"
            
            # Test successful import
            course_service.repository.add.return_value = True
            result = course_service.import_course("syllabus.pdf")
            assert result.success is True
            
            # Test failed import
            course_service.repository.add.return_value = False
            result = course_service.import_course("syllabus.pdf")
            assert result.success is False

    def test_get_course(self, course_service, sample_course):
        course_service.repository.get_by_code.return_value = sample_course
        result = course_service.get_course("CS101")
        assert result == sample_course
        course_service.repository.get_by_code.assert_called_with("CS101")

class TestTextPatternExtractor:
    def test_extract_course_info(self):
        extractor = TextPatternExtractor()
        sample_text = """
        CS101: Introduction to Computer Science
        Instructor: Dr. Smith
        Email: smith@university.edu
        Schedule: Monday/Wednesday 2:00 PM - 3:30 PM
        """
        
        result = extractor.extract_course_info(sample_text)
        assert result['code'] == "CS101"
        assert "Introduction to Computer Science" in result['name']
        assert result['instructor'].name == "Dr. Smith"
        assert result['instructor'].email == "smith@university.edu"
        assert "Monday" in result['schedule'].days