"""
Application Controller for the Academic Organizer.
Implements a modular architecture with dependency injection.
"""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import QApplication

from academic_organizer.gui.main_window import MainWindow
from academic_organizer.database.db_manager import DatabaseManager
from academic_organizer.modules.course_manager import CourseManager
from academic_organizer.modules.file_organizer import AdaptiveFileOrganizer
from academic_organizer.modules.assignment_tracker import AssignmentTracker
from academic_organizer.utils.exceptions import InitializationError

@dataclass
class AppComponents:
    """Container for application components."""
    db_manager: Optional[DatabaseManager] = None
    course_manager: Optional[CourseManager] = None
    file_organizer: Optional[AdaptiveFileOrganizer] = None
    assignment_tracker: Optional[AssignmentTracker] = None
    main_window: Optional[MainWindow] = None

class ApplicationController:
    """
    Main application controller implementing dependency injection pattern.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.app_data_dir = self._initialize_app_data_dir()
        self.components = AppComponents()
        
    def _initialize_app_data_dir(self) -> Path:
        """Initialize and return the application data directory."""
        app_data_dir = Path.home() / ".academic_organizer"
        try:
            app_data_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Application data directory: {app_data_dir}")
            return app_data_dir
        except Exception as e:
            raise InitializationError(f"Failed to create app data directory: {e}")

    def _initialize_database(self) -> None:
        """Initialize database component based on config."""
        try:
            db_engine = self.config.get("database.engine", "sqlite")
            if db_engine == "sqlite":
                db_path = self.app_data_dir / "academic_organizer.db"
                self.components.db_manager = DatabaseManager(db_path)
            elif db_engine == "postgresql":
                db_url = self.config.get("database.postgres_url")
                if not db_url:
                    raise ConfigurationError("PostgreSQL URL not configured.")
                self.components.db_manager = PostgresDatabaseManager(db_url)
            else:
                raise ConfigurationError(f"Unsupported database engine: {db_engine}")

            self.components.db_manager.initialize_database()
        except ConfigurationError as e:
            raise e # Re-raise ConfigurationError
        except Exception as e:
            raise InitializationError(f"Database initialization failed: {e}")

    def _initialize_modules(self) -> None:
        """Initialize application modules."""
        try:
            db = self.components.db_manager
            if not db:
                raise InitializationError("Database manager not initialized")
            
            self.components.course_manager = CourseManager(db)
            self.components.file_organizer = AdaptiveFileOrganizer(db)
            self.components.assignment_tracker = AssignmentTracker(db)
        except Exception as e:
            raise InitializationError(f"Module initialization failed: {e}")

    def _initialize_gui(self) -> None:
        """Initialize GUI components."""
        try:
            self.components.main_window = MainWindow(
                course_manager=self.components.course_manager,
                file_organizer=self.components.file_organizer,
                assignment_tracker=self.components.assignment_tracker
            )
        except Exception as e:
            raise InitializationError(f"GUI initialization failed: {e}")

    def initialize(self) -> bool:
        """
        Initialize all application components.
        Returns: bool indicating success
        """
        try:
            self._initialize_database()
            self._initialize_modules()
            self._initialize_gui()
            return True
        except InitializationError as e:
            self.logger.error(f"Initialization failed: {e}")
            return False

    def start(self) -> None:
        """Start the application."""
        if self.components.main_window:
            self.components.main_window.show()
        else:
            raise InitializationError("Main window not initialized")

    def shutdown(self) -> None:
        """Clean shutdown of application components."""
        try:
            if self.components.db_manager:
                self.components.db_manager.close()
            self.logger.info("Application shutdown complete")
        except Exception as e:
            self.logger.info("Application shutdown complete")
