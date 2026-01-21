"""
Core File Operations Module
Provides hash calculation, categorization, and file manipulation functions
"""

import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import json

from config import (
    FileCategory, CATEGORIES, MIN_FILE_SIZE_FOR_HASH, MAX_FILE_SIZE_FOR_HASH,
    SIMILAR_FILENAME_THRESHOLD, get_category_for_file, is_protected_file
)

@dataclass
class FileInfo:
    """Represents a file with metadata"""
    path: Path
    name: str
    size_bytes: int
    modified_date: datetime
    created_date: datetime
    extension: str
    category: Optional[FileCategory] = None
    hash: Optional[str] = None
    is_protected: bool = False

    def __post_init__(self):
        """Calculate derived fields"""
        self.is_protected = is_protected_file(self.path)
        if self.category is None:
            self.category = get_category_for_file(self.path)

    @property
    def size_mb(self) -> float:
        """Size in megabytes"""
        return self.size_bytes / (1024 * 1024)

    @property
    def age_days(self) -> int:
        """Days since last modification"""
        return (datetime.now() - self.modified_date).days

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'path': str(self.path),
            'name': self.name,
            'size_bytes': self.size_bytes,
            'size_mb': round(self.size_mb, 2),
            'modified_date': self.modified_date.isoformat(),
            'created_date': self.created_date.isoformat(),
            'extension': self.extension,
            'category': self.category.name if self.category else None,
            'hash': self.hash,
            'is_protected': self.is_protected,
            'age_days': self.age_days
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'FileInfo':
        """Create FileInfo from dictionary"""
        return cls(
            path=Path(data['path']),
            name=data['name'],
            size_bytes=data['size_bytes'],
            modified_date=datetime.fromisoformat(data['modified_date']),
            created_date=datetime.fromisoformat(data['created_date']),
            extension=data['extension'],
            hash=data.get('hash')
        )

@dataclass
class SimilarGroup:
    """Group of similar files"""
    similarity: float  # 0.0 to 1.0
    files: List[FileInfo]
    common_base: str  # common part of filenames

    def total_size(self) -> int:
        """Total size of all files in group"""
        return sum(f.size_bytes for f in self.files)

def calculate_file_hash(file_path: Path, algorithm='md5', chunk_size=8192) -> Optional[str]:
    """
    Calculate hash of file for duplicate detection.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256)
        chunk_size: Read chunk size in bytes

    Returns:
        Hex string of hash, or None if file cannot be read
    """
    try:
        hash_obj = hashlib.new(algorithm)

        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    except (IOError, PermissionError, OSError) as e:
        print(f"Error hashing {file_path}: {e}")
        return None

def should_hash_file(file_info: FileInfo) -> bool:
    """
    Determine if file should be hashed based on size and other criteria.

    Args:
        file_info: File information

    Returns:
        True if file should be hashed
    """
    # Skip protected files
    if file_info.is_protected:
        return False

    # Check size bounds
    if file_info.size_bytes < MIN_FILE_SIZE_FOR_HASH:
        return False
    if file_info.size_bytes > MAX_FILE_SIZE_FOR_HASH:
        return False

    # Skip temporary files
    if file_info.extension in ['.tmp', '.cache']:
        return False

    return True

def find_duplicates_by_hash(files_with_hashes: List[FileInfo]) -> Dict[str, List[FileInfo]]:
    """
    Group files by hash to find exact duplicates.

    Args:
        files_with_hashes: List of FileInfo objects with hash calculated

    Returns:
        Dictionary mapping hash to list of duplicate files
    """
    hash_groups = {}

    for file_info in files_with_hashes:
        if file_info.hash is None:
            continue

        if file_info.hash not in hash_groups:
            hash_groups[file_info.hash] = []

        hash_groups[file_info.hash].append(file_info)

    # Filter to only groups with duplicates (>1 file)
    duplicates = {h: files for h, files in hash_groups.items() if len(files) > 1}

    return duplicates

def find_duplicates_by_size(files: List[FileInfo]) -> Dict[int, List[FileInfo]]:
    """
    Pre-filter: Group files by exact size (cheap operation before hashing).

    Args:
        files: List of FileInfo objects

    Returns:
        Dictionary mapping size to list of files with that size
    """
    size_groups = {}

    for file_info in files:
        size = file_info.size_bytes

        if size not in size_groups:
            size_groups[size] = []

        size_groups[size].append(file_info)

    # Filter to only groups with potential duplicates (>1 file)
    potential_duplicates = {s: files for s, files in size_groups.items() if len(files) > 1}

    return potential_duplicates

def calculate_filename_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two filenames using SequenceMatcher.

    Args:
        name1: First filename
        name2: Second filename

    Returns:
        Similarity score from 0.0 to 1.0
    """
    # Normalize to lowercase for comparison
    name1 = name1.lower()
    name2 = name2.lower()

    # Use SequenceMatcher for fuzzy matching
    matcher = SequenceMatcher(None, name1, name2)
    return matcher.ratio()

def find_similar_files(files: List[FileInfo], threshold: float = SIMILAR_FILENAME_THRESHOLD) -> List[SimilarGroup]:
    """
    Find files with similar names (fuzzy matching).

    Args:
        files: List of FileInfo objects
        threshold: Minimum similarity threshold (0.0 to 1.0)

    Returns:
        List of SimilarGroup objects
    """
    similar_groups = []
    processed = set()

    for i, file1 in enumerate(files):
        if file1.path in processed:
            continue

        group_files = [file1]

        for file2 in files[i+1:]:
            if file2.path in processed:
                continue

            # Only compare files with same extension
            if file1.extension != file2.extension:
                continue

            similarity = calculate_filename_similarity(file1.name, file2.name)

            if similarity >= threshold:
                group_files.append(file2)
                processed.add(file2.path)

        if len(group_files) > 1:
            # Find common base name
            common_base = find_common_prefix([f.name for f in group_files])

            similar_groups.append(SimilarGroup(
                similarity=threshold,  # minimum similarity in group
                files=group_files,
                common_base=common_base
            ))

            processed.add(file1.path)

    return similar_groups

def find_common_prefix(strings: List[str]) -> str:
    """
    Find common prefix of list of strings.

    Args:
        strings: List of strings

    Returns:
        Common prefix
    """
    if not strings:
        return ""

    # Find shortest string length
    min_len = min(len(s) for s in strings)

    # Find common prefix
    for i in range(min_len):
        char = strings[0][i]
        if not all(s[i] == char for s in strings):
            return strings[0][:i]

    return strings[0][:min_len]

def is_safe_to_delete(file_info: FileInfo, category: FileCategory) -> Tuple[bool, str]:
    """
    Check if file meets criteria for safe deletion.

    Args:
        file_info: File information
        category: File category

    Returns:
        Tuple of (is_safe, reason)
    """
    reasons = []

    # Protected files are never safe to delete
    if file_info.is_protected:
        return False, "File is in protected location"

    # Check if category allows auto-delete
    if not category.auto_delete:
        return False, f"Category '{category.name}' requires manual approval"

    # Check retention period
    if file_info.age_days < category.retention_days:
        return False, f"File age ({file_info.age_days} days) is less than retention period ({category.retention_days} days)"

    # Additional safety checks
    if file_info.extension in ['.db', '.sqlite']:
        return False, "Database files require manual review"

    if 'important' in file_info.name.lower():
        return False, "Filename contains 'important'"

    if 'backup' in file_info.name.lower() and file_info.size_bytes > 10 * 1024 * 1024:
        return False, "Large backup file requires manual review"

    return True, "File meets all safety criteria"

def archive_file(source: Path, archive_root: Path, preserve_structure: bool = True) -> Optional[Path]:
    """
    Move file to dated archive maintaining directory structure.

    Args:
        source: Source file path
        archive_root: Root directory for archives
        preserve_structure: Whether to maintain relative directory structure

    Returns:
        Path to archived file, or None if failed
    """
    try:
        # Create timestamped archive directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_dir = archive_root / timestamp

        if preserve_structure:
            # Maintain directory structure
            # Need to determine relative path from drive root
            # For now, use direct subfolder
            target_dir = archive_dir / source.parent.name
        else:
            target_dir = archive_dir

        target_dir.mkdir(parents=True, exist_ok=True)

        # Target file path
        target_path = target_dir / source.name

        # Handle name conflicts
        if target_path.exists():
            base = target_path.stem
            ext = target_path.suffix
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{base}_{counter}{ext}"
                counter += 1

        # Move file
        shutil.move(str(source), str(target_path))

        return target_path

    except (IOError, PermissionError, OSError) as e:
        print(f"Error archiving {source}: {e}")
        return None

def restore_file(archived_path: Path, original_location: Path) -> bool:
    """
    Restore file from archive to original location.

    Args:
        archived_path: Path to archived file
        original_location: Original file location

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure target directory exists
        original_location.parent.mkdir(parents=True, exist_ok=True)

        # Handle name conflicts
        if original_location.exists():
            base = original_location.stem
            ext = original_location.suffix
            counter = 1
            while original_location.exists():
                original_location = original_location.parent / f"{base}_restored_{counter}{ext}"
                counter += 1

        # Move file back
        shutil.move(str(archived_path), str(original_location))

        return True

    except (IOError, PermissionError, OSError) as e:
        print(f"Error restoring {archived_path}: {e}")
        return False

def load_directory_index(index_path: Path) -> List[FileInfo]:
    """
    Load directory index JSON and convert to FileInfo objects.

    Args:
        index_path: Path to directory_index.json

    Returns:
        List of FileInfo objects
    """
    try:
        # Try UTF-8 with BOM first, then regular UTF-8
        try:
            with open(index_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except:
            with open(index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

        files = []
        for item in data:
            # Skip folders
            if item.get('Type') == 'Folder':
                continue

            # Convert to FileInfo
            file_info = FileInfo(
                path=Path(item['Path']),
                name=item['Name'],
                size_bytes=item.get('SizeBytes', 0),
                modified_date=datetime.strptime(item['LastModified'], '%Y-%m-%d %H:%M:%S'),
                created_date=datetime.strptime(item['Created'], '%Y-%m-%d %H:%M:%S'),
                extension=item.get('Extension', '')
            )

            files.append(file_info)

        return files

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading index {index_path}: {e}")
        return []

if __name__ == "__main__":
    # Test module
    print("File Operations Module Test")
    print("=" * 50)

    # Test similarity calculation
    print("\nFilename Similarity Tests:")
    test_pairs = [
        ("document.pdf", "document (1).pdf"),
        ("report_v1.docx", "report_v2.docx"),
        ("image.jpg", "video.mp4"),
        ("backup_2024_01.zip", "backup_2024_02.zip")
    ]

    for name1, name2 in test_pairs:
        similarity = calculate_filename_similarity(name1, name2)
        print(f"  {name1} vs {name2}: {similarity:.2f}")

    # Test category detection
    print("\nCategory Detection Tests:")
    test_files = [
        Path("document.pdf"),
        Path("script.py"),
        Path("cache.tmp"),
        Path("archive/backup.zip"),
        Path("video.mp4")
    ]

    for test_file in test_files:
        category = get_category_for_file(test_file)
        print(f"  {test_file}: {category.name if category else 'No category'}")

    print("\nModule test complete!")
