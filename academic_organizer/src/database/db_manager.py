"""
Database Manager for the Academic Organizer application.

This module handles database operations, including schema creation,
data access, and query optimization.
"""

import logging
import sqlite3
from pathlib import Path


class DatabaseManager:
    """
    Database Manager for the Academic Organizer application.
    
    This class is responsible for:
    - Database connection management
    - Schema creation and updates
    - Providing data access methods for other components
    - Query optimization
    - Transaction management
    """
    
    def __init__(self, db_path):
        """
        Initialize the database manager.
        
        Args:
            db_path (str or Path): Path to the SQLite database file
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = Path(db_path)
        self.connection = None
        
    def initialize_database(self):
        """
        Initialize the database, creating it if it doesn't exist.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Ensure the parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to the database
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Create tables if they don't exist
            self._create_tables()
            
            self.logger.info(f"Database initialized successfully at {self.db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}", exc_info=True)
            return False
    
    def _create_tables(self):
        """
        Create database tables if they don't exist.
        """
        cursor = self.connection.cursor()
        
        # Create Courses table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT,
            semester TEXT,
            instructor_id INTEGER,
            syllabus_path TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instructor_id) REFERENCES instructors(id)
        )
        ''')
        
        # Create Instructors table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            office_location TEXT,
            office_hours TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create Assignments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            due_date TIMESTAMP,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 0,
            estimated_time INTEGER,  -- in minutes
            actual_time INTEGER,     -- in minutes
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
        ''')
        
        # Create Materials table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,
            tags TEXT,
            content_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
        ''')
        
        # Create Notes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            assignment_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (assignment_id) REFERENCES assignments(id)
        )
        ''')
        
        # Create virtual table for full-text search
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_materials
        USING fts5(
            title, 
            content_text,
            tags,
            content='materials',
            content_rowid='id'
        )
        ''')
        
        # Create trigger to keep FTS index updated
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS materials_ai AFTER INSERT ON materials BEGIN
            INSERT INTO fts_materials(rowid, title, content_text, tags)
            VALUES (new.id, new.title, new.content_text, new.tags);
        END;
        ''')
        
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS materials_ad AFTER DELETE ON materials BEGIN
            INSERT INTO fts_materials(fts_materials, rowid, title, content_text, tags)
            VALUES('delete', old.id, old.title, old.content_text, old.tags);
        END;
        ''')
        
        cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS materials_au AFTER UPDATE ON materials BEGIN
            INSERT INTO fts_materials(fts_materials, rowid, title, content_text, tags)
            VALUES('delete', old.id, old.title, old.content_text, old.tags);
            INSERT INTO fts_materials(rowid, title, content_text, tags)
            VALUES (new.id, new.title, new.content_text, new.tags);
        END;
        ''')
        
        self.connection.commit()
        self.logger.info("Database tables created successfully")
    
    def close(self):
        """
        Close the database connection.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Database connection closed")
    
    def get_connection(self):
        """
        Get the database connection.
        
        Returns:
            sqlite3.Connection: The database connection
        """
        if not self.connection:
            self.initialize_database()
        return self.connection
    
    def execute_query(self, query, params=None):
        """
        Execute a query and return the results.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            list: List of rows as dictionaries
        """
        try:
            cursor = self.get_connection().cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            results = [dict(row) for row in cursor.fetchall()]
            return results
            
        except Exception as e:
            self.logger.error(f"Error executing query: {e}", exc_info=True)
            raise
    
    def execute_update(self, query, params=None):
        """
        Execute an update query (INSERT, UPDATE, DELETE).
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            int: Number of rows affected
        """
        try:
            cursor = self.get_connection().cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            self.connection.commit()
            return cursor.rowcount
            
        except Exception as e:
            self.logger.error(f"Error executing update: {e}", exc_info=True)
            self.connection.rollback()
            raise