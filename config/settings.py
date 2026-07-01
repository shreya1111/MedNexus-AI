"""
Configuration settings for MedNexus-AI Knowledge Ingestion Framework.

This module provides centralized configuration management with environment
variable support, path resolution, and validation.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATASETS_DIR = PROJECT_ROOT / "datasets"
STORAGE_DIR = PROJECT_ROOT / "storage"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CONFIG_DIR = PROJECT_ROOT / "config"
LOGS_DIR = PROJECT_ROOT / "logs"
DOCS_DIR = PROJECT_ROOT / "docs"

# Dataset paths
RAW_DATA_DIR = DATASETS_DIR / "raw"
PROCESSED_DATA_DIR = DATASETS_DIR / "processed"
EVALUATION_DIR = DATASETS_DIR / "evaluation"

# Raw data subdirectories
CLINICAL_GUIDELINES_DIR = RAW_DATA_DIR / "clinical_guidelines"
DISEASE_INFO_DIR = RAW_DATA_DIR / "disease_information"
DRUG_DATABASE_DIR = RAW_DATA_DIR / "drug_database"
RESEARCH_PAPERS_DIR = RAW_DATA_DIR / "research_papers"
MEDICAL_BOOKS_DIR = RAW_DATA_DIR / "medical_books"
MEDICAL_QA_DIR = RAW_DATA_DIR / "medical_qa"

# Processed data subdirectories
CLEANED_DATA_DIR = PROCESSED_DATA_DIR / "cleaned"
CHUNKS_DIR = PROCESSED_DATA_DIR / "chunks"
METADATA_DIR = PROCESSED_DATA_DIR / "metadata"
EMBEDDINGS_DIR = PROCESSED_DATA_DIR / "embeddings"

# Storage paths
CHROMA_DB_DIR = STORAGE_DIR / "chroma_db"


@dataclass
class DownloadConfig:
    """Configuration for download operations."""
    
    max_retries: int = field(default_factory=lambda: int(os.getenv("DOWNLOAD_MAX_RETRIES", "3")))
    retry_delay: int = field(default_factory=lambda: int(os.getenv("DOWNLOAD_RETRY_DELAY", "5")))
    timeout: int = field(default_factory=lambda: int(os.getenv("DOWNLOAD_TIMEOUT", "300")))
    chunk_size: int = field(default_factory=lambda: int(os.getenv("DOWNLOAD_CHUNK_SIZE", "8192")))
    verify_ssl: bool = field(default_factory=lambda: os.getenv("DOWNLOAD_VERIFY_SSL", "true").lower() == "true")
    user_agent: str = field(default_factory=lambda: os.getenv(
        "DOWNLOAD_USER_AGENT",
        "MedNexus-AI-KnowledgeBot/1.0 (Medical Research; +https://mednexus-ai.example.com)"
    ))
    rate_limit_delay: float = field(default_factory=lambda: float(os.getenv("DOWNLOAD_RATE_LIMIT", "1.0")))
    max_file_size_mb: int = field(default_factory=lambda: int(os.getenv("DOWNLOAD_MAX_FILE_SIZE_MB", "500")))
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.rate_limit_delay < 0:
            raise ValueError("rate_limit_delay must be non-negative")
        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")


@dataclass
class ValidationConfig:
    """Configuration for validation operations."""
    
    check_duplicates: bool = field(default_factory=lambda: os.getenv("VALIDATION_CHECK_DUPLICATES", "true").lower() == "true")
    check_empty_files: bool = field(default_factory=lambda: os.getenv("VALIDATION_CHECK_EMPTY", "true").lower() == "true")
    check_metadata: bool = field(default_factory=lambda: os.getenv("VALIDATION_CHECK_METADATA", "true").lower() == "true")
    min_file_size_bytes: int = field(default_factory=lambda: int(os.getenv("VALIDATION_MIN_FILE_SIZE", "100")))
    allowed_extensions: list = field(default_factory=lambda: [
        ".pdf", ".txt", ".md", ".json", ".xml", ".html", ".csv"
    ])
    
    def __post_init__(self):
        """Validate configuration values."""
        if self.min_file_size_bytes < 0:
            raise ValueError("min_file_size_bytes must be non-negative")


@dataclass
class MetadataConfig:
    """Configuration for metadata management."""
    
    hash_algorithm: str = field(default_factory=lambda: os.getenv("METADATA_HASH_ALGORITHM", "sha256"))
    include_checksums: bool = field(default_factory=lambda: os.getenv("METADATA_INCLUDE_CHECKSUMS", "true").lower() == "true")
    track_lineage: bool = field(default_factory=lambda: os.getenv("METADATA_TRACK_LINEAGE", "true").lower() == "true")
    metadata_format: str = field(default_factory=lambda: os.getenv("METADATA_FORMAT", "json"))
    
    def __post_init__(self):
        """Validate configuration values."""
        valid_algorithms = ["md5", "sha1", "sha256", "sha512"]
        if self.hash_algorithm not in valid_algorithms:
            raise ValueError(f"hash_algorithm must be one of {valid_algorithms}")
        
        valid_formats = ["json", "yaml"]
        if self.metadata_format not in valid_formats:
            raise ValueError(f"metadata_format must be one of {valid_formats}")


@dataclass
class LoggingConfig:
    """Configuration for logging operations."""
    
    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    console_enabled: bool = field(default_factory=lambda: os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true")
    file_enabled: bool = field(default_factory=lambda: os.getenv("LOG_FILE_ENABLED", "true").lower() == "true")
    rotation_size_mb: int = field(default_factory=lambda: int(os.getenv("LOG_ROTATION_SIZE_MB", "10")))
    backup_count: int = field(default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", "5")))
    colored_console: bool = field(default_factory=lambda: os.getenv("LOG_COLORED_CONSOLE", "true").lower() == "true")
    
    def __post_init__(self):
        """Validate configuration values."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(f"level must be one of {valid_levels}")
        
        if self.rotation_size_mb <= 0:
            raise ValueError("rotation_size_mb must be positive")
        
        if self.backup_count < 0:
            raise ValueError("backup_count must be non-negative")


class Config:
    """Main configuration class for the Knowledge Ingestion Framework."""
    
    def __init__(self):
        """Initialize configuration with all sub-configs."""
        self.download = DownloadConfig()
        self.validation = ValidationConfig()
        self.metadata = MetadataConfig()
        self.logging = LoggingConfig()
        
        # Paths
        self.project_root = PROJECT_ROOT
        self.datasets_dir = DATASETS_DIR
        self.storage_dir = STORAGE_DIR
        self.scripts_dir = SCRIPTS_DIR
        self.config_dir = CONFIG_DIR
        self.logs_dir = LOGS_DIR
        self.docs_dir = DOCS_DIR
        
        # Raw data paths
        self.raw_data_dir = RAW_DATA_DIR
        self.clinical_guidelines_dir = CLINICAL_GUIDELINES_DIR
        self.disease_info_dir = DISEASE_INFO_DIR
        self.drug_database_dir = DRUG_DATABASE_DIR
        self.research_papers_dir = RESEARCH_PAPERS_DIR
        self.medical_books_dir = MEDICAL_BOOKS_DIR
        self.medical_qa_dir = MEDICAL_QA_DIR
        
        # Processed data paths
        self.processed_data_dir = PROCESSED_DATA_DIR
        self.cleaned_data_dir = CLEANED_DATA_DIR
        self.chunks_dir = CHUNKS_DIR
        self.metadata_dir = METADATA_DIR
        self.embeddings_dir = EMBEDDINGS_DIR
        
        # Storage paths
        self.chroma_db_dir = CHROMA_DB_DIR
        self.evaluation_dir = EVALUATION_DIR
    
    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        directories = [
            self.datasets_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.storage_dir,
            self.logs_dir,
            self.clinical_guidelines_dir,
            self.disease_info_dir,
            self.drug_database_dir,
            self.research_papers_dir,
            self.medical_books_dir,
            self.medical_qa_dir,
            self.cleaned_data_dir,
            self.chunks_dir,
            self.metadata_dir,
            self.embeddings_dir,
            self.chroma_db_dir,
            self.evaluation_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> list[str]:
        """
        Validate the configuration.
        
        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []
        
        # Validate paths exist
        if not self.project_root.exists():
            errors.append(f"Project root does not exist: {self.project_root}")
        
        # Validate sub-configs
        try:
            self.download.__post_init__()
        except ValueError as e:
            errors.append(f"Download config error: {e}")
        
        try:
            self.validation.__post_init__()
        except ValueError as e:
            errors.append(f"Validation config error: {e}")
        
        try:
            self.metadata.__post_init__()
        except ValueError as e:
            errors.append(f"Metadata config error: {e}")
        
        try:
            self.logging.__post_init__()
        except ValueError as e:
            errors.append(f"Logging config error: {e}")
        
        return errors
    
    def summary(self) -> dict:
        """
        Get a summary of the configuration.
        
        Returns:
            Dictionary containing configuration summary.
        """
        return {
            "project_root": str(self.project_root),
            "download": {
                "max_retries": self.download.max_retries,
                "timeout": self.download.timeout,
                "max_file_size_mb": self.download.max_file_size_mb,
            },
            "validation": {
                "check_duplicates": self.validation.check_duplicates,
                "check_empty_files": self.validation.check_empty_files,
                "min_file_size_bytes": self.validation.min_file_size_bytes,
            },
            "metadata": {
                "hash_algorithm": self.metadata.hash_algorithm,
                "format": self.metadata.metadata_format,
            },
            "logging": {
                "level": self.logging.level,
                "console_enabled": self.logging.console_enabled,
                "file_enabled": self.logging.file_enabled,
            },
        }


# Global configuration instance
config = Config()
