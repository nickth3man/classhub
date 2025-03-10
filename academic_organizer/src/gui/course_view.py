"""
Course View Widget for the Academic Organizer application.

This module contains the course view widget that displays and manages courses.
"""

import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox,
    QMessageBox, QMenu, QComboBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QAction


class CourseViewWidget(QWidget):
    """
    Course view widget that displays and manages courses.
    
    This widget shows:
    - List of courses
    - Course details
    - Course management options
    """
    
    def __init__(self, app_controller):
        """
        Initialize the course view widget.
        
        Args:
            app_controller: The application controller
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app_controller = app_controller
        
        # Set up the layout
        self._setup_ui()
        
        self.logger.debug("Course view widget initialized")
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        self.setLayout(main_layout)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Courses")
        header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        # Filter dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Courses")
        self.filter_combo.addItem("Current Semester")
        self.filter_combo.addItem("Past Courses")
        self.filter_combo.currentIndexChanged.connect(self._filter_courses)
        header_layout.addWidget(QLabel("Filter:"))
        header_layout.addWidget(self.filter_combo)
        
        header_layout.addStretch()
        
        # Add course button
        add_button = QPushButton("Add Course")
        add_button.clicked.connect(self._show_add_course_dialog)
        header_layout.addWidget(add_button)
        
        main_layout.addLayout(header_layout)
        
        # Course table
        self.course_table = QTableWidget()
        self.course_table.setColumnCount(5)
        self.course_table.setHorizontalHeaderLabels(["Course Code", "Course Name", "Instructor", "Semester", "Actions"])
        self.course_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.course_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.course_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.course_table.setAlternatingRowColors(True)
        self.course_table.verticalHeader().setVisible(False)
        self.course_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.course_table.customContextMenuRequested.connect(self._show_context_menu)
        
        main_layout.addWidget(self.course_table)
        
        # Load courses
        self._load_courses()
    
    def _load_courses(self):
        """Load courses from the database."""
        self.logger.debug("Loading courses")
        
        # TODO: Replace with actual data from the database
        # For now, add some placeholder items
        courses = [
            {"code": "MATH 201", "name": "Calculus II", "instructor": "Dr. Smith", "semester": "Spring 2025"},
            {"code": "PHYS 101", "name": "Physics 101", "instructor": "Dr. Johnson", "semester": "Spring 2025"},
            {"code": "CS 201", "name": "Data Structures", "instructor": "Prof. Williams", "semester": "Spring 2025"},
            {"code": "ENG 105", "name": "Technical Writing", "instructor": "Dr. Brown", "semester": "Fall 2024"},
            {"code": "CHEM 101", "name": "Introduction to Chemistry", "instructor": "Dr. Davis", "semester": "Fall 2024"},
        ]
        
        # Clear the table
        self.course_table.setRowCount(0)
        
        # Add courses to the table
        for i, course in enumerate(courses):
            self.course_table.insertRow(i)
            self.course_table.setItem(i, 0, QTableWidgetItem(course["code"]))
            self.course_table.setItem(i, 1, QTableWidgetItem(course["name"]))
            self.course_table.setItem(i, 2, QTableWidgetItem(course["instructor"]))
            self.course_table.setItem(i, 3, QTableWidgetItem(course["semester"]))
            
            # Actions cell
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_widget.setLayout(actions_layout)
            
            view_button = QPushButton("View")
            view_button.clicked.connect(lambda checked, row=i: self._view_course(row))
            actions_layout.addWidget(view_button)
            
            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda checked, row=i: self._edit_course(row))
            actions_layout.addWidget(edit_button)
            
            self.course_table.setCellWidget(i, 4, actions_widget)
        
        self.logger.debug(f"Loaded {len(courses)} courses")
    
    def _filter_courses(self, index):
        """
        Filter courses based on the selected filter.
        
        Args:
            index (int): Selected filter index
        """
        filter_text = self.filter_combo.currentText()
        self.logger.debug(f"Filtering courses: {filter_text}")
        
        # TODO: Implement actual filtering
        # For now, just reload all courses
        self._load_courses()
    
    def _show_add_course_dialog(self):
        """Show the add course dialog."""
        self.logger.debug("Showing add course dialog")
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Course")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        form_layout = QFormLayout()
        
        # Course code
        code_input = QLineEdit()
        form_layout.addRow("Course Code:", code_input)
        
        # Course name
        name_input = QLineEdit()
        form_layout.addRow("Course Name:", name_input)
        
        # Instructor
        instructor_input = QLineEdit()
        form_layout.addRow("Instructor:", instructor_input)
        
        # Semester
        semester_input = QLineEdit()
        semester_input.setText("Spring 2025")  # Default value
        form_layout.addRow("Semester:", semester_input)
        
        # Description
        description_input = QTextEdit()
        description_input.setMaximumHeight(100)
        form_layout.addRow("Description:", description_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # TODO: Add course to database
            self.logger.info(f"Adding course: {name_input.text()}")
            QMessageBox.information(self, "Course Added", f"Course '{name_input.text()}' has been added.")
            self._load_courses()
    
    def _view_course(self, row):
        """
        View course details.
        
        Args:
            row (int): Row index of the course
        """
        course_code = self.course_table.item(row, 0).text()
        course_name = self.course_table.item(row, 1).text()
        self.logger.debug(f"Viewing course: {course_name}")
        
        # TODO: Implement course details view
        QMessageBox.information(self, "View Course", f"Viewing details for {course_code}: {course_name}")
    
    def _edit_course(self, row):
        """
        Edit course details.
        
        Args:
            row (int): Row index of the course
        """
        course_code = self.course_table.item(row, 0).text()
        course_name = self.course_table.item(row, 1).text()
        instructor = self.course_table.item(row, 2).text()
        semester = self.course_table.item(row, 3).text()
        
        self.logger.debug(f"Editing course: {course_name}")
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Course: {course_name}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        form_layout = QFormLayout()
        
        # Course code
        code_input = QLineEdit(course_code)
        form_layout.addRow("Course Code:", code_input)
        
        # Course name
        name_input = QLineEdit(course_name)
        form_layout.addRow("Course Name:", name_input)
        
        # Instructor
        instructor_input = QLineEdit(instructor)
        form_layout.addRow("Instructor:", instructor_input)
        
        # Semester
        semester_input = QLineEdit(semester)
        form_layout.addRow("Semester:", semester_input)
        
        # Description
        description_input = QTextEdit()
        description_input.setMaximumHeight(100)
        form_layout.addRow("Description:", description_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # TODO: Update course in database
            self.logger.info(f"Updating course: {name_input.text()}")
            QMessageBox.information(self, "Course Updated", f"Course '{name_input.text()}' has been updated.")
            self._load_courses()
    
    def _delete_course(self, row):
        """
        Delete a course.
        
        Args:
            row (int): Row index of the course
        """
        course_name = self.course_table.item(row, 1).text()
        self.logger.debug(f"Deleting course: {course_name}")
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the course '{course_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: Delete course from database
            self.logger.info(f"Deleted course: {course_name}")
            QMessageBox.information(self, "Course Deleted", f"Course '{course_name}' has been deleted.")
            self._load_courses()
    
    def _show_context_menu(self, position):
        """
        Show context menu for the course table.
        
        Args:
            position: Position where the context menu should be shown
        """
        row = self.course_table.rowAt(position.y())
        
        if row >= 0:
            menu = QMenu(self)
            
            view_action = QAction("View Course", self)
            view_action.triggered.connect(lambda: self._view_course(row))
            menu.addAction(view_action)
            
            edit_action = QAction("Edit Course", self)
            edit_action.triggered.connect(lambda: self._edit_course(row))
            menu.addAction(edit_action)
            
            menu.addSeparator()
            
            delete_action = QAction("Delete Course", self)
            delete_action.triggered.connect(lambda: self._delete_course(row))
            menu.addAction(delete_action)
            
            menu.exec(self.course_table.viewport().mapToGlobal(position))