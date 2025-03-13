"""
Abstract base class for database managers.
"""
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy.orm import Session

class BaseDatabaseManager(ABC):
    """
    Abstract base class for database managers.
    Defines the interface for database operations.
    """

    @abstractmethod
    def __init__(self, db_url: str):
        """Initialize database manager."""
        pass

    @abstractmethod
    def initialize_database(self) -> None:
        """Create database schema if it doesn't exist."""
        pass

    @abstractmethod
    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        pass

    @abstractmethod
    def verify_connection(self) -> bool:
        """Verify database connection is working."""
        pass

    @abstractmethod
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Create a backup of the database."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connections."""
        pass