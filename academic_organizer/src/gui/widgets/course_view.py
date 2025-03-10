"""
Course View Widget
Main interface for course management functionality.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableView, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, QSortFilterProxyModel

from academic_organizer.modules.course_manager import CourseManager
from academic_organizer.gui.models.course_table_model import CourseTableModel
from academic_organizer.gui.dialogs.course_dialog import CourseDialog
from academic_organizer.database.models.course import Course

class CourseViewWidget(QWidget):
    """Widget for displaying and managing courses."""

    def __init__(self, course_manager: CourseManager, parent: Optional[QWidget] = None):
        """Initialize the course view widget."""
        super().__init__(parent)
        self.course_manager = course_manager
        self.setup_ui()
        self.load_courses()

    def setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Button toolbar
        toolbar = QHBoxLayout()
        
        self.add_button = QPushButton("Add Course")
        self.add_button.clicked.connect(self.add_course)
        toolbar.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit Course")
        self.edit_button.clicked.connect(self.edit_course)
        self.edit_button.setEnabled(False)
        toolbar.addWidget(self.edit_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_courses)
        toolbar.addWidget(self.refresh_button)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Course table
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        
        # Set up the model
        self.model = CourseTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.table_view.setModel(self.proxy_model)
        
        # Configure table appearance
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Course name column
        
        self.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table_view)

    def load_courses(self) -> None:
        """Load courses from the database."""
        try:
            courses = self.course_manager.get_active_courses()
            self.model.set_courses(courses)
            self.table_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load courses: {str(e)}"
            )

    def add_course(self) -> None:
        """Open dialog to add a new course."""
        dialog = CourseDialog(self.course_manager, parent=self)
        if dialog.exec():
            self.load_courses()

    def edit_course(self) -> None:
        """Open dialog to edit selected course."""
        selected_row = self.table_view.selectionModel().selectedRows()
        if not selected_row:
            return
            
        index = self.proxy_model.mapToSource(selected_row[0])
        course = self.model.get_course(index.row())
        
        dialog = CourseDialog(self.course_manager, course=course, parent=self)
        if dialog.exec():
            self.load_courses()

    def on_selection_changed(self) -> None:
        """Handle selection changes in the table view."""
        has_selection = bool(self.table_view.selectionModel().selectedRows())
        self.edit_button.setEnabled(has_selection)