"""
Course Manager module for Academic Organizer.
Handles course information extraction, management, and organization.
"""

from .course_manager import CourseManager
from .extractors import OCRExtractor, TextPatternExtractor
from .models import Course, Instructor, Schedule

__all__ = ['CourseManager', 'OCRExtractor', 'TextPatternExtractor', 
           'Course', 'Instructor', 'Schedule']