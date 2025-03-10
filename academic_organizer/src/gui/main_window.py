"""
Main Window for the Academic Organizer application.

This module contains the main application window and its components.
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStatusBar, QToolBar, QAction, QMenu,
    QMessageBox, QFileDialog
)
from PyQt6.QtGui import QIcon, QAction, QKeySequence
from PyQt6.QtCore import Qt, QSize

from academic_organizer.gui.dashboard import DashboardWidget
from academic_organizer.gui.course_view import CourseViewWidget
from academic_organizer.gui.assignment_view import AssignmentViewWidget
from academic_organizer.gui.file_view import FileViewWidget


class MainWindow(QMainWindow):
    """
    Main application window for the Academic Organizer.
    
    This class is responsible for:
    - Creating the main UI layout
    - Setting up menus and toolbars
    - Managing the central tab widget
    - Coordinating between different UI components
    """
    
    def __init__(self, app_controller):
        """
        Initialize the main window.
        
        Args:
            app_controller: The application controller
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app_controller = app_controller
        
        # Set window properties
        self.setWindowTitle("Academic Organizer")
        self.setMinimumSize(1000, 700)
        
        # Initialize UI components
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        self._create_status_bar()
        self._create_central_widget()
        
        self.logger.info("Main window initialized")
    
    def _create_actions(self):
        """Create actions for menus and toolbars."""
        # File menu actions
        self.new_course_action = QAction("New Course", self)
        self.new_course_action.setShortcut(QKeySequence.New)
        self.new_course_action.setStatusTip("Create a new course")
        self.new_course_action.triggered.connect(self._on_new_course)
        
        self.import_action = QAction("Import Files", self)
        self.import_action.setShortcut(QKeySequence("Ctrl+I"))
        self.import_action.setStatusTip("Import files into the organizer")
        self.import_action.triggered.connect(self._on_import)
        
        self.export_action = QAction("Export Data", self)
        self.export_action.setShortcut(QKeySequence("Ctrl+E"))
        self.export_action.setStatusTip("Export data from the organizer")
        self.export_action.triggered.connect(self._on_export)
        
        self.exit_action = QAction("Exit", self)
        self.exit_action.setShortcut(QKeySequence.Quit)
        self.exit_action.setStatusTip("Exit the application")
        self.exit_action.triggered.connect(self.close)
        
        # Edit menu actions
        self.preferences_action = QAction("Preferences", self)
        self.preferences_action.setShortcut(QKeySequence("Ctrl+,"))
        self.preferences_action.setStatusTip("Edit application preferences")
        self.preferences_action.triggered.connect(self._on_preferences)
        
        # View menu actions
        self.refresh_action = QAction("Refresh", self)
        self.refresh_action.setShortcut(QKeySequence.Refresh)
        self.refresh_action.setStatusTip("Refresh the current view")
        self.refresh_action.triggered.connect(self._on_refresh)
        
        # Help menu actions
        self.about_action = QAction("About", self)
        self.about_action.setStatusTip("Show information about the application")
        self.about_action.triggered.connect(self._on_about)
        
        self.help_action = QAction("Help", self)
        self.help_action.setShortcut(QKeySequence.HelpContents)
        self.help_action.setStatusTip("Show help")
        self.help_action.triggered.connect(self._on_help)
    
    def _create_menus(self):
        """Create the application menus."""
        # File menu
        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.new_course_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.import_action)
        self.file_menu.addAction(self.export_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
        
        # Edit menu
        self.edit_menu = self.menuBar().addMenu("&Edit")
        self.edit_menu.addAction(self.preferences_action)
        
        # View menu
        self.view_menu = self.menuBar().addMenu("&View")
        self.view_menu.addAction(self.refresh_action)
        
        # Help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        self.help_menu.addAction(self.help_action)
        self.help_menu.addAction(self.about_action)
    
    def _create_toolbars(self):
        """Create the application toolbars."""
        # Main toolbar
        self.main_toolbar = QToolBar("Main Toolbar")
        self.main_toolbar.setMovable(False)
        self.addToolBar(self.main_toolbar)
        
        self.main_toolbar.addAction(self.new_course_action)
        self.main_toolbar.addAction(self.import_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.refresh_action)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _create_central_widget(self):
        """Create the central widget with tabs."""
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Create and add tabs
        self.dashboard_widget = DashboardWidget(self.app_controller)
        self.course_widget = CourseViewWidget(self.app_controller)
        self.assignment_widget = AssignmentViewWidget(self.app_controller)
        self.file_widget = FileViewWidget(self.app_controller)
        
        self.tab_widget.addTab(self.dashboard_widget, "Dashboard")
        self.tab_widget.addTab(self.course_widget, "Courses")
        self.tab_widget.addTab(self.assignment_widget, "Assignments")
        self.tab_widget.addTab(self.file_widget, "Files")
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _on_tab_changed(self, index):
        """
        Handle tab change event.
        
        Args:
            index (int): Index of the selected tab
        """
        tab_name = self.tab_widget.tabText(index)
        self.logger.debug(f"Tab changed to {tab_name}")
        self.status_bar.showMessage(f"Viewing {tab_name}")
    
    def _on_new_course(self):
        """Handle new course action."""
        self.logger.debug("New course action triggered")
        # TODO: Implement new course dialog
        QMessageBox.information(self, "New Course", "New course dialog will be implemented here.")
    
    def _on_import(self):
        """Handle import action."""
        self.logger.debug("Import action triggered")
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Files",
            "",
            "All Files (*);;Documents (*.pdf *.docx *.txt);;Images (*.png *.jpg *.jpeg)"
        )
        
        if files:
            self.logger.debug(f"Selected files for import: {files}")
            # TODO: Implement file import logic
            QMessageBox.information(self, "Import Files", f"Selected {len(files)} files for import.")
    
    def _on_export(self):
        """Handle export action."""
        self.logger.debug("Export action triggered")
        # TODO: Implement export dialog
        QMessageBox.information(self, "Export Data", "Export dialog will be implemented here.")
    
    def _on_preferences(self):
        """Handle preferences action."""
        self.logger.debug("Preferences action triggered")
        # TODO: Implement preferences dialog
        QMessageBox.information(self, "Preferences", "Preferences dialog will be implemented here.")
    
    def _on_refresh(self):
        """Handle refresh action."""
        self.logger.debug("Refresh action triggered")
        current_widget = self.tab_widget.currentWidget()
        # TODO: Implement refresh logic for each widget type
        QMessageBox.information(self, "Refresh", "Refresh functionality will be implemented here.")
    
    def _on_about(self):
        """Handle about action."""
        self.logger.debug("About action triggered")
        QMessageBox.about(
            self,
            "About Academic Organizer",
            "Academic Organizer v0.1.0\n\n"
            "A comprehensive desktop application designed to help students "
            "organize their educational materials, track assignments, "
            "manage courses, and provide AI-powered study assistance."
        )
    
    def _on_help(self):
        """Handle help action."""
        self.logger.debug("Help action triggered")
        # TODO: Implement help system
        QMessageBox.information(self, "Help", "Help system will be implemented here.")
    
    def closeEvent(self, event):
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        reply = QMessageBox.question(
            self,
            "Exit Confirmation",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logger.info("Application exit confirmed by user")
            self.app_controller.shutdown()
            event.accept()
        else:
            self.logger.debug("Application exit cancelled by user")
            event.ignore()