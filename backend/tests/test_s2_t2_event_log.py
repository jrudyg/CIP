"""
Event Log Tests — P7.S2.T2
Validates event persistence, replay, and TTL management.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from event_log.models import EventLogEntry
from event_log.repository import EventLogRepository


class TestEventLogEntry(unittest.TestCase):
    """Test EventLogEntry dataclass."""

    def test_create_factory(self):
        """Factory creates valid entry."""
        entry = EventLogEntry.create(
            session_id="sess-001",
            sequence=1,
            event_type="test_event",
            payload={"data": "value"},
        )
        self.assertEqual(entry.session_id, "sess-001")
        self.assertEqual(entry.sequence, 1)
        self.assertEqual(entry.event_type, "test_event")
        self.assertIsNotNone(entry.event_id)
        self.assertIsNotNone(entry.expires_at)

    def test_default_ttl(self):
        """Default TTL is 1 hour."""
        entry = EventLogEntry.create(
            session_id="sess-001",
            sequence=1,
            event_type="test",
        )
        delta = entry.expires_at - entry.created_at
        self.assertAlmostEqual(delta.total_seconds(), 3600, delta=1)

    def test_custom_ttl(self):
        """Custom TTL is respected."""
        entry = EventLogEntry.create(
            session_id="sess-001",
            sequence=1,
            event_type="test",
            ttl_hours=2.5,
        )
        delta = entry.expires_at - entry.created_at
        self.assertAlmostEqual(delta.total_seconds(), 9000, delta=1)

    def test_is_expired(self):
        """Expiration check works."""
        # Not expired
        entry = EventLogEntry.create(
            session_id="sess-001",
            sequence=1,
            event_type="test",
            ttl_hours=1.0,
        )
        self.assertFalse(entry.is_expired())

        # Expired (set expires_at in past)
        entry.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        self.assertTrue(entry.is_expired())

    def test_serialization(self):
        """To/from dict round-trips correctly."""
        entry = EventLogEntry.create(
            session_id="sess-001",
            sequence=42,
            event_type="test_event",
            payload={"key": "value"},
        )
        
        data = entry.to_dict()
        restored = EventLogEntry.from_dict(data)
        
        self.assertEqual(restored.event_id, entry.event_id)
        self.assertEqual(restored.sequence, entry.sequence)
        self.assertEqual(restored.payload, entry.payload)

    def test_to_sse_data(self):
        """SSE data format is correct."""
        entry = EventLogEntry.create(
            session_id="sess-001",
            sequence=10,
            event_type="scroll_sync",
            payload={"position": 0.5},
        )
        
        sse_data = entry.to_sse_data()
        
        self.assertEqual(sse_data["event_id"], entry.event_id)
        self.assertEqual(sse_data["sequence"], 10)
        self.assertEqual(sse_data["event_type"], "scroll_sync")
        self.assertEqual(sse_data["payload"]["position"], 0.5)


class TestEventLogRepository(unittest.TestCase):
    """Test repository persistence and replay."""

    def setUp(self):
        """Create temp database for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_events.db")
        self.repo = EventLogRepository(
            db_path=self.db_path,
            max_events_per_session=10,  # Low limit for testing
        )

    def tearDown(self):
        """Cleanup temp database."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_append_event(self):
        """Event appends to log."""
        entry = EventLogEntry.create(
            session_id="sess-001",
            sequence=1,
            event_type="test",
        )
        result = self.repo.append(entry)
        self.assertTrue(result)

    def test_duplicate_event_id_rejected(self):
        """Duplicate event_id is rejected."""
        entry = EventLogEntry.create(
            session_id="sess-001",
            sequence=1,
            event_type="test",
        )
        self.repo.append(entry)
        
        # Try same event_id again
        result = self.repo.append(entry)
        self.assertFalse(result)

    def test_get_events_from_sequence(self):
        """Retrieves events from sequence number."""
        # Insert 5 events
        for i in range(1, 6):
            entry = EventLogEntry.create(
                session_id="sess-001",
                sequence=i,
                event_type="test",
            )
            self.repo.append(entry, enforce_max=False)

        # Get from sequence 3
        events = self.repo.get_events_from_sequence("sess-001", from_seq=3)
        
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].sequence, 3)
        self.assertEqual(events[2].sequence, 5)

    def test_get_events_in_range(self):
        """Retrieves events in range."""
        for i in range(1, 11):
            entry = EventLogEntry.create(
                session_id="sess-001",
                sequence=i,
                event_type="test",
            )
            self.repo.append(entry, enforce_max=False)

        events = self.repo.get_events_in_range("sess-001", from_seq=3, to_seq=7)
        
        self.assertEqual(len(events), 5)
        sequences = [e.sequence for e in events]
        self.assertEqual(sequences, [3, 4, 5, 6, 7])

    def test_get_latest_sequence(self):
        """Gets latest sequence number."""
        for i in [1, 5, 3, 10, 7]:
            entry = EventLogEntry.create(
                session_id="sess-001",
                sequence=i,
                event_type="test",
            )
            self.repo.append(entry, enforce_max=False)

        latest = self.repo.get_latest_sequence("sess-001")
        self.assertEqual(latest, 10)

    def test_max_events_enforcement(self):
        """Enforces max events per session (FIFO)."""
        # Max is 10, insert 15
        for i in range(1, 16):
            entry = EventLogEntry.create(
                session_id="sess-001",
                sequence=i,
                event_type="test",
            )
            self.repo.append(entry, enforce_max=True)

        # Should have 10 events, oldest pruned
        count = self.repo.get_event_count("sess-001")
        self.assertEqual(count, 10)

        # Oldest should be sequence 6 (1-5 pruned)
        events = self.repo.get_events_from_sequence("sess-001", from_seq=1)
        self.assertEqual(events[0].sequence, 6)

    def test_detect_gaps(self):
        """Detects sequence gaps."""
        # Insert sequences 1, 2, 5, 6, 10 (gaps at 3-4, 7-9)
        for seq in [1, 2, 5, 6, 10]:
            entry = EventLogEntry.create(
                session_id="sess-001",
                sequence=seq,
                event_type="test",
            )
            self.repo.append(entry, enforce_max=False)

        gaps = self.repo.detect_gaps("sess-001", from_seq=1, to_seq=10)
        
        self.assertEqual(len(gaps), 2)
        self.assertEqual(gaps[0], (3, 4))
        self.assertEqual(gaps[1], (7, 9))

    def test_prune_expired(self):
        """Prunes expired events."""
        # Create expired entry
        entry = EventLogEntry.create(
            session_id="sess-001",
            sequence=1,
            event_type="test",
            ttl_hours=0,  # Expires immediately
        )
        entry.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        self.repo.append(entry, enforce_max=False)

        # Create non-expired entry
        entry2 = EventLogEntry.create(
            session_id="sess-001",
            sequence=2,
            event_type="test",
            ttl_hours=1.0,
        )
        self.repo.append(entry2, enforce_max=False)

        # Prune
        pruned = self.repo.prune_expired()
        self.assertEqual(pruned, 1)

        # Verify only non-expired remains
        count = self.repo.get_event_count("sess-001")
        self.assertEqual(count, 1)

    def test_batch_append(self):
        """Batch append works."""
        entries = [
            EventLogEntry.create(
                session_id="sess-001",
                sequence=i,
                event_type="test",
            )
            for i in range(1, 6)
        ]

        count = self.repo.append_batch(entries)
        self.assertEqual(count, 5)

        stored_count = self.repo.get_event_count("sess-001")
        self.assertEqual(stored_count, 5)

    def test_delete_session_events(self):
        """Deletes all events for session."""
        for i in range(1, 6):
            entry = EventLogEntry.create(
                session_id="sess-001",
                sequence=i,
                event_type="test",
            )
            self.repo.append(entry, enforce_max=False)

        deleted = self.repo.delete_session_events("sess-001")
        self.assertEqual(deleted, 5)

        count = self.repo.get_event_count("sess-001")
        self.assertEqual(count, 0)

    def test_stats(self):
        """Repository stats are accurate."""
        for i in range(1, 4):
            entry = EventLogEntry.create(
                session_id="sess-001",
                sequence=i,
                event_type="test",
            )
            self.repo.append(entry, enforce_max=False)

        stats = self.repo.get_stats()
        self.assertEqual(stats["total_events"], 3)
        self.assertEqual(stats["sessions_with_events"], 1)


def run_tests():
    """Run all S2.T2 tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestEventLogEntry))
    suite.addTests(loader.loadTestsFromTestCase(TestEventLogRepository))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
