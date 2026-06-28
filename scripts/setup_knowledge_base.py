"""
Setup script for MedNexus-AI Knowledge Ingestion Framework.

Initializes the knowledge base infrastructure, validates configuration,
and prepares the system for data ingestion.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config.settings import config
from utils.logger import setup_logging, get_logger
from validators import FolderValidator, DatasetValidator
from utils.config_loader import load_yaml_config


def print_banner():
    """Print setup banner."""
    print("=" * 80)
    print("MedNexus-AI Knowledge Ingestion Framework")
    print("Setup and Initialization")
    print("=" * 80)
    print()


def verify_configuration():
    """Verify configuration settings."""
    logger = get_logger(__name__)
    logger.info("Step 1: Verifying configuration...")
    
    errors = config.validate()
    
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  ✗ {error}")
        return False
    
    logger.info("  ✓ Configuration valid")
    
    # Display configuration summary
    summary = config.summary()
    logger.info(f"  ✓ Project root: {summary['project_root']}")
    logger.info(f"  ✓ Download max retries: {summary['download']['max_retries']}")
    logger.info(f"  ✓ Hash algorithm: {summary['metadata']['hash_algorithm']}")
    logger.info(f"  ✓ Log level: {summary['logging']['level']}")
    
    return True


def create_folders():
    """Create required folder structure."""
    logger = get_logger(__name__)
    logger.info("Step 2: Creating folder structure...")
    
    try:
        config.ensure_directories()
        logger.info("  ✓ All directories created")
        
        # List created directories
        directories = [
            ("Raw Data", config.raw_data_dir),
            ("  - Clinical Guidelines", config.clinical_guidelines_dir),
            ("  - Disease Information", config.disease_info_dir),
            ("  - Drug Database", config.drug_database_dir),
            ("  - Research Papers", config.research_papers_dir),
            ("  - Medical Books", config.medical_books_dir),
            ("  - Medical Q&A", config.medical_qa_dir),
            ("Processed Data", config.processed_data_dir),
            ("  - Cleaned", config.cleaned_data_dir),
            ("  - Chunks", config.chunks_dir),
            ("  - Metadata", config.metadata_dir),
            ("Storage", config.storage_dir),
            ("Logs", config.logs_dir),
        ]
        
        for name, path in directories:
            exists = "✓" if path.exists() else "✗"
            logger.info(f"    {exists} {name}: {path}")
        
        return True
        
    except Exception as e:
        logger.error(f"  ✗ Failed to create directories: {e}")
        return False


def initialize_logging():
    """Initialize logging system."""
    logger = get_logger(__name__)
    logger.info("Step 3: Initializing logging system...")
    
    try:
        # Logging already initialized by setup_logging() call
        logger.info("  ✓ Console logging enabled")
        logger.info("  ✓ File logging enabled")
        logger.info(f"  ✓ Log directory: {config.logs_dir}")
        logger.info("  ✓ Log rotation configured")
        
        return True
        
    except Exception as e:
        logger.error(f"  ✗ Failed to initialize logging: {e}")
        return False


def run_validation():
    """Run validation checks."""
    logger = get_logger(__name__)
    logger.info("Step 4: Running validation checks...")
    
    try:
        # Validate folder structure
        required_folders = [
            config.datasets_dir,
            config.raw_data_dir,
            config.processed_data_dir,
            config.metadata_dir,
            config.logs_dir,
            config.storage_dir,
        ]
        
        folder_validator = FolderValidator(required_folders)
        results = folder_validator.validate()
        
        all_valid = all(results.values())
        
        if all_valid:
            logger.info("  ✓ All required folders exist")
        else:
            logger.warning("  ⚠ Some folders are missing:")
            for folder, exists in results.items():
                status = "✓" if exists else "✗"
                logger.warning(f"    {status} {folder}")
        
        # Check configuration files
        sources_config = config.config_dir / "sources.yaml"
        if sources_config.exists():
            logger.info(f"  ✓ Sources configuration found: {sources_config}")
            
            # Load and validate
            try:
                config_data = load_yaml_config(sources_config)
                num_sources = len(config_data.get("data_sources", {}))
                logger.info(f"  ✓ Loaded {num_sources} data source configurations")
            except Exception as e:
                logger.warning(f"  ⚠ Failed to load sources config: {e}")
        else:
            logger.warning(f"  ⚠ Sources configuration not found: {sources_config}")
        
        return all_valid
        
    except Exception as e:
        logger.error(f"  ✗ Validation failed: {e}")
        return False


def print_summary():
    """Print setup summary."""
    logger = get_logger(__name__)
    
    print()
    print("=" * 80)
    logger.info("Setup Summary")
    print("=" * 80)
    
    logger.info("\n✓ Knowledge Ingestion Framework initialized successfully!")
    logger.info("\nNext Steps:")
    logger.info("  1. Review configuration: config/sources.yaml")
    logger.info("  2. Configure API keys (if needed) in environment variables")
    logger.info("  3. Use CLI to manage knowledge base:")
    logger.info("       python -m scripts.cli.main status")
    logger.info("       python -m scripts.cli.main sources")
    logger.info("       python -m scripts.cli.main validate")
    logger.info("\n  4. Phase 2B: Implement actual downloaders")
    logger.info("  5. Phase 2C: Begin data ingestion")
    
    logger.info("\nDocumentation:")
    logger.info(f"  - Architecture: {config.docs_dir}/knowledge_base/knowledge_ingestion.md")
    logger.info(f"  - Logs: {config.logs_dir}/")
    logger.info(f"  - Configuration: {config.config_dir}/")
    
    print("=" * 80)


def main():
    """Main setup function."""
    print_banner()
    
    # Setup logging first
    setup_logging(
        log_dir=config.logs_dir,
        log_level="INFO",
        console_enabled=True,
        file_enabled=True,
        colored_console=True,
    )
    
    logger = get_logger(__name__)
    logger.info("Starting Knowledge Base setup...")
    
    # Run setup steps
    steps = [
        ("Verify Configuration", verify_configuration),
        ("Create Folders", create_folders),
        ("Initialize Logging", initialize_logging),
        ("Run Validation", run_validation),
    ]
    
    all_success = True
    
    for step_name, step_func in steps:
        try:
            success = step_func()
            if not success:
                logger.warning(f"⚠ {step_name} completed with warnings")
                all_success = False
        except Exception as e:
            logger.error(f"✗ {step_name} failed: {e}")
            all_success = False
    
    print()
    
    if all_success:
        logger.info("✓ All setup steps completed successfully")
        print_summary()
        return 0
    else:
        logger.warning("⚠ Setup completed with warnings. Please review the logs.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
