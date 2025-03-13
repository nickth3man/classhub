"""Test configuration and fixtures."""
import pytest
from pathlib import Path
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..src.database.models.base import Base
from ..src.database.db_manager import DatabaseManager
from ..src.config.config_manager import ConfigManager

@pytest.fixture(scope="session")
def test_db_path():
    """Create temporary database file."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = Path(f.name)
    print(f"Temporary database path: {temp_db_path}")  # Added log
    yield temp_db_path
    temp_db_path.unlink()

@pytest.fixture(scope="session")
def test_config(test_db_path):
    """Create test configuration."""
    return {
        'database': {
            'path': str(test_db_path),
            'pool_size': 3,
            'max_overflow': 5,
            'pool_timeout': 10
        },
        'testing': {
            'enabled': True,
            'log_level': 'DEBUG'
        }
    }

@pytest.fixture(scope="session")
def db_manager(test_config):
    """Create database manager instance."""
    manager = DatabaseManager(ConfigManager(test_config))
    manager.initialize_database()
    yield manager
    manager.cleanup()

@pytest.fixture
def db_session(db_manager):
    """Create database session."""
    with db_manager.session_scope() as session:
        yield session
