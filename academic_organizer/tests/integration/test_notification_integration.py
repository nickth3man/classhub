import pytest
from datetime import datetime, timedelta
from academic_organizer.modules.notification import NotificationManager

class TestNotificationIntegration:
    def test_deadline_notifications(self, qtbot, notification_widget, sample_assignment):
        """Test deadline notification system"""
        # Create upcoming deadline
        deadline = datetime.now() + timedelta(days=1)
        sample_assignment.due_date = deadline
        
        # Check notification generation
        notifications = notification_widget.get_notifications()
        deadline_notice = next(n for n in notifications 
                             if n.assignment_id == sample_assignment.id)
        
        assert deadline_notice is not None
        assert deadline_notice.type == "DEADLINE"
        assert deadline_notice.urgency == "HIGH"
        
    def test_notification_preferences(self, qtbot, notification_widget):
        """Test notification preference management"""
        # Set preferences
        preferences = {
            "deadline_advance_notice": 48,  # hours
            "email_notifications": True,
            "desktop_notifications": True,
            "notification_quiet_hours": ["22:00", "06:00"]
        }
        
        notification_widget.update_preferences(preferences)
        
        # Verify preferences applied
        current_prefs = notification_widget.get_preferences()
        assert current_prefs == preferences
        
    def test_notification_delivery(self, qtbot, notification_widget, sample_notification):
        """Test notification delivery system"""
        # Test email delivery
        email_result = notification_widget.send_email_notification(sample_notification)
        assert email_result.status == "SENT"
        
        # Test desktop notification
        desktop_result = notification_widget.send_desktop_notification(sample_notification)
        assert desktop_result.status == "DISPLAYED"
        
    def test_notification_history(self, qtbot, notification_widget):
        """Test notification history tracking"""
        # Generate test notifications
        notifications = [
            {"type": "DEADLINE", "message": "Test 1"},
            {"type": "SYSTEM", "message": "Test 2"},
            {"type": "UPDATE", "message": "Test 3"}
        ]
        
        for notif in notifications:
            notification_widget.create_notification(**notif)
            
        # Verify history
        history = notification_widget.get_notification_history()
        assert len(history) == 3
        assert all(n.status == "DELIVERED" for n in history)