#!/usr/bin/env python3
"""
Run script for the Academic Organizer application.

This script provides a convenient way to run the application during development.
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from academic_organizer.core.main import main


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )
    
    # Create application data directory if it doesn't exist
    app_data_dir = Path.home() / ".academic_organizer"
    if not app_data_dir.exists():
        app_data_dir.mkdir(parents=True)
        logging.info(f"Created application data directory: {app_data_dir}")
    
    # Run the application
    sys.exit(main())