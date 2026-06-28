# MedNexus-AI Knowledge Ingestion Framework

**Version:** 1.0.0 (Phase 2A)  
**Status:** Framework Complete - Ready for Implementation  
**Last Updated:** June 28, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Folder Structure](#folder-structure)
4. [Configuration](#configuration)
5. [Components](#components)
6. [Usage](#usage)
7. [Extension Guide](#extension-guide)
8. [Phase 2B: Next Steps](#phase-2b-next-steps)

---

## Overview

The Knowledge Ingestion Framework provides a production-ready infrastructure for downloading, validating, and managing medical knowledge sources for the MedNexus-AI RAG system.

### Key Features

✅ **Modular Architecture** - Clean separation of concerns  
✅ **Extensible Design** - Easy to add new data sources  
✅ **Retry Logic** - Robust error handling with exponential backoff  
✅ **Progress Tracking** - Visual feedback for long operations  
✅ **Metadata Management** - Comprehensive file tracking  
✅ **Validation Framework** - Data quality assurance  
✅ **CLI Interface** - Command-line management tools  
✅ **Structured Logging** - Colored console + rotating file logs  

### Phase 2A Scope

This phase implements **only the framework infrastructure**. Actual data downloading, PDF processing, chunking, and embeddings are **Phase 2B and beyond**.

**Implemented:**
- Configuration system
- Logging infrastructure
- Utility modules (file, hash, retry, progress)
- Base downloader class with retry/resume support
- Validation framework
- Metadata system
- CLI interface
- Documentation

**NOT Implemented (Future Phases):**
- Actual file downloading
- PDF/HTML processing
- Text chunking
- Embedding generation
- Vector database integration
- LangChain/ChromaDB/LLM integration

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    Knowledge Ingestion Framework                │
└─────────────────────────────────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
    ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
    │ Config  │          │  Utils  │          │  CLI    │
    │ System  │          │ Package │          │Interface│
    └────┬────┘          └────┬────┘          └────┬────┘
         │                    │                    │
    ┌────▼─────────────────────▼──────────────────▼────┐
    │              Core Framework                       │
    │  - Logging    - Retry       - Progress          │
    │  - Hashing    - File Utils  - Config Loader     │
    └────┬──────────────────────────────────────┬──────┘
         │                                      │
    ┌────▼────┐                          ┌─────▼──────┐
    │Download │                          │Validation  │
    │Framework│                          │Framework   │
    └────┬────┘                          └─────┬──────┘
         │                                     │
    ┌────▼──────────────────────────────────────▼──────┐
    │            Data Storage Layer                     │
    │  datasets/     storage/     logs/                 │
    └───────────────────────────────────────────────────┘
```

### Data Flow (Planned for Phase 2B)

```
Source → Downloader → Raw Data → Validator → Metadata
                         │
                         ▼
                   [Phase 2C: Processing]
                         │
                         ▼
              Cleaner → Chunker → Embedder → Vector DB
```

---

## Folder Structure

```
mednexus-ai/
├── config/
│   ├── settings.py              # Core configuration
│   └── sources.yaml             # Data source definitions
│
├── datasets/
│   ├── raw/                     # Downloaded raw files
│   │   ├── clinical_guidelines/
│   │   ├── disease_information/
│   │   ├── drug_database/
│   │   ├── research_papers/
│   │   ├── medical_books/
│   │   └── medical_qa/
│   ├── processed/               # Processed datasets
│   │   ├── cleaned/            # Cleaned text
│   │   ├── chunks/             # Chunked documents
│   │   └── metadata/           # Metadata files
│   └── evaluation/             # Evaluation datasets
│
├── storage/
│   └── chroma_db/              # Vector database (Phase 2C)
│
├── scripts/
│   ├── downloaders/            # Download implementations
│   │   ├── base_downloader.py # Abstract base class
│   │   ├── medquad_downloader.py
│   │   ├── pubmed_downloader.py
│   │   ├── cdc_downloader.py
│   │   ├── dailymed_downloader.py
│   │   └── who_downloader.py
│   │
│   ├── validators/             # Validation modules
│   │   ├── dataset_validator.py
│   │   ├── folder_validator.py
│   │   └── metadata_validator.py
│   │
│   ├── utils/                  # Utility modules
│   │   ├── logger.py          # Logging system
│   │   ├── file_utils.py      # File operations
│   │   ├── hash_utils.py      # Checksum verification
│   │   ├── retry.py           # Retry logic
│   │   ├── progress.py        # Progress tracking
│   │   └── config_loader.py   # Config loading
│   │
│   ├── cli/                    # Command-line interface
│   │   └── main.py
│   │
│   └── setup_knowledge_base.py # Setup script
│
├── logs/                       # Log files
├── docs/knowledge_base/        # Documentation
└── requirements-kb.txt         # Python dependencies
```

---

## Configuration

### settings.py

Core configuration with environment variable support:

```python
from config.settings import config

# Access paths
config.raw_data_dir           # datasets/raw/
config.metadata_dir           # datasets/processed/metadata/
config.logs_dir               # logs/

# Sub-configurations
config.download.max_retries   # Retry attempts
config.download.timeout       # Request timeout
config.metadata.hash_algorithm # 'sha256', 'md5', etc.
config.logging.level          # 'INFO', 'DEBUG', etc.
```

**Environment Variables:**

- `DOWNLOAD_MAX_RETRIES` - Maximum retry attempts (default: 3)
- `DOWNLOAD_TIMEOUT` - Timeout in seconds (default: 300)
- `DOWNLOAD_MAX_FILE_SIZE_MB` - Max file size (default: 500)
- `LOG_LEVEL` - Logging level (default: INFO)
- `METADATA_HASH_ALGORITHM` - Hash algorithm (default: sha256)

### sources.yaml

Define data sources:

```yaml
data_sources:
  medquad:
    name: "MedQuAD Medical Q&A Dataset"
    category: "medical_qa"
    url: "https://github.com/abachaa/MedQuAD"
    format: "xml"
    license: "Public Domain"
    enabled: true
    priority: 1
    estimated_size_mb: 50
```

---

## Components

### 1. Configuration System

**Purpose:** Centralized configuration with validation

**Files:**
- `config/settings.py` - Core settings
- `config/sources.yaml` - Data source definitions

**Features:**
- Environment variable support
- Path management
- Validation on initialization
- Type-safe dataclasses

### 2. Logging System

**Purpose:** Structured logging with rotation

**Module:** `utils/logger.py`

**Features:**
- Colored console output
- File logging with rotation (10MB, 5 backups)
- Module-specific loggers
- Timestamp and level formatting

**Usage:**
```python
from utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Processing started")
logger.error("Failed to download", exc_info=True)
```

### 3. File Utilities

**Module:** `utils/file_utils.py`

**Functions:**
- `ensure_directory()` - Create directory if missing
- `get_file_size()` - Get file size in bytes/MB
- `list_files_recursive()` - List files with pattern
- `is_empty_file()` - Check if file is empty
- `get_file_metadata()` - Extract file metadata
- `safe_filename()` - Sanitize filenames

### 4. Hash Utilities

**Module:** `utils/hash_utils.py`

**Functions:**
- `compute_file_hash()` - Calculate file checksum
- `verify_checksum()` - Verify against expected
- `find_duplicate_files()` - Detect duplicates
- `compute_multiple_hashes()` - Multiple algorithms at once

### 5. Retry Logic

**Module:** `utils/retry.py`

**Features:**
- Exponential backoff
- Configurable attempts
- Exception filtering
- Decorator and functional API

**Usage:**
```python
from utils.retry import retry_with_backoff

@retry_with_backoff(max_attempts=3, initial_delay=1.0)
def download_file(url):
    # Download logic
    pass
```

### 6. Progress Tracking

**Module:** `utils/progress.py`

**Features:**
- Visual progress bars
- ETA calculation
- Success/failure tracking
- Context manager support

**Usage:**
```python
from utils.progress import ProgressTracker

with ProgressTracker(total=100, description="Downloading") as progress:
    for item in items:
        process(item)
        progress.update()
```

### 7. Downloader Framework

**Base Class:** `downloaders/base_downloader.py`

**Key Methods:**
- `get_source_name()` - Return source identifier
- `get_download_list()` - List items to download
- `download_file()` - Download single file
- `should_download()` - Check if download needed
- `generate_metadata()` - Create metadata
- `download_all()` - Batch download with progress

**Status:** Framework complete, implementations are placeholders

### 8. Validation Framework

**Components:**
- `DatasetValidator` - Validate dataset integrity
- `FolderValidator` - Check folder structure
- `MetadataValidator` - Verify metadata completeness

**Checks:**
- Missing folders
- Duplicate files (by hash)
- Empty or corrupt files
- Invalid file naming
- Metadata consistency

### 9. CLI Interface

**Script:** `scripts/cli/main.py`

**Commands:**
```bash
# Initialize knowledge base
python -m scripts.cli.main init

# Validate structure
python -m scripts.cli.main validate

# Validate specific dataset
python -m scripts.cli.main validate --dataset medical_qa --output report.json

# Show status
python -m scripts.cli.main status

# List sources
python -m scripts.cli.main sources
python -m scripts.cli.main sources --verbose
```

---

## Usage

### Setup

1. **Install Dependencies:**
```bash
pip install -r requirements-kb.txt
```

2. **Initialize Framework:**
```bash
python scripts/setup_knowledge_base.py
```

This will:
- Create all required directories
- Validate configuration
- Initialize logging
- Run validation checks

### CLI Usage

**Check Status:**
```bash
python -m scripts.cli.main status
```

Output shows:
- File counts per category
- Total size
- Configuration summary

**Validate Dataset:**
```bash
python -m scripts.cli.main validate --dataset medical_qa
```

**List Data Sources:**
```bash
python -m scripts.cli.main sources --verbose
```

### Programmatic Usage

**Using Validators:**
```python
from validators import DatasetValidator
from config.settings import config

validator = DatasetValidator(
    check_duplicates=True,
    check_empty_files=True,
    min_file_size_bytes=100,
)

report = validator.validate_dataset(
    dataset_dir=config.medical_qa_dir,
    dataset_name="medical_qa"
)

print(f"Valid files: {report.valid_files}/{report.total_files}")
print(f"Errors: {report.error_count}")
```

**Using Downloaders (Phase 2B):**
```python
from downloaders import MedQuADDownloader
from config.settings import config

downloader = MedQuADDownloader(
    output_dir=config.medical_qa_dir,
    metadata_dir=config.metadata_dir,
)

# Phase 2B: Implement download_all()
results = downloader.download_all(max_files=10)
stats = downloader.get_download_stats(results)
```

---

## Extension Guide

### Adding a New Data Source

1. **Update sources.yaml:**
```yaml
my_source:
  name: "My Medical Database"
  category: "medical_qa"
  url: "https://example.com/data"
  format: "json"
  enabled: true
  priority: 2
```

2. **Create Downloader:**
```python
# scripts/downloaders/my_source_downloader.py
from .base_downloader import BaseDownloader, DownloadResult

class MySourceDownloader(BaseDownloader):
    def get_source_name(self) -> str:
        return "MySource"
    
    def get_download_list(self) -> List[Dict]:
        # Return list of items to download
        pass
    
    def download_file(self, url, output_path, **kwargs) -> DownloadResult:
        # Implement download logic
        pass
```

3. **Use in CLI or Scripts:**
```python
from downloaders.my_source_downloader import MySourceDownloader

downloader = MySourceDownloader(output_dir, metadata_dir)
results = downloader.download_all()
```

### Adding Custom Validation

```python
from validators import DatasetValidator, ValidationIssue

class CustomValidator(DatasetValidator):
    def validate_medical_format(self, files, report):
        for file in files:
            # Custom validation logic
            if not is_valid_medical_format(file):
                report.issues.append(ValidationIssue(
                    severity='error',
                    category='format',
                    message='Invalid medical data format',
                    file_path=file,
                ))
```

---

## Phase 2B: Next Steps

### Implementation Roadmap

**Phase 2B: Data Ingestion Implementation**
1. Implement actual downloaders:
   - HTTP/HTTPS downloads with requests
   - Git clone functionality
   - FTP downloads
   - API integrations (PubMed, MedlinePlus)
2. Add PDF processing (pypdf2, pdfplumber)
3. Add HTML parsing (BeautifulSoup4)
4. Add text extraction and cleaning
5. Implement resume capability for interrupted downloads
6. Add rate limiting and respect robots.txt

**Phase 2C: Processing & RAG Preparation**
1. Text chunking (LangChain TextSplitters)
2. Embedding generation (OpenAI/HuggingFace)
3. Vector database integration (ChromaDB)
4. Metadata enrichment
5. Quality scoring
6. Deduplication at content level

**Phase 2D: RAG Pipeline**
1. Query processing
2. Retrieval strategies
3. Context assembly
4. LLM integration
5. Response generation

### Required Dependencies for Phase 2B

```txt
# HTTP and Web
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0

# Document Processing
pypdf2>=3.0.0
pdfplumber>=0.10.0
python-docx>=1.1.0

# Git Operations
gitpython>=3.1.40

# For API Access
httpx>=0.25.0
```

### Testing Checklist

- [ ] Download from HTTP/HTTPS sources
- [ ] Clone Git repositories
- [ ] Extract text from PDFs
- [ ] Parse HTML documents
- [ ] Handle network errors gracefully
- [ ] Resume interrupted downloads
- [ ] Verify checksums
- [ ] Generate metadata correctly
- [ ] Validate downloaded files
- [ ] Handle rate limiting

---

## Coding Standards

### Python Style
- Follow PEP 8
- Use type hints (Python 3.11+)
- Docstrings for all public functions
- Maximum line length: 100 characters

### Architecture Principles
- **SOLID** principles
- **DRY** (Don't Repeat Yourself)
- **Separation of Concerns**
- **Interface Segregation**
- **Dependency Injection**

### Error Handling
- Use specific exceptions
- Always log errors
- Provide context in error messages
- Fail gracefully where possible

### Documentation
- Docstrings with Args/Returns/Raises
- README for each major component
- Inline comments for complex logic
- Keep docs up to date

---

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Ensure you're running from project root
python -m scripts.cli.main status
```

**2. Permission Errors**
```bash
# Check folder permissions
ls -la datasets/
chmod -R 755 datasets/
```

**3. Configuration Errors**
```python
# Validate config
from config.settings import config
errors = config.validate()
print(errors)
```

**4. Logging Not Working**
```python
# Reinitialize logging
from utils.logger import setup_logging
from config.settings import config

setup_logging(config.logs_dir, log_level="DEBUG")
```

---

## License

MIT License - See main project LICENSE file

---

## Changelog

### Version 1.0.0 (Phase 2A) - June 28, 2026
- ✅ Initial framework release
- ✅ Configuration system
- ✅ Logging infrastructure
- ✅ Utility modules
- ✅ Base downloader class
- ✅ Validation framework
- ✅ CLI interface
- ✅ Documentation

### Next Version (Phase 2B) - Planned
- [ ] Implement actual downloaders
- [ ] PDF/HTML processing
- [ ] Text extraction and cleaning
- [ ] Resume capability
- [ ] Comprehensive testing

---

**For questions or issues, see project documentation or create a GitHub issue.**
