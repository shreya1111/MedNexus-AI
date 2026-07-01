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


def chunk_command(args):
    """Chunk processed documents."""
    logger = get_logger(__name__)
    logger.info("Starting document chunking...")
    
    try:
        from chunkers.chunk_manager import ChunkManager
        from utils.file_utils import list_files_recursive
        
        # Load chunking configuration
        chunking_config = load_yaml_config(config.config_dir / "chunking.yaml")
        
        # Determine input directory
        if args.input:
            input_dir = Path(args.input)
        else:
            input_dir = config.cleaned_data_dir
        
        if not input_dir.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return 1
        
        # Find documents to chunk
        input_files = list(input_dir.rglob('*.txt'))
        
        # Filter by source if specified
        if args.source:
            input_files = [f for f in input_files if args.source.lower() in str(f).lower()]
        
        # Filter by document if specified
        if args.document:
            input_files = [f for f in input_files if args.document in f.stem]
        
        if args.limit:
            input_files = input_files[:args.limit]
        
        logger.info(f"Found {len(input_files)} documents to chunk")
        
        if not input_files:
            logger.warning("No documents found")
            return 0
        
        # Initialize chunk manager
        strategy = chunking_config.get('default_strategy', 'recursive')
        chunk_manager = ChunkManager(
            output_dir=config.chunks_dir,
            config=chunking_config,
            strategy=strategy,
            enable_incremental=not args.force
        )
        
        # Process documents
        results = chunk_manager.process_batch(
            input_paths=input_files,
            source=args.source or "unknown",
            force=args.force,
            show_progress=not args.no_progress
        )
        
        # Calculate statistics
        stats = chunk_manager.get_statistics(results)
        
        # Log summary
        logger.info(f"\n{'='*80}")
        logger.info(f"Chunking Summary:")
        logger.info(f"  Total documents: {stats['total_documents']}")
        logger.info(f"  Successful: {stats['successful_documents']}")
        logger.info(f"  Failed: {stats['failed_documents']}")
        logger.info(f"  Skipped: {stats['skipped_documents']}")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        logger.info(f"  Average chunks/doc: {stats['average_chunks_per_document']:.1f}")
        logger.info(f"  Average chunk size: {stats['average_chunk_size']:.0f} chars")
        logger.info(f"  Processing time: {stats['total_processing_time']:.2f}s")
        logger.info(f"{'='*80}")
        
        # Save statistics if requested
        if args.stats:
            stats_path = config.evaluation_dir / "chunk_statistics.json"
            stats_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
            logger.info(f"\n✓ Statistics saved to: {stats_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Chunking failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def evaluate_command(args):
    """Evaluate chunk quality."""
    logger = get_logger(__name__)
    logger.info("Starting chunk quality evaluation...")
    
    try:
        from evaluators.chunk_evaluator import ChunkEvaluator
        
        # Load evaluation configuration
        eval_config = load_yaml_config(config.config_dir / "evaluation.yaml")
        
        # Initialize evaluator
        evaluator = ChunkEvaluator(
            chunks_dir=config.chunks_dir,
            output_dir=config.evaluation_dir,
            config=eval_config
        )
        
        # Run evaluation
        results = evaluator.evaluate(
            source=args.source,
            strategy=args.strategy
        )
        
        if not results:
            logger.warning("No evaluation results generated")
            return 0
        
        # Save reports
        evaluator.save_reports(results)
        
        # Run benchmark if requested
        if args.benchmark:
            logger.info("\nRunning strategy benchmark...")
            benchmark_results = evaluator.evaluate_benchmark()
            evaluator.save_benchmark_csv(benchmark_results)
            
            # Display benchmark summary
            logger.info(f"\n{'='*80}")
            logger.info("Strategy Benchmark:")
            logger.info(f"{'='*80}")
            for result in benchmark_results:
                logger.info(f"\n{result.strategy.upper()}:")
                logger.info(f"  Quality Score: {result.quality_score:.1f}/100")
                logger.info(f"  Avg Chunk Size: {result.avg_chunk_size:.0f} chars")
                logger.info(f"  Chunk Count: {result.chunk_count}")
                logger.info(f"  Overlap: {result.overlap_percentage:.1f}%")
                logger.info(f"  Duplicate Rate: {result.duplicate_rate:.2%}")
                logger.info(f"  Use Case: {result.recommended_use_case}")
        
        # Display summary
        quality = results['quality_score']
        metrics = results['metrics']
        
        logger.info(f"\n{'='*80}")
        logger.info("Quality Evaluation Summary:")
        logger.info(f"{'='*80}")
        logger.info(f"Overall Score: {quality['overall_score']:.1f}/100 (Grade: {quality.get('grade', 'N/A')})")
        logger.info(f"\nComponent Scores:")
        logger.info(f"  Chunk Size: {quality['chunk_size_score']*100:.0f}/100")
        logger.info(f"  Metadata: {quality['metadata_score']*100:.0f}/100")
        logger.info(f"  Structure: {quality['structure_score']*100:.0f}/100")
        logger.info(f"  Duplicates: {quality['duplicate_score']*100:.0f}/100")
        logger.info(f"  Overlap: {quality['overlap_score']*100:.0f}/100")
        logger.info(f"\nKey Metrics:")
        logger.info(f"  Total Chunks: {metrics['total_chunks']}")
        logger.info(f"  Avg Chunk Size: {metrics['avg_chunk_size']:.0f} chars")
        logger.info(f"  Duplicate Rate: {metrics['duplicate_rate']:.2%}")
        logger.info(f"  Avg Overlap: {metrics['avg_overlap_percentage']:.1f}%")
        
        # Display recommendations
        recommendations = results.get('recommendations', [])
        if recommendations:
            logger.info(f"\nTop Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                logger.info(f"  {i}. [{rec['priority'].upper()}] {rec['recommendation']}")
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Reports saved to: {config.evaluation_dir}")
        logger.info(f"{'='*80}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def embed_command(args):
    """Generate embeddings for chunks."""
    logger = get_logger(__name__)
    logger.info("Starting embedding generation...")
    
    try:
        from embeddings.embedding_manager import EmbeddingManager
        from embeddings.embedding_benchmark import EmbeddingBenchmark
        
        # Load embedding configuration
        embedding_config = load_yaml_config(config.config_dir / "embedding.yaml")
        
        # Override provider if specified
        if args.provider:
            embedding_config['provider']['active'] = args.provider
        
        # Override force regenerate if specified
        if args.force:
            embedding_config['processing']['force_regenerate'] = True
        
        # Initialize manager
        manager = EmbeddingManager(
            config=embedding_config,
            chunks_dir=config.chunks_dir,
            output_dir=config.embeddings_dir
        )
        
        # Process chunks
        stats = manager.process_chunks(
            source=args.source,
            document=args.document,
            limit=args.limit,
            show_progress=not args.no_progress
        )
        
        # Cleanup
        manager.cleanup()
        
        # Generate reports
        benchmark_config = embedding_config.get('benchmark', {})
        if benchmark_config.get('enabled', True):
            benchmark = EmbeddingBenchmark(benchmark_config)
            
            # Statistics report
            stats_file = Path(benchmark_config.get('output_files', {}).get(
                'statistics',
                'datasets/evaluation/embedding_statistics.json'
            ))
            benchmark.generate_statistics(stats, stats_file)
            
            # Validation report
            validation_file = Path(benchmark_config.get('output_files', {}).get(
                'validation',
                'datasets/evaluation/embedding_validation.json'
            ))
            benchmark.generate_validation_report(
                stats.get('validation_stats', {}),
                validation_file
            )
            
            # Cost estimation
            cost_file = Path(benchmark_config.get('output_files', {}).get(
                'cost_estimation',
                'datasets/evaluation/embedding_cost_estimation.json'
            ))
            provider_info = stats.get('provider_info', {})
            benchmark.generate_cost_estimation(
                stats,
                provider_info.get('provider', 'unknown'),
                provider_info.get('dimension', 0),
                cost_file
            )
        
        logger.info(f"\n{'='*80}")
        logger.info("Embedding Generation Summary:")
        logger.info(f"{'='*80}")
        logger.info(f"Total Chunks: {stats['total_chunks']}")
        logger.info(f"Successful: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Cached: {stats['cached']}")
        logger.info(f"Generation Time: {stats['generation_time']:.2f}s")
        logger.info(f"{'='*80}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def validate_embeddings_command(args):
    """Validate generated embeddings."""
    logger = get_logger(__name__)
    logger.info("Validating embeddings...")
    
    try:
        import json
        from embeddings.embedding_validator import EmbeddingValidator
        
        # Load embedding configuration
        embedding_config = load_yaml_config(config.config_dir / "embedding.yaml")
        validation_config = embedding_config.get('validation', {})
        
        # Initialize validator
        validator = EmbeddingValidator(validation_config)
        
        # Find embedding files
        embedding_files = list(config.embeddings_dir.rglob('*_embeddings.json'))
        
        if not embedding_files:
            logger.warning("No embedding files found")
            return 0
        
        logger.info(f"Found {len(embedding_files)} embedding files")
        
        total_embeddings = 0
        total_valid = 0
        total_invalid = 0
        
        for emb_file in embedding_files:
            try:
                with open(emb_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                embeddings_data = data.get('embeddings', [])
                dimension = data.get('dimension', 0)
                
                for emb_data in embeddings_data:
                    embedding = emb_data.get('embedding', [])
                    chunk_id = emb_data.get('chunk_id', '')
                    
                    result = validator.validate_embedding(
                        embedding=embedding,
                        expected_dimension=dimension,
                        chunk_id=chunk_id
                    )
                    
                    total_embeddings += 1
                    if result.is_valid:
                        total_valid += 1
                    else:
                        total_invalid += 1
                        logger.warning(f"Invalid: {chunk_id} - {result.errors}")
                
            except Exception as e:
                logger.error(f"Error validating {emb_file}: {e}")
        
        logger.info(f"\n{'='*80}")
        logger.info("Validation Summary:")
        logger.info(f"{'='*80}")
        logger.info(f"Total Embeddings: {total_embeddings}")
        logger.info(f"Valid: {total_valid}")
        logger.info(f"Invalid: {total_invalid}")
        logger.info(f"Pass Rate: {(total_valid/total_embeddings*100):.1f}%")
        logger.info(f"{'='*80}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def benchmark_embeddings_command(args):
    """Benchmark embedding generation."""
    logger = get_logger(__name__)
    logger.info("Running embedding benchmark...")
    
    try:
        logger.info("Benchmark command implementation")
        logger.info("This would compare multiple providers and configurations")
        
        # TODO: Implement full benchmark comparing providers
        
        return 0
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        return 1


def index_command(args):
    """Index embeddings into ChromaDB."""
    logger = get_logger(__name__)
    logger.info("Starting indexing...")
    
    try:
        from vector_db.collection_manager import CollectionManager
        from vector_db.index_builder import IndexBuilder
        
        # Load configuration
        retrieval_config = load_yaml_config(config.config_dir / "retrieval.yaml")
        
        # Initialize collection manager
        collection_manager = CollectionManager(retrieval_config)
        
        # Initialize index builder
        index_builder = IndexBuilder(
            config=retrieval_config,
            embeddings_dir=config.embeddings_dir,
            collection_manager=collection_manager
        )
        
        # Build index
        stats = index_builder.build_index(
            source=args.source,
            force=args.force,
            show_progress=not args.no_progress
        )
        
        # Display summary
        logger.info(f"\n{'='*80}")
        logger.info("Indexing Summary:")
        logger.info(f"{'='*80}")
        logger.info(f"Total Processed: {stats['total_processed']}")
        logger.info(f"Indexed: {stats['indexed']}")
        logger.info(f"Skipped: {stats['skipped']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Duration: {stats.get('duration_seconds', 0):.2f}s")
        logger.info(f"{'='*80}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def search_command(args):
    """Search the knowledge base."""
    logger = get_logger(__name__)
    
    try:
        from vector_db.collection_manager import CollectionManager
        from vector_db.retriever import VectorRetriever
        from vector_db.query_processor import QueryProcessor
        from embeddings.provider_factory import ProviderFactory
        from utils.config_loader import load_yaml_config
        
        # Load configurations
        retrieval_config = load_yaml_config(config.config_dir / "retrieval.yaml")
        embedding_config = load_yaml_config(config.config_dir / "embedding.yaml")
        
        # Initialize collection manager
        collection_manager = CollectionManager(retrieval_config)
        collection_manager.get_or_create_collection()
        
        # Initialize query processor
        query_processor = QueryProcessor(retrieval_config)
        
        # Process query
        processed_query = query_processor.process(args.query)
        logger.info(f"Searching for: {processed_query}")
        
        # Initialize embedder for query
        provider_config = embedding_config.get('provider', {})
        active_provider = provider_config.get('active', 'sentence-transformers')
        provider_settings = provider_config.get(active_provider, {})
        
        embedder = ProviderFactory.create_embedder(active_provider, provider_settings)
        embedder.initialize()
        
        # Generate query embedding
        query_embedding = embedder.embed_batch([processed_query])[0]
        
        # Initialize retriever
        retriever = VectorRetriever(retrieval_config, collection_manager)
        
        # Search
        results = retriever.search(
            query_embedding=query_embedding,
            top_k=args.top_k or 10
        )
        
        # Cleanup
        embedder.cleanup()
        
        # Display results
        logger.info(f"\n{'='*80}")
        logger.info(f"Search Results ({len(results)} found):")
        logger.info(f"{'='*80}")
        
        for i, result in enumerate(results, 1):
            logger.info(f"\n{i}. {result['chunk_id']}")
            logger.info(f"   Similarity: {result['similarity']:.4f}")
            doc_preview = result['document'][:200] if result['document'] else "N/A"
            logger.info(f"   Preview: {doc_preview}...")
        
        logger.info(f"\n{'='*80}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def collection_status_command(args):
    """Show collection status."""
    logger = get_logger(__name__)
    logger.info("Checking collection status...")
    
    try:
        from vector_db.collection_manager import CollectionManager
        
        # Load configuration
        retrieval_config = load_yaml_config(config.config_dir / "retrieval.yaml")
        
        # Initialize collection manager
        collection_manager = CollectionManager(retrieval_config)
        
        # List collections
        collections = collection_manager.list_collections()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Collections ({len(collections)} found):")
        logger.info(f"{'='*80}")
        
        for coll_name in collections:
            stats = collection_manager.get_collection_stats(coll_name)
            logger.info(f"\nCollection: {coll_name}")
            logger.info(f"  Documents: {stats.get('count', 0)}")
            logger.info(f"  Metadata: {stats.get('metadata', {})}")
        
        logger.info(f"\n{'='*80}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        import traceback
        traceback.print_exc()
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


def validate_index_command(args):
    """Validate index consistency."""
    logger = get_logger(__name__)
    logger.info("Validating index...")
    
    try:
        from vector_db.collection_manager import CollectionManager
        from vector_db.retrieval_validator import RetrievalValidator
        
        # Load configuration
        retrieval_config = load_yaml_config(config.config_dir / "retrieval.yaml")
        
        # Initialize collection manager
        collection_manager = CollectionManager(retrieval_config)
        
        # Initialize validator
        validator = RetrievalValidator(retrieval_config)
        
        # Validate collection
        result = validator.validate_collection(collection_manager)
        
        # Display results
        logger.info(f"\n{'='*80}")
        logger.info("Index Validation Results:")
        logger.info(f"{'='*80}")
        logger.info(f"Valid: {result.is_valid}")
        logger.info(f"Errors: {len(result.errors)}")
        logger.info(f"Warnings: {len(result.warnings)}")
        
        if result.errors:
            logger.info(f"\nErrors:")
            for error in result.errors:
                logger.error(f"  - {error}")
        
        if result.warnings:
            logger.info(f"\nWarnings:")
            for warning in result.warnings:
                logger.warning(f"  - {warning}")
        
        logger.info(f"\nStatistics:")
        for key, value in result.statistics.items():
            logger.info(f"  {key}: {value}")
        
        logger.info(f"\n{'='*80}")
        
        # Save report
        if args.output:
            validator.generate_report(result, Path(args.output))
        
        return 0 if result.is_valid else 1
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def ask_command(args):
    """Ask a medical question to the AI assistant."""
    logger = get_logger(__name__)
    
    try:
        from ai.assistant import MedicalAssistant
        
        logger.info("Initializing Medical AI Assistant...")
        
        # Initialize assistant
        assistant = MedicalAssistant()
        
        # Ask question
        logger.info(f"Processing question: {args.question}")
        response = assistant.ask(args.question)
        
        # Display response
        print("\n" + "="*80)
        print("MEDICAL AI ASSISTANT")
        print("="*80 + "\n")
        
        print(f"Question: {response.query}\n")
        
        print("Answer:")
        print(response.answer)
        
        # Display metadata if verbose
        if args.verbose:
            print("\n" + "-"*80)
            print("Metadata:")
            print(f"  Latency: {response.latency_ms:.0f}ms")
            print(f"  Tokens: {response.token_usage['input']} in + {response.token_usage['output']} out")
            print(f"  Confidence: {response.confidence:.2%}")
            print(f"  Documents: {response.context_metadata.get('num_docs', 0)}")
            print(f"  Sources: {', '.join(response.context_metadata.get('sources', []))}")
            print(f"  Safety: {response.safety_check.category} (risk: {response.safety_check.risk_level})")
        
        print("\n" + "="*80 + "\n")
        
        # Cleanup
        assistant.cleanup()
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to process question: {e}")
        import traceback
        traceback.print_exc()
        return 1


def benchmark_search_command(args):
    """Benchmark search performance."""
    logger = get_logger(__name__)
    logger.info("Running search benchmark...")
    
    try:
        from vector_db.collection_manager import CollectionManager
        from vector_db.retriever import VectorRetriever
        from vector_db.retrieval_benchmark import RetrievalBenchmark
        
        # Load configuration
        retrieval_config = load_yaml_config(config.config_dir / "retrieval.yaml")
        
        # Initialize collection manager
        collection_manager = CollectionManager(retrieval_config)
        collection_manager.get_or_create_collection()
        
        # Initialize retriever
        retriever = VectorRetriever(retrieval_config, collection_manager)
        
        # Initialize benchmark
        benchmark = RetrievalBenchmark(retrieval_config)
        
        # Run benchmark
        if args.queries:
            # Load queries from file
            import json
            with open(args.queries, 'r', encoding='utf-8') as f:
                queries = json.load(f)
            metrics = benchmark.benchmark_retrieval(retriever, queries)
        else:
            metrics = benchmark.benchmark_retrieval(retriever)
        
        # Display results
        benchmark.print_metrics(metrics)
        
        # Save results
        benchmark.save_metrics(metrics)
        
        return 0
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def chat_command(args):
    """Interactive chat with the medical AI assistant."""
    logger = get_logger(__name__)
    
    try:
        from ai.assistant import MedicalAssistant
        import uuid
        
        logger.info("Initializing Medical AI Assistant (Chat Mode)...")
        
        # Initialize assistant
        assistant = MedicalAssistant()
        
        # Start or resume session
        if args.session_id:
            session_id = args.session_id
            logger.info(f"Resuming session: {session_id}")
        else:
            session_id = assistant.start_conversation()
            logger.info(f"Started new session: {session_id}")
        
        print("\n" + "="*80)
        print("MEDICAL AI ASSISTANT - INTERACTIVE CHAT")
        print("="*80)
        print(f"Session ID: {session_id}")
        print("Type 'exit' or 'quit' to end the conversation")
        print("="*80 + "\n")
        
        # Interactive loop
        while True:
            try:
                # Get user input
                question = input("\nYou: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['exit', 'quit', 'bye']:
                    print("\nGoodbye! Your session has been saved.")
                    break
                
                # Get conversation history
                history = assistant.get_conversation_history(session_id, max_messages=10)
                
                # Ask question
                print("\nAssistant: ", end="", flush=True)
                response = assistant.ask(
                    query=question,
                    conversation_history=history,
                    session_id=session_id
                )
                
                print(response.answer)
                
                # Show follow-up questions if available
                if response.followup_questions:
                    print("\n💡 You might also want to ask:")
                    for i, fq in enumerate(response.followup_questions, 1):
                        print(f"   {i}. {fq}")
                
                # Show confidence warning if low
                if response.confidence < 0.5:
                    print(f"\n⚠️  Confidence: {response.confidence:.0%} - Limited supporting evidence available")
            
            except KeyboardInterrupt:
                print("\n\nInterrupted. Your session has been saved.")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                print(f"\nError: {str(e)}")
        
        # Cleanup
        assistant.cleanup()
        
        return 0
        
    except Exception as e:
        logger.error(f"Chat session failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def history_command(args):
    """Show conversation history for a session."""
    logger = get_logger(__name__)
    
    try:
        from ai.assistant import MedicalAssistant
        
        # Initialize assistant
        assistant = MedicalAssistant()
        
        # Get conversation history
        history = assistant.get_conversation_history(
            session_id=args.session_id,
            max_messages=args.limit
        )
        
        if not history:
            print(f"No conversation history found for session: {args.session_id}")
            return 0
        
        print("\n" + "="*80)
        print(f"CONVERSATION HISTORY - Session: {args.session_id}")
        print("="*80 + "\n")
        
        for i, msg in enumerate(history, 1):
            role = msg['role'].upper()
            content = msg['content']
            
            print(f"{i}. {role}:")
            print(f"   {content}\n")
        
        print("="*80 + "\n")
        
        # Cleanup
        assistant.cleanup()
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to retrieve history: {e}")
        import traceback
        traceback.print_exc()
        return 1


def clear_history_command(args):
    """Clear conversation history for a session."""
    logger = get_logger(__name__)
    
    try:
        from ai.assistant import MedicalAssistant
        
        # Initialize assistant
        assistant = MedicalAssistant()
        
        # Clear conversation
        assistant.clear_conversation(args.session_id)
        
        print(f"✓ Conversation history cleared for session: {args.session_id}")
        
        # Cleanup
        assistant.cleanup()
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to clear history: {e}")
        return 1


def session_status_command(args):
    """Show status of conversation sessions."""
    logger = get_logger(__name__)
    
    try:
        from ai.assistant import MedicalAssistant
        from datetime import datetime
        
        # Initialize assistant
        assistant = MedicalAssistant()
        
        # List all conversations
        sessions = assistant.list_conversations()
        
        if not sessions:
            print("No active conversation sessions found.")
            return 0
        
        print("\n" + "="*80)
        print(f"ACTIVE CONVERSATION SESSIONS ({len(sessions)})")
        print("="*80 + "\n")
        
        for session in sessions:
            print(f"Session ID: {session['id']}")
            print(f"  Created: {session['created_at']}")
            print(f"  Last Accessed: {session['last_accessed']}")
            print(f"  Message Count: {session['message_count']}")
            
            if session.get('metadata'):
                print(f"  Metadata: {session['metadata']}")
            
            print()
        
        print("="*80 + "\n")
        
        # Cleanup
        assistant.cleanup()
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        import traceback
        traceback.print_exc()
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
  
  # Chunk documents
  python -m scripts.cli.main chunk
  python -m scripts.cli.main chunk --source medquad --stats
  python -m scripts.cli.main chunk --force --limit 100
  
  # Evaluate chunk quality
  python -m scripts.cli.main evaluate
  python -m scripts.cli.main evaluate --source medquad
  python -m scripts.cli.main evaluate --benchmark
  
  # Generate embeddings
  python -m scripts.cli.main embed
  python -m scripts.cli.main embed --provider gemini
  python -m scripts.cli.main embed --provider sentence-transformers --source medquad
  python -m scripts.cli.main embed --force --limit 100
  
  # Validate embeddings
  python -m scripts.cli.main validate-embeddings
  
  # Benchmark embeddings
  python -m scripts.cli.main benchmark-embeddings
  
  # Index into ChromaDB
  python -m scripts.cli.main index
  python -m scripts.cli.main index --source medquad
  python -m scripts.cli.main index --force
  
  # Search knowledge base
  python -m scripts.cli.main search "What causes diabetes?"
  python -m scripts.cli.main search "Metformin dosage" --top-k 5
  
  # Collection status
  python -m scripts.cli.main collection-status
  
  # Validate index
  python -m scripts.cli.main validate-index
  python -m scripts.cli.main validate-index --output datasets/evaluation/validation_report.json
  
  # Benchmark search
  python -m scripts.cli.main benchmark-search
  python -m scripts.cli.main benchmark-search --queries datasets/evaluation/test_queries.json
  
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
    
    # Chunk command
    parser_chunk = subparsers.add_parser("chunk", help="Chunk processed documents")
    parser_chunk.add_argument("--input", help="Input directory (default: datasets/processed/cleaned)")
    parser_chunk.add_argument("--source", help="Filter by source name")
    parser_chunk.add_argument("--document", help="Filter by document name")
    parser_chunk.add_argument("--force", action="store_true", help="Force reprocessing (ignore checksums)")
    parser_chunk.add_argument("--limit", type=int, help="Limit number of documents to chunk")
    parser_chunk.add_argument("--stats", action="store_true", help="Save statistics report")
    parser_chunk.add_argument("--no-progress", action="store_true", help="Disable progress bars")
    parser_chunk.set_defaults(func=chunk_command)
    
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
    
    # Evaluate command
    parser_evaluate = subparsers.add_parser("evaluate", help="Evaluate chunk quality")
    parser_evaluate.add_argument("--source", help="Filter by source name")
    parser_evaluate.add_argument("--strategy", help="Filter by chunking strategy")
    parser_evaluate.add_argument("--benchmark", action="store_true", help="Run strategy benchmark comparison")
    parser_evaluate.add_argument("--no-progress", action="store_true", help="Disable progress bars")
    parser_evaluate.set_defaults(func=evaluate_command)
    
    # Embed command
    parser_embed = subparsers.add_parser("embed", help="Generate embeddings for chunks")
    parser_embed.add_argument("--provider", help="Embedding provider (gemini, sentence-transformers)")
    parser_embed.add_argument("--source", help="Filter by source name")
    parser_embed.add_argument("--document", help="Filter by document name")
    parser_embed.add_argument("--limit", type=int, help="Limit number of chunks to process")
    parser_embed.add_argument("--force", action="store_true", help="Force regeneration of all embeddings")
    parser_embed.add_argument("--no-progress", action="store_true", help="Disable progress bars")
    parser_embed.set_defaults(func=embed_command)
    
    # Validate embeddings command
    parser_val_emb = subparsers.add_parser("validate-embeddings", help="Validate generated embeddings")
    parser_val_emb.set_defaults(func=validate_embeddings_command)
    
    # Benchmark embeddings command
    parser_bench_emb = subparsers.add_parser("benchmark-embeddings", help="Benchmark embedding generation")
    parser_bench_emb.set_defaults(func=benchmark_embeddings_command)
    
    # Index command
    parser_index = subparsers.add_parser("index", help="Index embeddings into ChromaDB")
    parser_index.add_argument("--source", help="Filter by source name")
    parser_index.add_argument("--force", action="store_true", help="Force full reindex")
    parser_index.add_argument("--no-progress", action="store_true", help="Disable progress bars")
    parser_index.set_defaults(func=index_command)
    
    # Search command
    parser_search = subparsers.add_parser("search", help="Search the knowledge base")
    parser_search.add_argument("query", help="Search query")
    parser_search.add_argument("--top-k", type=int, help="Number of results (default: 10)")
    parser_search.set_defaults(func=search_command)
    
    # Collection status command
    parser_coll_status = subparsers.add_parser("collection-status", help="Show collection status")
    parser_coll_status.set_defaults(func=collection_status_command)
    
    # Validate index command
    parser_val_idx = subparsers.add_parser("validate-index", help="Validate index consistency")
    parser_val_idx.add_argument("--output", help="Output path for validation report")
    parser_val_idx.set_defaults(func=validate_index_command)
    
    # Benchmark search command
    parser_bench_search = subparsers.add_parser("benchmark-search", help="Benchmark search performance")
    parser_bench_search.add_argument("--queries", help="Path to test queries JSON file")
    parser_bench_search.set_defaults(func=benchmark_search_command)
    
    # Ask command (Medical AI Assistant)
    parser_ask = subparsers.add_parser("ask", help="Ask a medical question to the AI assistant")
    parser_ask.add_argument("question", help="Medical question to ask")
    parser_ask.add_argument("--verbose", "-v", action="store_true", help="Show detailed metadata")
    parser_ask.set_defaults(func=ask_command)
    
    # Chat command (Interactive conversation)
    parser_chat = subparsers.add_parser("chat", help="Interactive chat with the AI assistant")
    parser_chat.add_argument("--session-id", help="Resume specific session (optional)")
    parser_chat.set_defaults(func=chat_command)
    
    # History command
    parser_history = subparsers.add_parser("history", help="Show conversation history")
    parser_history.add_argument("session_id", help="Session ID")
    parser_history.add_argument("--limit", type=int, help="Maximum messages to show")
    parser_history.set_defaults(func=history_command)
    
    # Clear history command
    parser_clear = subparsers.add_parser("clear-history", help="Clear conversation history")
    parser_clear.add_argument("session_id", help="Session ID")
    parser_clear.set_defaults(func=clear_history_command)
    
    # Session status command
    parser_sessions = subparsers.add_parser("session-status", help="Show active conversation sessions")
    parser_sessions.set_defaults(func=session_status_command)
    
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
