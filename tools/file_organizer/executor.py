"""
File Organizer - Execution Engine
Safely executes approved file operations with validation and rollback
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib

from config import (
    ARCHIVE_ROOT,
    MAX_FILES_PER_OPERATION,
    MAX_SIZE_PER_OPERATION,
    MIN_FILE_SIZE_FOR_HASH
)
from database import get_connection
from file_ops import calculate_file_hash, archive_file, restore_file
from logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ExecutionResult:
    """Result of an execution operation"""
    success: bool
    operations_completed: int
    operations_failed: int
    total_size_processed: int
    session_id: str
    errors: List[str]
    warnings: List[str]
    archived_files: List[Dict[str, str]]  # original_path, archived_path

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'success': self.success,
            'operations_completed': self.operations_completed,
            'operations_failed': self.operations_failed,
            'total_size_processed': self.total_size_processed,
            'total_size_mb': round(self.total_size_processed / (1024 * 1024), 2),
            'session_id': self.session_id,
            'errors': self.errors,
            'warnings': self.warnings,
            'archived_files': self.archived_files
        }


@dataclass
class OperationValidation:
    """Validation result for an operation"""
    valid: bool
    file_count: int
    total_size: int
    errors: List[str]
    warnings: List[str]
    files_to_process: List[Dict[str, any]]


class ExecutionEngine:
    """
    Safely executes approved file operations with:
    - Pre-execution validation
    - Hash verification
    - Disk space checks
    - Transaction logging
    - Rollback capability
    """

    def __init__(self, dry_run: bool = True):
        """
        Initialize execution engine

        Args:
            dry_run: If True, simulate operations without making changes
        """
        self.dry_run = dry_run
        self.session_id = datetime.now().strftime("archive_%Y%m%d_%H%M%S")
        self.archive_path = ARCHIVE_ROOT / self.session_id
        self.operations_log: List[Dict] = []

    def validate_operation(self, group_ids: Optional[List[int]] = None) -> OperationValidation:
        """
        Validate operations before execution

        Args:
            group_ids: Specific group IDs to process, or None for all approved

        Returns:
            OperationValidation with validation results
        """
        errors = []
        warnings = []
        files_to_process = []
        total_size = 0

        try:
            with get_connection() as conn:
                # Build query to get approved duplicate groups
                if group_ids:
                    placeholders = ','.join(['?'] * len(group_ids))
                    query = f"""
                        SELECT g.id as group_id, g.hash, g.file_count, g.total_size,
                               m.file_path, m.file_size, m.keep
                        FROM duplicate_groups g
                        JOIN duplicate_members m ON g.id = m.group_id
                        WHERE g.status = 'approved' AND g.id IN ({placeholders})
                        ORDER BY g.id, m.keep DESC
                    """
                    cursor = conn.execute(query, group_ids)
                else:
                    query = """
                        SELECT g.id as group_id, g.hash, g.file_count, g.total_size,
                               m.file_path, m.file_size, m.keep
                        FROM duplicate_groups g
                        JOIN duplicate_members m ON g.id = m.group_id
                        WHERE g.status = 'approved'
                        ORDER BY g.id, m.keep DESC
                    """
                    cursor = conn.execute(query)

                rows = cursor.fetchall()

                if not rows:
                    errors.append("No approved operations found")
                    return OperationValidation(
                        valid=False,
                        file_count=0,
                        total_size=0,
                        errors=errors,
                        warnings=warnings,
                        files_to_process=[]
                    )

                # Group by group_id to process each duplicate group
                current_group = None
                group_files = []

                for row in rows:
                    if current_group != row['group_id']:
                        # Process previous group
                        if group_files:
                            self._process_group_validation(
                                group_files, files_to_process, warnings
                            )

                        # Start new group
                        current_group = row['group_id']
                        group_files = []

                    group_files.append({
                        'group_id': row['group_id'],
                        'hash': row['hash'],
                        'file_path': row['file_path'],
                        'file_size': row['file_size'],
                        'keep': bool(row['keep'])
                    })

                # Process last group
                if group_files:
                    self._process_group_validation(
                        group_files, files_to_process, warnings
                    )

                # Calculate total size
                total_size = sum(f['file_size'] for f in files_to_process)

                # Validate against safety limits
                if len(files_to_process) > MAX_FILES_PER_OPERATION:
                    errors.append(
                        f"Operation exceeds max files limit: {len(files_to_process)} > {MAX_FILES_PER_OPERATION}"
                    )

                if total_size > MAX_SIZE_PER_OPERATION:
                    warnings.append(
                        f"Operation size ({total_size / (1024**3):.2f} GB) exceeds recommended limit "
                        f"({MAX_SIZE_PER_OPERATION / (1024**3):.2f} GB)"
                    )

                # Check disk space
                disk_validation = self._validate_disk_space(total_size)
                if not disk_validation['sufficient']:
                    errors.append(disk_validation['error'])

                return OperationValidation(
                    valid=len(errors) == 0,
                    file_count=len(files_to_process),
                    total_size=total_size,
                    errors=errors,
                    warnings=warnings,
                    files_to_process=files_to_process
                )

        except Exception as e:
            logger.error(f"Error validating operations: {e}")
            errors.append(f"Validation error: {str(e)}")
            return OperationValidation(
                valid=False,
                file_count=0,
                total_size=0,
                errors=errors,
                warnings=warnings,
                files_to_process=[]
            )

    def _process_group_validation(
        self,
        group_files: List[Dict],
        files_to_process: List[Dict],
        warnings: List[str]
    ):
        """Process validation for a single duplicate group"""
        # Find file to keep (should have keep=True)
        keep_files = [f for f in group_files if f['keep']]
        delete_files = [f for f in group_files if not f['keep']]

        if not keep_files:
            warnings.append(
                f"Group {group_files[0]['group_id']}: No file marked to keep, skipping"
            )
            return

        if len(keep_files) > 1:
            warnings.append(
                f"Group {group_files[0]['group_id']}: Multiple files marked to keep, using first"
            )

        # Add delete files to processing list
        for file_info in delete_files:
            file_path = Path(file_info['file_path'])

            # Check if file exists
            if not file_path.exists():
                warnings.append(f"File not found: {file_path}")
                continue

            # Check if file size matches (file may have changed)
            actual_size = file_path.stat().st_size
            if actual_size != file_info['file_size']:
                warnings.append(
                    f"File size mismatch for {file_path}: "
                    f"expected {file_info['file_size']}, got {actual_size}"
                )
                continue

            files_to_process.append(file_info)

    def _validate_disk_space(self, required_bytes: int) -> Dict[str, any]:
        """
        Validate sufficient disk space for archive

        Args:
            required_bytes: Bytes needed for archive

        Returns:
            Dict with 'sufficient' bool and optional 'error' message
        """
        try:
            # Ensure archive root parent exists
            if not ARCHIVE_ROOT.parent.exists():
                return {
                    'sufficient': False,
                    'error': f"Archive root parent does not exist: {ARCHIVE_ROOT.parent}"
                }

            # Get disk space
            stat = shutil.disk_usage(ARCHIVE_ROOT.parent)
            available_bytes = stat.free

            # Require 20% buffer beyond needed space
            required_with_buffer = required_bytes * 1.2

            if available_bytes < required_with_buffer:
                return {
                    'sufficient': False,
                    'error': (
                        f"Insufficient disk space: need {required_with_buffer / (1024**3):.2f} GB, "
                        f"have {available_bytes / (1024**3):.2f} GB available"
                    )
                }

            return {'sufficient': True}

        except Exception as e:
            return {
                'sufficient': False,
                'error': f"Error checking disk space: {str(e)}"
            }

    def execute(self, group_ids: Optional[List[int]] = None) -> ExecutionResult:
        """
        Execute approved operations

        Args:
            group_ids: Specific group IDs to process, or None for all approved

        Returns:
            ExecutionResult with operation results
        """
        logger.info(f"Starting execution (dry_run={self.dry_run})")

        # Validate operations
        validation = self.validate_operation(group_ids)

        if not validation.valid:
            logger.error(f"Validation failed: {validation.errors}")
            return ExecutionResult(
                success=False,
                operations_completed=0,
                operations_failed=0,
                total_size_processed=0,
                session_id=self.session_id,
                errors=validation.errors,
                warnings=validation.warnings,
                archived_files=[]
            )

        # Log warnings
        for warning in validation.warnings:
            logger.warning(warning)

        # Create archive session in database
        if not self.dry_run:
            self._create_archive_session(validation.file_count, validation.total_size)

        # Execute operations
        completed = 0
        failed = 0
        total_processed = 0
        errors = []
        archived_files = []

        for file_info in validation.files_to_process:
            result = self._execute_single_file(file_info)

            if result['success']:
                completed += 1
                total_processed += file_info['file_size']
                archived_files.append({
                    'original_path': file_info['file_path'],
                    'archived_path': result.get('archived_path', 'N/A (dry-run)')
                })
            else:
                failed += 1
                errors.append(result['error'])

        # Update archive session status
        if not self.dry_run and completed > 0:
            self._complete_archive_session()

        logger.info(
            f"Execution complete: {completed} succeeded, {failed} failed, "
            f"{total_processed / (1024**2):.2f} MB processed"
        )

        return ExecutionResult(
            success=(failed == 0),
            operations_completed=completed,
            operations_failed=failed,
            total_size_processed=total_processed,
            session_id=self.session_id,
            errors=errors,
            warnings=validation.warnings,
            archived_files=archived_files
        )

    def _execute_single_file(self, file_info: Dict) -> Dict[str, any]:
        """
        Execute operation for a single file with hash verification

        Args:
            file_info: File information dict

        Returns:
            Dict with 'success' bool and optional 'error' or 'archived_path'
        """
        file_path = Path(file_info['file_path'])

        try:
            # Verify file still exists
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f"File no longer exists: {file_path}"
                }

            # Verify hash if file is large enough and hash is provided
            if file_info.get('hash') and file_path.stat().st_size >= MIN_FILE_SIZE_FOR_HASH:
                current_hash = calculate_file_hash(file_path)
                if current_hash != file_info['hash']:
                    return {
                        'success': False,
                        'error': f"Hash mismatch for {file_path} - file may have changed"
                    }

            # Log operation in database
            operation_id = self._log_operation(
                operation='archive',
                original_path=str(file_path),
                file_size=file_info['file_size'],
                file_hash=file_info.get('hash'),
                status='in_progress'
            )

            if self.dry_run:
                # Dry-run: just log, don't actually move
                logger.info(f"[DRY-RUN] Would archive: {file_path}")

                # Update operation status
                if operation_id:
                    self._update_operation_status(operation_id, 'completed',
                                                  target_path='[dry-run]')

                return {
                    'success': True,
                    'archived_path': '[dry-run]'
                }

            else:
                # Actually archive the file
                archived_path = archive_file(file_path, self.archive_path)

                if archived_path:
                    logger.info(f"Archived: {file_path} -> {archived_path}")

                    # Update operation status
                    if operation_id:
                        self._update_operation_status(operation_id, 'completed',
                                                      target_path=str(archived_path))

                    # Store in operations log for rollback
                    self.operations_log.append({
                        'operation_id': operation_id,
                        'original_path': str(file_path),
                        'archived_path': str(archived_path),
                        'timestamp': datetime.now().isoformat()
                    })

                    return {
                        'success': True,
                        'archived_path': str(archived_path)
                    }
                else:
                    # Update operation status
                    if operation_id:
                        self._update_operation_status(operation_id, 'failed')

                    return {
                        'success': False,
                        'error': f"Failed to archive {file_path}"
                    }

        except Exception as e:
            logger.error(f"Error executing operation for {file_path}: {e}")
            return {
                'success': False,
                'error': f"Exception: {str(e)}"
            }

    def _create_archive_session(self, file_count: int, total_size: int):
        """Create archive session record in database"""
        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO archive_sessions
                    (session_id, file_count, total_size, archive_path, status)
                    VALUES (?, ?, ?, ?, 'active')
                """, (self.session_id, file_count, total_size, str(self.archive_path)))
                conn.commit()
                logger.info(f"Created archive session: {self.session_id}")
        except Exception as e:
            logger.error(f"Error creating archive session: {e}")

    def _complete_archive_session(self):
        """Mark archive session as completed"""
        try:
            with get_connection() as conn:
                conn.execute("""
                    UPDATE archive_sessions
                    SET status = 'completed'
                    WHERE session_id = ?
                """, (self.session_id,))
                conn.commit()
                logger.info(f"Completed archive session: {self.session_id}")
        except Exception as e:
            logger.error(f"Error completing archive session: {e}")

    def _log_operation(
        self,
        operation: str,
        original_path: str,
        file_size: int,
        file_hash: Optional[str],
        status: str,
        target_path: Optional[str] = None
    ) -> Optional[int]:
        """
        Log operation to database

        Returns:
            Operation ID if successful, None otherwise
        """
        try:
            with get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO file_operations
                    (operation, original_path, target_path, file_size, file_hash,
                     session_id, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (operation, original_path, target_path, file_size, file_hash,
                      self.session_id, status))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error logging operation: {e}")
            return None

    def _update_operation_status(
        self,
        operation_id: int,
        status: str,
        target_path: Optional[str] = None
    ):
        """Update operation status in database"""
        try:
            with get_connection() as conn:
                if target_path:
                    conn.execute("""
                        UPDATE file_operations
                        SET status = ?, target_path = ?
                        WHERE id = ?
                    """, (status, target_path, operation_id))
                else:
                    conn.execute("""
                        UPDATE file_operations
                        SET status = ?
                        WHERE id = ?
                    """, (status, operation_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating operation status: {e}")

    def rollback(self) -> Dict[str, any]:
        """
        Attempt to rollback operations from this session

        Returns:
            Dict with rollback results
        """
        if self.dry_run:
            return {
                'success': True,
                'message': 'Dry-run mode - no operations to rollback'
            }

        logger.warning(f"Attempting rollback for session {self.session_id}")

        restored = 0
        failed = 0
        errors = []

        # Restore files from operations log (in reverse order)
        for op in reversed(self.operations_log):
            try:
                original_path = Path(op['original_path'])
                archived_path = Path(op['archived_path'])

                if restore_file(archived_path, original_path):
                    restored += 1
                    logger.info(f"Restored: {archived_path} -> {original_path}")
                else:
                    failed += 1
                    errors.append(f"Failed to restore {archived_path}")

            except Exception as e:
                failed += 1
                error_msg = f"Error restoring {op['original_path']}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Update archive session status
        try:
            with get_connection() as conn:
                conn.execute("""
                    UPDATE archive_sessions
                    SET status = 'deleted', notes = 'Rolled back'
                    WHERE session_id = ?
                """, (self.session_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating session status: {e}")

        return {
            'success': (failed == 0),
            'restored': restored,
            'failed': failed,
            'errors': errors
        }


def get_archive_sessions(limit: int = 50) -> List[Dict]:
    """
    Get list of archive sessions

    Args:
        limit: Maximum number of sessions to return

    Returns:
        List of archive session dicts
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute("""
                SELECT session_id, created_at, file_count, total_size,
                       archive_path, status, notes
                FROM archive_sessions
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row['session_id'],
                    'created_at': row['created_at'],
                    'file_count': row['file_count'],
                    'total_size': row['total_size'],
                    'archive_path': row['archive_path'],
                    'status': row['status'],
                    'notes': row['notes']
                })

            return sessions

    except Exception as e:
        logger.error(f"Error getting archive sessions: {e}")
        return []


def restore_from_session(session_id: str) -> Dict[str, any]:
    """
    Restore all files from an archive session

    Args:
        session_id: Archive session ID

    Returns:
        Dict with restore results
    """
    logger.info(f"Restoring from session: {session_id}")

    try:
        with get_connection() as conn:
            # Get all operations from session
            cursor = conn.execute("""
                SELECT id, original_path, target_path
                FROM file_operations
                WHERE session_id = ? AND operation = 'archive' AND status = 'completed'
                ORDER BY id
            """, (session_id,))

            operations = cursor.fetchall()

            if not operations:
                return {
                    'success': False,
                    'error': f"No operations found for session {session_id}"
                }

            restored = 0
            failed = 0
            errors = []

            for op in operations:
                try:
                    original_path = Path(op['original_path'])
                    archived_path = Path(op['target_path'])

                    if not archived_path.exists():
                        errors.append(f"Archived file not found: {archived_path}")
                        failed += 1
                        continue

                    if restore_file(archived_path, original_path):
                        restored += 1

                        # Log restore operation
                        conn.execute("""
                            INSERT INTO file_operations
                            (operation, original_path, target_path, session_id, status)
                            VALUES ('restore', ?, ?, ?, 'completed')
                        """, (str(archived_path), str(original_path), session_id))

                        logger.info(f"Restored: {archived_path} -> {original_path}")
                    else:
                        failed += 1
                        errors.append(f"Failed to restore {archived_path}")

                except Exception as e:
                    failed += 1
                    error_msg = f"Error restoring {op['original_path']}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            # Update session status
            conn.execute("""
                UPDATE archive_sessions
                SET status = 'deleted', notes = ?
                WHERE session_id = ?
            """, (f"Restored: {restored} files", session_id))

            conn.commit()

            return {
                'success': (failed == 0),
                'restored': restored,
                'failed': failed,
                'errors': errors
            }

    except Exception as e:
        logger.error(f"Error restoring session: {e}")
        return {
            'success': False,
            'error': str(e)
        }
