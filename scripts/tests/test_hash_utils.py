"""
Unit tests for hash utilities.
"""

import pytest
from pathlib import Path
import tempfile

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.hash_utils import compute_file_hash, compute_string_hash, verify_checksum, find_duplicate_files


class TestHashUtils:
    """Test cases for hash utilities."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_compute_string_hash_sha256(self):
        """Test computing SHA-256 hash of string."""
        text = "Hello, World!"
        hash_value = compute_string_hash(text, algorithm='sha256')
        
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA-256 produces 64 hex characters
    
    def test_compute_string_hash_md5(self):
        """Test computing MD5 hash of string."""
        text = "Hello, World!"
        hash_value = compute_string_hash(text, algorithm='md5')
        
        assert hash_value is not None
        assert len(hash_value) == 32  # MD5 produces 32 hex characters
    
    def test_compute_file_hash(self, temp_dir):
        """Test computing file hash."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content", encoding='utf-8')
        
        # Compute hash
        hash_value = compute_file_hash(test_file, algorithm='sha256')
        
        assert hash_value is not None
        assert len(hash_value) == 64
    
    def test_verify_checksum_valid(self, temp_dir):
        """Test verifying valid checksum."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content", encoding='utf-8')
        
        # Compute hash
        expected_hash = compute_file_hash(test_file, algorithm='sha256')
        
        # Verify
        assert verify_checksum(test_file, expected_hash, algorithm='sha256')
    
    def test_verify_checksum_invalid(self, temp_dir):
        """Test verifying invalid checksum."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test content", encoding='utf-8')
        
        # Use wrong hash
        wrong_hash = "0" * 64
        
        # Verify
        assert not verify_checksum(test_file, wrong_hash, algorithm='sha256')
    
    def test_find_duplicate_files(self, temp_dir):
        """Test finding duplicate files."""
        # Create identical files
        content = "Duplicate content"
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file3 = temp_dir / "file3.txt"
        
        file1.write_text(content, encoding='utf-8')
        file2.write_text(content, encoding='utf-8')
        file3.write_text("Different content", encoding='utf-8')
        
        # Find duplicates
        duplicates = find_duplicate_files(temp_dir)
        
        # Should find file1 and file2 as duplicates
        assert len(duplicates) > 0
        
        # Find the duplicate group
        for hash_value, files in duplicates.items():
            if len(files) == 2:
                file_names = {f.name for f in files}
                assert "file1.txt" in file_names
                assert "file2.txt" in file_names
                assert "file3.txt" not in file_names
    
    def test_hash_consistency(self, temp_dir):
        """Test that same content produces same hash."""
        content = "Consistent content"
        
        # Create two files with same content
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file1.write_text(content, encoding='utf-8')
        file2.write_text(content, encoding='utf-8')
        
        # Compute hashes
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        
        assert hash1 == hash2
    
    def test_hash_different_content(self, temp_dir):
        """Test that different content produces different hash."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        
        file1.write_text("Content A", encoding='utf-8')
        file2.write_text("Content B", encoding='utf-8')
        
        # Compute hashes
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        
        assert hash1 != hash2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
