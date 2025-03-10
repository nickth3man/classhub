import pytest
from datetime import datetime, timedelta
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox
from academic_organizer.modules.course_manager import CourseManager
from academic_organizer.database.models import Course, Syllabus

class TestCourseIntegration:
    def test_course_creation_workflow(self, qtbot, course_widget, sample_course_data):
        """Test complete course creation workflow"""
        initial_count = course_widget.course_table.rowCount()
        
        # Click add course button
        qtbot.mouseClick(course_widget.add_button, Qt.MouseButton.LeftButton)
        dialog = course_widget.findChild(CourseDialog)
        
        # Fill course details
        dialog.name_input.setText(sample_course_data["name"])
        dialog.code_input.setText(sample_course_data["code"])
        dialog.semester_input.setText(sample_course_data["semester"])
        
        # Save course
        qtbot.mouseClick(dialog.button_box.button(QMessageBox.StandardButton.Ok),
                        Qt.MouseButton.LeftButton)
                        
        # Verify course added
        assert course_widget.course_table.rowCount() == initial_count + 1
        
    def test_syllabus_import(self, qtbot, course_widget, tmp_path):
        """Test syllabus import and parsing"""
        # Create mock syllabus file
        syllabus_file = tmp_path / "test_syllabus.pdf"
        syllabus_file.write_bytes(b"Test syllabus content")
        
        # Import syllabus
        course_widget.import_syllabus(str(syllabus_file))
        
        # Verify extracted information
        latest_course = CourseManager.get_latest_course()
        assert latest_course.name is not None
        assert latest_course.instructor is not None
        assert len(latest_course.assignments) > 0
        
    def test_course_schedule_generation(self, qtbot, course_widget, sample_course):
        """Test schedule generation for courses"""
        # Generate schedule
        schedule = course_widget.generate_schedule([sample_course])
        
        # Verify schedule properties
        assert len(schedule.time_slots) > 0
        assert all(slot.course_id == sample_course.id for slot in schedule.time_slots)
        assert not schedule.has_conflicts()
        
    def test_course_statistics(self, qtbot, course_widget, sample_course):
        """Test course statistics calculation"""
        stats = course_widget.calculate_course_stats(sample_course.id)
        
        assert "assignment_count" in stats
        assert "completion_rate" in stats
        assert "average_grade" in stats
        assert "workload_distribution" in stats

    def test_course_export(self, qtbot, course_widget, sample_course, tmp_path):
        """Test course data export"""
        export_path = tmp_path / "course_export.json"
        
        # Export course data
        course_widget.export_course_data(sample_course.id, str(export_path))
        
        # Verify exported file
        assert export_path.exists()
        exported_data = json.loads(export_path.read_text())
        assert exported_data["name"] == sample_course.name
        assert exported_data["code"] == sample_course.code