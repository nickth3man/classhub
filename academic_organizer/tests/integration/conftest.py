import pytest
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from academic_organizer.src.database.base import Base
from academic_organizer.src.database.models import *  # Import all models

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine"""
    return create_engine('sqlite:///:memory:')

@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables for testing"""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def session(engine, tables):
    """Create a new database session for a test"""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app