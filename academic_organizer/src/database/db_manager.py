"""
Database Manager for Academic Organizer.
Implements repository pattern and connection management.
"""

import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Any, Optional

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from academic_organizer.utils.exceptions import DatabaseError
from academic_organizer.database.models import Base
from academic_organizer.database.repositories import (
    CourseRepository,
    AssignmentRepository,
    MaterialRepository,
    NotesRepository,
    InstructorRepository
)

class DatabaseManager:
    """Manages database connections and provides access to repositories."""

    def __init__(self, db_path: Path):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.engine = None
        self.SessionFactory = None
        self._setup_engine()
        self._initialize_repositories()

    def _setup_engine(self) -> None:
        """Initialize database engine and session factory."""
        try:
            db_url = f"sqlite:///{self.db_path}"
            self.engine = create_engine(
                db_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,  # Enable connection health checks
                connect_args={"check_same_thread": False}  # Required for SQLite
            )
            self.SessionFactory = sessionmaker(bind=self.engine)
        except Exception as e:
            raise DatabaseError(f"Failed to setup database engine: {e}")

    def _initialize_repositories(self) -> None:
        """Initialize repository instances."""
        self.courses = CourseRepository(self)
        self.assignments = AssignmentRepository(self)
        self.materials = MaterialRepository(self)
        self.notes = NotesRepository(self)
        self.instructors = InstructorRepository(self)

    def initialize_database(self) -> None:
        """Create database schema if it doesn't exist."""
        try:
            Base.metadata.create_all(self.engine)
            self.logger.info("Database schema created successfully")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to create database schema: {e}")

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise DatabaseError(f"Database transaction failed: {e}")
        finally:
            session.close()

    def verify_connection(self) -> bool:
        """Verify database connection is working."""
        try:
            with self.session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"Database connection verification failed: {e}")
            return False

    def backup_database(self, backup_path: Optional[Path] = None) -> Path:
        """Create a backup of the database."""
        if backup_path is None:
            backup_path = self.db_path.parent / f"{self.db_path.stem}_backup.db"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            raise DatabaseError(f"Failed to backup database: {e}")

    def close(self) -> None:
        """Close database connections."""
        try:
            if self.engine:
                self.engine.dispose()
            self.logger.info("Database connections closed")
        except Exception as e:
            raise DatabaseError(f"Failed to close database connections: {e}")
