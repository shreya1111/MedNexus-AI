"""
Logging utilities for MedNexus-AI Knowledge Ingestion Framework.

Provides centralized logging with console and file output, colored formatting,
rotation, and module-specific loggers.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for console."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    def __init__(self, fmt: str, datefmt: Optional[str] = None, colored: bool = True):
        """
        Initialize the colored formatter.
        
        Args:
            fmt: Log format string
            datefmt: Date format string
            colored: Whether to use colored output
        """
        super().__init__(fmt, datefmt)
        self.colored = colored
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with colors.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string with color codes
        """
        if self.colored and sys.stdout.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = (
                    f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
                )
        
        return super().format(record)


class LoggerManager:
    """Manager for creating and configuring loggers."""
    
    _loggers: dict[str, logging.Logger] = {}
    _configured: bool = False
    
    @classmethod
    def setup(
        cls,
        log_dir: Path,
        log_level: str = "INFO",
        console_enabled: bool = True,
        file_enabled: bool = True,
        colored_console: bool = True,
        rotation_size_mb: int = 10,
        backup_count: int = 5,
    ) -> None:
        """
        Setup the logging system with console and file handlers.
        
        Args:
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_enabled: Whether to enable console logging
            file_enabled: Whether to enable file logging
            colored_console: Whether to use colored console output
            rotation_size_mb: Size in MB before rotating log files
            backup_count: Number of backup log files to keep
        """
        if cls._configured:
            return
        
        # Ensure log directory exists
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Log format
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        
        # Console handler
        if console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level.upper()))
            console_formatter = ColoredFormatter(
                log_format,
                datefmt=date_format,
                colored=colored_console
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # File handler with rotation
        if file_enabled:
            log_file = log_dir / f"knowledge_ingestion_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=rotation_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)  # Always DEBUG for file
            file_formatter = logging.Formatter(log_format, datefmt=date_format)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        
        cls._configured = True
        
        # Log initial message
        root_logger.info("=" * 80)
        root_logger.info("MedNexus-AI Knowledge Ingestion Framework - Logging Initialized")
        root_logger.info(f"Log Level: {log_level}")
        root_logger.info(f"Console: {'Enabled' if console_enabled else 'Disabled'}")
        root_logger.info(f"File Logging: {'Enabled' if file_enabled else 'Disabled'}")
        if file_enabled:
            root_logger.info(f"Log Directory: {log_dir}")
        root_logger.info("=" * 80)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a logger with the given name.
        
        Args:
            name: Name of the logger (usually __name__)
            
        Returns:
            Configured logger instance
        """
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def reset(cls) -> None:
        """Reset the logging system (useful for testing)."""
        cls._loggers.clear()
        cls._configured = False
        
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance
    """
    return LoggerManager.get_logger(name)


def setup_logging(
    log_dir: Path,
    log_level: str = "INFO",
    console_enabled: bool = True,
    file_enabled: bool = True,
    colored_console: bool = True,
    rotation_size_mb: int = 10,
    backup_count: int = 5,
) -> None:
    """
    Setup the logging system (convenience function).
    
    Args:
        log_dir: Directory for log files
        log_level: Logging level
        console_enabled: Enable console output
        file_enabled: Enable file output
        colored_console: Use colored console output
        rotation_size_mb: File size before rotation
        backup_count: Number of backup files
    """
    LoggerManager.setup(
        log_dir=log_dir,
        log_level=log_level,
        console_enabled=console_enabled,
        file_enabled=file_enabled,
        colored_console=colored_console,
        rotation_size_mb=rotation_size_mb,
        backup_count=backup_count,
    )
