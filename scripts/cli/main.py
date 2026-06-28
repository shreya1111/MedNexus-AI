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


def download_command(args):
    """Download data from configured sources."""
    logger = get_logger(__name__)
    logger.info("Starting download...")
    
    try:
        # Import downloaders
        from downloaders.medquad_downloader import MedQuADDownloader
        
        # Load sources config
        sources_config = load_yaml_config(config.config_dir / "sources.yaml")
        data_sources = sources_config.get("data_sources", {})
        
        # Filter by source if specified
        if args.source:
            if args.source not in data_sources:
                logger.error(f"Unknown source: {args.source}")
                logger.info(f"Available sources: {', '.join(data_sources.keys())}")
                return 1
            sources_to_download = {args.source: data_sources[args.source]}
        else:
            # Download only enabled sources
            sources_to_download = {
                k: v for k, v in data_sources.items()
                if v.get("enabled", False)
            }
        
        if not sources_to_download:
            logger.warning("No sources to download")
            return 0
        
        logger.info(f"Downloading from {len(sources_to_download)} source(s)")
        
        # Download each source
        for source_id, source_info in sources_to_download.items():
            logger.info(f"\n{'='*80}")
            logger.info(f"Downloading: {source_info.get('name', source_id)}")
            logger.info(f"{'='*80}")
            
            category = source_info.get("category", "")
            
            # Map category to output directory
            category_dirs = {
                "medical_qa": config.medical_qa_dir,
                "clinical_guidelines": config.clinical_guidelines_dir,
                "disease_information": config.disease_info_dir,
                "drug_database": config.drug_database_dir,
                "research_papers": config.research_papers_dir,
                "medical_books": config.medical_books_dir,
            }
            
            output_dir = category_dirs.get(category, config.raw_data_dir / category)
            
            # Initialize downloader based on source
            if source_id == "medquad":
                downloader = MedQuADDownloader(
                    output_dir=output_dir,
                    metadata_dir=config.metadata_dir
                )
                results = downloader.download_all(
                    max_files=args.limit,
                    show_progress=not args.no_progress
                )
                
                # Log stats
                stats = downloader.get_download_stats(results)
                logger.info(f"\nDownload Statistics:")
                logger.info(f"  Total files: {stats['total_files']}")
                logger.info(f"  Completed: {stats['completed']}")
                logger.info(f"  Failed: {stats['failed']}")
                logger.info(f"  Skipped: {stats['skipped']}")
                logger.info(f"  Total size: {stats['total_size_mb']:.2f} MB")
            else:
                logger.warning(f"Downloader not implemented for: {source_id}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def process_command(args):
    """Process (extract text from) downloaded documents."""
    logger = get_logger(__name__)
    logger.info("Starting document processing...")
    
    try:
        from processors.document_processor import DocumentProcessor
        from utils.file_utils import list_files_recursive
        
        # Determine input directory
        if args.input:
            input_dir = Path(args.input)
        else:
            input_dir = config.raw_data_dir
        
        if not input_dir.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return 1
        
        # Find documents to process
        extensions = ['.pdf', '.txt', '.md', '.xml', '.html', '.htm']
        input_files = []
        
        for ext in extensions:
            input_files.extend(input_dir.rglob(f'*{ext}'))
        
        if args.limit:
            input_files = input_files[:args.limit]
        
        logger.info(f"Found {len(input_files)} documents to process")
        
        if not input_files:
            logger.warning("No documents found")
            return 0
        
        # Initialize processor
        processor = DocumentProcessor(
            output_dir=config.cleaned_data_dir,
            metadata_dir=config.metadata_dir,
            enable_cleaning=not args.no_clean
        )
        
        # Process documents
        results = processor.process_batch(
            input_paths=input_files,
            source=args.source or "unknown",
            show_progress=not args.no_progress
        )
        
        # Log summary
        successful = sum(1 for r in results if r.status == 'success')
        partial = sum(1 for r in results if r.status == 'partial')
        failed = sum(1 for r in results if r.status == 'failed')
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing Summary:")
        logger.info(f"  Total: {len(results)}")
        logger.info(f"  Success: {successful}")
        logger.info(f"  Partial: {partial}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"{'='*80}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def clean_command(args):
    """Clean extracted text documents."""
    logger = get_logger(__name__)
    logger.info("Starting document cleaning...")
    
    try:
        from processors.document_cleaner import DocumentCleaner
        from utils.file_utils import list_files_recursive
        
        # Determine input directory
        if args.input:
            input_dir = Path(args.input)
        else:
            input_dir = config.cleaned_data_dir
        
        if not input_dir.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return 1
        
        # Find text files
        input_files = list(input_dir.rglob('*.txt'))
        
        if args.limit:
            input_files = input_files[:args.limit]
        
        logger.info(f"Found {len(input_files)} text files to clean")
        
        if not input_files:
            logger.warning("No text files found")
            return 0
        
        # Initialize cleaner
        cleaner = DocumentCleaner(
            remove_excessive_whitespace=True,
            normalize_unicode=True,
            remove_duplicate_lines=True,
            preserve_structure=True
        )
        
        # Clean documents
        output_dir = Path(args.output) if args.output else input_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        successful = 0
        failed = 0
        
        for input_file in input_files:
            try:
                output_file = output_dir / input_file.name
                result = cleaner.clean_file(input_file, output_file)
                logger.info(
                    f"Cleaned {input_file.name}: "
                    f"{result.reduction_percent:.1f}% reduction"
                )
                successful += 1
            except Exception as e:
                logger.error(f"Failed to clean {input_file}: {e}")
                failed += 1
        
        logger.info(f"\nCleaning Summary:")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
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
  # Initialization
  python -m scripts.cli.main init
  
  # Download data
  python -m scripts.cli.main download --source medquad
  python -m scripts.cli.main download --limit 100
  
  # Process documents
  python -m scripts.cli.main process --input datasets/raw/medical_qa
  python -m scripts.cli.main process --no-clean --limit 50
  
  # Clean text
  python -m scripts.cli.main clean --input datasets/processed/cleaned
  
  # Validation
  python -m scripts.cli.main validate
  python -m scripts.cli.main validate --dataset medical_qa
  
  # Status and info
  python -m scripts.cli.main status
  python -m scripts.cli.main sources --verbose
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
    
    # Download command
    parser_download = subparsers.add_parser("download", help="Download data from sources")
    parser_download.add_argument("--source", help="Specific source to download (e.g., medquad)")
    parser_download.add_argument("--limit", type=int, help="Limit number of files to download")
    parser_download.add_argument("--no-progress", action="store_true", help="Disable progress bars")
    parser_download.set_defaults(func=download_command)
    
    # Process command
    parser_process = subparsers.add_parser("process", help="Process (extract text from) documents")
    parser_process.add_argument("--input", help="Input directory (default: datasets/raw)")
    parser_process.add_argument("--source", help="Source name for metadata")
    parser_process.add_argument("--no-clean", action="store_true", help="Skip text cleaning")
    parser_process.add_argument("--limit", type=int, help="Limit number of files to process")
    parser_process.add_argument("--no-progress", action="store_true", help="Disable progress bars")
    parser_process.set_defaults(func=process_command)
    
    # Clean command
    parser_clean = subparsers.add_parser("clean", help="Clean extracted text documents")
    parser_clean.add_argument("--input", help="Input directory (default: datasets/processed/cleaned)")
    parser_clean.add_argument("--output", help="Output directory (default: same as input)")
    parser_clean.add_argument("--limit", type=int, help="Limit number of files to clean")
    parser_clean.set_defaults(func=clean_command)
    
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
