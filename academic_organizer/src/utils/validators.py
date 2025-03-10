"""Data validation utilities."""

from typing import Dict, Any
from academic_organizer.utils.exceptions import ValidationError

def validate_course_data(data: Dict[str, Any]) -> None:
    """
    Validate course data.
    
    Args:
        data: Dictionary containing course information
        
    Raises:
        ValidationError: If validation fails
    """
    required_fields = ['code', 'name', 'semester', 'year']
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
        
    if not isinstance(data['code'], str) or len(data['code']) > 20:
        raise ValidationError("Invalid course code")
        
    if not isinstance(data['name'], str) or len(data['name']) > 100:
        raise ValidationError("Invalid course name")
        
    if not isinstance(data['semester'], str) or len(data['semester']) > 20:
        raise ValidationError("Invalid semester")
        
    if not isinstance(data['year'], int) or data['year'] < 1900:
        raise ValidationError("Invalid year")

def validate_instructor_data(data: Dict[str, Any]) -> None:
    """
    Validate instructor data.
    
    Args:
        data: Dictionary containing instructor information
        
    Raises:
        ValidationError: If validation fails
    """
    required_fields = ['first_name', 'last_name', 'email']
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
            
    if not isinstance(data['first_name'], str) or len(data['first_name']) > 50:
        raise ValidationError("Invalid first name")
        
    if not isinstance(data['last_name'], str) or len(data['last_name']) > 50:
        raise ValidationError("Invalid last name")
        
    if not isinstance(data['email'], str) or len(data['email']) > 100:
        raise ValidationError("Invalid email")