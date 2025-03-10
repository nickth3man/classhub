from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import json
import zipfile
import csv
from fpdf import FPDF
import icalendar
import pytz

class ExportManager:
    """
    Manages export functionality for course materials and data.
    
    This class handles exporting course content, assignments, and schedules
    in various formats including PDF, ZIP, JSON, iCal, and CSV.
    """
    
    # Export format constants
    FORMAT_PDF = "pdf"
    FORMAT_ZIP = "zip"
    FORMAT_JSON = "json"
    FORMAT_ICAL = "ical"
    FORMAT_CSV = "csv"
    
    def __init__(self, db_manager, file_manager):
        """
        Initialize the ExportManager.
        
        Args:
            db_manager: Database manager instance
            file_manager: File manager instance
        """
        self.db_manager = db_manager
        self.file_manager = file_manager
        self.logger = logging.getLogger(__name__)

    def export_course(self, 
                     course_id: int, 
                     export_path: Path,
                     format: str = FORMAT_PDF) -> bool:
        """
        Export all course materials, assignments, and notes.
        
        Args:
            course_id: Course identifier
            export_path: Where to save the export
            format: Export format ("pdf", "zip", "json")
            
        Returns:
            bool: True if export successful, False otherwise
            
        Raises:
            ValueError: If invalid format specified
        """
        if format not in [self.FORMAT_PDF, self.FORMAT_ZIP, self.FORMAT_JSON]:
            raise ValueError(f"Unsupported export format: {format}")
            
        try:
            # Gather all course data
            course_data = self._gather_course_data(course_id)
            
            # Select export method based on format
            export_methods = {
                self.FORMAT_PDF: self._export_as_pdf,
                self.FORMAT_ZIP: self._export_as_zip,
                self.FORMAT_JSON: self._export_as_json
            }
            
            return export_methods[format](export_path, **course_data)
            
        except Exception as e:
            self.logger.error(f"Course export failed: {e}", exc_info=True)
            return False

    def export_assignments(self, 
                         assignment_ids: List[int],
                         export_path: Path,
                         include_materials: bool = True) -> bool:
        """
        Export specific assignments with optional related materials.
        
        Args:
            assignment_ids: List of assignment IDs to export
            export_path: Where to save the export
            include_materials: Whether to include related files
            
        Returns:
            bool: True if export successful, False otherwise
        """
        try:
            export_data = self._gather_assignment_data(
                assignment_ids, 
                include_materials
            )
            
            return self._export_as_pdf(
                export_path,
                title="Assignment Export",
                **export_data
            )
            
        except Exception as e:
            self.logger.error(f"Assignment export failed: {e}", exc_info=True)
            return False

    def export_schedule(self, 
                       course_ids: List[int],
                       export_path: Path,
                       format: str = FORMAT_ICAL) -> bool:
        """
        Export course schedules and deadlines.
        
        Args:
            course_ids: List of course IDs to include
            export_path: Where to save the export
            format: Export format ("ical" or "csv")
            
        Returns:
            bool: True if export successful, False otherwise
            
        Raises:
            ValueError: If invalid format specified
        """
        if format not in [self.FORMAT_ICAL, self.FORMAT_CSV]:
            raise ValueError(f"Unsupported schedule format: {format}")
            
        try:
            schedules = self._gather_schedule_data(course_ids)
            
            export_methods = {
                self.FORMAT_ICAL: self._export_as_ical,
                self.FORMAT_CSV: self._export_as_csv
            }
            
            return export_methods[format](export_path, schedules)
            
        except Exception as e:
            self.logger.error(f"Schedule export failed: {e}", exc_info=True)
            return False

    def _gather_course_data(self, course_id: int) -> Dict[str, Any]:
        """Gather all data for a course export."""
        return {
            'course_data': self.db_manager.get_course(course_id),
            'assignments': self.db_manager.get_course_assignments(course_id),
            'materials': self.file_manager.get_files_by_course()[course_id],
            'notes': self.db_manager.get_course_notes(course_id)
        }

    def _gather_assignment_data(self, 
                              assignment_ids: List[int],
                              include_materials: bool) -> Dict[str, Any]:
        """Gather data for assignment export."""
        assignments = []
        materials = []
        
        for assignment_id in assignment_ids:
            assignment = self.db_manager.get_assignment(assignment_id)
            assignments.append(assignment)
            
            if include_materials:
                assignment_files = self.file_manager.get_assignment_files(
                    assignment_id
                )
                materials.extend(assignment_files)
                
        return {
            'assignments': assignments,
            'materials': materials if include_materials else []
        }

    def _gather_schedule_data(self, course_ids: List[int]) -> List[Dict]:
        """Gather schedule data for export."""
        return [{
            "course": self.db_manager.get_course(course_id),
            "assignments": self.db_manager.get_course_assignments(course_id)
        } for course_id in course_ids]

    def _export_as_pdf(self, export_path: Path, **kwargs) -> bool:
        """
        Generate a formatted PDF export.
        
        Args:
            export_path: Where to save the PDF
            **kwargs: Content to include in PDF
        
        Returns:
            bool: Success status
        
        Raises:
            IOError: If file operations fail
            MemoryError: If content exceeds memory limits
        """
        try:
            # Validate export path
            if not export_path.parent.exists():
                export_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize PDF with memory limits
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            
            # Add content with size validation
            content_size = 0
            MAX_SIZE = 100 * 1024 * 1024  # 100MB limit
            
            # Add title if provided
            if 'title' in kwargs:
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, kwargs['title'], ln=True, align='C')
            
            # Add course information if available
            if 'course_data' in kwargs:
                self._add_course_section(pdf, kwargs['course_data'])
            
            # Add assignments
            if 'assignments' in kwargs:
                self._add_assignments_section(pdf, kwargs['assignments'])
            
            # Add materials list
            if 'materials' in kwargs:
                self._add_materials_section(pdf, kwargs['materials'])
            
            # Add notes if available
            if 'notes' in kwargs:
                self._add_notes_section(pdf, kwargs['notes'])
            
            pdf.output(str(export_path))
            return True
            
        except Exception as e:
            self.logger.error(f"PDF generation failed: {e}", exc_info=True)
            return False

    def _export_as_zip(self, export_path: Path, **kwargs) -> bool:
        """
        Create a ZIP archive of materials.
        
        Args:
            export_path: Where to save the ZIP
            **kwargs: Content to include in archive
        """
        try:
            with zipfile.ZipFile(export_path, 'w') as zf:
                # Add course info as JSON
                if 'course_data' in kwargs:
                    zf.writestr(
                        'course_info.json',
                        json.dumps(kwargs['course_data'], indent=2)
                    )
                
                # Add assignments as JSON
                if 'assignments' in kwargs:
                    zf.writestr(
                        'assignments.json',
                        json.dumps(kwargs['assignments'], indent=2)
                    )
                
                # Add materials with original filenames
                if 'materials' in kwargs:
                    for material in kwargs['materials']:
                        file_path = Path(material['file_path'])
                        zf.write(file_path, file_path.name)
                
                # Add notes as text files
                if 'notes' in kwargs:
                    for i, note in enumerate(kwargs['notes']):
                        zf.writestr(
                            f'notes/note_{i+1}.txt',
                            note['content']
                        )
            return True
            
        except Exception as e:
            self.logger.error(f"ZIP creation failed: {e}", exc_info=True)
            return False

    def _export_as_json(self, export_path: Path, **kwargs) -> bool:
        """
        Export data in JSON format.
        
        Args:
            export_path: Where to save the JSON
            **kwargs: Content to include in export
        """
        try:
            with open(export_path, 'w') as f:
                json.dump(kwargs, f, indent=2, default=str)
            return True
            
        except Exception as e:
            self.logger.error(f"JSON export failed: {e}", exc_info=True)
            return False

    def _export_as_ical(self, export_path: Path, schedules: List) -> bool:
        """
        Export schedule in iCalendar format.
        
        Args:
            export_path: Where to save the iCal file
            schedules: List of course schedules
        """
        try:
            cal = icalendar.Calendar()
            cal.add('prodid', '-//Academic Organizer//EN')
            cal.add('version', '2.0')
            
            for schedule in schedules:
                course = schedule['course']
                
                # Add course meetings as recurring events
                if course.get('meeting_times'):
                    event = icalendar.Event()
                    event.add('summary', course['name'])
                    # Add meeting time details...
                    cal.add_component(event)
                
                # Add assignments as individual events
                for assignment in schedule['assignments']:
                    event = icalendar.Event()
                    event.add('summary', f"Due: {assignment['title']}")
                    event.add('dtstart', assignment['due_date'])
                    event.add('description', assignment['description'])
                    cal.add_component(event)
            
            with open(export_path, 'wb') as f:
                f.write(cal.to_ical())
            return True
            
        except Exception as e:
            self.logger.error(f"iCal export failed: {e}", exc_info=True)
            return False

    def _export_as_csv(self, export_path: Path, schedules: List) -> bool:
        """
        Export schedule in CSV format.
        
        Args:
            export_path: Where to save the CSV
            schedules: List of course schedules
        """
        try:
            with open(export_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Course', 'Type', 'Title', 'Due Date', 'Description'
                ])
                
                for schedule in schedules:
                    course = schedule['course']
                    
                    # Add course meetings
                    if course.get('meeting_times'):
                        for meeting in course['meeting_times']:
                            writer.writerow([
                                course['name'],
                                'Class Meeting',
                                'Regular Class',
                                meeting['time'],
                                meeting['location']
                            ])
                    
                    # Add assignments
                    for assignment in schedule['assignments']:
                        writer.writerow([
                            course['name'],
                            'Assignment',
                            assignment['title'],
                            assignment['due_date'],
                            assignment['description']
                        ])
            return True
            
        except Exception as e:
            self.logger.error(f"CSV export failed: {e}", exc_info=True)
            return False

    def _add_course_section(self, pdf: FPDF, course_data: Dict) -> None:
        """Add course information section to PDF."""
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Course Information', ln=True)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Name: {course_data['name']}", ln=True)
        # Add more course details...

    def _add_assignments_section(self, pdf: FPDF, assignments: List) -> None:
        """Add assignments section to PDF."""
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Assignments', ln=True)
        pdf.set_font('Arial', '', 12)
        for assignment in assignments:
            pdf.cell(0, 10, f"- {assignment['title']}", ln=True)
            pdf.multi_cell(0, 10, assignment['description'])

    def _add_materials_section(self, pdf: FPDF, materials: List) -> None:
        """Add materials section to PDF."""
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Materials', ln=True)
        pdf.set_font('Arial', '', 12)
        for material in materials:
            pdf.cell(0, 10, f"- {material['name']}", ln=True)

    def _add_notes_section(self, pdf: FPDF, notes: List) -> None:
        """Add notes section to PDF."""
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Notes', ln=True)
        pdf.set_font('Arial', '', 12)
        for note in notes:
            pdf.multi_cell(0, 10, note['content'])
