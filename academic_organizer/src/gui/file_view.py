"""
File View Widget for the Academic Organizer application.

This module contains the file view widget that displays and manages files.
"""

import logging
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox,
    QMessageBox, QMenu, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QAction


class FileViewWidget(QWidget):
    """
    File view widget that displays and manages files.
    
    This widget shows:
    - List of files
    - File details
    - File management options
    """
    
    def __init__(self, app_controller):
        """
        Initialize the file view widget.
        
        Args:
            app_controller: The application controller
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app_controller = app_controller
        
        # Set up the layout
        self._setup_ui()
        
        self.logger.debug("File view widget initialized")
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        self.setLayout(main_layout)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Files")
        header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        # Filter dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Files")
        self.filter_combo.addItem("Documents")
        self.filter_combo.addItem("Images")
        self.filter_combo.addItem("Audio")
        self.filter_combo.addItem("Video")
        self.filter_combo.currentIndexChanged.connect(self._filter_files)
        header_layout.addWidget(QLabel("Filter:"))
        header_layout.addWidget(self.filter_combo)
        
        # Course filter
        self.course_combo = QComboBox()
        self.course_combo.addItem("All Courses")
        # TODO: Populate with actual courses from the database
        self.course_combo.addItem("MATH 201: Calculus II")
        self.course_combo.addItem("PHYS 101: Physics 101")
        self.course_combo.addItem("CS 201: Data Structures")
        self.course_combo.currentIndexChanged.connect(self._filter_files)
        header_layout.addWidget(QLabel("Course:"))
        header_layout.addWidget(self.course_combo)
        
        header_layout.addStretch()
        
        # Import button
        import_button = QPushButton("Import Files")
        import_button.clicked.connect(self._import_files)
        header_layout.addWidget(import_button)
        
        main_layout.addLayout(header_layout)
        
        # File table
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(6)
        self.file_table.setHorizontalHeaderLabels(["Filename", "Type", "Course", "Size", "Date Added", "Actions"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.file_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self._show_context_menu)
        
        main_layout.addWidget(self.file_table)
        
        # Load files
        self._load_files()
    
    def _load_files(self):
        """Load files from the database."""
        self.logger.debug("Loading files")
        
        # TODO: Replace with actual data from the database
        # For now, add some placeholder items
        files = [
            {
                "filename": "Calculus_Syllabus.pdf",
                "type": "PDF",
                "course": "MATH 201: Calculus II",
                "size": "245 KB",
                "date_added": datetime.now().strftime("%Y-%m-%d")
            },
            {
                "filename": "Physics_Lab_Report.docx",
                "type": "Word Document",
                "course": "PHYS 101: Physics 101",
                "size": "1.2 MB",
                "date_added": datetime.now().strftime("%Y-%m-%d")
            },
            {
                "filename": "Data_Structures_Notes.txt",
                "type": "Text",
                "course": "CS 201: Data Structures",
                "size": "45 KB",
                "date_added": datetime.now().strftime("%Y-%m-%d")
            },
            {
                "filename": "Lecture_Slides.pptx",
                "type": "PowerPoint",
                "course": "MATH 201: Calculus II",
                "size": "3.5 MB",
                "date_added": datetime.now().strftime("%Y-%m-%d")
            },
            {
                "filename": "Lab_Experiment_Data.xlsx",
                "type": "Excel",
                "course": "PHYS 101: Physics 101",
                "size": "780 KB",
                "date_added": datetime.now().strftime("%Y-%m-%d")
            },
        ]
        
        # Apply filters
        filter_text = self.filter_combo.currentText()
        course_filter = self.course_combo.currentText()
        
        filtered_files = []
        for file in files:
            # Filter by type
            if filter_text == "Documents" and file["type"] not in ["PDF", "Word Document", "Text", "PowerPoint", "Excel"]:
                continue
            if filter_text == "Images" and file["type"] not in ["JPEG", "PNG", "GIF"]:
                continue
            if filter_text == "Audio" and file["type"] not in ["MP3", "WAV", "FLAC"]:
                continue
            if filter_text == "Video" and file["type"] not in ["MP4", "AVI", "MOV"]:
                continue
            
            # Filter by course
            if course_filter != "All Courses" and file["course"] != course_filter:
                continue
            
            filtered_files.append(file)
        
        # Clear the table
        self.file_table.setRowCount(0)
        
        # Add files to the table
        for i, file in enumerate(filtered_files):
            self.file_table.insertRow(i)
            self.file_table.setItem(i, 0, QTableWidgetItem(file["filename"]))
            self.file_table.setItem(i, 1, QTableWidgetItem(file["type"]))
            self.file_table.setItem(i, 2, QTableWidgetItem(file["course"]))
            self.file_table.setItem(i, 3, QTableWidgetItem(file["size"]))
            self.file_table.setItem(i, 4, QTableWidgetItem(file["date_added"]))
            
            # Actions cell
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_widget.setLayout(actions_layout)
            
            view_button = QPushButton("View")
            view_button.clicked.connect(lambda checked, row=i: self._view_file(row))
            actions_layout.addWidget(view_button)
            
            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda checked, row=i: self._edit_file_metadata(row))
            actions_layout.addWidget(edit_button)
            
            self.file_table.setCellWidget(i, 5, actions_widget)
        
        self.logger.debug(f"Loaded {len(filtered_files)} files")
    
    def _filter_files(self):
        """Filter files based on the selected filters."""
        self.logger.debug("Filtering files")
        self._load_files()
    
    def _import_files(self):
        """Import files into the application."""
        self.logger.debug("Importing files")
        
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Files",
            "",
            "All Files (*);;Documents (*.pdf *.docx *.txt *.pptx *.xlsx);;Images (*.jpg *.jpeg *.png *.gif);;Audio (*.mp3 *.wav *.flac);;Video (*.mp4 *.avi *.mov)"
        )
        
        if files:
            # TODO: Implement actual file import logic
            self.logger.info(f"Selected {len(files)} files for import")
            
            # Show course selection dialog
            course = self._show_course_selection_dialog()
            
            if course:
                # TODO: Import files to database
                QMessageBox.information(self, "Files Imported", f"Imported {len(files)} files to {course}")
                self._load_files()
    
    def _show_course_selection_dialog(self):
        """
        Show a dialog to select a course for imported files.
        
        Returns:
            str: Selected course or None if cancelled
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Course")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        form_layout = QFormLayout()
        
        # Course selection
        course_combo = QComboBox()
        course_combo.addItem("MATH 201: Calculus II")
        course_combo.addItem("PHYS 101: Physics 101")
        course_combo.addItem("CS 201: Data Structures")
        form_layout.addRow("Course:", course_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return course_combo.currentText()
        
        return None
    
    def _view_file(self, row):
        """
        View a file.
        
        Args:
            row (int): Row index of the file
        """
        filename = self.file_table.item(row, 0).text()
        self.logger.debug(f"Viewing file: {filename}")
        
        # TODO: Implement file viewing
        QMessageBox.information(self, "View File", f"Viewing file: {filename}")
    
    def _edit_file_metadata(self, row):
        """
        Edit file metadata.
        
        Args:
            row (int): Row index of the file
        """
        filename = self.file_table.item(row, 0).text()
        file_type = self.file_table.item(row, 1).text()
        course = self.file_table.item(row, 2).text()
        
        self.logger.debug(f"Editing file metadata: {filename}")
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit File: {filename}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        form_layout = QFormLayout()
        
        # Filename
        filename_input = QLineEdit(filename)
        form_layout.addRow("Filename:", filename_input)
        
        # Course
        course_combo = QComboBox()
        course_combo.addItem("MATH 201: Calculus II")
        course_combo.addItem("PHYS 101: Physics 101")
        course_combo.addItem("CS 201: Data Structures")
        course_combo.setCurrentText(course)
        form_layout.addRow("Course:", course_combo)
        
        # Tags
        tags_input = QLineEdit()
        form_layout.addRow("Tags (comma-separated):", tags_input)
        
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
            # TODO: Update file metadata in database
            self.logger.info(f"Updating file metadata: {filename_input.text()}")
            QMessageBox.information(self, "File Updated", f"File metadata updated for {filename_input.text()}")
            self._load_files()
    
    def _delete_file(self, row):
        """
        Delete a file.
        
        Args:
            row (int): Row index of the file
        """
        filename = self.file_table.item(row, 0).text()
        self.logger.debug(f"Deleting file: {filename}")
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the file '{filename}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: Delete file from database
            self.logger.info(f"Deleted file: {filename}")
            QMessageBox.information(self, "File Deleted", f"File '{filename}' has been deleted.")
            self._load_files()
    
    def _show_context_menu(self, position):
        """
        Show context menu for the file table.
        
        Args:
            position: Position where the context menu should be shown
        """
        row = self.file_table.rowAt(position.y())
        
        if row >= 0:
            menu = QMenu(self)
            
            view_action = QAction("View File", self)
            view_action.triggered.connect(lambda: self._view_file(row))
            menu.addAction(view_action)
            
            edit_action = QAction("Edit Metadata", self)
            edit_action.triggered.connect(lambda: self._edit_file_metadata(row))
            menu.addAction(edit_action)
            
            menu.addSeparator()
            
            delete_action = QAction("Delete File", self)
            delete_action.triggered.connect(lambda: self._delete_file(row))
            menu.addAction(delete_action)
            
            menu.exec(self.file_table.viewport().mapToGlobal(position))