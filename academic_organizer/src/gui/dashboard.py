"""
Dashboard Widget for the Academic Organizer application.

This module contains the dashboard widget that displays an overview
of the user's academic information.
"""

import logging
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QPalette


class DashboardWidget(QWidget):
    """
    Dashboard widget that displays an overview of the user's academic information.
    
    This widget shows:
    - Upcoming assignments and deadlines
    - Course schedule
    - Recent materials
    - Study progress
    """
    
    def __init__(self, app_controller):
        """
        Initialize the dashboard widget.
        
        Args:
            app_controller: The application controller
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app_controller = app_controller
        
        # Set up the layout
        self._setup_ui()
        
        self.logger.debug("Dashboard widget initialized")
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        self.setLayout(main_layout)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Dashboard")
        header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._refresh_dashboard)
        header_layout.addWidget(refresh_button)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # Create a grid layout for dashboard widgets
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        # Add dashboard widgets
        self._add_upcoming_assignments_widget(grid_layout, 0, 0)
        self._add_course_schedule_widget(grid_layout, 0, 1)
        self._add_recent_materials_widget(grid_layout, 1, 0)
        self._add_study_progress_widget(grid_layout, 1, 1)
        
        main_layout.addLayout(grid_layout)
        main_layout.addStretch()
    
    def _create_dashboard_card(self, title):
        """
        Create a dashboard card widget.
        
        Args:
            title (str): Card title
            
        Returns:
            tuple: (card_widget, content_layout)
        """
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setFrameShadow(QFrame.Shadow.Raised)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card.setMinimumHeight(200)
        
        card_layout = QVBoxLayout()
        card.setLayout(card_layout)
        
        # Card header
        header_label = QLabel(title)
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        card_layout.addWidget(header_label)
        
        # Card content
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_widget.setLayout(content_layout)
        
        # Add scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        card_layout.addWidget(scroll_area)
        
        return card, content_layout
    
    def _add_upcoming_assignments_widget(self, parent_layout, row, col):
        """
        Add the upcoming assignments widget to the dashboard.
        
        Args:
            parent_layout: Parent layout
            row (int): Grid row
            col (int): Grid column
        """
        card, content_layout = self._create_dashboard_card("Upcoming Assignments")
        
        # TODO: Replace with actual data from the database
        # For now, add some placeholder items
        assignments = [
            {"title": "Math Homework", "course": "Calculus II", "due_date": datetime.now() + timedelta(days=1)},
            {"title": "Physics Lab Report", "course": "Physics 101", "due_date": datetime.now() + timedelta(days=2)},
            {"title": "Programming Project", "course": "CS 201", "due_date": datetime.now() + timedelta(days=5)},
        ]
        
        for assignment in assignments:
            days_left = (assignment["due_date"] - datetime.now()).days
            
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(0, 5, 0, 5)
            item_widget.setLayout(item_layout)
            
            # Assignment title and course
            title_label = QLabel(f"<b>{assignment['title']}</b><br>{assignment['course']}")
            item_layout.addWidget(title_label)
            
            item_layout.addStretch()
            
            # Due date
            due_label = QLabel(f"Due in {days_left} days")
            if days_left <= 1:
                due_label.setStyleSheet("color: red;")
            elif days_left <= 3:
                due_label.setStyleSheet("color: orange;")
            item_layout.addWidget(due_label)
            
            content_layout.addWidget(item_widget)
            
            # Add separator line
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            content_layout.addWidget(line)
        
        content_layout.addStretch()
        parent_layout.addWidget(card, row, col)
    
    def _add_course_schedule_widget(self, parent_layout, row, col):
        """
        Add the course schedule widget to the dashboard.
        
        Args:
            parent_layout: Parent layout
            row (int): Grid row
            col (int): Grid column
        """
        card, content_layout = self._create_dashboard_card("Today's Schedule")
        
        # TODO: Replace with actual data from the database
        # For now, add some placeholder items
        schedule = [
            {"course": "Calculus II", "time": "9:00 AM - 10:30 AM", "location": "Math Building 101"},
            {"course": "Physics 101", "time": "11:00 AM - 12:30 PM", "location": "Science Center 305"},
            {"course": "CS 201", "time": "2:00 PM - 3:30 PM", "location": "Computer Science Building 205"},
        ]
        
        for class_info in schedule:
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(0, 5, 0, 5)
            item_widget.setLayout(item_layout)
            
            # Course name
            course_label = QLabel(f"<b>{class_info['course']}</b>")
            item_layout.addWidget(course_label)
            
            item_layout.addStretch()
            
            # Time and location
            details_label = QLabel(f"{class_info['time']}<br>{class_info['location']}")
            details_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            item_layout.addWidget(details_label)
            
            content_layout.addWidget(item_widget)
            
            # Add separator line
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            content_layout.addWidget(line)
        
        content_layout.addStretch()
        parent_layout.addWidget(card, row, col)
    
    def _add_recent_materials_widget(self, parent_layout, row, col):
        """
        Add the recent materials widget to the dashboard.
        
        Args:
            parent_layout: Parent layout
            row (int): Grid row
            col (int): Grid column
        """
        card, content_layout = self._create_dashboard_card("Recent Materials")
        
        # TODO: Replace with actual data from the database
        # For now, add some placeholder items
        materials = [
            {"title": "Lecture Notes - Week 5", "course": "Calculus II", "date": "Yesterday"},
            {"title": "Lab Instructions", "course": "Physics 101", "date": "2 days ago"},
            {"title": "Programming Examples", "course": "CS 201", "date": "3 days ago"},
        ]
        
        for material in materials:
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(0, 5, 0, 5)
            item_widget.setLayout(item_layout)
            
            # Material title and course
            title_label = QLabel(f"<b>{material['title']}</b><br>{material['course']}")
            item_layout.addWidget(title_label)
            
            item_layout.addStretch()
            
            # Date
            date_label = QLabel(material['date'])
            item_layout.addWidget(date_label)
            
            content_layout.addWidget(item_widget)
            
            # Add separator line
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            content_layout.addWidget(line)
        
        content_layout.addStretch()
        parent_layout.addWidget(card, row, col)
    
    def _add_study_progress_widget(self, parent_layout, row, col):
        """
        Add the study progress widget to the dashboard.
        
        Args:
            parent_layout: Parent layout
            row (int): Grid row
            col (int): Grid column
        """
        card, content_layout = self._create_dashboard_card("Study Progress")
        
        # TODO: Replace with actual data from the database
        # For now, add some placeholder items
        progress = [
            {"course": "Calculus II", "progress": 65},
            {"course": "Physics 101", "progress": 80},
            {"course": "CS 201", "progress": 45},
        ]
        
        for course_progress in progress:
            item_widget = QWidget()
            item_layout = QVBoxLayout()
            item_layout.setContentsMargins(0, 5, 0, 5)
            item_widget.setLayout(item_layout)
            
            # Course name
            course_label = QLabel(f"<b>{course_progress['course']}</b>")
            item_layout.addWidget(course_label)
            
            # Progress bar
            progress_frame = QFrame()
            progress_frame.setFrameShape(QFrame.Shape.StyledPanel)
            progress_frame.setFixedHeight(20)
            progress_frame.setMinimumWidth(200)
            
            # Create a progress indicator
            progress_value = course_progress['progress']
            progress_layout = QHBoxLayout()
            progress_layout.setContentsMargins(0, 0, 0, 0)
            progress_frame.setLayout(progress_layout)
            
            # Filled part
            filled = QFrame()
            filled.setFixedWidth(int(progress_frame.minimumWidth() * progress_value / 100))
            filled.setStyleSheet("background-color: #4CAF50;")
            progress_layout.addWidget(filled)
            
            # Empty part
            empty = QFrame()
            empty.setStyleSheet("background-color: #E0E0E0;")
            progress_layout.addWidget(empty)
            
            item_layout.addWidget(progress_frame)
            
            # Progress percentage
            percentage_label = QLabel(f"{progress_value}% complete")
            percentage_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            item_layout.addWidget(percentage_label)
            
            content_layout.addWidget(item_widget)
            
            # Add separator line
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            content_layout.addWidget(line)
        
        content_layout.addStretch()
        parent_layout.addWidget(card, row, col)
    
    def _refresh_dashboard(self):
        """Refresh the dashboard data."""
        self.logger.debug("Refreshing dashboard")
        # TODO: Implement actual data refresh
        # For now, just show a message in the log
        self.logger.info("Dashboard refreshed")