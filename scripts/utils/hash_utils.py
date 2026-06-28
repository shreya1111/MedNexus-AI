"""
Hashing and checksum utilities for MedNexus-AI Knowledge Ingestion Framework.

Provides file integrity verification and duplicate detection.
"""

import hashlib
from pathlib import Path
from typing import Optional, Literal

from .file_utils import read_file_chunks

HashAlgorithm = Literal["md5", "sha1", "sha256", "sha512"]


def compute_file_hash(
    file_path: Path,
    algorithm: HashAlgorithm = "sha256",
    chunk_size: int = 8192,
) -> str:
    """
    Compute hash of file contents.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm to use
        chunk_size: Size of chunks to read
        
    Returns:
        Hexadecimal hash string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If algorithm is not supported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get hash function
    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    # Read file in chunks and update hash
    for chunk in read_file_chunks(file_path, chunk_size):
        hasher.update(chunk)
    
    return hasher.hexdigest()


def compute_string_hash(
    text: str,
    algorithm: HashAlgorithm = "sha256",
    encoding: str = "utf-8",
) -> str:
    """
    Compute hash of string.
    
    Args:
        text: String to hash
        algorithm: Hash algorithm to use
        encoding: Text encoding
        
    Returns:
        Hexadecimal hash string
    """
    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    hasher.update(text.encode(encoding))
    return hasher.hexdigest()


def verify_checksum(
    file_path: Path,
    expected_checksum: str,
    algorithm: HashAlgorithm = "sha256",
) -> bool:
    """
    Verify file checksum against expected value.
    
    Args:
        file_path: Path to file
        expected_checksum: Expected checksum (hex string)
        algorithm: Hash algorithm to use
        
    Returns:
        True if checksum matches
    """
    try:
        actual_checksum = compute_file_hash(file_path, algorithm)
        return actual_checksum.lower() == expected_checksum.lower()
    except (FileNotFoundError, ValueError):
        return False


def compute_multiple_hashes(
    file_path: Path,
    algorithms: list[HashAlgorithm] = ["md5", "sha256"],
    chunk_size: int = 8192,
) -> dict[str, str]:
    """
    Compute multiple hashes of a file in single pass.
    
    Args:
        file_path: Path to file
        algorithms: List of hash algorithms
        chunk_size: Size of chunks to read
        
    Returns:
        Dictionary mapping algorithm names to hash values
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Initialize hashers
    hashers = {}
    for algorithm in algorithms:
        try:
            hashers[algorithm] = hashlib.new(algorithm)
        except ValueError:
            continue
    
    # Read file once and update all hashers
    for chunk in read_file_chunks(file_path, chunk_size):
        for hasher in hashers.values():
            hasher.update(chunk)
    
    # Return all hashes
    return {
        algorithm: hasher.hexdigest()
        for algorithm, hasher in hashers.items()
    }


def get_file_fingerprint(file_path: Path) -> dict:
    """
    Generate a comprehensive file fingerprint.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with multiple hashes and metadata
    """
    from .file_utils import get_file_size
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hashes = compute_multiple_hashes(file_path, ["md5", "sha256"])
    
    return {
        "filename": file_path.name,
        "size_bytes": get_file_size(file_path),
        "md5": hashes.get("md5"),
        "sha256": hashes.get("sha256"),
    }


def find_duplicate_files(
    directory: Path,
    algorithm: HashAlgorithm = "sha256",
) -> dict[str, list[Path]]:
    """
    Find duplicate files in directory based on hash.
    
    Args:
        directory: Directory to search
        algorithm: Hash algorithm to use
        
    Returns:
        Dictionary mapping hashes to lists of duplicate file paths
    """
    from .file_utils import list_files_recursive
    
    hash_to_files: dict[str, list[Path]] = {}
    
    for file_path in list_files_recursive(directory):
        try:
            file_hash = compute_file_hash(file_path, algorithm)
            
            if file_hash not in hash_to_files:
                hash_to_files[file_hash] = []
            
            hash_to_files[file_hash].append(file_path)
        except (OSError, ValueError):
            continue
    
    # Return only hashes with duplicates
    return {
        file_hash: paths
        for file_hash, paths in hash_to_files.items()
        if len(paths) > 1
    }


def generate_content_id(content: bytes) -> str:
    """
    Generate a content-based identifier.
    
    Args:
        content: Binary content
        
    Returns:
        SHA-256 hash as content ID
    """
    return hashlib.sha256(content).hexdigest()


def quick_hash(file_path: Path, sample_size: int = 1024 * 1024) -> str:
    """
    Compute a quick hash using only part of the file.
    Useful for fast duplicate detection of large files.
    
    Args:
        file_path: Path to file
        sample_size: Number of bytes to sample
        
    Returns:
        Hash of sampled content
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        # Sample from beginning
        chunk = f.read(sample_size // 2)
        hasher.update(chunk)
        
        # Sample from end if file is large enough
        file_size = file_path.stat().st_size
        if file_size > sample_size:
            f.seek(file_size - sample_size // 2)
            chunk = f.read(sample_size // 2)
            hasher.update(chunk)
    
    return hasher.hexdigest()
