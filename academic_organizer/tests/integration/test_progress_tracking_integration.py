import pytest
from academic_organizer.modules.progress_tracking import ProgressTracker

class TestProgressTrackingIntegration:
    def test_course_progress_tracking(self, qtbot, progress_widget, sample_course):
        """Test course progress tracking"""
        # Track various activities
        progress_widget.log_activity(sample_course.id, "assignment_completed")
        progress_widget.log_activity(sample_course.id, "lecture_attended")
        
        # Verify progress calculation
        progress = progress_widget.calculate_course_progress(sample_course.id)
        assert 0 <= progress <= 100
        assert "completed_assignments" in progress
        assert "attendance_rate" in progress
        
    def test_goal_tracking(self, qtbot, progress_widget):
        """Test academic goal tracking"""
        # Create academic goals
        goals = [
            {"type": "GPA", "target": 3.5, "deadline": "2025-05-01"},
            {"type": "COMPLETION", "target": 85, "deadline": "2025-04-15"}
        ]
        
        for goal in goals:
            progress_widget.set_goal(**goal)
            
        # Track progress
        progress_widget.update_goal_progress("GPA", 3.4)
        progress_widget.update_goal_progress("COMPLETION", 80)
        
        # Verify goal status
        goal_status = progress_widget.get_goal_status()
        assert len(goal_status) == 2
        assert all(g.progress is not None for g in goal_status)
        
    def test_performance_analytics(self, qtbot, progress_widget, sample_student_data):
        """Test performance analytics"""
        # Generate analytics
        analytics = progress_widget.generate_analytics(sample_student_data)
        
        # Verify analytics components
        assert "gpa_trend" in analytics
        assert "completion_rate" in analytics
        assert "performance_prediction" in analytics
        assert "improvement_areas" in analytics
        
    def test_progress_reporting(self, qtbot, progress_widget, sample_course):
        """Test progress report generation"""
        # Generate progress report
        report = progress_widget.generate_progress_report(sample_course.id)
        
        # Verify report contents
        assert "course_progress" in report
        assert "assignments_summary" in report
        assert "attendance_summary" in report
        assert "performance_metrics" in report