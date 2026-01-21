"""
Database Module for File Organizer
Creates and manages SQLite database for tracking operations
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

from config import DB_PATH

# Database schema
SCHEMA = """
-- File operations tracking
CREATE TABLE IF NOT EXISTS file_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operation TEXT CHECK(operation IN ('archive', 'delete', 'restore', 'scan')) NOT NULL,
    original_path TEXT NOT NULL,
    target_path TEXT,
    file_size BIGINT,
    file_hash TEXT,
    category TEXT,
    reason TEXT,
    session_id TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'failed'))
);

-- Duplicate groups
CREATE TABLE IF NOT EXISTS duplicate_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash TEXT NOT NULL UNIQUE,
    file_count INTEGER NOT NULL,
    total_size BIGINT NOT NULL,
    representative_file TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'reviewed', 'approved', 'ignored')),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Duplicate group members
CREATE TABLE IF NOT EXISTS duplicate_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES duplicate_groups(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    modified_date TIMESTAMP NOT NULL,
    keep BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, file_path)
);

-- Archive sessions
CREATE TABLE IF NOT EXISTS archive_sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_count INTEGER DEFAULT 0,
    total_size BIGINT DEFAULT 0,
    archive_path TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'deleted')),
    notes TEXT
);

-- Similar file groups
CREATE TABLE IF NOT EXISTS similar_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    common_base TEXT,
    file_count INTEGER NOT NULL,
    similarity_score REAL NOT NULL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'reviewed', 'merged', 'ignored')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Similar group members
CREATE TABLE IF NOT EXISTS similar_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES similar_groups(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    keep BOOLEAN DEFAULT FALSE,
    UNIQUE(group_id, file_path)
);

-- Scan results
CREATE TABLE IF NOT EXISTS scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    drive_path TEXT NOT NULL,
    total_files INTEGER NOT NULL,
    total_size BIGINT NOT NULL,
    duplicate_groups INTEGER DEFAULT 0,
    similar_groups INTEGER DEFAULT 0,
    potential_savings BIGINT DEFAULT 0,
    scan_duration_seconds REAL,
    notes TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_file_ops_session ON file_operations(session_id);
CREATE INDEX IF NOT EXISTS idx_file_ops_status ON file_operations(status);
CREATE INDEX IF NOT EXISTS idx_file_ops_hash ON file_operations(file_hash);
CREATE INDEX IF NOT EXISTS idx_dup_groups_status ON duplicate_groups(status);
CREATE INDEX IF NOT EXISTS idx_dup_groups_hash ON duplicate_groups(hash);
CREATE INDEX IF NOT EXISTS idx_similar_groups_status ON similar_groups(status);
"""

@contextmanager
def get_connection():
    """
    Context manager for database connections.
    Ensures proper cleanup.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """
    Initialize database with schema.
    Safe to call multiple times (IF NOT EXISTS).
    """
    # Ensure parent directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.commit()

    print(f"Database initialized: {DB_PATH}")

def log_operation(
    operation: str,
    original_path: str,
    target_path: Optional[str] = None,
    file_size: Optional[int] = None,
    file_hash: Optional[str] = None,
    category: Optional[str] = None,
    reason: Optional[str] = None,
    session_id: Optional[str] = None,
    status: str = 'pending'
) -> int:
    """
    Log a file operation to the database.

    Returns:
        Operation ID
    """
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO file_operations
            (operation, original_path, target_path, file_size, file_hash, category, reason, session_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (operation, original_path, target_path, file_size, file_hash, category, reason, session_id, status))
        conn.commit()
        return cursor.lastrowid

def add_duplicate_group(hash_value: str, files: List[Dict], representative_file: str) -> int:
    """
    Add a duplicate group to the database.
    Updates if group already exists.

    Args:
        hash_value: File hash
        files: List of file dictionaries with path, size, modified_date
        representative_file: Path of file to keep

    Returns:
        Group ID
    """
    with get_connection() as conn:
        # Check if group already exists
        existing = conn.execute("""
            SELECT id FROM duplicate_groups WHERE hash = ?
        """, (hash_value,)).fetchone()

        if existing:
            # Update existing group
            group_id = existing['id']
            conn.execute("""
                UPDATE duplicate_groups
                SET file_count = ?, total_size = ?, representative_file = ?
                WHERE id = ?
            """, (len(files), sum(f['size'] for f in files), representative_file, group_id))

            # Delete old members
            conn.execute("DELETE FROM duplicate_members WHERE group_id = ?", (group_id,))
        else:
            # Create new group
            cursor = conn.execute("""
                INSERT INTO duplicate_groups (hash, file_count, total_size, representative_file)
                VALUES (?, ?, ?, ?)
            """, (hash_value, len(files), sum(f['size'] for f in files), representative_file))
            group_id = cursor.lastrowid

        # Add members
        for file in files:
            keep = (file['path'] == representative_file)
            conn.execute("""
                INSERT INTO duplicate_members (group_id, file_path, file_size, modified_date, keep)
                VALUES (?, ?, ?, ?, ?)
            """, (group_id, file['path'], file['size'], file['modified_date'], keep))

        conn.commit()
        return group_id

def get_pending_duplicate_groups(limit: int = 100) -> List[Dict]:
    """
    Get duplicate groups pending review.

    Returns:
        List of duplicate group dictionaries
    """
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT g.id, g.hash, g.file_count, g.total_size, g.representative_file, g.status,
                   COUNT(m.id) as member_count
            FROM duplicate_groups g
            LEFT JOIN duplicate_members m ON g.id = m.group_id
            WHERE g.status = 'pending'
            GROUP BY g.id
            ORDER BY g.total_size DESC
            LIMIT ?
        """, (limit,))

        groups = []
        for row in cursor:
            group = dict(row)

            # Get members
            members_cursor = conn.execute("""
                SELECT file_path, file_size, modified_date, keep
                FROM duplicate_members
                WHERE group_id = ?
                ORDER BY modified_date DESC
            """, (group['id'],))

            group['members'] = [dict(m) for m in members_cursor]
            groups.append(group)

        return groups

def approve_duplicate_group(group_id: int) -> bool:
    """
    Approve a duplicate group for deletion.

    Returns:
        True if successful
    """
    with get_connection() as conn:
        conn.execute("""
            UPDATE duplicate_groups
            SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (group_id,))
        conn.commit()
        return True

def create_archive_session(archive_path: str, notes: Optional[str] = None) -> str:
    """
    Create a new archive session.

    Returns:
        Session ID
    """
    session_id = datetime.now().strftime("archive_%Y%m%d_%H%M%S")

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO archive_sessions (session_id, archive_path, notes)
            VALUES (?, ?, ?)
        """, (session_id, archive_path, notes))
        conn.commit()

    return session_id

def update_archive_session(session_id: str, file_count: int, total_size: int, status: str = 'active'):
    """Update archive session statistics"""
    with get_connection() as conn:
        conn.execute("""
            UPDATE archive_sessions
            SET file_count = ?, total_size = ?, status = ?
            WHERE session_id = ?
        """, (file_count, total_size, status, session_id))
        conn.commit()

def get_archive_sessions(limit: int = 50) -> List[Dict]:
    """
    Get archive sessions.

    Returns:
        List of session dictionaries
    """
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT session_id, created_at, file_count, total_size, archive_path, status, notes
            FROM archive_sessions
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor]

def log_scan_result(
    drive_path: str,
    total_files: int,
    total_size: int,
    duplicate_groups: int = 0,
    similar_groups: int = 0,
    potential_savings: int = 0,
    scan_duration: float = 0.0,
    notes: Optional[str] = None
) -> int:
    """
    Log scan results to database.

    Returns:
        Scan ID
    """
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO scan_results
            (drive_path, total_files, total_size, duplicate_groups, similar_groups,
             potential_savings, scan_duration_seconds, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (drive_path, total_files, total_size, duplicate_groups, similar_groups,
              potential_savings, scan_duration, notes))
        conn.commit()
        return cursor.lastrowid

def get_latest_scan() -> Optional[Dict]:
    """
    Get most recent scan result.

    Returns:
        Scan dictionary or None
    """
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT *
            FROM scan_results
            ORDER BY scan_date DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        return dict(row) if row else None

def get_statistics() -> Dict:
    """
    Get overall statistics from database.

    Returns:
        Dictionary of statistics
    """
    with get_connection() as conn:
        stats = {}

        # Total operations
        cursor = conn.execute("SELECT COUNT(*) as count FROM file_operations")
        stats['total_operations'] = cursor.fetchone()['count']

        # Pending duplicate groups
        cursor = conn.execute("SELECT COUNT(*) as count FROM duplicate_groups WHERE status = 'pending'")
        stats['pending_duplicates'] = cursor.fetchone()['count']

        # Total potential savings
        cursor = conn.execute("""
            SELECT SUM(total_size) - MAX(total_size) as savings
            FROM (
                SELECT g.id, SUM(m.file_size) as total_size
                FROM duplicate_groups g
                JOIN duplicate_members m ON g.id = m.group_id
                WHERE g.status = 'pending'
                GROUP BY g.id
            )
        """)
        savings_row = cursor.fetchone()
        stats['potential_savings_bytes'] = savings_row['savings'] if savings_row['savings'] else 0

        # Active archive sessions
        cursor = conn.execute("SELECT COUNT(*) as count FROM archive_sessions WHERE status = 'active'")
        stats['active_archives'] = cursor.fetchone()['count']

        return stats

if __name__ == "__main__":
    # Test database setup
    print("File Organizer Database Setup")
    print("=" * 50)

    # Initialize database
    init_database()

    # Test operations
    print("\nTesting database operations...")

    # Log a test operation
    op_id = log_operation(
        operation='scan',
        original_path='G:\\My Drive',
        status='completed',
        reason='Test scan'
    )
    print(f"Logged operation ID: {op_id}")

    # Create test archive session
    session_id = create_archive_session(
        archive_path='G:\\My Drive\\Archive_AutoOrganize\\test',
        notes='Test session'
    )
    print(f"Created archive session: {session_id}")

    # Get statistics
    stats = get_statistics()
    print(f"\nDatabase Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nDatabase setup and test complete!")
