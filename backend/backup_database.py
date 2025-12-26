"""
CIP Automated Database Backup Script
Creates timestamped backups with retention policy
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Databases to backup
DATABASES = {
    'contracts': DATA_DIR / "contracts.db",
    'reports': DATA_DIR / "reports.db"
}

# Retention policy (days)
RETENTION_DAYS = 30

def create_backup(db_name: str, db_path: Path) -> Optional[Path]:
    """
    Create timestamped backup of database

    Args:
        db_name: Name of database (for backup filename)
        db_path: Path to database file

    Returns:
        Path to backup file
    """
    if not db_path.exists():
        print(f"  [SKIP] {db_name} - database not found")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{db_name}_backup_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_filename

    # Use SQLite backup API for consistency
    try:
        source = sqlite3.connect(str(db_path))
        dest = sqlite3.connect(str(backup_path))

        with dest:
            source.backup(dest)

        source.close()
        dest.close()

        # Get file size
        size_kb = backup_path.stat().st_size / 1024

        print(f"  [OK] {db_name} -> {backup_filename} ({size_kb:.1f} KB)")
        return backup_path

    except Exception as e:
        print(f"  [ERROR] {db_name} - {str(e)}")
        return None

def clean_old_backups(retention_days: int = RETENTION_DAYS):
    """
    Remove backups older than retention period

    Args:
        retention_days: Number of days to keep backups
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    removed_count = 0
    removed_size = 0

    print(f"\nCleaning backups older than {retention_days} days...")

    for backup_file in BACKUP_DIR.glob("*_backup_*.db"):
        try:
            # Extract timestamp from filename
            # Format: dbname_backup_YYYYMMDD_HHMMSS.db
            parts = backup_file.stem.split('_backup_')
            if len(parts) == 2:
                timestamp_str = parts[1]
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                if file_date < cutoff_date:
                    size = backup_file.stat().st_size
                    backup_file.unlink()
                    removed_count += 1
                    removed_size += size
                    print(f"  [REMOVED] {backup_file.name}")

        except Exception as e:
            print(f"  [ERROR] Could not process {backup_file.name}: {e}")

    if removed_count > 0:
        print(f"\nRemoved {removed_count} old backup(s), freed {removed_size / 1024:.1f} KB")
    else:
        print("  [OK] No old backups to remove")

def list_backups():
    """List all existing backups"""
    backups = sorted(BACKUP_DIR.glob("*_backup_*.db"), reverse=True)

    if not backups:
        print("\nNo backups found")
        return

    print(f"\nExisting Backups ({len(backups)} total):")
    print("-" * 70)

    for backup in backups:
        size_kb = backup.stat().st_size / 1024
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        age_days = (datetime.now() - mtime).days

        print(f"  {backup.name:50} {size_kb:8.1f} KB  {age_days:3}d old")

def restore_backup(backup_path: Path, target_db: str):
    """
    Restore database from backup

    Args:
        backup_path: Path to backup file
        target_db: Name of target database (contracts or reports)
    """
    if target_db not in DATABASES:
        print(f"[ERROR] Unknown database: {target_db}")
        return False

    target_path = DATABASES[target_db]

    # Create backup of current database before restoring
    print(f"Creating safety backup of current {target_db} database...")
    safety_backup = create_backup(f"{target_db}_pre_restore", target_path)

    if not safety_backup:
        print("[ERROR] Could not create safety backup - aborting restore")
        return False

    # Restore from backup
    try:
        print(f"Restoring {target_db} from {backup_path.name}...")
        shutil.copy2(backup_path, target_path)
        print(f"[OK] Database restored successfully")
        return True

    except Exception as e:
        print(f"[ERROR] Restore failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("CIP Database Backup Utility")
    print("=" * 70)

    # Create backups
    print("\nCreating backups...")
    for db_name, db_path in DATABASES.items():
        create_backup(db_name, db_path)

    # Clean old backups
    clean_old_backups()

    # List all backups
    list_backups()

    print("\n" + "=" * 70)
    print("Backup complete!")
    print(f"Backups stored in: {BACKUP_DIR}")
    print(f"Retention policy: {RETENTION_DAYS} days")
    print("=" * 70)
