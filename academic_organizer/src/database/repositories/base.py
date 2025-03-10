"""Base repository implementation."""

from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from academic_organizer.utils.exceptions import DatabaseError
from academic_organizer.database.models import Base

T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    """Generic repository implementation for database operations."""

    def __init__(self, db_manager: 'DatabaseManager', model: Type[T]):
        self.db = db_manager
        self.model = model

    def create(self, **kwargs: Any) -> T:
        """Create a new record."""
        try:
            with self.db.session() as session:
                instance = self.model(**kwargs)
                session.add(instance)
                session.flush()  # Flush to get the ID
                return instance
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to create {self.model.__name__}: {e}")

    def get(self, id: int) -> Optional[T]:
        """Retrieve a record by ID."""
        try:
            with self.db.session() as session:
                return session.query(self.model).get(id)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to retrieve {self.model.__name__}: {e}")

    def get_all(self) -> List[T]:
        """Retrieve all records."""
        try:
            with self.db.session() as session:
                return session.query(self.model).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to retrieve {self.model.__name__} list: {e}")

    def update(self, id: int, **kwargs: Any) -> Optional[T]:
        """Update a record."""
        try:
            with self.db.session() as session:
                instance = session.query(self.model).get(id)
                if instance:
                    for key, value in kwargs.items():
                        setattr(instance, key, value)
                return instance
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to update {self.model.__name__}: {e}")

    def delete(self, id: int) -> bool:
        """Delete a record."""
        try:
            with self.db.session() as session:
                instance = session.query(self.model).get(id)
                if instance:
                    session.delete(instance)
                    return True
                return False
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to delete {self.model.__name__}: {e}")

    def exists(self, id: int) -> bool:
        """Check if a record exists."""
        try:
            with self.db.session() as session:
                return session.query(self.model).filter_by(id=id).first() is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to check {self.model.__name__} existence: {e}")