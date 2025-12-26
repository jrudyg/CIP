"""
Session State Tests — P7.S2.T1
Validates session and SSE connection state management.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from session_state.models import (
    SSEConnectionStatus,
    SSEConnectionInfo,
    SessionSSEState,
)
from session_state.repository import SessionStateRepository


class TestSSEConnectionInfo(unittest.TestCase):
    """Test SSEConnectionInfo dataclass."""

    def test_default_creation(self):
        """Connection creates with defaults."""
        conn = SSEConnectionInfo()
        self.assertIsNotNone(conn.connection_id)
        self.assertEqual(conn.status, SSEConnectionStatus.INACTIVE)
        self.assertEqual(conn.events_sent, 0)

    def test_mark_connected(self):
        """Mark connected updates status and timestamps."""
        conn = SSEConnectionInfo()
        conn.mark_connected()
        self.assertEqual(conn.status, SSEConnectionStatus.ACTIVE)
        self.assertIsNotNone(conn.connected_at)

    def test_mark_event_sent(self):
        """Event sent updates sequence and count."""
        conn = SSEConnectionInfo()
        conn.mark_event_sent(42)
        self.assertEqual(conn.last_sequence, 42)
        self.assertEqual(conn.events_sent, 1)

    def test_serialization(self):
        """To/from dict round-trips correctly."""
        conn = SSEConnectionInfo()
        conn.mark_connected()
        conn.mark_event_sent(10)
        
        data = conn.to_dict()
        restored = SSEConnectionInfo.from_dict(data)
        
        self.assertEqual(restored.connection_id, conn.connection_id)
        self.assertEqual(restored.status, conn.status)
        self.assertEqual(restored.last_sequence, conn.last_sequence)


class TestSessionSSEState(unittest.TestCase):
    """Test SessionSSEState with multi-connection support."""

    def test_max_5_connections(self):
        """Enforces max 5 connections per session."""
        session = SessionSSEState(session_id="test-session")
        
        # Add 5 connections
        for i in range(5):
            conn = SSEConnectionInfo()
            conn.mark_connected()
            result = session.add_connection(conn)
            self.assertTrue(result, f"Connection {i+1} should be added")
        
        # 6th should fail
        conn = SSEConnectionInfo()
        conn.mark_connected()
        result = session.add_connection(conn)
        self.assertFalse(result, "6th connection should be rejected")

    def test_remove_connection(self):
        """Connection removal works correctly."""
        session = SessionSSEState(session_id="test-session")
        conn = SSEConnectionInfo()
        session.add_connection(conn)
        
        result = session.remove_connection(conn.connection_id)
        self.assertTrue(result)
        self.assertEqual(len(session.sse_connections), 0)

    def test_cleanup_terminated(self):
        """Terminated connections are cleaned on add."""
        session = SessionSSEState(session_id="test-session")
        
        # Add terminated connection
        conn1 = SSEConnectionInfo()
        conn1.mark_terminated()
        session.sse_connections.append(conn1)
        
        # Add new connection triggers cleanup
        conn2 = SSEConnectionInfo()
        session.add_connection(conn2)
        
        # Only active connection remains
        self.assertEqual(len(session.sse_connections), 1)
        self.assertEqual(session.sse_connections[0].connection_id, conn2.connection_id)

    def test_get_active_connections(self):
        """Active connections filter works."""
        session = SessionSSEState(session_id="test-session")
        
        # Add mixed status connections
        active = SSEConnectionInfo()
        active.mark_connected()
        session.sse_connections.append(active)
        
        inactive = SSEConnectionInfo()
        session.sse_connections.append(inactive)
        
        actives = session.get_active_connections()
        self.assertEqual(len(actives), 1)
        self.assertEqual(actives[0].status, SSEConnectionStatus.ACTIVE)


class TestSessionStateRepository(unittest.TestCase):
    """Test repository persistence."""

    def setUp(self):
        """Create temp database for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_sessions.db")
        self.repo = SessionStateRepository(self.db_path)

    def tearDown(self):
        """Cleanup temp database."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_session(self):
        """Session creation persists to DB."""
        session = self.repo.create_session("sess-001", "user-123")
        self.assertEqual(session.session_id, "sess-001")
        self.assertEqual(session.user_id, "user-123")

    def test_get_session(self):
        """Session retrieval loads from DB."""
        self.repo.create_session("sess-002")
        loaded = self.repo.get_session("sess-002")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.session_id, "sess-002")

    def test_get_or_create(self):
        """Get or create handles both cases."""
        # Create new
        s1 = self.repo.get_or_create_session("sess-003")
        self.assertIsNotNone(s1)
        
        # Get existing
        s2 = self.repo.get_or_create_session("sess-003")
        self.assertEqual(s1.session_id, s2.session_id)

    def test_save_with_connections(self):
        """Session saves with SSE connections."""
        session = SessionSSEState(session_id="sess-004")
        conn = SSEConnectionInfo()
        conn.mark_connected()
        session.add_connection(conn)
        
        self.repo.save_session(session)
        
        loaded = self.repo.get_session("sess-004")
        self.assertEqual(len(loaded.sse_connections), 1)
        self.assertEqual(loaded.sse_connections[0].status, SSEConnectionStatus.ACTIVE)

    def test_update_connection_status(self):
        """Connection status updates persist."""
        session = SessionSSEState(session_id="sess-005")
        conn = SSEConnectionInfo()
        conn.mark_connected()
        session.add_connection(conn)
        self.repo.save_session(session)
        
        # Update status
        result = self.repo.update_connection_status(
            conn.connection_id,
            SSEConnectionStatus.TERMINATED
        )
        self.assertTrue(result)
        
        # Verify
        loaded = self.repo.get_session("sess-005")
        self.assertEqual(
            loaded.sse_connections[0].status,
            SSEConnectionStatus.TERMINATED
        )

    def test_delete_session(self):
        """Session deletion removes session and connections."""
        session = SessionSSEState(session_id="sess-006")
        conn = SSEConnectionInfo()
        session.add_connection(conn)
        self.repo.save_session(session)
        
        result = self.repo.delete_session("sess-006")
        self.assertTrue(result)
        
        loaded = self.repo.get_session("sess-006")
        self.assertIsNone(loaded)

    def test_stats(self):
        """Repository stats are accurate."""
        self.repo.create_session("sess-007")
        session = self.repo.get_session("sess-007")
        conn = SSEConnectionInfo()
        conn.mark_connected()
        session.add_connection(conn)
        self.repo.save_session(session)
        
        stats = self.repo.get_stats()
        self.assertEqual(stats["total_sessions"], 1)
        self.assertEqual(stats["total_connections"], 1)
        self.assertEqual(stats["active_connections"], 1)


def run_tests():
    """Run all S2.T1 tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestSSEConnectionInfo))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionSSEState))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionStateRepository))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
