import pytest
from datetime import datetime, timedelta
from academic_organizer.src.database.operations.assignment_ops import AssignmentManager
from academic_organizer.src.database.models.assignment import Assignment
from academic_organizer.src.database.models.course import Course

@pytest.fixture
def sample_course(session):
    course = Course(name="MATH 201: Calculus II", code="MATH201")
    session.add(course)
    session.commit()
    return course

@pytest.fixture
def sample_assignment_data(sample_course):
    return {
        "title": "Test Assignment",
        "course": sample_course.name,
        "due_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        "status": "Not Started",
        "priority": "Medium",
        "estimated_time": 5,
        "description": "Test assignment description"
    }

class TestAssignmentManager:
    def test_create_assignment(self, sample_assignment_data):
        """Test creating a new assignment."""
        assignment = AssignmentManager.create_assignment(sample_assignment_data)
        assert assignment['title'] == sample_assignment_data['title']
        assert assignment['course'] == sample_assignment_data['course']

    def test_get_assignment(self, sample_assignment_data):
        """Test retrieving an assignment."""
        created = AssignmentManager.create_assignment(sample_assignment_data)
        retrieved = AssignmentManager.get_assignment(created['id'])
        assert retrieved['title'] == sample_assignment_data['title']

    def test_update_assignment(self, sample_assignment_data):
        """Test updating an assignment."""
        created = AssignmentManager.create_assignment(sample_assignment_data)
        updated_data = sample_assignment_data.copy()
        updated_data['title'] = "Updated Assignment"
        updated = AssignmentManager.update_assignment(created['id'], updated_data)
        assert updated['title'] == "Updated Assignment"

    def test_delete_assignment(self, sample_assignment_data):
        """Test deleting an assignment."""
        created = AssignmentManager.create_assignment(sample_assignment_data)
        assert AssignmentManager.delete_assignment(created['id']) is True
        assert AssignmentManager.get_assignment(created['id']) is None

    def test_get_all_assignments(self, sample_assignment_data):
        """Test retrieving all assignments."""
        AssignmentManager.create_assignment(sample_assignment_data)
        assignments = AssignmentManager.get_all_assignments()
        assert len(assignments) > 0