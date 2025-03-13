"""
PostgreSQL Database Manager for Academic Organizer.
Implements repository pattern and connection management for PostgreSQL.
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

import subprocess
import urllib.parse # For parsing database URL

class PostgresDatabaseManager(BaseDatabaseManager):
    """Manages PostgreSQL database connections and provides access to repositories."""

    def __init__(self, db_url: str): # Changed to accept db_url directly
        super().__init__(db_url)
        self.logger = logging.getLogger(__name__)
        self.db_url = db_url # Using db_url directly
        self.engine = None
        self.SessionFactory = None
        self._setup_engine()
        self._initialize_repositories()

    def _setup_engine(self) -> None:
        """Initialize PostgreSQL engine and session factory."""
        try:
            self.engine = create_engine(
                self.db_url, # Use db_url from base class
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,  # Enable connection health checks
                pool_size=10, # Example pool size
                max_overflow=20 # Example max overflow
            )
            self.SessionFactory = sessionmaker(bind=self.engine)
        except Exception as e:
            raise DatabaseError(f"Failed to setup PostgreSQL engine: {e}")

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
            print("PostgreSQL database schema created.")
            self.logger.info("PostgreSQL database schema created successfully")
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to create PostgreSQL database schema: {e}")

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise DatabaseError(f"PostgreSQL transaction failed: {e}")
        finally:
            session.close()

    def verify_connection(self) -> bool:
        """Verify PostgreSQL database connection is working."""
        try:
            with self.session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"PostgreSQL connection verification failed: {e}")
            return False

    def backup_database(self, backup_path: Optional[Path] = None) -> Path:
        """Create a backup of the PostgreSQL database using pg_dump."""
        if backup_path is None:
            backup_path = self.db_path.parent / f"{self.db_path.stem}_backup.sql" # Changed extension to .sql

        try:
            # Construct pg_dump command - adjust as necessary for Windows and PostgreSQL installation
            db_url_parts = urllib.parse.urlparse(self.db_url)
            cmd = [
                "pg_dump",
                "-h", db_url_parts.hostname or "localhost", # Default to localhost if no hostname
                "-p", str(db_url_parts.port or 5432), # Default port 5432 if no port
                "-U", db_url_parts.username or "postgres", # Default user postgres
                "-Fc", # Format custom, compressed archive
                "-f", str(backup_path),
                db_url_parts.path[1:] # Database name, remove leading slash
            ]

            # Execute pg_dump command - consider using subprocess.run for better control and error handling
            subprocess.run(cmd, check=True) # check=True will raise an exception if the command fails

            self.logger.info(f"PostgreSQL database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            raise DatabaseError(f"Failed to backup PostgreSQL database: {e}")

    def close(self) -> None:
        """Close PostgreSQL database connections."""
        try:
            if self.engine:
                self.engine.dispose()
            self.logger.info("PostgreSQL connections closed")
        except Exception as e:
            raise DatabaseError(f"Failed to close PostgreSQL connections: {e}")

    def get_connection_pool_size(self) -> Optional[int]:
        """Get the size of the connection pool."""
        return self.engine.pool.size() if self.engine and self.engine.pool else None

    def get_connections_in_use(self) -> Optional[int]:
        """Get the number of connections currently in use."""
        return self.engine.pool.checkedin() if self.engine and self.engine.pool else None

    def get_connections_idle(self) -> Optional[int]:
        """Get the number of idle connections in the pool."""
        return self.engine.pool.checkedout() if self.engine and self.engine.pool else None