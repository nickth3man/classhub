"""Configuration management system."""
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from ..utils.error_handler import ConfigurationError, handle_errors

class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/config.yaml")
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    @handle_errors(ConfigurationError)
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            self._create_default_config()
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        default_config = {
            'database': {
                'engine': 'sqlite', # or 'postgresql'
                'sqlite_path': 'data/academic_organizer.db',
                'postgres_url': 'postgresql://user:password@host:port/database', # Placeholder
                'backup_dir': 'data/backups'
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/app.log'
            },
            'paths': {
                'materials': 'data/materials',
                'temp': 'data/temp'
            },
            'ui': {
                'theme': 'light',
                'font_size': 12
            }
        }
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f)
        
        self.config = default_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    @handle_errors(ConfigurationError)
    def update(self, key: str, value: Any) -> None:
        """Update configuration value."""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
        
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f)