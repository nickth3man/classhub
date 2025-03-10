"""
Application Controller for the Academic Organizer.

This module contains the main application controller that coordinates
all aspects of the application.
"""

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from academic_organizer.gui.main_window import MainWindow
from academic_organizer.database.db_manager import DatabaseManager
from academic_organizer.modules.course_manager import CourseManager
from academic_organizer.modules.file_organizer import AdaptiveFileOrganizer
from academic_organizer.modules.assignment_tracker import AssignmentTracker


class ApplicationController:
    """
    Main application controller that coordinates all aspects of the application.
    
    This class is responsible for:
    - Initializing all components
    - Managing the application lifecycle
    - Coordinating between different modules
    - Handling configuration
    """
    
    def __init__(self, config):
        """
        Initialize the application controller.
        
        Args:
            config (dict): Application configuration
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.app_data_dir = self._initialize_app_data_dir()
        
        # Initialize database
        self.db_manager = None
        
        # Initialize modules
        self.course_manager = None
        self.file_organizer = None
        self.assignment_tracker = None
        
        # Initialize GUI
        self.main_window = None
        
    def _initialize_app_data_dir(self):
        """
        Initialize the application data directory.
        
        Returns:
            Path: Path to the application data directory
        """
        app_data_dir = Path.home() / ".academic_organizer"
        if not app_data_dir.exists():
            app_data_dir.mkdir(parents=True)
            self.logger.info(f"Created application data directory: {app_data_dir}")
        return app_data_dir
        
    def initialize(self):
        """
        Initialize all application components.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Initialize database
            db_path = self.app_data_dir / "academic_organizer.db"
            self.db_manager = DatabaseManager(db_path)
            self.db_manager.initialize_database()
            
            # Initialize modules
            self.course_manager = CourseManager(self.db_manager)
            self.file_organizer = AdaptiveFileOrganizer(self.db_manager)
            self.assignment_tracker = AssignmentTracker(self.db_manager)
            
            # Initialize GUI
            self.main_window = MainWindow(self)
            
            self.logger.info("Application initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during application initialization: {e}", exc_info=True)
            return False
    
    def run(self):
        """
        Run the application.
        
        Returns:
            int: Exit code
        """
        if not self.initialize():
            self.logger.error("Application initialization failed")
            return 1
            
        # Show the main window
        self.main_window.show()
        
        # Run the application event loop
        return QApplication.instance().exec()
    
    def shutdown(self):
        """
        Perform cleanup and shutdown operations.
        """
        self.logger.info("Shutting down application")
        
        # Close database connections
        if self.db_manager:
            self.db_manager.close()
            
        # Perform any other cleanup
        # ...
        
        self.logger.info("Application shutdown complete")