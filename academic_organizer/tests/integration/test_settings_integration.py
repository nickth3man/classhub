import pytest
from academic_organizer.modules.settings import SettingsManager

class TestSettingsIntegration:
    def test_user_preferences(self, qtbot, settings_widget):
        """Test user preference management"""
        # Set preferences
        preferences = {
            "theme": "dark",
            "language": "en_US",
            "auto_save": True,
            "backup_frequency": "daily"
        }
        
        settings_widget.update_preferences(preferences)
        
        # Verify preferences
        current_prefs = settings_widget.get_preferences()
        assert current_prefs == preferences
        
    def test_backup_restore(self, qtbot, settings_widget, tmp_path):
        """Test backup and restore functionality"""
        # Create backup
        backup_path = tmp_path / "backup.zip"
        settings_widget.create_backup(str(backup_path))
        
        # Verify backup
        assert backup_path.exists()
        
        # Test restore
        restore_result = settings_widget.restore_from_backup(str(backup_path))
        assert restore_result.success
        
    def test_system_integration(self, qtbot, settings_widget):
        """Test system integration settings"""
        # Configure system integration
        integrations = {
            "calendar_sync": True,
            "cloud_backup": True,
            "email_notifications": True
        }
        
        settings_widget.configure_integrations(integrations)
        
        # Verify integration status
        status = settings_widget.get_integration_status()
        assert all(status[key].active for key in integrations)

    def test_notification_settings(self, qtbot, settings_widget):
        """Test notification settings configuration"""
        notification_settings = {
            "assignment_reminders": True,
            "deadline_alerts": True,
            "reminder_advance_time": 24,  # hours
            "notification_sound": "default",
            "quiet_hours": {"start": "22:00", "end": "07:00"}
        }
        
        # Configure notification settings
        settings_widget.update_notification_settings(notification_settings)
        
        # Verify settings were applied
        current_settings = settings_widget.get_notification_settings()
        assert current_settings == notification_settings
        
        # Test quiet hours functionality
        assert settings_widget.is_quiet_hours("23:00") == True
        assert settings_widget.is_quiet_hours("12:00") == False

    def test_appearance_settings(self, qtbot, settings_widget):
        """Test appearance settings configuration"""
        appearance_settings = {
            "theme": "dark",
            "font_size": 12,
            "font_family": "Arial",
            "custom_colors": {
                "primary": "#007AFF",
                "secondary": "#5856D6",
                "background": "#000000"
            }
        }
        
        # Apply appearance settings
        settings_widget.update_appearance_settings(appearance_settings)
        
        # Verify settings
        current_appearance = settings_widget.get_appearance_settings()
        assert current_appearance == appearance_settings
        
        # Verify theme application
        assert settings_widget.get_current_theme() == "dark"

    def test_performance_settings(self, qtbot, settings_widget):
        """Test performance-related settings"""
        performance_settings = {
            "auto_save_interval": 5,  # minutes
            "cache_size": 100,  # MB
            "max_recent_files": 10,
            "enable_animations": True,
            "hardware_acceleration": True
        }
        
        # Configure performance settings
        settings_widget.update_performance_settings(performance_settings)
        
        # Verify settings
        current_settings = settings_widget.get_performance_settings()
        assert current_settings == performance_settings
        
        # Test cache management
        settings_widget.clear_cache()
        assert settings_widget.get_cache_size() == 0
