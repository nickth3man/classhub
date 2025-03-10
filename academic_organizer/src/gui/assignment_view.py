"""
Assignment View Widget for the Academic Organizer application.

This module contains the assignment view widget that displays and manages assignments.
It provides functionality for:
- Viewing assignments in a table format
- Adding new assignments
- Editing existing assignments
- Filtering assignments by status and course
- Managing assignment status and priorities
- Context menu operations for quick actions
"""

import logging
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox,
    QMessageBox, QMenu, QComboBox, QDateEdit, QSpinBox
)
from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import QFont, QIcon, QAction, QColor
from ..database.operations.assignment_ops import AssignmentManager
from .assignment_dialog import AssignmentDialog
from ..utils.logger import get_logger

logger = get_logger(__name__)

class AssignmentViewWidget(QWidget):
    """
    Assignment view widget that displays and manages assignments.
    
    This widget provides a comprehensive interface for:
    - Displaying assignments in a sortable table
    - Filtering assignments by status and course
    - Adding, editing, and deleting assignments
    - Managing assignment status, due dates, and priorities
    - Viewing assignment details
    
    Attributes:
        app_controller: The main application controller instance
        logger: Logger instance for this class
        filter_combo: ComboBox for filtering assignments by status
        course_combo: ComboBox for filtering assignments by course
        assignment_table: Table widget displaying assignments
    """
    
    def __init__(self, app_controller):
        """
        Initialize the assignment view widget.
        
        Args:
            app_controller: The application controller instance for managing business logic
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app_controller = app_controller
        
        self._setup_ui()
        
        self.logger.debug("Assignment view widget initialized")
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        self.setLayout(main_layout)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Assignments")
        header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        # Filter dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Assignments")
        self.filter_combo.addItem("Upcoming")
        self.filter_combo.addItem("Past Due")
        self.filter_combo.addItem("Completed")
        self.filter_combo.currentIndexChanged.connect(self._filter_assignments)
        header_layout.addWidget(QLabel("Filter:"))
        header_layout.addWidget(self.filter_combo)
        
        # Course filter
        self.course_combo = QComboBox()
        self.course_combo.addItem("All Courses")
        # TODO: Populate with actual courses from the database
        self.course_combo.addItem("MATH 201: Calculus II")
        self.course_combo.addItem("PHYS 101: Physics 101")
        self.course_combo.addItem("CS 201: Data Structures")
        self.course_combo.currentIndexChanged.connect(self._filter_assignments)
        header_layout.addWidget(QLabel("Course:"))
        header_layout.addWidget(self.course_combo)
        
        header_layout.addStretch()
        
        # Add assignment button
        add_button = QPushButton("Add Assignment")
        add_button.clicked.connect(self._add_assignment)
        header_layout.addWidget(add_button)
        
        main_layout.addLayout(header_layout)
        
        # Assignment table
        self.assignment_table = QTableWidget()
        self.assignment_table.setColumnCount(6)
        self.assignment_table.setHorizontalHeaderLabels(["Title", "Course", "Due Date", "Status", "Priority", "Actions"])
        self.assignment_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.assignment_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.assignment_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.assignment_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.assignment_table.setAlternatingRowColors(True)
        self.assignment_table.verticalHeader().setVisible(False)
        self.assignment_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.assignment_table.customContextMenuRequested.connect(self._show_context_menu)
        
        main_layout.addWidget(self.assignment_table)
        
        # Load assignments
        self._load_assignments()
    
    def _load_assignments(self):
        """Load assignments from the database."""
        self.logger.debug("Loading assignments")
        
        try:
            # Get assignments from database through controller
            assignments = self.app_controller.get_assignments()
        except Exception as e:
            self.logger.error(f"Failed to load assignments: {e}")
            QMessageBox.critical(self, "Error", "Failed to load assignments from database")
            return
        
        # Apply filters
        filter_text = self.filter_combo.currentText()
        course_filter = self.course_combo.currentText()
        
        filtered_assignments = []
        for assignment in assignments:
            # Filter by status
            if filter_text == "Upcoming" and assignment["status"] == "Completed":
                continue
            if filter_text == "Past Due" and (assignment["due_date"] > datetime.now() or assignment["status"] == "Completed"):
                continue
            if filter_text == "Completed" and assignment["status"] != "Completed":
                continue
            
            # Filter by course
            if course_filter != "All Courses" and assignment["course"] != course_filter:
                continue
            
            filtered_assignments.append(assignment)
        
        self._populate_table(filtered_assignments)
    
    def _populate_table(self, assignments):
        """Populate the assignment table with the given assignments."""
        # Clear the table
        self.assignment_table.setRowCount(0)
        
        # Add assignments to the table
        for i, assignment in enumerate(assignments):
            self.assignment_table.insertRow(i)
            self.assignment_table.setItem(i, 0, QTableWidgetItem(assignment["title"]))
            self.assignment_table.setItem(i, 1, QTableWidgetItem(assignment["course"]))
            
            # Format due date
            due_date = assignment["due_date"].strftime("%Y-%m-%d")
            days_left = (assignment["due_date"] - datetime.now()).days
            
            due_date_item = self._create_due_date_item(due_date, days_left, assignment["status"])
            self.assignment_table.setItem(i, 2, due_date_item)
            
            # Status with color coding
            status_item = self._create_status_item(assignment["status"], days_left)
            self.assignment_table.setItem(i, 3, status_item)
            
            # Priority with color coding
            priority_item = self._create_priority_item(assignment["priority"])
            self.assignment_table.setItem(i, 4, priority_item)
            
            # Actions cell
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_widget.setLayout(actions_layout)
            
            view_button = QPushButton("View")
            view_button.clicked.connect(lambda checked, row=i: self._view_assignment(row))
            actions_layout.addWidget(view_button)
            
            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda checked, row=i: self._edit_assignment(row))
            actions_layout.addWidget(edit_button)
            
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda checked, row=i: self._delete_assignment(row))
            actions_layout.addWidget(delete_button)
            
            self.assignment_table.setCellWidget(i, 5, actions_widget)
        
        self.logger.debug(f"Loaded {len(assignments)} assignments")
    
    def _filter_assignments(self):
        """Filter assignments based on the selected filters."""
        self.logger.debug("Filtering assignments")
        self._load_assignments()
    
    def _add_assignment(self):
        """Show dialog to add a new assignment."""
        dialog = AssignmentDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            assignment_data = dialog.get_assignment_data()
            self._add_assignment_to_database(assignment_data)
    
    def _view_assignment(self, row):
        """
        View assignment details.
        
        Args:
            row (int): Row index of the assignment
        """
        assignment_title = self.assignment_table.item(row, 0).text()
        course = self.assignment_table.item(row, 1).text()
        self.logger.debug(f"Viewing assignment: {assignment_title}")
        
        # TODO: Implement assignment details view
        QMessageBox.information(self, "View Assignment", f"Viewing details for '{assignment_title}' in {course}")
    
    def _edit_assignment(self, row):
        """
        Show dialog to edit an existing assignment.
        
        Args:
            row: Row index of the assignment to edit
        """
        assignment_data = {
            "title": self.assignment_table.item(row, 0).text(),
            "course": self.assignment_table.item(row, 1).text(),
            "due_date": self.assignment_table.item(row, 2).text(),
            "status": self.assignment_table.item(row, 3).text(),
            "priority": self.assignment_table.item(row, 4).text(),
            "estimated_time": int(self.assignment_table.item(row, 5).text().split()[0]),
            "description": self.assignment_table.item(row, 6).text()
        }
        
        dialog = AssignmentDialog(self, assignment_data)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_assignment_data()
            self._update_assignment_in_database(row, updated_data)
    
    def _delete_assignment(self, row):
        """
        Delete an assignment.
        
        Args:
            row (int): Row index of the assignment
        """
        assignment_title = self.assignment_table.item(row, 0).text()
        self.logger.debug(f"Deleting assignment: {assignment_title}")
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the assignment '{assignment_title}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: Delete assignment from database
            self.logger.info(f"Deleted assignment: {assignment_title}")
            QMessageBox.information(self, "Assignment Deleted", f"Assignment '{assignment_title}' has been deleted.")
            self._load_assignments()
    
    def _show_context_menu(self, position):
        """
        Show context menu for the assignment table.
        
        Args:
            position: Position where the context menu should be shown
        """
        row = self.assignment_table.rowAt(position.y())
        
        if row >= 0:
            menu = QMenu(self)
            
            view_action = QAction("View Assignment", self)
            view_action.triggered.connect(lambda: self._view_assignment(row))
            menu.addAction(view_action)
            
            edit_action = QAction("Edit Assignment", self)
            edit_action.triggered.connect(lambda: self._edit_assignment(row))
            menu.addAction(edit_action)
            
            # Mark as completed action
            status = self.assignment_table.item(row, 3).text()
            if status != "Completed":
                complete_action = QAction("Mark as Completed", self)
                complete_action.triggered.connect(lambda: self._mark_as_completed(row))
                menu.addAction(complete_action)
            
            menu.addSeparator()
            
            delete_action = QAction("Delete Assignment", self)
            delete_action.triggered.connect(lambda: self._delete_assignment(row))
            menu.addAction(delete_action)
            
            menu.exec(self.assignment_table.viewport().mapToGlobal(position))
    
    def _mark_as_completed(self, row):
        """
        Mark an assignment as completed.
        
        Args:
            row (int): Row index of the assignment
        """
        assignment_title = self.assignment_table.item(row, 0).text()
        self.logger.debug(f"Marking assignment as completed: {assignment_title}")
        
        # TODO: Update assignment status in database
        self.logger.info(f"Marked assignment as completed: {assignment_title}")
        QMessageBox.information(self, "Assignment Completed", f"Assignment '{assignment_title}' has been marked as completed.")
        self._load_assignments()

    def _create_due_date_item(self, due_date, days_left, status):
        """Create a table item for the due date with appropriate formatting."""
        item = QTableWidgetItem(due_date)
        
        if status == "Completed":
            item.setForeground(QColor("green"))
        elif days_left < 0:
            item.setForeground(QColor("red"))
        elif days_left <= 3:
            item.setForeground(QColor("orange"))
            
        return item
    
    def _create_status_item(self, status, days_left):
        """Create a table item for the status with appropriate formatting."""
        item = QTableWidgetItem(status)
        
        if status == "Completed":
            item.setForeground(QColor("green"))
        elif status == "In Progress":
            item.setForeground(QColor("blue"))
        elif days_left < 0:
            item.setForeground(QColor("red"))
            
        return item
    
    def _create_priority_item(self, priority):
        """Create a table item for the priority with appropriate formatting."""
        item = QTableWidgetItem(priority)
        
        if priority == "High":
            item.setForeground(QColor("red"))
        elif priority == "Medium":
            item.setForeground(QColor("orange"))
        elif priority == "Low":
            item.setForeground(QColor("green"))
            
        return item

    def _add_assignment_to_database(self, assignment_data):
        """Add assignment to database with error handling."""
        try:
            self.app_controller.add_assignment(assignment_data)
            QMessageBox.information(self, "Success", f"Assignment '{assignment_data['title']}' has been added.")
            self._load_assignments()
        except Exception as e:
            self.logger.error(f"Failed to add assignment: {e}")
            QMessageBox.critical(self, "Error", "Failed to add assignment to database")

    def _update_assignment_in_database(self, assignment_id, assignment_data):
        """Update assignment in database with error handling."""
        try:
            self.app_controller.update_assignment(assignment_id, assignment_data)
            QMessageBox.information(self, "Success", f"Assignment '{assignment_data['title']}' has been updated.")
            self._load_assignments()
        except Exception as e:
            self.logger.error(f"Failed to update assignment: {e}")
            QMessageBox.critical(self, "Error", "Failed to update assignment in database")


class AssignmentDialog(QDialog):
    """Dialog for creating and editing assignments."""
    
    def __init__(self, parent=None, assignment_data=None):
        """
        Initialize the assignment dialog.
        
        Args:
            parent: Parent widget
            assignment_data: Optional dictionary containing assignment data for editing
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.assignment_data = assignment_data
        
        self.setWindowTitle("New Assignment" if not assignment_data else "Edit Assignment")
        self.setMinimumWidth(400)
        
        self._init_ui()
        
        if assignment_data:
            self._populate_fields()
    
    def _init_ui(self):
        """Initialize the dialog UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Form layout for input fields
        form_layout = QFormLayout()
        
        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter assignment title")
        form_layout.addRow("Title:", self.title_input)
        
        # Course
        self.course_combo = QComboBox()
        # TODO: Populate with actual courses from the database
        self.course_combo.addItems([
            "MATH 201: Calculus II",
            "PHYS 101: Physics 101",
            "CS 201: Data Structures"
        ])
        form_layout.addRow("Course:", self.course_combo)
        
        # Due date
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate().addDays(7))
        form_layout.addRow("Due Date:", self.due_date_input)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Not Started", "In Progress", "Completed"])
        form_layout.addRow("Status:", self.status_combo)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        form_layout.addRow("Priority:", self.priority_combo)
        
        # Estimated time (hours)
        self.time_input = QSpinBox()
        self.time_input.setRange(1, 100)
        self.time_input.setSuffix(" hours")
        form_layout.addRow("Estimated Time:", self.time_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("Enter assignment description")
        form_layout.addRow("Description:", self.description_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _populate_fields(self):
        """Populate fields with existing assignment data."""
        self.title_input.setText(self.assignment_data["title"])
        self.course_combo.setCurrentText(self.assignment_data["course"])
        self.due_date_input.setDate(QDate.fromString(self.assignment_data["due_date"]))
        self.status_combo.setCurrentText(self.assignment_data["status"])
        self.priority_combo.setCurrentText(self.assignment_data["priority"])
        self.time_input.setValue(self.assignment_data["estimated_time"])
        self.description_input.setText(self.assignment_data["description"])
    
    def validate_and_accept(self):
        """Validate input fields before accepting the dialog."""
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Title is required.")
            self.title_input.setFocus()
            return
            
        if self.due_date_input.date() < QDate.currentDate():
            QMessageBox.warning(self, "Validation Error", "Due date cannot be in the past.")
            self.due_date_input.setFocus()
            return
        
        self.accept()
    
    def get_assignment_data(self):
        """
        Get the assignment data from the dialog.
        
        Returns:
            dict: Assignment data dictionary
        """
        return {
            "title": self.title_input.text().strip(),
            "course": self.course_combo.currentText(),
            "due_date": self.due_date_input.date().toString("yyyy-MM-dd"),
            "status": self.status_combo.currentText(),
            "priority": self.priority_combo.currentText(),
            "estimated_time": self.time_input.value(),
            "description": self.description_input.toPlainText().strip()
        }
