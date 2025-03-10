"""
Pytest configuration and fixtures for the Academic Organizer application.
"""

import os
import tempfile
import pytest
from pathlib import Path

from academic_organizer.src.database.db_manager import DatabaseManager
from academic_organizer.src.utils.config import load_config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return {
        "application": {
            "name": "Academic Organizer Test",
            "version": "0.1.0",
            "data_dir": "~/.academic_organizer_test",
        },
        "database": {
            "type": "sqlite",
            "name": "academic_organizer_test.db",
        },
        "gui": {
            "theme": "system",
            "font_size": 10,
            "window_size": {
                "width": 1200,
                "height": 800,
            },
        },
        "modules": {
            "course_manager": {
                "enabled": True,
            },
            "file_organizer": {
                "enabled": True,
                "default_storage_path": "~/Documents/Academic_Organizer_Test",
            },
            "assignment_tracker": {
                "enabled": True,
                "reminder_days_before": 3,
            },
            "study_enhancement": {
                "enabled": True,
            },
            "lms_bridge": {
                "enabled": False,
            },
        },
        "ai": {
            "enabled": False,  # Disable AI in tests
            "api_type": "openrouter",
            "api_key_env_var": "OPENROUTER_API_KEY",
        },
    }


@pytest.fixture
def in_memory_db():
    """Create an in-memory database for testing."""
    db_manager = DatabaseManager(":memory:")
    db_manager.initialize_database()
    yield db_manager
    db_manager.close()


@pytest.fixture
def sample_courses(in_memory_db):
    """Create sample courses in the database."""
    courses = [
        {"name": "Calculus II", "code": "MATH 201", "semester": "Spring 2025"},
        {"name": "Physics 101", "code": "PHYS 101", "semester": "Spring 2025"},
        {"name": "Data Structures", "code": "CS 201", "semester": "Spring 2025"},
    ]
    
    for course in courses:
        in_memory_db.execute_update(
            "INSERT INTO courses (name, code, semester) VALUES (?, ?, ?)",
            (course["name"], course["code"], course["semester"])
        )
    
    return courses


@pytest.fixture
def sample_assignments(in_memory_db, sample_courses):
    """Create sample assignments in the database."""
    # Get course IDs
    courses = in_memory_db.execute_query("SELECT id, code FROM courses")
    course_ids = {course["code"]: course["id"] for course in courses}
    
    assignments = [
        {
            "title": "Calculus Homework 5",
            "course_code": "MATH 201",
            "due_date": "2025-04-15",
            "status": "Not Started",
            "priority": 2,
        },
        {
            "title": "Physics Lab Report",
            "course_code": "PHYS 101",
            "due_date": "2025-04-20",
            "status": "Not Started",
            "priority": 1,
        },
        {
            "title": "Programming Project",
            "course_code": "CS 201",
            "due_date": "2025-05-01",
            "status": "Not Started",
            "priority": 2,
        },
    ]
    
    for assignment in assignments:
        course_id = course_ids[assignment["course_code"]]
        in_memory_db.execute_update(
            "INSERT INTO assignments (course_id, title, due_date, status, priority) VALUES (?, ?, ?, ?, ?)",
            (
                course_id,
                assignment["title"],
                assignment["due_date"],
                assignment["status"],
                assignment["priority"],
            )
        )
    
    return assignments