"""
CIP Log Parser

Shared utilities for parsing CIP log files.
"""

import re
import os
import time
import threading
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Callable, Iterator

try:
    from .config import LOG_PATTERN, LOG_FILES, COLORS
except ImportError:
    from config import LOG_PATTERN, LOG_FILES, COLORS


class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_string(cls, level: str) -> "LogLevel":
        """Convert string to LogLevel."""
        try:
            return cls[level.upper()]
        except KeyError:
            return cls.INFO

    def __ge__(self, other):
        order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        return order.index(self.value) >= order.index(other.value)

    def __gt__(self, other):
        order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        return order.index(self.value) > order.index(other.value)


@dataclass
class LogEntry:
    """Parsed log entry."""
    timestamp: datetime
    logger_name: str
    level: LogLevel
    filename: Optional[str]
    line_number: Optional[int]
    message: str
    raw_line: str

    def colored(self, use_color: bool = True) -> str:
        """Return colored string representation."""
        if not use_color:
            return self.raw_line.rstrip()

        color = COLORS.get(self.level.value, COLORS["RESET"])
        reset = COLORS["RESET"]
        dim = COLORS["DIM"]

        ts = self.timestamp.strftime("%H:%M:%S")
        level = f"{color}{self.level.value:8}{reset}"
        logger = f"{dim}{self.logger_name[:20]:20}{reset}"

        return f"{dim}{ts}{reset} {level} {logger} {self.message}"


class LogParser:
    """Parse CIP log format."""

    def __init__(self):
        self.pattern = re.compile(LOG_PATTERN)

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """Parse a single log line."""
        line = line.strip()
        if not line:
            return None

        match = self.pattern.match(line)
        if not match:
            # Return unparsed line as INFO
            return LogEntry(
                timestamp=datetime.now(),
                logger_name="unknown",
                level=LogLevel.INFO,
                filename=None,
                line_number=None,
                message=line,
                raw_line=line,
            )

        groups = match.groups()
        ts_str = groups[0]

        # Parse timestamp
        try:
            if ',' in ts_str:
                timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")
            else:
                timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            timestamp = datetime.now()

        return LogEntry(
            timestamp=timestamp,
            logger_name=groups[1],
            level=LogLevel.from_string(groups[2]),
            filename=groups[3],
            line_number=int(groups[4]) if groups[4] else None,
            message=groups[5],
            raw_line=line,
        )

    def parse_file(
        self,
        filepath: Path,
        limit: int = 100,
        min_level: LogLevel = LogLevel.DEBUG,
        offset: int = 0,
    ) -> List[LogEntry]:
        """Parse last N lines from a log file."""
        entries = []

        if not filepath.exists():
            return entries

        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                # Read all lines and get last N
                lines = f.readlines()
                start = max(0, len(lines) - limit - offset)
                end = len(lines) - offset if offset > 0 else len(lines)

                for line in lines[start:end]:
                    entry = self.parse_line(line)
                    if entry and entry.level >= min_level:
                        entries.append(entry)
        except Exception as e:
            print(f"Error reading log file: {e}")

        return entries

    def tail_file(
        self,
        filepath: Path,
        callback: Callable[[LogEntry], None],
        min_level: LogLevel = LogLevel.DEBUG,
    ) -> "LogTailer":
        """Start tailing a log file."""
        return LogTailer(filepath, callback, self, min_level)


class LogTailer:
    """Real-time log file tailing."""

    def __init__(
        self,
        filepath: Path,
        callback: Callable[[LogEntry], None],
        parser: LogParser,
        min_level: LogLevel = LogLevel.DEBUG,
    ):
        self.filepath = filepath
        self.callback = callback
        self.parser = parser
        self.min_level = min_level
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_pos = 0

    def start(self):
        """Start tailing the log file."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._tail_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop tailing the log file."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _tail_loop(self):
        """Main tailing loop."""
        # Start from end of file
        if self.filepath.exists():
            self._file_pos = self.filepath.stat().st_size

        while self._running:
            try:
                if not self.filepath.exists():
                    time.sleep(1)
                    continue

                current_size = self.filepath.stat().st_size

                # File was truncated/rotated
                if current_size < self._file_pos:
                    self._file_pos = 0

                if current_size > self._file_pos:
                    with open(self.filepath, 'r', encoding='utf-8', errors='replace') as f:
                        f.seek(self._file_pos)
                        for line in f:
                            entry = self.parser.parse_line(line)
                            if entry and entry.level >= self.min_level:
                                self.callback(entry)
                        self._file_pos = f.tell()

                time.sleep(0.5)

            except Exception as e:
                print(f"Tail error: {e}")
                time.sleep(1)


def get_recent_errors(limit: int = 20) -> List[LogEntry]:
    """Get recent ERROR and CRITICAL entries from error.log."""
    parser = LogParser()
    error_log = LOG_FILES.get("error")
    if error_log:
        return parser.parse_file(error_log, limit=limit, min_level=LogLevel.ERROR)
    return []


def get_recent_api_calls(limit: int = 50) -> List[LogEntry]:
    """Get recent API call entries from api.log."""
    parser = LogParser()
    api_log = LOG_FILES.get("api")
    if api_log:
        return parser.parse_file(api_log, limit=limit)
    return []


def format_log_entries(
    entries: List[LogEntry],
    use_color: bool = True,
    max_width: int = 120,
) -> str:
    """Format log entries for display."""
    lines = []
    for entry in entries:
        line = entry.colored(use_color)
        if len(line) > max_width:
            line = line[:max_width-3] + "..."
        lines.append(line)
    return "\n".join(lines)
