"""
Domain models for the Course Manager module.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Instructor:
    name: str
    email: Optional[str] = None
    office_hours: Optional[str] = None
    office_location: Optional[str] = None
    contact_info: Optional[str] = None

@dataclass
class Schedule:
    days: List[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None

@dataclass
class Course:
    code: str
    name: str
    instructor: Instructor
    schedule: Schedule
    description: Optional[str] = None
    syllabus_path: Optional[str] = None

@dataclass
class ImportResult:
    success: bool
    course: Optional[Course] = None
    error_message: Optional[str] = None