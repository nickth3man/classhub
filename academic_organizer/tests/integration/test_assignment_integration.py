import pytest
from datetime import datetime, timedelta
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox

from academic_organizer.src.gui.assignment_view import AssignmentViewWidget
from academic_organizer.src.gui.assignment_dialog import AssignmentDialog
from academic_organizer.src.database.operations.assignment_ops import AssignmentManager
from academic_organizer.src.database.models.course import Course

@pytest.fixture
def app(qtbot):
    """Create the QApplication instance"""
    return QApplication.instance() or QApplication([])

@pytest.fixture
def sample_course(session):
    """Create a sample course for testing"""
    course = Course(name="TEST 101: Integration Testing", code="TEST101")
    session.add(course)
    session.commit()
    return course

@pytest.fixture
def assignment_widget(qtbot, sample_course):
    """Create and show the assignment widget"""
    widget = AssignmentViewWidget()
    qtbot.addWidget(widget)
    widget.show()
    return widget

@pytest.fixture
def sample_assignment_data(sample_course):
    """Create sample assignment data"""
    return {
        "title": "Integration Test Assignment",
        "course": sample_course.name,
        "due_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        "status": "Not Started",
        "priority": "High",
        "estimated_time": 3,
        "description": "Test assignment for integration testing"
    }

class TestAssignmentIntegration:
    def test_add_assignment_workflow(self, qtbot, assignment_widget, sample_assignment_data):
        """Test the complete workflow of adding a new assignment"""
        # Initial count of assignments
        initial_count = assignment_widget.assignment_table.rowCount()

        # Click the add button
        qtbot.mouseClick(assignment_widget.add_button, Qt.MouseButton.LeftButton)

        # Get the dialog that appears
        dialog = assignment_widget.findChild(AssignmentDialog)
        assert dialog is not None

        # Fill in the dialog fields
        dialog.title_input.setText(sample_assignment_data["title"])
        dialog.course_combo.setCurrentText(sample_assignment_data["course"])
        dialog.due_date_edit.setDate(datetime.strptime(sample_assignment_data["due_date"], '%Y-%m-%d'))
        dialog.priority_combo.setCurrentText(sample_assignment_data["priority"])
        dialog.status_combo.setCurrentText(sample_assignment_data["status"])
        dialog.time_spin.setValue(sample_assignment_data["estimated_time"])
        dialog.description_text.setPlainText(sample_assignment_data["description"])

        # Click OK
        qtbot.mouseClick(dialog.button_box.button(QMessageBox.StandardButton.Ok),
                        Qt.MouseButton.LeftButton)

        # Verify the assignment was added to the table
        assert assignment_widget.assignment_table.rowCount() == initial_count + 1
        
        # Verify the data in the table
        last_row = assignment_widget.assignment_table.rowCount() - 1
        assert assignment_widget.assignment_table.item(last_row, 1).text() == sample_assignment_data["title"]

    def test_edit_assignment_workflow(self, qtbot, assignment_widget, sample_assignment_data):
        """Test the complete workflow of editing an assignment"""
        # First add an assignment
        assignment = AssignmentManager.create_assignment(sample_assignment_data)
        assignment_widget._load_assignments()  # Refresh the table

        # Find the row with our assignment
        row = -1
        for i in range(assignment_widget.assignment_table.rowCount()):
            if assignment_widget.assignment_table.item(i, 0).data(Qt.ItemDataRole.UserRole) == assignment['id']:
                row = i
                break
        assert row != -1

        # Double click to edit
        item = assignment_widget.assignment_table.item(row, 1)  # Title column
        assignment_widget.assignment_table.setCurrentItem(item)
        qtbot.mouseDClick(assignment_widget.assignment_table.viewport(),
                         Qt.MouseButton.LeftButton,
                         pos=assignment_widget.assignment_table.visualItemRect(item).center())

        # Get the edit dialog
        dialog = assignment_widget.findChild(AssignmentDialog)
        assert dialog is not None

        # Modify the title
        new_title = "Updated Integration Test Assignment"
        dialog.title_input.setText(new_title)

        # Click OK
        qtbot.mouseClick(dialog.button_box.button(QMessageBox.StandardButton.Ok),
                        Qt.MouseButton.LeftButton)

        # Verify the change in the table
        assert assignment_widget.assignment_table.item(row, 1).text() == new_title

        # Verify the change in the database
        updated_assignment = AssignmentManager.get_assignment(assignment['id'])
        assert updated_assignment['title'] == new_title

    def test_delete_assignment_workflow(self, qtbot, assignment_widget, sample_assignment_data):
        """Test the complete workflow of deleting an assignment"""
        # First add an assignment
        assignment = AssignmentManager.create_assignment(sample_assignment_data)
        assignment_widget._load_assignments()  # Refresh the table

        initial_count = assignment_widget.assignment_table.rowCount()

        # Find the row with our assignment
        row = -1
        for i in range(initial_count):
            if assignment_widget.assignment_table.item(i, 0).data(Qt.ItemDataRole.UserRole) == assignment['id']:
                row = i
                break
        assert row != -1

        # Select the row
        assignment_widget.assignment_table.selectRow(row)

        # Click delete button
        qtbot.mouseClick(assignment_widget.delete_button, Qt.MouseButton.LeftButton)

        # Handle confirmation dialog
        def handle_dialog():
            dialog = QApplication.activeModalWidget()
            if dialog:
                qtbot.mouseClick(dialog.button(QMessageBox.StandardButton.Yes),
                               Qt.MouseButton.LeftButton)

        QTimer.singleShot(100, handle_dialog)
        
        # Verify the row was removed
        assert assignment_widget.assignment_table.rowCount() == initial_count - 1

        # Verify the assignment was deleted from the database
        assert AssignmentManager.get_assignment(assignment['id']) is None

    def test_assignment_sort_filter(self, qtbot, assignment_widget):
        """Test sorting and filtering assignments"""
        # Add multiple assignments with different priorities
        assignments = [
            {"title": "High Priority Task", "priority": "High"},
            {"title": "Medium Priority Task", "priority": "Medium"},
            {"title": "Low Priority Task", "priority": "Low"}
        ]

        for assignment_data in assignments:
            full_data = sample_assignment_data.copy()
            full_data.update(assignment_data)
            AssignmentManager.create_assignment(full_data)

        assignment_widget._load_assignments()

        # Test sorting by priority
        priority_column = 3  # Adjust based on your table structure
        assignment_widget.assignment_table.sortByColumn(priority_column, Qt.SortOrder.DescendingOrder)

        # Verify sort order
        assert assignment_widget.assignment_table.item(0, 1).text() == "High Priority Task"
        assert assignment_widget.assignment_table.item(2, 1).text() == "Low Priority Task"

    def test_error_handling(self, qtbot, assignment_widget, monkeypatch):
        """Test error handling during database operations"""
        def mock_db_error(*args, **kwargs):
            raise Exception("Database error")

        # Mock database error
        monkeypatch.setattr(AssignmentManager, "create_assignment", mock_db_error)

        # Try to add assignment
        qtbot.mouseClick(assignment_widget.add_button, Qt.MouseButton.LeftButton)
        dialog = assignment_widget.findChild(AssignmentDialog)
        
        # Fill minimal required fields
        dialog.title_input.setText("Test Assignment")
        
        # Click OK and verify error handling
        qtbot.mouseClick(dialog.button_box.button(QMessageBox.StandardButton.Ok),
                        Qt.MouseButton.LeftButton)

        # Verify error dialog appears
        error_dialog = QApplication.activeModalWidget()
        assert error_dialog is not None
        assert "Database error" in error_dialog.text()

    def test_due_date_notifications(self, qtbot, assignment_widget, sample_assignment_data):
        """Test due date notification integration"""
        # Create assignments with different due dates
        upcoming = sample_assignment_data.copy()
        upcoming["due_date"] = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        upcoming["title"] = "Upcoming Assignment"
        
        overdue = sample_assignment_data.copy()
        overdue["due_date"] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        overdue["title"] = "Overdue Assignment"
        
        AssignmentManager.create_assignment(upcoming)
        AssignmentManager.create_assignment(overdue)
        
        # Refresh view
        assignment_widget._load_assignments()
        
        # Verify color coding
        for row in range(assignment_widget.assignment_table.rowCount()):
            item = assignment_widget.assignment_table.item(row, 1)  # Title column
            if item.text() == "Upcoming Assignment":
                assert "background-color: yellow" in item.styleSheet()
            elif item.text() == "Overdue Assignment":
                assert "background-color: red" in item.styleSheet()

    def test_workload_calculation(self, qtbot, assignment_widget, sample_assignment_data):
        """Test workload calculation integration"""
        # Create multiple assignments
        assignments = [
            {"title": "Assignment 1", "estimated_time": 2},
            {"title": "Assignment 2", "estimated_time": 3},
            {"title": "Assignment 3", "estimated_time": 1}
        ]
        
        for assignment in assignments:
            data = sample_assignment_data.copy()
            data.update(assignment)
            AssignmentManager.create_assignment(data)
            
        assignment_widget._load_assignments()
        
        # Verify total workload calculation
        total_workload = assignment_widget.calculate_total_workload()
        assert total_workload == 6  # Sum of estimated times
        
        # Verify workload distribution visualization
        workload_chart = assignment_widget.workload_chart
        assert len(workload_chart.series()) == len(assignments)

    def test_file_attachment_integration(self, qtbot, assignment_widget, sample_assignment_data, tmp_path):
        """Test file attachment functionality"""
        # Create a temporary file
        test_file = tmp_path / "test_attachment.pdf"
        test_file.write_text("Test content")
        
        # Create assignment with attachment
        assignment_data = sample_assignment_data.copy()
        
        # Add attachment through UI
        qtbot.mouseClick(assignment_widget.add_button, Qt.MouseButton.LeftButton)
        dialog = assignment_widget.findChild(AssignmentDialog)
        
        # Mock file dialog selection
        def mock_file_dialog():
            return str(test_file)
            
        dialog._get_file_path = mock_file_dialog
        qtbot.mouseClick(dialog.attach_file_button, Qt.MouseButton.LeftButton)
        
        # Fill other fields and save
        dialog.title_input.setText("Assignment with Attachment")
        qtbot.mouseClick(dialog.button_box.button(QMessageBox.StandardButton.Ok),
                        Qt.MouseButton.LeftButton)
                        
        # Verify attachment in database and UI
        row = assignment_widget.assignment_table.rowCount() - 1
        assert assignment_widget.assignment_table.item(row, 1).text() == "Assignment with Attachment"
        assert test_file.name in assignment_widget.get_attachment_list(row)

    def test_course_integration(self, qtbot, assignment_widget, sample_course, session):
        """Test course-assignment relationship integration"""
        # Create multiple courses
        course2 = Course(name="TEST 102: Advanced Testing", code="TEST102")
        session.add(course2)
        session.commit()
        
        # Add assignments to different courses
        assignments = [
            {"title": "Course 1 Assignment", "course": sample_course.name},
            {"title": "Course 2 Assignment", "course": course2.name}
        ]
        
        for assignment_data in assignments:
            data = sample_assignment_data.copy()
            data.update(assignment_data)
            AssignmentManager.create_assignment(data)
            
        assignment_widget._load_assignments()
        
        # Test course filtering
        assignment_widget.course_filter.setCurrentText(sample_course.name)
        
        # Verify only assignments from selected course are shown
        for row in range(assignment_widget.assignment_table.rowCount()):
            assert assignment_widget.assignment_table.item(row, 2).text() == sample_course.name

    def test_status_workflow(self, qtbot, assignment_widget, sample_assignment_data):
        """Test assignment status workflow integration"""
        # Create assignment
        assignment = AssignmentManager.create_assignment(sample_assignment_data)
        assignment_widget._load_assignments()
        
        # Find assignment row
        row = -1
        for i in range(assignment_widget.assignment_table.rowCount()):
            if assignment_widget.assignment_table.item(i, 0).data(Qt.ItemDataRole.UserRole) == assignment['id']:
                row = i
                break
                
        # Test status transitions
        statuses = ["Not Started", "In Progress", "Under Review", "Completed"]
        for status in statuses:
            # Change status through UI
            assignment_widget.assignment_table.selectRow(row)
            assignment_widget.status_combo.setCurrentText(status)
            
            # Verify status update in UI and database
            assert assignment_widget.assignment_table.item(row, 4).text() == status
            updated_assignment = AssignmentManager.get_assignment(assignment['id'])
            assert updated_assignment['status'] == status
            
            # Verify status history is recorded
            history = AssignmentManager.get_status_history(assignment['id'])
            assert status in [h['status'] for h in history]

    def test_bulk_operations(self, qtbot, assignment_widget, sample_assignment_data):
        """Test bulk assignment operations"""
        # Create multiple assignments
        assignments = []
        for i in range(3):
            data = sample_assignment_data.copy()
            data['title'] = f"Bulk Test Assignment {i}"
            assignments.append(AssignmentManager.create_assignment(data))
            
        assignment_widget._load_assignments()
        
        # Select multiple assignments
        for i in range(3):
            assignment_widget.assignment_table.selectRow(i)
            
        # Test bulk status update
        qtbot.mouseClick(assignment_widget.bulk_status_button, Qt.MouseButton.LeftButton)
        status_dialog = QApplication.activeModalWidget()
        status_dialog.status_combo.setCurrentText("In Progress")
        qtbot.mouseClick(status_dialog.button_box.button(QMessageBox.StandardButton.Ok),
                        Qt.MouseButton.LeftButton)
        
        # Verify all selected assignments updated
        for i in range(3):
            assert assignment_widget.assignment_table.item(i, 4).text() == "In Progress"
