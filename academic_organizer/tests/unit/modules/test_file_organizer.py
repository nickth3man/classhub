"""
Unit tests for the Adaptive File Organizer module.
"""
import pytest
from unittest.mock import Mock, patch
from academic_organizer.modules.file_organizer import AdaptiveFileOrganizer

class TestAdaptiveFileOrganizer:
    """Tests for the AdaptiveFileOrganizer class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db_manager_mock = Mock()
        self.file_organizer = AdaptiveFileOrganizer(self.db_manager_mock)

    def teardown_method(self):
        """Tear down test fixtures after each test method."""
        pass

    def test_import_file_pdf(self):
        """Test import_file method with a PDF file."""
        # Arrange
        file_path = "test_syllabus.pdf" # Placeholder path
        # Act
        material_id = self.file_organizer.import_file(file_path)
        # Assert
        assert material_id is not None

    def test_extract_text_content_pdf(self, temp_file_path):
        """Test extract_text_content method with a PDF file."""
        # Arrange
        pdf_content = b"%PDF-1.5\\n...dummy pdf content...\\n"  # Minimal PDF content
        test_pdf_path = Path(temp_file_path)
        test_pdf_path.write_bytes(pdf_content)

        # Act
        text_content = self.file_organizer.extract_text_content(test_pdf_path)

        # Assert
        assert isinstance(text_content, str)
        assert text_content != ""