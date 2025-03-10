"""Custom exceptions for the Academic Organizer."""

class AcademicOrganizerError(Exception):
    """Base exception for all application errors."""
    pass

class InitializationError(AcademicOrganizerError):
    """Raised when application initialization fails."""
    pass

class DatabaseError(AcademicOrganizerError):
    """Raised when database operations fail."""
    pass

class ModuleError(AcademicOrganizerError):
    """Raised when module operations fail."""
    pass

class GUIError(AcademicOrganizerError):
    """Raised when GUI operations fail."""
    pass