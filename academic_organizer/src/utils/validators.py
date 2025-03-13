"""Input validation and sanitization utilities."""
import re
from typing import Any, Optional
import html
from .error_handler import ValidationError

def sanitize_input(value: Any) -> str:
    """Sanitize input string to prevent XSS and injection attacks."""
    if value is None:
        return ""
    
    # Convert to string and trim
    value = str(value).strip()
    
    # HTML escape
    value = html.escape(value)
    
    # Remove potentially dangerous characters
    value = re.sub(r'[<>\'";`]', '', value)
    
    return value

def validate_email(email: str) -> str:
    """Validate email format."""
    email = sanitize_input(email)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format")
    return email

def validate_phone(phone: str) -> str:
    """Validate phone number format."""
    phone = sanitize_input(phone)
    # Remove all non-numeric characters
    phone = re.sub(r'\D', '', phone)
    if not (7 <= len(phone) <= 15):
        raise ValidationError("Invalid phone number length")
    return phone

def validate_file_path(path: str) -> str:
    """Validate and sanitize file path."""
    path = sanitize_input(path)
    # Remove potentially dangerous path traversal attempts
    path = re.sub(r'\.\./', '', path)
    path = re.sub(r'\.\.\\', '', path)
    return path

def validate_date_format(date_str: str) -> bool:
    """Validate date string format (YYYY-MM-DD)."""
    pattern = r'^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$'
    return bool(re.match(pattern, date_str))

def validate_time_format(time_str: str) -> bool:
    """Validate time string format (HH:MM or HH:MM:SS)."""
    pattern = r'^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$'
    return bool(re.match(pattern, time_str))
