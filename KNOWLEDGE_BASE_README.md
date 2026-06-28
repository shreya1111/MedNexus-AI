# MedNexus-AI Knowledge Base

## Overview

The MedNexus-AI Knowledge Ingestion Framework provides a complete pipeline for downloading, processing, and managing medical knowledge sources for the RAG (Retrieval-Augmented Generation) system.

## Current Status

- ✅ **Phase 2A Complete** - Framework infrastructure
- ✅ **Phase 2B Complete** - Document acquisition & processing
- 🔄 **Phase 2C Pending** - RAG implementation (LangChain, ChromaDB, embeddings)

## Quick Start

### 1. Installation

```bash
cd d:\mednexus-ai

# Install dependencies
pip install -r requirements-kb.txt
```

**Dependencies include:**
- HTTP & Git: requests, gitpython
- PDF Processing: pypdf, pdfplumber  
- Text Processing: beautifulsoup4, ftfy, markdown
- Progress & Testing: tqdm, pytest

### 2. Initialize Knowledge Base

```bash
python -m scripts.cli.main init
```

This creates all required directories:
- `datasets/raw/` - Downloaded documents
- `datasets/processed/cleaned/` - Extracted & cleaned text
- `datasets/processed/metadata/` - Document metadata
- `logs/` - Application logs

### 3. Download Medical Data

```bash
# Download MedQuAD dataset (47K medical Q&A pairs, ~45MB)
python -m scripts.cli.main download --source medquad

# Check what was downloaded
python -m scripts.cli.main status
```

### 4. Process Documents

```bash
# Extract and clean text from downloaded documents
python -m scripts.cli.main process --source medquad

# Check processing results
python -m scripts.cli.main status
```

### 5. Validate Data

```bash
# Validate folder structure and data integrity
python -m scripts.cli.main validate

# Validate specific dataset
python -m scripts.cli.main validate --dataset medical_qa
```

## CLI Commands Reference

### `init` - Initialize knowledge base
```bash
python -m scripts.cli.main init
```

### `download` - Download medical data
```bash
# Download all enabled sources
python -m scripts.cli.main download

# Download specific source
python -m scripts.cli.main download --source medquad

# Limit number of files
python -m scripts.cli.main download --limit 100

# Disable progress bars
python -m scripts.cli.main download --no-progress
```

### `process` - Extract text from documents
```bash
# Process all raw documents
python -m scripts.cli.main process

# Process specific directory
python -m scripts.cli.main process --input datasets/raw/medical_qa

# Skip cleaning step
python -m scripts.cli.main process --no-clean

# Limit and specify source
python -m scripts.cli.main process --source medquad --limit 50

# Disable progress bars
python -m scripts.cli.main process --no-progress
```

### `clean` - Clean extracted text
```bash
# Clean all processed documents
python -m scripts.cli.main clean

# Clean specific directory
python -m scripts.cli.main clean --input datasets/processed/cleaned

# Output to different directory
python -m scripts.cli.main clean --output datasets/final

# Limit files
python -m scripts.cli.main clean --limit 100
```

### `validate` - Validate datasets
```bash
# Validate folder structure
python -m scripts.cli.main validate

# Validate specific dataset
python -m scripts.cli.main validate --dataset medical_qa

# Save validation report
python -m scripts.cli.main validate --dataset medical_qa --output report.json
```

### `status` - Show knowledge base status
```bash
python -m scripts.cli.main status
```

Example output:
```
Knowledge Base Status
================================================================================

Raw Data:
  Medical Q&A                   :  13000 files,    45.20 MB

Processed Data:
  Processed files: 12950
  Total size: 38.50 MB
```

### `sources` - List data sources
```bash
# List all configured sources
python -m scripts.cli.main sources

# Show detailed information
python -m scripts.cli.main sources --verbose
```

## Programmatic Usage

### Download Documents

```python
from config.settings import config
from downloaders.medquad_downloader import MedQuADDownloader

# Initialize downloader
downloader = MedQuADDownloader(
    output_dir=config.medical_qa_dir,
    metadata_dir=config.metadata_dir
)

# Download
results = downloader.download_all()

# Check stats
stats = downloader.get_download_stats(results)
print(f"Downloaded {stats['completed']} files ({stats['total_size_mb']:.2f} MB)")
```

### Process Documents

```python
from pathlib import Path
from config.settings import config
from processors.document_processor import DocumentProcessor

# Initialize processor
processor = DocumentProcessor(
    output_dir=config.cleaned_data_dir,
    metadata_dir=config.metadata_dir,
    enable_cleaning=True
)

# Get input files
input_files = list(config.medical_qa_dir.rglob('*.xml'))

# Process batch
results = processor.process_batch(
    input_paths=input_files,
    source='medquad',
    show_progress=True
)

# Summary
successful = sum(1 for r in results if r.status == 'success')
print(f"Successfully processed {successful}/{len(results)} documents")
```

### Extract and Clean Text

```python
from pathlib import Path
from processors.text_extractor import TextExtractor
from processors.document_cleaner import DocumentCleaner

# Initialize
extractor = TextExtractor()
cleaner = DocumentCleaner()

# Extract
extraction_result = extractor.extract(Path("document.pdf"))
print(f"Extracted {extraction_result.char_count} characters")

# Clean
cleaning_result = cleaner.clean(extraction_result.text)
print(f"Cleaned text: {cleaning_result.reduction_percent:.1f}% reduction")

# Save
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(cleaning_result.cleaned_text)
```

## Data Sources

### Implemented

| Source | Status | Files | Size | Format | License |
|--------|--------|-------|------|--------|---------|
| **MedQuAD** | ✅ Working | ~13,000 | ~45MB | XML | Public Domain |

### Framework Ready (Can be implemented)

| Source | Format | Notes |
|--------|--------|-------|
| **PubMed Central** | PDF | Need API key |
| **WHO Guidelines** | PDF | Manual list needed |
| **CDC Documents** | PDF/HTML | Manual list needed |
| **DailyMed** | XML | Large dataset (5GB+) |

## Supported File Formats

**Text Extraction:**
- ✅ PDF (pypdf with pdfplumber fallback)
- ✅ Plain text (.txt)
- ✅ Markdown (.md)
- ✅ XML
- ✅ HTML

**Text Cleaning:**
- ✅ Unicode normalization
- ✅ Whitespace normalization
- ✅ Duplicate removal
- ✅ Structure preservation (headings, lists, tables)

## Testing

```bash
# Run all tests
pytest scripts/tests/ -v

# Run with coverage
pytest scripts/tests/ --cov=scripts --cov-report=html

# Run specific test file
pytest scripts/tests/test_text_extractor.py -v
```

**Test Coverage:**
- Text extraction (6 tests)
- Document cleaning (9 tests)
- Hash utilities (8 tests)

## Directory Structure

```
mednexus-ai/
│
├── config/
│   ├── settings.py                    # Configuration management
│   └── sources.yaml                   # Data source definitions
│
├── datasets/
│   ├── raw/                           # Downloaded documents
│   │   ├── clinical_guidelines/
│   │   ├── disease_information/
│   │   ├── drug_database/
│   │   ├── research_papers/
│   │   ├── medical_books/
│   │   └── medical_qa/                # MedQuAD goes here
│   ├── processed/
│   │   ├── cleaned/                   # Cleaned text files
│   │   ├── chunks/                    # For Phase 2C (chunking)
│   │   └── metadata/                  # Document metadata (JSON)
│   └── evaluation/                    # Validation reports
│
├── scripts/
│   ├── downloaders/                   # Data downloaders
│   ├── processors/                    # Text extraction & cleaning
│   ├── validators/                    # Data validation
│   ├── utils/                         # Utilities
│   ├── tests/                         # Unit tests
│   └── cli/                           # Command-line interface
│
├── logs/                              # Application logs
│
└── storage/
    └── chroma_db/                     # For Phase 2C (vector DB)
```

## Configuration

Configuration is managed through:

1. **Environment variables** (`.env` file)
2. **config/settings.py** (Python configuration)
3. **config/sources.yaml** (Data source definitions)

### Environment Variables

```bash
# Download settings
DOWNLOAD_MAX_RETRIES=3
DOWNLOAD_RETRY_DELAY=5
DOWNLOAD_TIMEOUT=300
DOWNLOAD_VERIFY_SSL=true

# Validation settings
VALIDATION_CHECK_DUPLICATES=true
VALIDATION_CHECK_EMPTY=true
VALIDATION_MIN_FILE_SIZE=100

# Metadata settings
METADATA_HASH_ALGORITHM=sha256
METADATA_INCLUDE_CHECKSUMS=true

# Logging settings
LOG_LEVEL=INFO
LOG_CONSOLE_ENABLED=true
LOG_FILE_ENABLED=true
LOG_COLORED_CONSOLE=true
```

## Logging

Logs are written to:
- **Console** - Colored output with INFO level
- **File** - `logs/knowledge_ingestion_YYYYMMDD.log` with DEBUG level
- **Rotation** - 10MB per file, 5 backup files

View logs:
```bash
# Real-time monitoring
tail -f logs/knowledge_ingestion_20260628.log

# On Windows
Get-Content logs\knowledge_ingestion_20260628.log -Wait
```

## Troubleshooting

### Issue: GitPython not found
**Error:** `GitPython not installed`

**Solution:**
```bash
pip install gitpython
```

### Issue: PDF extraction fails
**Error:** `pypdf not installed`

**Solution:**
```bash
pip install pypdf pdfplumber
```

### Issue: Out of memory during processing
**Error:** Memory error when processing large PDFs

**Solution:** Process in smaller batches:
```bash
python -m scripts.cli.main process --limit 100
```

### Issue: Download interrupted
**Solution:** Downloads support resume - just run the command again:
```bash
python -m scripts.cli.main download --source medquad
```

## Performance

**MedQuAD Processing (13,000 documents):**
- Download: ~12 seconds (Git clone, 45MB)
- Text extraction: ~5 minutes (40 docs/sec)
- Cleaning: ~2 minutes (100 docs/sec)
- **Total: ~7 minutes**

**Resource Usage:**
- CPU: 1-2 cores (single-threaded processing)
- Memory: ~500MB peak
- Disk: 45MB raw + 38MB processed = ~83MB total

## Next Steps (Phase 2C)

1. **Document Chunking**
   - Implement chunking strategies
   - Configure chunk size and overlap
   - Preserve metadata in chunks

2. **Embedding Generation**
   - Choose embedding model (OpenAI, Sentence Transformers, etc.)
   - Generate embeddings for chunks
   - Cache embeddings

3. **Vector Database (ChromaDB)**
   - Initialize ChromaDB
   - Ingest documents
   - Build indexes
   - Test retrieval

4. **LangChain Integration**
   - Implement document loaders
   - Setup retrieval chains
   - Build QA system
   - Test end-to-end pipeline

## Documentation

- **Phase 2A Report:** `docs/knowledge_base/PHASE_2A_COMPLETE.md`
- **Phase 2B Report:** `docs/knowledge_base/PHASE_2B_COMPLETE.md`
- **Knowledge Ingestion Guide:** `docs/knowledge_base/knowledge_ingestion.md`
- **Architecture:** `docs/architecture.md`

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review documentation in `docs/knowledge_base/`
3. Check logs in `logs/` directory
4. Run validation: `python -m scripts.cli.main validate`

## License

MedNexus-AI Knowledge Base - Phase 2B
Copyright © 2026
