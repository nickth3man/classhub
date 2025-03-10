import pytest
from pathlib import Path
from academic_organizer.modules.file_organizer import FileOrganizer

class TestFileOrganizerIntegration:
    def test_file_import_and_categorization(self, qtbot, file_widget, tmp_path):
        """Test file import and automatic categorization"""
        # Create test files
        test_files = [
            ("syllabus.pdf", b"syllabus content"),
            ("assignment.docx", b"assignment content"),
            ("notes.txt", b"lecture notes")
        ]
        
        for name, content in test_files:
            file_path = tmp_path / name
            file_path.write_bytes(content)
            file_widget.import_file(str(file_path))
            
        # Verify categorization
        categories = file_widget.get_file_categories()
        assert "Syllabi" in categories
        assert "Assignments" in categories
        assert "Notes" in categories
        
    def test_content_analysis(self, qtbot, file_widget, sample_file):
        """Test AI-powered content analysis"""
        # Analyze file content
        analysis = file_widget.analyze_content(sample_file)
        
        # Verify analysis results
        assert "keywords" in analysis
        assert "summary" in analysis
        assert "suggested_category" in analysis
        
    def test_file_search(self, qtbot, file_widget, sample_files):
        """Test file search functionality"""
        # Perform various searches
        keyword_results = file_widget.search_files("programming")
        date_results = file_widget.search_files_by_date(
            datetime.now() - timedelta(days=7),
            datetime.now()
        )
        category_results = file_widget.search_files_by_category("Assignments")
        
        # Verify search results
        assert len(keyword_results) > 0
        assert len(date_results) > 0
        assert len(category_results) > 0
        
    def test_file_versioning(self, qtbot, file_widget, sample_file):
        """Test file version control"""
        # Create multiple versions
        for i in range(3):
            file_widget.update_file(sample_file, f"Content version {i}")
            
        # Verify version history
        versions = file_widget.get_file_versions(sample_file)
        assert len(versions) == 3
        
        # Test version restoration
        file_widget.restore_version(sample_file, versions[0].id)
        current_content = file_widget.get_file_content(sample_file)
        assert current_content == "Content version 0"