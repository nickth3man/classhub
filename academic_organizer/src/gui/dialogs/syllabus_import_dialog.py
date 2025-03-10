"""
Syllabus Import Dialog
Dialog for importing and parsing course syllabi.
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QProgressBar, QMessageBox,
    QWidget, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from academic_organizer.modules.course_manager.syllabus_parser import SyllabusParser, SyllabusInfo
from academic_organizer.modules.course_manager import CourseManager

class SyllabusParserWorker(QThread):
    """Worker thread for parsing syllabi."""
    finished = pyqtSignal(SyllabusInfo)
    error = pyqtSignal(str)

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path
        self.parser = SyllabusParser()

    def run(self):
        """Run the parser in a separate thread."""
        try:
            info = self.parser.parse_file(self.file_path)
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))

class SyllabusImportDialog(QDialog):
    """Dialog for importing course syllabi."""

    def __init__(
        self,
        course_manager: CourseManager,
        parent: Optional[QWidget] = None
    ):
        """Initialize the syllabus import dialog."""
        super().__init__(parent)
        self.course_manager = course_manager
        self.setup_ui()
        self.setWindowTitle("Import Syllabus")
        self.resize(600, 400)

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # File selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        file_layout.addWidget(self.file_label)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_button)
        layout.addLayout(file_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Preview area
        layout.addWidget(QLabel("Extracted Information:"))
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)

        # Buttons
        button_layout = QHBoxLayout()
        self.import_button = QPushButton("Import")
        self.import_button.setEnabled(False)
        self.import_button.clicked.connect(self.import_syllabus)
        button_layout.addWidget(self.import_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.syllabus_info = None

    def browse_file(self):
        """Open file dialog to select syllabus file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Syllabus",
            "",
            "Documents (*.pdf *.png *.jpg *.jpeg *.tiff)"
        )
        
        if file_path:
            self.file_label.setText(file_path)
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)  # Indeterminate progress
            
            # Start parsing in background
            self.worker = SyllabusParserWorker(Path(file_path))
            self.worker.finished.connect(self.handle_parsed_syllabus)
            self.worker.error.connect(self.handle_parser_error)
            self.worker.start()

    def handle_parsed_syllabus(self, info: SyllabusInfo):
        """Handle parsed syllabus information."""
        self.progress.setVisible(False)
        self.syllabus_info = info
        
        # Update preview
        preview_text = (
            f"Course Code: {info.course_code}\n"
            f"Course Name: {info.course_name}\n"
            f"Instructor: {info.instructor_name}\n"
            f"Email: {info.instructor_email or 'Not found'}\n"
            f"Semester: {info.semester} {info.year}\n\n"
            "Textbooks:\n" + "\n".join(f"- {book}" for book in info.textbooks) + "\n\n"
            "Grading Scheme:\n" + 
            "\n".join(f"- {category}: {percentage}%" 
                     for category, percentage in info.grading_scheme.items())
        )
        
        self.preview.setText(preview_text)
        self.import_button.setEnabled(True)

    def handle_parser_error(self, error_msg: str):
        """Handle parser errors."""
        self.progress.setVisible(False)
        QMessageBox.critical(
            self,
            "Parser Error",
            f"Failed to parse syllabus: {error_msg}"
        )

    def import_syllabus(self):
        """Import the parsed syllabus information."""
        try:
            # Create course from syllabus info
            self.course_manager.create_course_from_syllabus(self.syllabus_info)
            QMessageBox.information(
                self,
                "Success",
                "Syllabus imported successfully!"
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import syllabus: {str(e)}"
            )