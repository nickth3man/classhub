import pytest
from pathlib import Path
from src.modules.file_organizer.file_organizer import AdaptiveFileOrganizer

@pytest.fixture
def file_organizer(tmp_path):
    return AdaptiveFileOrganizer(tmp_path)

@pytest.fixture
def sample_file(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Sample content for testing")
    return file_path

def test_import_file_success(file_organizer, sample_file):
    """Test successful file import"""
    result = file_organizer.import_file(sample_file)
    assert result == True
    assert (file_organizer.base_storage_path / "incoming" / sample_file.name).exists()

def test_import_file_nonexistent(file_organizer):
    """Test importing non-existent file"""
    result = file_organizer.import_file(Path("nonexistent.txt"))
    assert result == False

def test_import_file_duplicate(file_organizer, sample_file):
    """Test importing the same file twice"""
    file_organizer.import_file(sample_file)
    result = file_organizer.import_file(sample_file)
    assert result == True
    # TODO: Add verification for duplicate handling

def test_search_files(file_organizer, sample_file):
    """Test file search functionality"""
    file_organizer.import_file(sample_file)
    results = file_organizer.search_files("Sample content")
    # TODO: Update assertion once search is implemented
    assert isinstance(results, list)
