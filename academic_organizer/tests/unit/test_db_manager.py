"""
Unit tests for the database manager.
"""

import os
import tempfile
import unittest
from pathlib import Path

import pytest

from academic_organizer.src.database.db_manager import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test cases for the database manager."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.db_path = self.temp_path / "test.db"
        
        # Create a database manager with an in-memory database
        self.db_manager = DatabaseManager(":memory:")
        self.db_manager.initialize_database()

    def tearDown(self):
        """Tear down test fixtures."""
        # Close the database connection
        self.db_manager.close()
        
        # Clean up temporary directory
        self.temp_dir.cleanup()

    def test_initialize_database(self):
        """Test database initialization."""
        # Create a database manager with a file database
        file_db_manager = DatabaseManager(self.db_path)
        result = file_db_manager.initialize_database()
        file_db_manager.close()
        
        # Verify initialization was successful
        self.assertTrue(result)
        self.assertTrue(self.db_path.exists())

    def test_course_operations(self):
        """Test course CRUD operations."""
        # Insert a course
        self.db_manager.execute_update(
            "INSERT INTO courses (name, code, semester, description) VALUES (?, ?, ?, ?)",
            ("Calculus II", "MATH 201", "Spring 2025", "Advanced calculus topics")
        )
        
        # Query the course
        courses = self.db_manager.execute_query(
            "SELECT * FROM courses WHERE code = ?",
            ("MATH 201",)
        )
        
        # Verify course was inserted
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0]["name"], "Calculus II")
        self.assertEqual(courses[0]["code"], "MATH 201")
        self.assertEqual(courses[0]["semester"], "Spring 2025")
        self.assertEqual(courses[0]["description"], "Advanced calculus topics")
        
        # Update the course
        self.db_manager.execute_update(
            "UPDATE courses SET name = ? WHERE code = ?",
            ("Advanced Calculus", "MATH 201")
        )
        
        # Query the updated course
        courses = self.db_manager.execute_query(
            "SELECT * FROM courses WHERE code = ?",
            ("MATH 201",)
        )
        
        # Verify course was updated
        self.assertEqual(courses[0]["name"], "Advanced Calculus")
        
        # Delete the course
        self.db_manager.execute_update(
            "DELETE FROM courses WHERE code = ?",
            ("MATH 201",)
        )
        
        # Query the deleted course
        courses = self.db_manager.execute_query(
            "SELECT * FROM courses WHERE code = ?",
            ("MATH 201",)
        )
        
        # Verify course was deleted
        self.assertEqual(len(courses), 0)

    def test_assignment_operations(self):
        """Test assignment CRUD operations."""
        # Insert a course first (for foreign key constraint)
        self.db_manager.execute_update(
            "INSERT INTO courses (name, code, semester) VALUES (?, ?, ?)",
            ("Calculus II", "MATH 201", "Spring 2025")
        )
        
        # Get the course ID
        courses = self.db_manager.execute_query(
            "SELECT id FROM courses WHERE code = ?",
            ("MATH 201",)
        )
        course_id = courses[0]["id"]
        
        # Insert an assignment
        self.db_manager.execute_update(
            "INSERT INTO assignments (course_id, title, description, due_date, status, priority) VALUES (?, ?, ?, ?, ?, ?)",
            (course_id, "Homework 5", "Problems 1-20", "2025-04-15", "Not Started", 1)
        )
        
        # Query the assignment
        assignments = self.db_manager.execute_query(
            "SELECT * FROM assignments WHERE title = ?",
            ("Homework 5",)
        )
        
        # Verify assignment was inserted
        self.assertEqual(len(assignments), 1)
        self.assertEqual(assignments[0]["course_id"], course_id)
        self.assertEqual(assignments[0]["title"], "Homework 5")
        self.assertEqual(assignments[0]["description"], "Problems 1-20")
        self.assertEqual(assignments[0]["status"], "Not Started")
        
        # Update the assignment
        self.db_manager.execute_update(
            "UPDATE assignments SET status = ? WHERE title = ?",
            ("In Progress", "Homework 5")
        )
        
        # Query the updated assignment
        assignments = self.db_manager.execute_query(
            "SELECT * FROM assignments WHERE title = ?",
            ("Homework 5",)
        )
        
        # Verify assignment was updated
        self.assertEqual(assignments[0]["status"], "In Progress")

    def test_full_text_search(self):
        """Test full-text search functionality."""
        # Insert a material
        self.db_manager.execute_update(
            "INSERT INTO materials (title, file_path, content_text, tags) VALUES (?, ?, ?, ?)",
            ("Calculus Notes", "/path/to/notes.pdf", "Derivatives and integrals are fundamental concepts in calculus", "math,calculus,notes")
        )
        
        # Verify the FTS index was updated via trigger
        results = self.db_manager.execute_query(
            "SELECT * FROM fts_materials WHERE content_text MATCH ?",
            ("derivatives",)
        )
        
        # Verify search results
        self.assertEqual(len(results), 1)
        
        # Search for a tag
        results = self.db_manager.execute_query(
            "SELECT * FROM fts_materials WHERE tags MATCH ?",
            ("calculus",)
        )
        
        # Verify search results
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()