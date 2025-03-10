"""
Course Dialog
Dialog for adding and editing courses.
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QSpinBox, QPushButton, QDialogButtonBox,
    QMessageBox, QWidget
)

from academic_organizer.modules.course_manager import CourseManager
from academic_organizer.database.models.course import Course
from academic_organizer.utils.exceptions import ValidationError

class CourseDialog(QDialog):
    """Dialog for adding or editing a course."""

    def __init__(
        self,
        course_manager: CourseManager,
        course: Optional[Course] = None,
        parent: Optional[QWidget] = None
    ):
        """Initialize the course dialog."""
        super().__init__(parent)
        self.course_manager = course_manager
        self.course = course
        self.setup_ui()
        
        if course:
            self.setWindowTitle("Edit Course")
            self.load_course_data()
        else:
            self.setWindowTitle("Add Course")

    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Form layout for inputs
        form = QFormLayout()
        
        self.code_edit = QLineEdit()
        form.addRow("Course Code:", self.code_edit)
        
        self.name_edit = QLineEdit()
        form.addRow("Course Name:", self.name_edit)
        
        self.semester_edit = QLineEdit()
        form.addRow("Semester:", self.semester_edit)
        
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1900, 2100)
        self.year_spin.setValue(2025)  # Default to current year
        form.addRow("Year:", self.year_spin)
        
        # Instructor information
        self.instructor_first_name = QLineEdit()
        form.addRow("Instructor First Name:", self.instructor_first_name)
        
        self.instructor_last_name = QLineEdit()
        form.addRow("Instructor Last Name:", self.instructor_last_name)
        
        self.instructor_email = QLineEdit()
        form.addRow("Instructor Email:", self.instructor_email)
        
        layout.addLayout(form)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_course_data(self) -> None:
        """Load existing course data into the form."""
        if not self.course:
            return
            
        self.code_edit.setText(self.course.code)
        self.name_edit.setText(self.course.name)
        self.semester_edit.setText(self.course.semester)
        self.year_spin.setValue(self.course.year)
        
        if self.course.instructor:
            self.instructor_first_name.setText(self.course.instructor.first_name)
            self.instructor_last_name.setText(self.course.instructor.last_name)
            self.instructor_email.setText(self.course.instructor.email)

    def get_form_data(self) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Get the form data as dictionaries."""
        course_data = {
            'code': self.code_edit.text().strip(),
            'name': self.name_edit.text().strip(),
            'semester': self.semester_edit.text().strip(),
            'year': self.year_spin.value()
        }
        
        instructor_data = {
            'first_name': self.instructor_first_name.text().strip(),
            'last_name': self.instructor_last_name.text().strip(),
            'email': self.instructor_email.text().strip()
        }
        
        return course_data, instructor_data

    def accept(self) -> None:
        """Handle dialog acceptance."""
        try:
            course_data, instructor_data = self.get_form_data()
            
            if self.course:
                # Update existing course
                self.course_manager.update_course(
                    self.course.id,
                    course_data
                )
            else:
                # Create new course
                self.course_manager.create_course(
                    course_data,
                    instructor_data
                )
            
            super().accept()
            
        except ValidationError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save course: {str(e)}")