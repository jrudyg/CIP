"""
Event Log Module — P7.S2

Provides event persistence for replay and audit.
"""

from .models import EventLogEntry
from .repository import (
    EventLogRepository,
    get_event_log_repository,
)

__all__ = [
    "EventLogEntry",
    "EventLogRepository",
    "get_event_log_repository",
]
