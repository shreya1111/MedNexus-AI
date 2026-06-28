"""
File system utilities for MedNexus-AI Knowledge Ingestion Framework.

Provides file operations, validation, and path management.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Generator
from datetime import datetime


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        The directory path
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Path) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    return file_path.stat().st_size


def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB
    """
    return get_file_size(file_path) / (1024 * 1024)


def get_file_extension(file_path: Path) -> str:
    """
    Get file extension (lowercase, with dot).
    
    Args:
        file_path: Path to file
        
    Returns:
        File extension (e.g., '.pdf')
    """
    return file_path.suffix.lower()


def is_valid_filename(filename: str, pattern: Optional[str] = None) -> bool:
    """
    Check if filename is valid according to pattern.
    
    Args:
        filename: Filename to validate
        pattern: Regex pattern (default: alphanumeric, underscore, hyphen, dot)
        
    Returns:
        True if filename is valid
    """
    if pattern is None:
        pattern = r'^[a-zA-Z0-9_-]+\.[a-zA-Z0-9]+$'
    
    return bool(re.match(pattern, filename))


def safe_filename(filename: str, replacement: str = '_') -> str:
    """
    Convert a string to a safe filename.
    
    Args:
        filename: Original filename
        replacement: Character to replace unsafe characters
        
    Returns:
        Safe filename
    """
    # Replace unsafe characters
    safe = re.sub(r'[^a-zA-Z0-9._-]', replacement, filename)
    
    # Remove multiple consecutive replacements
    safe = re.sub(f'{re.escape(replacement)}+', replacement, safe)
    
    # Remove leading/trailing replacements
    safe = safe.strip(replacement)
    
    # Ensure not empty
    if not safe:
        safe = f"unnamed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return safe


def list_files_recursive(
    directory: Path,
    pattern: str = '*',
    extensions: Optional[List[str]] = None,
) -> Generator[Path, None, None]:
    """
    List all files in directory recursively.
    
    Args:
        directory: Root directory to search
        pattern: Glob pattern
        extensions: List of allowed extensions (e.g., ['.pdf', '.txt'])
        
    Yields:
        Path objects for matching files
    """
    if not directory.exists():
        return
    
    for path in directory.rglob(pattern):
        if not path.is_file():
            continue
        
        if extensions is None:
            yield path
        elif get_file_extension(path) in extensions:
            yield path


def count_files(
    directory: Path,
    pattern: str = '*',
    extensions: Optional[List[str]] = None,
) -> int:
    """
    Count files in directory recursively.
    
    Args:
        directory: Root directory
        pattern: Glob pattern
        extensions: List of allowed extensions
        
    Returns:
        Number of matching files
    """
    return sum(1 for _ in list_files_recursive(directory, pattern, extensions))


def get_directory_size(directory: Path) -> int:
    """
    Calculate total size of all files in directory (bytes).
    
    Args:
        directory: Directory path
        
    Returns:
        Total size in bytes
    """
    total_size = 0
    
    for file_path in list_files_recursive(directory):
        try:
            total_size += get_file_size(file_path)
        except (OSError, FileNotFoundError):
            continue
    
    return total_size


def get_directory_size_mb(directory: Path) -> float:
    """
    Calculate total size of all files in directory (MB).
    
    Args:
        directory: Directory path
        
    Returns:
        Total size in MB
    """
    return get_directory_size(directory) / (1024 * 1024)


def is_empty_file(file_path: Path, min_size_bytes: int = 100) -> bool:
    """
    Check if file is empty or too small.
    
    Args:
        file_path: Path to file
        min_size_bytes: Minimum acceptable file size
        
    Returns:
        True if file is empty or smaller than minimum
    """
    try:
        return get_file_size(file_path) < min_size_bytes
    except FileNotFoundError:
        return True


def get_file_metadata(file_path: Path) -> dict:
    """
    Get basic file metadata.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file metadata
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat = file_path.stat()
    
    return {
        "filename": file_path.name,
        "path": str(file_path),
        "size_bytes": stat.st_size,
        "size_mb": stat.st_size / (1024 * 1024),
        "extension": get_file_extension(file_path),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
    }


def copy_file_with_metadata(source: Path, destination: Path) -> None:
    """
    Copy file and preserve metadata.
    
    Args:
        source: Source file path
        destination: Destination file path
    """
    import shutil
    
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def move_file(source: Path, destination: Path) -> None:
    """
    Move file to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
    """
    import shutil
    
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))


def delete_file_safe(file_path: Path) -> bool:
    """
    Safely delete a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file was deleted, False otherwise
    """
    try:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
    except OSError:
        pass
    
    return False


def get_mime_type(file_path: Path) -> Optional[str]:
    """
    Get MIME type of file.
    
    Args:
        file_path: Path to file
        
    Returns:
        MIME type string or None
    """
    import mimetypes
    
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type


def read_file_chunks(file_path: Path, chunk_size: int = 8192) -> Generator[bytes, None, None]:
    """
    Read file in chunks (generator).
    
    Args:
        file_path: Path to file
        chunk_size: Size of each chunk in bytes
        
    Yields:
        Byte chunks from file
    """
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk
