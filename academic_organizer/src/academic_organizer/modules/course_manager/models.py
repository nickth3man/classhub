"""
Data models for the Course Manager module.
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
    location: str
    
@dataclass
class Course:
    name: str
    code: str
    instructor: Instructor
    schedule: Schedule
    syllabus_path: Optional[str] = None
    description: Optional[str] = None
    grading_scheme: Optional[dict] = None