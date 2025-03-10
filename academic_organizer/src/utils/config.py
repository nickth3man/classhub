"""
Configuration utilities for the Academic Organizer application.

This module handles loading, validating, and accessing application configuration.
"""

import os
import logging
import yaml
from pathlib import Path


logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "application": {
        "name": "Academic Organizer",
        "version": "0.1.0",
        "data_dir": "~/.academic_organizer",
    },
    "database": {
        "type": "sqlite",
        "name": "academic_organizer.db",
    },
    "gui": {
        "theme": "system",
        "font_size": 10,
        "window_size": {
            "width": 1200,
            "height": 800,
        },
    },
    "modules": {
        "course_manager": {
            "enabled": True,
        },
        "file_organizer": {
            "enabled": True,
            "default_storage_path": "~/Documents/Academic_Organizer",
        },
        "assignment_tracker": {
            "enabled": True,
            "reminder_days_before": 3,
        },
        "study_enhancement": {
            "enabled": True,
        },
        "lms_bridge": {
            "enabled": False,
        },
    },
    "ai": {
        "enabled": True,
        "api_type": "openrouter",
        "api_key_env_var": "OPENROUTER_API_KEY",
    },
}


def load_config(config_path=None):
    """
    Load application configuration from a file.
    
    Args:
        config_path (str, optional): Path to the configuration file.
            If not provided, the function will look for a config file in standard locations.
            
    Returns:
        dict: The loaded configuration, merged with default values.
    """
    config = DEFAULT_CONFIG.copy()
    
    # Determine config file path
    if config_path is None:
        # Look in standard locations
        potential_paths = [
            Path.cwd() / "config.yaml",
            Path.cwd() / "config.yml",
            Path.home() / ".academic_organizer" / "config.yaml",
            Path.home() / ".config" / "academic_organizer" / "config.yaml",
        ]
        
        for path in potential_paths:
            if path.exists():
                config_path = path
                break
    
    # Load config file if it exists
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    # Merge user config with default config
                    config = _merge_configs(config, user_config)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
    else:
        logger.info("No configuration file found, using default configuration")
    
    # Expand paths
    _expand_paths(config)
    
    return config


def _merge_configs(default_config, user_config):
    """
    Recursively merge user configuration with default configuration.
    
    Args:
        default_config (dict): Default configuration
        user_config (dict): User configuration
        
    Returns:
        dict: Merged configuration
    """
    result = default_config.copy()
    
    for key, value in user_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
            
    return result


def _expand_paths(config):
    """
    Expand paths in the configuration.
    
    Args:
        config (dict): Configuration dictionary
    """
    if "application" in config and "data_dir" in config["application"]:
        config["application"]["data_dir"] = os.path.expanduser(config["application"]["data_dir"])
        
    if "modules" in config and "file_organizer" in config["modules"] and "default_storage_path" in config["modules"]["file_organizer"]:
        config["modules"]["file_organizer"]["default_storage_path"] = os.path.expanduser(
            config["modules"]["file_organizer"]["default_storage_path"]
        )