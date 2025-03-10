"""
Unit tests for the Course Manager module.
"""
import pytest
from datetime import datetime
from academic_organizer.modules.course_manager import (
    CourseManager, Course, Instructor, Schedule
)

@pytest.fixture
def sample_course():
    instructor = Instructor(
        name="Dr. Smith",
        email="smith@university.edu"
    )
    schedule = Schedule(
        days=["Monday", "Wednesday"],
        start_time=datetime.strptime("09:00", "%H:%M"),
        end_time=datetime.strptime("10:30", "%H:%M"),
        location="Room 101"
    )
    return Course(
        name="Introduction to Computer Science",
        code="CS101",
        instructor=instructor,
        schedule=schedule
    )

@pytest.fixture
def course_manager():
    return CourseManager()

def test_add_course(course_manager, sample_course):
    course_manager.add_course(sample_course)
    retrieved_course = course_manager.get_course(sample_course.code)
    assert retrieved_course == sample_course

def test_get_nonexistent_course(course_manager):
    assert course_manager.get_course("NONEXISTENT") is None
