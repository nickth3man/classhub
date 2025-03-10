#!/usr/bin/env python3
"""
Main entry point for the Academic Organizer application.
"""

import sys
import logging
from pathlib import Path
import argparse

from PyQt6.QtWidgets import QApplication

from academic_organizer.core.app_controller import ApplicationController
from academic_organizer.utils.config import load_config


def setup_logging(log_level=logging.INFO):
    """Configure application logging."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Path.home() / ".academic_organizer" / "app.log"),
        ],
    )
    return logging.getLogger("academic_organizer")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Academic Organizer")
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    return parser.parse_args()


def main():
    """Main application entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging(log_level)
    logger.info("Starting Academic Organizer")
    
    # Load configuration
    config_path = args.config if args.config else None
    config = load_config(config_path)
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Academic Organizer")
    app.setApplicationVersion("0.1.0")
    
    # Create and initialize the application controller
    controller = ApplicationController(config)
    
    # Start the application
    exit_code = controller.run()
    
    logger.info(f"Application exited with code {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())