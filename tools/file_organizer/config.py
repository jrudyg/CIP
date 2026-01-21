"""
File Organizer Configuration
Defines file categories, retention policies, and system settings
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List

@dataclass
class FileCategory:
    """Represents a category of files with associated policies"""
    name: str
    patterns: List[str]  # glob patterns for matching files
    retention_days: int  # how long to keep before archiving
    priority: int  # 1=highest priority for cleanup, 5=lowest
    auto_delete: bool  # whether automatic deletion is allowed
    description: str = ""

# File category definitions
# Priority order: 1 (clean first) to 5 (clean last)
CATEGORIES = {
    'temp_cache': FileCategory(
        name='Temporary/Cache Files',
        patterns=['*.tmp', '*.cache', '__pycache__', '*.pyc'],
        retention_days=30,
        priority=1,
        auto_delete=True,
        description='System-generated temporary and cache files that can be safely regenerated'
    ),

    'compiled': FileCategory(
        name='Compiled/Derived Files',
        patterns=['*.pyc', '*.pyd', '*.o', '*.class', '*.dll', '*.so'],
        retention_days=90,
        priority=2,
        auto_delete=False,
        description='Files generated from source code - can be rebuilt but require approval'
    ),

    'old_backups': FileCategory(
        name='Old Backups',
        patterns=['**/backup/**', '**/archive/**', '**/*_backup_*', '**/*.bak'],
        retention_days=180,
        priority=2,
        auto_delete=False,
        description='Backup and archive files older than retention period'
    ),

    'media': FileCategory(
        name='Media Files',
        patterns=['*.mp4', '*.mov', '*.avi', '*.mkv', '*.mp3', '*.wav', '*.flac',
                  '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.heic'],
        retention_days=180,
        priority=3,
        auto_delete=False,
        description='Audio, video, and image files'
    ),

    'documents': FileCategory(
        name='Documents',
        patterns=['*.pdf', '*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt', '*.pptx',
                  '*.txt', '*.rtf', '*.odt'],
        retention_days=365,
        priority=4,
        auto_delete=False,
        description='Office documents and PDFs'
    ),

    'code': FileCategory(
        name='Source Code',
        patterns=['*.py', '*.js', '*.java', '*.cpp', '*.h', '*.c', '*.cs',
                  '*.go', '*.rs', '*.ts', '*.tsx', '*.jsx'],
        retention_days=90,
        priority=5,
        auto_delete=False,
        description='Source code files'
    ),

    'reference': FileCategory(
        name='Reference Data',
        patterns=['*.xml', '*.json', '*.csv', '*.db', '*.sqlite', '*.yaml', '*.yml'],
        retention_days=365,
        priority=5,
        auto_delete=False,
        description='Data files and databases'
    ),

    'archives': FileCategory(
        name='Compressed Archives',
        patterns=['*.zip', '*.rar', '*.7z', '*.tar', '*.gz', '*.tgz'],
        retention_days=180,
        priority=3,
        auto_delete=False,
        description='Compressed archive files'
    )
}

# Protected patterns - never auto-delete, always require manual review
PROTECTED_PATTERNS = [
    '**/Documents/**',
    '**/Desktop/**',
    '**/Pictures/**',
    '**/.git/**',
    '**/node_modules/**',  # too many files, skip hashing
    '**/venv/**',          # virtual environments, skip
    '**/.env',             # environment variables
    '**/*.db',             # databases (except in temp/cache)
    '**/config.py',        # configuration files
]

# Archive configuration
ARCHIVE_ROOT = Path(r"G:\My Drive\Archive_AutoOrganize")

# Duplicate detection settings
MIN_FILE_SIZE_FOR_HASH = 1 * 1024 * 1024  # 1 MB - only hash files above this size
MAX_FILE_SIZE_FOR_HASH = 500 * 1024 * 1024  # 500 MB - skip very large files for performance
SIMILAR_FILENAME_THRESHOLD = 0.85  # fuzzy match threshold (0.0 to 1.0)

# Archive retention settings
ARCHIVE_RETENTION_DAYS = 30  # keep archives for 30 days before permanent deletion

# Database configuration
DB_PATH = Path(r"C:\Users\jrudy\CIP\tools\file_organizer\organizer.db")

# Logging configuration
LOG_FILE = Path(r"C:\Users\jrudy\CIP\logs\file_organizer.log")
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Dashboard configuration
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 5001

# Safety limits
MAX_FILES_PER_OPERATION = 1000  # maximum files to process in single operation
MAX_SIZE_PER_OPERATION = 1 * 1024 * 1024 * 1024  # 1 GB - warn if operation exceeds this

# Directory index paths
GDRIVE_INDEX = Path(r"G:\My Drive\file_dir\directory_index.json")
ONEDRIVE_INDEX = Path(r"C:\Users\jrudy\OneDrive\Directory_Index\directory_index.json")

def get_category_for_file(file_path: Path) -> FileCategory | None:
    """
    Determine which category a file belongs to based on patterns.
    Returns None if no category matches.
    """
    from fnmatch import fnmatch

    file_str = str(file_path).replace('\\', '/')
    filename = file_path.name

    # Check each category
    for category_key, category in CATEGORIES.items():
        for pattern in category.patterns:
            # Handle directory patterns (with **)
            if '**' in pattern:
                if fnmatch(file_str, pattern):
                    return category
            # Handle simple file patterns
            else:
                if fnmatch(filename, pattern):
                    return category

    return None

def is_protected_file(file_path: Path) -> bool:
    """
    Check if a file is protected and should never be auto-deleted.
    """
    from fnmatch import fnmatch

    file_str = str(file_path).replace('\\', '/')

    for pattern in PROTECTED_PATTERNS:
        if fnmatch(file_str, pattern):
            return True

    return False

def validate_config() -> List[str]:
    """
    Validate configuration and return list of warnings/errors.
    """
    warnings = []

    # Check if archive root exists or can be created
    if not ARCHIVE_ROOT.parent.exists():
        warnings.append(f"Archive root parent directory does not exist: {ARCHIVE_ROOT.parent}")

    # Check if database directory exists
    if not DB_PATH.parent.exists():
        warnings.append(f"Database directory does not exist: {DB_PATH.parent}")

    # Check if log directory exists
    if not LOG_FILE.parent.exists():
        warnings.append(f"Log directory does not exist: {LOG_FILE.parent}")

    # Validate G: Drive index exists
    if not GDRIVE_INDEX.exists():
        warnings.append(f"G: Drive index not found: {GDRIVE_INDEX}")

    # Check for priority conflicts
    priorities = {}
    for key, cat in CATEGORIES.items():
        if cat.priority in priorities:
            warnings.append(f"Priority {cat.priority} used by both {cat.name} and {priorities[cat.priority]}")
        priorities[cat.priority] = cat.name

    return warnings

if __name__ == "__main__":
    # Test configuration
    print("File Organizer Configuration")
    print("=" * 50)
    print(f"\nArchive Root: {ARCHIVE_ROOT}")
    print(f"Database: {DB_PATH}")
    print(f"Log File: {LOG_FILE}")
    print(f"\nG: Drive Index: {GDRIVE_INDEX}")
    print(f"  Exists: {GDRIVE_INDEX.exists()}")

    print(f"\nFile Categories ({len(CATEGORIES)}):")
    for key, cat in sorted(CATEGORIES.items(), key=lambda x: x[1].priority):
        print(f"  [{cat.priority}] {cat.name}")
        print(f"      Retention: {cat.retention_days} days")
        print(f"      Auto-delete: {cat.auto_delete}")
        print(f"      Patterns: {', '.join(cat.patterns[:3])}...")

    print(f"\nProtected Patterns ({len(PROTECTED_PATTERNS)}):")
    for pattern in PROTECTED_PATTERNS[:5]:
        print(f"  - {pattern}")
    if len(PROTECTED_PATTERNS) > 5:
        print(f"  ... and {len(PROTECTED_PATTERNS) - 5} more")

    # Run validation
    warnings = validate_config()
    if warnings:
        print(f"\nConfiguration Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  WARNING: {warning}")
    else:
        print("\nConfiguration valid")
