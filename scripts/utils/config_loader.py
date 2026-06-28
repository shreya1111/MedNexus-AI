"""
Configuration loading utilities for MedNexus-AI Knowledge Ingestion Framework.

Provides YAML and JSON configuration file loading with validation.
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from .logger import get_logger

logger = get_logger(__name__)


def load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    logger.debug(f"Loading YAML configuration from: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if config is None:
            config = {}
        
        logger.info(f"Successfully loaded YAML configuration from: {file_path}")
        return config
        
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML file {file_path}: {e}")
        raise


def load_json_config(file_path: Path) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    logger.debug(f"Loading JSON configuration from: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logger.info(f"Successfully loaded JSON configuration from: {file_path}")
        return config
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {file_path}: {e}")
        raise


def save_yaml_config(config: Dict[str, Any], file_path: Path) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary
        file_path: Path to save YAML file
    """
    logger.debug(f"Saving YAML configuration to: {file_path}")
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Successfully saved YAML configuration to: {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save YAML file {file_path}: {e}")
        raise


def save_json_config(
    config: Dict[str, Any],
    file_path: Path,
    indent: int = 2,
) -> None:
    """
    Save configuration to JSON file.
    
    Args:
        config: Configuration dictionary
        file_path: Path to save JSON file
        indent: JSON indentation level
    """
    logger.debug(f"Saving JSON configuration to: {file_path}")
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=indent, ensure_ascii=False)
        
        logger.info(f"Successfully saved JSON configuration to: {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        raise


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries.
    Later configs override earlier ones.
    
    Args:
        *configs: Configuration dictionaries to merge
        
    Returns:
        Merged configuration
    """
    result = {}
    
    for config in configs:
        _deep_merge(result, config)
    
    return result


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """
    Deep merge override dictionary into base dictionary (in-place).
    
    Args:
        base: Base dictionary (modified in-place)
        override: Override dictionary
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def load_config_with_defaults(
    file_path: Path,
    defaults: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Load configuration with default values.
    
    Args:
        file_path: Path to configuration file
        defaults: Default configuration values
        
    Returns:
        Merged configuration
    """
    if defaults is None:
        defaults = {}
    
    # Determine file type and load
    if file_path.suffix.lower() in ['.yaml', '.yml']:
        config = load_yaml_config(file_path)
    elif file_path.suffix.lower() == '.json':
        config = load_json_config(file_path)
    else:
        raise ValueError(f"Unsupported configuration file format: {file_path.suffix}")
    
    # Merge with defaults
    return merge_configs(defaults, config)


def validate_config_schema(
    config: Dict[str, Any],
    required_keys: list[str],
) -> list[str]:
    """
    Validate configuration against required keys.
    
    Args:
        config: Configuration dictionary
        required_keys: List of required keys
        
    Returns:
        List of missing keys (empty if valid)
    """
    missing = []
    
    for key in required_keys:
        if '.' in key:
            # Handle nested keys like 'database.host'
            parts = key.split('.')
            current = config
            
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    missing.append(key)
                    break
                current = current[part]
        else:
            if key not in config:
                missing.append(key)
    
    return missing


class ConfigLoader:
    """
    Configuration loader with caching and validation.
    """
    
    def __init__(self, config_dir: Path):
        """
        Initialize configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def load(
        self,
        filename: str,
        required_keys: Optional[list[str]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Load configuration file.
        
        Args:
            filename: Configuration filename
            required_keys: List of required keys for validation
            use_cache: Whether to use cached configuration
            
        Returns:
            Configuration dictionary
        """
        # Check cache
        if use_cache and filename in self._cache:
            logger.debug(f"Using cached configuration for: {filename}")
            return self._cache[filename]
        
        # Load file
        file_path = self.config_dir / filename
        
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            config = load_yaml_config(file_path)
        elif file_path.suffix.lower() == '.json':
            config = load_json_config(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Validate
        if required_keys:
            missing = validate_config_schema(config, required_keys)
            if missing:
                raise ValueError(f"Missing required configuration keys: {missing}")
        
        # Cache
        if use_cache:
            self._cache[filename] = config
        
        return config
    
    def clear_cache(self, filename: Optional[str] = None) -> None:
        """
        Clear configuration cache.
        
        Args:
            filename: Specific file to clear (None = clear all)
        """
        if filename is None:
            self._cache.clear()
        elif filename in self._cache:
            del self._cache[filename]
