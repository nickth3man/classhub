"""Base UI components with consistent styling and behavior."""
from typing import Optional, Callable, Any
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QLabel, 
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from ...utils.error_handler import handle_errors, ApplicationError

class BaseWidget(QWidget):
    """Base widget with error handling and consistent styling."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize UI components."""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
    
    @handle_errors()
    def show_error(self, message: str) -> None:
        """Display error message."""
        QMessageBox.critical(self, "Error", message)
    
    @handle_errors()
    def show_info(self, message: str) -> None:
        """Display info message."""
        QMessageBox.information(self, "Information", message)

class StyledButton(QPushButton):
    """Button with consistent styling."""
    
    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setup_style()
    
    def setup_style(self) -> None:
        """Apply consistent button styling."""
        self.setMinimumWidth(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class ValidatedLineEdit(QLineEdit):
    """Line edit with input validation."""
    
    validation_failed = pyqtSignal(str)  # Signal for validation failure
    
    def __init__(
        self, 
        parent: Optional[QWidget] = None,
        validator: Optional[Callable[[str], bool]] = None,
        placeholder: str = ""
    ):
        super().__init__(parent)
        self.validator = validator
        self.setPlaceholderText(placeholder)
        self.textChanged.connect(self.validate_input)
    
    @handle_errors()
    def validate_input(self, text: str) -> None:
        """Validate input text."""
        if self.validator:
            try:
                is_valid = self.validator(text)
                self.set_validation_style(is_valid)
            except ValidationError as e:
                self.validation_failed.emit(str(e))
                self.set_validation_style(False)
    
    def set_validation_style(self, is_valid: bool) -> None:
        """Apply validation status styling."""
        style = "" if is_valid else "border: 1px solid red;"
        self.setStyleSheet(style)

class FormLayout(QVBoxLayout):
    """Standard form layout with consistent spacing."""
    
    def __init__(self):
        super().__init__()
        self.setSpacing(10)
        self.setContentsMargins(10, 10, 10, 10)
    
    def add_field(
        self, 
        label: str, 
        widget: QWidget,
        help_text: Optional[str] = None
    ) -> None:
        """Add a form field with label and optional help text."""
        field_layout = QHBoxLayout()
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(120)
        field_layout.addWidget(label_widget)
        field_layout.addWidget(widget)
        self.addLayout(field_layout)
        
        if help_text:
            help_label = QLabel(help_text)
            help_label.setStyleSheet("color: gray; font-size: 10px;")
            self.addWidget(help_label)