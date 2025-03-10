"""
Unit tests for the configuration module.
"""

import os
import tempfile
import unittest
from pathlib import Path

import pytest
import yaml

from academic_organizer.src.utils.config import load_config, DEFAULT_CONFIG, _merge_configs, _expand_paths


class TestConfig(unittest.TestCase):
    """Test cases for the configuration module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary directory
        self.temp_dir.cleanup()

    def test_default_config(self):
        """Test that default configuration is loaded when no config file is provided."""
        config = load_config()
        
        # Verify default values
        self.assertEqual(config["application"]["name"], "Academic Organizer")
        self.assertEqual(config["database"]["type"], "sqlite")
        self.assertEqual(config["gui"]["theme"], "system")
        self.assertTrue(config["modules"]["course_manager"]["enabled"])

    def test_load_custom_config(self):
        """Test loading a custom configuration file."""
        # Create a custom config file
        custom_config = {
            "application": {
                "name": "Custom Organizer",
                "version": "0.2.0"
            },
            "gui": {
                "theme": "dark"
            }
        }
        
        config_path = self.temp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(custom_config, f)
        
        # Load the custom config
        config = load_config(str(config_path))
        
        # Verify custom values are loaded
        self.assertEqual(config["application"]["name"], "Custom Organizer")
        self.assertEqual(config["application"]["version"], "0.2.0")
        self.assertEqual(config["gui"]["theme"], "dark")
        
        # Verify default values for unspecified settings
        self.assertEqual(config["database"]["type"], "sqlite")
        self.assertTrue(config["modules"]["course_manager"]["enabled"])

    def test_merge_configs(self):
        """Test merging configurations."""
        default = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3
            }
        }
        
        user = {
            "a": 10,
            "b": {
                "c": 20
            }
        }
        
        merged = _merge_configs(default, user)
        
        # Verify merged values
        self.assertEqual(merged["a"], 10)  # Overridden
        self.assertEqual(merged["b"]["c"], 20)  # Overridden
        self.assertEqual(merged["b"]["d"], 3)  # Preserved from default

    def test_expand_paths(self):
        """Test path expansion in configuration."""
        config = {
            "application": {
                "data_dir": "~/app_data"
            },
            "modules": {
                "file_organizer": {
                    "default_storage_path": "~/Documents/Files"
                }
            }
        }
        
        _expand_paths(config)
        
        # Verify paths are expanded
        self.assertEqual(
            config["application"]["data_dir"],
            os.path.expanduser("~/app_data")
        )
        self.assertEqual(
            config["modules"]["file_organizer"]["default_storage_path"],
            os.path.expanduser("~/Documents/Files")
        )

    def test_nonexistent_config_file(self):
        """Test behavior when config file doesn't exist."""
        config_path = self.temp_path / "nonexistent.yaml"
        
        # Should load default config without errors
        config = load_config(str(config_path))
        
        # Verify default values
        self.assertEqual(config["application"]["name"], "Academic Organizer")
        self.assertEqual(config["database"]["type"], "sqlite")


if __name__ == "__main__":
    unittest.main()