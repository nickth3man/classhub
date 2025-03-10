import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QDate
from academic_organizer.src.gui.assignment_view import AssignmentDialog, AssignmentViewWidget

# Fixture for QApplication instance
@pytest.fixture(scope="session")
def qapp():
    app = QApplication([])
    yield app
    app.quit()

# Fixtures for test data
@pytest.fixture
def sample_assignment_data():
    return {
        "title": "Test Assignment",
        "course": "MATH 201: Calculus II",
        "due_date": "2025-03-14",
        "status": "Not Started",
        "priority": "Medium",
        "estimated_time": 5,
        "description": "Test assignment description"
    }

class TestAssignmentDialog:
    def test_dialog_initialization(self, qapp):
        """Test that dialog initializes with default values"""
        dialog = AssignmentDialog()
        
        assert dialog.windowTitle() == "New Assignment"
        assert dialog.title_input.text() == ""
        assert dialog.status_combo.currentText() == "Not Started"
        assert dialog.priority_combo.currentText() == "Low"
        assert dialog.time_input.value() == 1

    def test_dialog_initialization_with_data(self, qapp, sample_assignment_data):
        """Test that dialog initializes correctly with existing data"""
        dialog = AssignmentDialog(assignment_data=sample_assignment_data)
        
        assert dialog.windowTitle() == "Edit Assignment"
        assert dialog.title_input.text() == sample_assignment_data["title"]
        assert dialog.course_combo.currentText() == sample_assignment_data["course"]
        assert dialog.status_combo.currentText() == sample_assignment_data["status"]
        assert dialog.priority_combo.currentText() == sample_assignment_data["priority"]
        assert dialog.time_input.value() == sample_assignment_data["estimated_time"]

    def test_validation_empty_title(self, qapp, qtbot):
        """Test that validation fails with empty title"""
        dialog = AssignmentDialog()
        qtbot.addWidget(dialog)
        
        # Clear title and try to accept
        dialog.title_input.clear()
        
        # Mock QMessageBox.warning
        def mock_warning(*args, **kwargs):
            return QMessageBox.StandardButton.Ok
        
        QMessageBox.warning = mock_warning
        
        # Try to accept the dialog
        dialog.validate_and_accept()
        
        assert dialog.result() != QDialog.DialogCode.Accepted

    def test_validation_past_date(self, qapp, qtbot):
        """Test that validation fails with past due date"""
        dialog = AssignmentDialog()
        qtbot.addWidget(dialog)
        
        # Set past date
        past_date = QDate.currentDate().addDays(-1)
        dialog.due_date_input.setDate(past_date)
        
        # Mock QMessageBox.warning
        def mock_warning(*args, **kwargs):
            return QMessageBox.StandardButton.Ok
        
        QMessageBox.warning = mock_warning
        
        # Try to accept the dialog
        dialog.validate_and_accept()
        
        assert dialog.result() != QDialog.DialogCode.Accepted

    def test_get_assignment_data(self, qapp, qtbot):
        """Test that get_assignment_data returns correct data"""
        dialog = AssignmentDialog()
        qtbot.addWidget(dialog)
        
        # Set test data
        dialog.title_input.setText("Test Assignment")
        dialog.course_combo.setCurrentText("MATH 201: Calculus II")
        test_date = QDate.currentDate().addDays(7)
        dialog.due_date_input.setDate(test_date)
        dialog.status_combo.setCurrentText("In Progress")
        dialog.priority_combo.setCurrentText("High")
        dialog.time_input.setValue(3)
        dialog.description_input.setText("Test description")
        
        # Get data
        data = dialog.get_assignment_data()
        
        assert data["title"] == "Test Assignment"
        assert data["course"] == "MATH 201: Calculus II"
        assert data["due_date"] == test_date.toString("yyyy-MM-dd")
        assert data["status"] == "In Progress"
        assert data["priority"] == "High"
        assert data["estimated_time"] == 3
        assert data["description"] == "Test description"

class TestAssignmentViewWidget:
    @pytest.fixture
    def widget(self, qapp):
        return AssignmentViewWidget()

    def test_widget_initialization(self, widget):
        """Test that widget initializes correctly"""
        assert widget.assignment_table is not None
        assert widget.assignment_table.columnCount() == 7  # Verify column count
        assert widget.assignment_table.rowCount() == 0     # Should start empty

    def test_add_assignment(self, widget, qtbot, sample_assignment_data):
        """Test adding a new assignment"""
        # Mock the dialog to return test data
        def mock_dialog_exec():
            return QDialog.DialogCode.Accepted
            
        def mock_get_assignment_data():
            return sample_assignment_data
            
        widget._show_dialog = lambda: (mock_dialog_exec(), mock_get_assignment_data())
        
        # Initial row count
        initial_rows = widget.assignment_table.rowCount()
        
        # Add assignment
        widget._add_assignment()
        
        # Verify new row was added
        assert widget.assignment_table.rowCount() == initial_rows + 1
        assert widget.assignment_table.item(0, 0).text() == sample_assignment_data["title"]

    def test_edit_assignment(self, widget, qtbot, sample_assignment_data):
        """Test editing an existing assignment"""
        # First add an assignment
        widget._add_assignment_to_table(sample_assignment_data)
        
        # Prepare modified data
        modified_data = sample_assignment_data.copy()
        modified_data["title"] = "Modified Assignment"
        
        # Mock the dialog to return modified data
        def mock_dialog_exec():
            return QDialog.DialogCode.Accepted
            
        def mock_get_assignment_data():
            return modified_data
            
        widget._show_dialog = lambda: (mock_dialog_exec(), mock_get_assignment_data())
        
        # Edit the assignment
        widget._edit_assignment(0)
        
        # Verify the modification
        assert widget.assignment_table.item(0, 0).text() == "Modified Assignment"

    def test_delete_assignment(self, widget, qtbot, sample_assignment_data):
        """Test deleting an assignment"""
        # First add an assignment
        widget._add_assignment_to_table(sample_assignment_data)
        initial_rows = widget.assignment_table.rowCount()
        
        # Delete the assignment
        widget._delete_assignment(0)
        
        # Verify row was deleted
        assert widget.assignment_table.rowCount() == initial_rows - 1
