"""
Course Table Model
Data model for displaying courses in a table view.
"""

from typing import List, Any
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from academic_organizer.database.models.course import Course

class CourseTableModel(QAbstractTableModel):
    """Model for displaying course data in a table view."""
    
    HEADERS = ["Code", "Name", "Semester", "Year", "Instructor"]

    def __init__(self):
        """Initialize the course table model."""
        super().__init__()
        self.courses: List[Course] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows in the model."""
        return len(self.courses)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns in the model."""
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return the data for the given role and index."""
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            course = self.courses[index.row()]
            column = index.column()
            
            if column == 0:
                return course.code
            elif column == 1:
                return course.name
            elif column == 2:
                return course.semester
            elif column == 3:
                return str(course.year)
            elif column == 4:
                return f"{course.instructor.last_name}, {course.instructor.first_name}"

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return the header data for the given role and section."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]
        return None

    def set_courses(self, courses: List[Course]) -> None:
        """Update the model with new course data."""
        self.beginResetModel()
        self.courses = courses
        self.endResetModel()

    def get_course(self, row: int) -> Course:
        """Get the course at the specified row."""
        return self.courses[row]