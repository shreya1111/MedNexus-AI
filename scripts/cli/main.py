"""
CLI for MedNexus-AI Knowledge Ingestion Framework.

Provides command-line interface for managing knowledge base operations.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import config
from utils.logger import setup_logging, get_logger
from validators import DatasetValidator, FolderValidator
from utils.config_loader import load_yaml_config


def init_command(args):
    """Initialize knowledge base structure."""
    logger = get_logger(__name__)
    logger.info("Initializing knowledge base...")
    
    try:
        # Ensure all directories exist
        config.ensure_directories()
        logger.info("✓ All directories created successfully")
        
        # Validate configuration
        errors = config.validate()
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return 1
        
        logger.info("✓ Configuration validated")
        
        logger.info("=" * 80)
        logger.info("Knowledge Base initialized successfully!")
        logger.info(f"Root directory: {config.project_root}")
        logger.info(f"Datasets directory: {config.datasets_dir}")
        logger.info(f"Logs directory: {config.logs_dir}")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return 1


def validate_command(args):
    """Validate datasets and folder structure."""
    logger = get_logger(__name__)
    logger.info("Running validation...")
    
    try:
        # Validate folder structure
        required_folders = [
            config.raw_data_dir,
            config.processed_data_dir,
            config.metadata_dir,
            config.logs_dir,
        ]
        
        folder_validator = FolderValidator(required_folders)
        folder_results = folder_validator.validate()
        
        all_exist = all(folder_results.values())
        if all_exist:
            logger.info("✓ All required folders exist")
        else:
            logger.warning("⚠ Some folders are missing:")
            for folder, exists in folder_results.items():
                if not exists:
                    logger.warning(f"  - {folder}")
        
        # Validate datasets if requested
        if args.dataset:
            dataset_path = config.raw_data_dir / args.dataset
            validator = DatasetValidator()
            report = validator.validate_dataset(dataset_path, args.dataset)
            
            logger.info(f"\nDataset: {args.dataset}")
            logger.info(f"Total files: {report.total_files}")
            logger.info(f"Valid files: {report.valid_files}")
            logger.info(f"Errors: {report.error_count}")
            logger.info(f"Warnings: {report.warning_count}")
            
            if args.output:
                output_path = Path(args.output)
                report.save(output_path)
                logger.info(f"\n✓ Report saved to: {output_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 1


def status_command(args):
    """Show status of knowledge base."""
    logger = get_logger(__name__)
    logger.info("Knowledge Base Status")
    logger.info("=" * 80)
    
    try:
        from utils.file_utils import count_files, get_directory_size_mb
        
        # Count files in each category
        categories = {
            "Clinical Guidelines": config.clinical_guidelines_dir,
            "Disease Information": config.disease_info_dir,
            "Drug Database": config.drug_database_dir,
            "Research Papers": config.research_papers_dir,
            "Medical Books": config.medical_books_dir,
            "Medical Q&A": config.medical_qa_dir,
        }
        
        logger.info("\nRaw Data:")
        total_files = 0
        total_size = 0.0
        
        for category, directory in categories.items():
            if directory.exists():
                count = count_files(directory)
                size = get_directory_size_mb(directory)
                total_files += count
                total_size += size
                logger.info(f"  {category:30s}: {count:6d} files, {size:8.2f} MB")
            else:
                logger.info(f"  {category:30s}: Directory not found")
        
        logger.info(f"\n  {'TOTAL':30s}: {total_files:6d} files, {total_size:8.2f} MB")
        
        # Processed data
        logger.info("\nProcessed Data:")
        if config.processed_data_dir.exists():
            processed_count = count_files(config.processed_data_dir)
            processed_size = get_directory_size_mb(config.processed_data_dir)
            logger.info(f"  Processed files: {processed_count}")
            logger.info(f"  Total size: {processed_size:.2f} MB")
        else:
            logger.info("  No processed data yet")
        
        # Configuration summary
        logger.info("\nConfiguration:")
        summary = config.summary()
        logger.info(f"  Download max retries: {summary['download']['max_retries']}")
        logger.info(f"  Download timeout: {summary['download']['timeout']}s")
        logger.info(f"  Hash algorithm: {summary['metadata']['hash_algorithm']}")
        logger.info(f"  Log level: {summary['logging']['level']}")
        
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return 1


def sources_command(args):
    """List configured data sources."""
    logger = get_logger(__name__)
    
    try:
        sources_config = load_yaml_config(config.config_dir / "sources.yaml")
        data_sources = sources_config.get("data_sources", {})
        
        logger.info("Configured Data Sources")
        logger.info("=" * 80)
        
        for source_id, source_info in data_sources.items():
            enabled = "✓" if source_info.get("enabled", False) else "✗"
            name = source_info.get("name", source_id)
            category = source_info.get("category", "unknown")
            logger.info(f"\n[{enabled}] {name}")
            logger.info(f"    ID: {source_id}")
            logger.info(f"    Category: {category}")
            logger.info(f"    Format: {source_info.get('format', 'N/A')}")
            logger.info(f"    Priority: {source_info.get('priority', 'N/A')}")
            
            if args.verbose:
                logger.info(f"    URL: {source_info.get('url', 'N/A')}")
                logger.info(f"    License: {source_info.get('license', 'N/A')}")
                logger.info(f"    Description: {source_info.get('description', 'N/A')}")
        
        logger.info("\n" + "=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to list sources: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MedNexus-AI Knowledge Ingestion Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scripts.cli.main init                    # Initialize knowledge base
  python -m scripts.cli.main validate                # Validate folder structure
  python -m scripts.cli.main validate --dataset medical_qa  # Validate specific dataset
  python -m scripts.cli.main status                  # Show knowledge base status
  python -m scripts.cli.main sources                 # List data sources
  python -m scripts.cli.main sources --verbose       # List sources with details
        """
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    parser_init = subparsers.add_parser("init", help="Initialize knowledge base")
    parser_init.set_defaults(func=init_command)
    
    # Validate command
    parser_validate = subparsers.add_parser("validate", help="Validate datasets")
    parser_validate.add_argument("--dataset", help="Specific dataset to validate")
    parser_validate.add_argument("--output", help="Output path for validation report")
    parser_validate.set_defaults(func=validate_command)
    
    # Status command
    parser_status = subparsers.add_parser("status", help="Show knowledge base status")
    parser_status.set_defaults(func=status_command)
    
    # Sources command
    parser_sources = subparsers.add_parser("sources", help="List data sources")
    parser_sources.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    parser_sources.set_defaults(func=sources_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(
        log_dir=config.logs_dir,
        log_level=args.log_level,
        console_enabled=True,
        file_enabled=True,
        colored_console=True,
    )
    
    # Execute command
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
