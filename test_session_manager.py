"""
Comprehensive test suite for the Session Manager system.

Tests all functionality including basic session management, expiry logic,
bonus features (persistent and sliding sessions), and edge cases.
"""

import unittest
import time
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
import sys
import logging

# Import from restaurant_management.utils
from restaurant_management.utils.session_manager import (
    SessionManager, 
    PersistentSessionManager, 
    SlidingSessionManager
)

# Set up logging for tests
logging.basicConfig(level=logging.DEBUG)


class TestSessionManager(unittest.TestCase):
    """Test cases for the basic SessionManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.session_manager = SessionManager(expiry_seconds=5)  # 5 second expiry for testing
    
    def test_init_valid_expiry(self):
        """Test SessionManager initialization with valid expiry time."""
        sm = SessionManager(30)
        self.assertEqual(sm.expiry_seconds, 30)
        self.assertEqual(len(sm.sessions), 0)
        self.assertIsInstance(sm.sessions, dict)
    
    def test_init_invalid_expiry(self):
        """Test SessionManager initialization with invalid expiry time."""
        with self.assertRaises(ValueError):
            SessionManager(0)
        
        with self.assertRaises(ValueError):
            SessionManager(-5)
        
        with self.assertRaises(ValueError):
            SessionManager("invalid")
        
        with self.assertRaises(ValueError):
            SessionManager(3.14)  # Float should not be accepted
    
    def test_create_session_valid(self):
        """Test creating a session with valid session ID."""
        session_id = "driver_123"
        self.session_manager.create_session(session_id)
        
        self.assertIn(session_id, self.session_manager.sessions)
        self.assertIsInstance(self.session_manager.sessions[session_id], float)
        # Should be approximately current time
        self.assertAlmostEqual(
            self.session_manager.sessions[session_id], 
            time.time(), 
            delta=1.0
        )
    
    def test_create_session_invalid(self):
        """Test creating a session with invalid session ID."""
        with self.assertRaises(ValueError):
            self.session_manager.create_session("")
        
        with self.assertRaises(ValueError):
            self.session_manager.create_session(None)
        
        with self.assertRaises(ValueError):
            self.session_manager.create_session(123)
        
        with self.assertRaises(ValueError):
            self.session_manager.create_session([])
    
    def test_create_session_overwrite(self):
        """Test creating a session with existing session ID overwrites it."""
        session_id = "rider_456"
        
        # Create first session
        self.session_manager.create_session(session_id)
        first_timestamp = self.session_manager.sessions[session_id]
        
        # Wait a bit and create again
        time.sleep(0.1)
        self.session_manager.create_session(session_id)
        second_timestamp = self.session_manager.sessions[session_id]
        
        # Should be overwritten with new timestamp
        self.assertGreater(second_timestamp, first_timestamp)
    
    def test_is_session_active_valid(self):
        """Test checking active session that exists and is not expired."""
        session_id = "driver_123"
        self.session_manager.create_session(session_id)
        
        # Should be active immediately after creation
        self.assertTrue(self.session_manager.is_session_active(session_id))
    
    def test_is_session_active_nonexistent(self):
        """Test checking session that doesn't exist."""
        self.assertFalse(self.session_manager.is_session_active("nonexistent"))
        self.assertFalse(self.session_manager.is_session_active(""))
        self.assertFalse(self.session_manager.is_session_active(None))
    
    def test_is_session_active_expired(self):
        """Test checking session that has expired."""
        session_id = "driver_123"
        self.session_manager.create_session(session_id)
        
        # Manually set session to be older than expiry time
        self.session_manager.sessions[session_id] = time.time() - 10  # 10 seconds ago
        
        # Should be False and session should be auto-deleted
        self.assertFalse(self.session_manager.is_session_active(session_id))
        self.assertNotIn(session_id, self.session_manager.sessions)
    
    def test_delete_session_existing(self):
        """Test deleting an existing session."""
        session_id = "rider_789"
        self.session_manager.create_session(session_id)
        
        result = self.session_manager.delete_session(session_id)
        
        self.assertEqual(result, "Deleted")
        self.assertNotIn(session_id, self.session_manager.sessions)
    
    def test_delete_session_nonexistent(self):
        """Test deleting a session that doesn't exist."""
        result = self.session_manager.delete_session("nonexistent")
        self.assertEqual(result, "Not Found")
        
        # Test with empty string
        result = self.session_manager.delete_session("")
        self.assertEqual(result, "Not Found")
    
    def test_session_expiry_with_sleep(self):
        """Test session expiry using actual time delays."""
        # Create a session manager with 1 second expiry
        sm = SessionManager(1)
        session_id = "test_expiry"
        
        # Create session
        sm.create_session(session_id)
        self.assertTrue(sm.is_session_active(session_id))
        
        # Wait for expiry
        time.sleep(1.1)  # Wait slightly more than expiry time
        
        # Session should be expired and auto-deleted
        self.assertFalse(sm.is_session_active(session_id))
        self.assertNotIn(session_id, sm.sessions)
    
    def test_multiple_sessions(self):
        """Test managing multiple sessions simultaneously."""
        sessions = ["driver_1", "rider_2", "driver_3"]
        
        # Create multiple sessions
        for session_id in sessions:
            self.session_manager.create_session(session_id)
        
        # All should be active
        for session_id in sessions:
            self.assertTrue(self.session_manager.is_session_active(session_id))
        
        # Delete one session
        result = self.session_manager.delete_session("rider_2")
        self.assertEqual(result, "Deleted")
        
        # Check status
        self.assertTrue(self.session_manager.is_session_active("driver_1"))
        self.assertFalse(self.session_manager.is_session_active("rider_2"))
        self.assertTrue(self.session_manager.is_session_active("driver_3"))
    
    def test_get_active_session_count(self):
        """Test utility method for getting active session count."""
        # Initially no sessions
        self.assertEqual(self.session_manager.get_active_session_count(), 0)
        
        # Create some sessions
        self.session_manager.create_session("driver_1")
        self.session_manager.create_session("rider_2")
        self.assertEqual(self.session_manager.get_active_session_count(), 2)
        
        # Expire one session manually
        self.session_manager.sessions["driver_1"] = time.time() - 10
        
        # Count should automatically clean up and return 1
        self.assertEqual(self.session_manager.get_active_session_count(), 1)
        self.assertNotIn("driver_1", self.session_manager.sessions)
    
    def test_get_session_info(self):
        """Test utility method for getting session information."""
        session_id = "info_test"
        self.session_manager.create_session(session_id)
        
        info = self.session_manager.get_session_info(session_id)
        
        self.assertIsNotNone(info)
        self.assertEqual(info['session_id'], session_id)
        self.assertIn('age_seconds', info)
        self.assertIn('remaining_seconds', info)
        self.assertIn('start_time', info)
        self.assertIn('expires_at', info)
        self.assertTrue(info['remaining_seconds'] > 0)
        self.assertTrue(info['age_seconds'] >= 0)
        
        # Test non-existent session
        self.assertIsNone(self.session_manager.get_session_info("nonexistent"))
        
        # Test expired session
        self.session_manager.sessions[session_id] = time.time() - 10
        self.assertIsNone(self.session_manager.get_session_info(session_id))
    
    def test_cleanup_expired_sessions(self):
        """Test manual cleanup of expired sessions."""
        # Create multiple sessions
        self.session_manager.create_session("active_1")
        self.session_manager.create_session("active_2")
        self.session_manager.create_session("expired_1")
        self.session_manager.create_session("expired_2")
        
        # Manually expire some sessions
        self.session_manager.sessions["expired_1"] = time.time() - 10
        self.session_manager.sessions["expired_2"] = time.time() - 15
        
        # Should clean up 2 expired sessions
        cleaned_count = self.session_manager.cleanup_expired_sessions()
        self.assertEqual(cleaned_count, 2)
        
        # Should have 2 active sessions remaining
        self.assertEqual(len(self.session_manager.sessions), 2)
        self.assertIn("active_1", self.session_manager.sessions)
        self.assertIn("active_2", self.session_manager.sessions)
    
    def test_generate_session_id(self):
        """Test session ID generation utility."""
        session_id = self.session_manager.generate_session_id()
        
        self.assertIsInstance(session_id, str)
        self.assertEqual(len(session_id), 32)  # UUID4 hex should be 32 chars
        
        # Should be unique
        session_id2 = self.session_manager.generate_session_id()
        self.assertNotEqual(session_id, session_id2)
    
    def test_backwards_compatibility(self):
        """Test backwards compatibility with end_session method."""
        session_id = "compat_test"
        self.session_manager.create_session(session_id)
        
        # end_session should return True for existing session
        result = self.session_manager.end_session(session_id)
        self.assertTrue(result)
        self.assertNotIn(session_id, self.session_manager.sessions)
        
        # end_session should return False for non-existent session
        result = self.session_manager.end_session("nonexistent")
        self.assertFalse(result)


class TestPersistentSessionManager(unittest.TestCase):
    """Test cases for the PersistentSessionManager class."""
    
    def setUp(self):
        """Set up test fixtures with temporary file."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.storage_file = self.temp_file.name
        
    def tearDown(self):
        """Clean up temporary file."""
        if os.path.exists(self.storage_file):
            os.unlink(self.storage_file)
    
    def test_persistent_session_creation(self):
        """Test that sessions are persisted to file."""
        psm = PersistentSessionManager(30, self.storage_file)
        psm.create_session("driver_123")
        
        # Verify file was created and contains session
        self.assertTrue(os.path.exists(self.storage_file))
        
        with open(self.storage_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn("driver_123", data)
        
        # Create new instance to test loading
        psm2 = PersistentSessionManager(30, self.storage_file)
        self.assertTrue(psm2.is_session_active("driver_123"))
    
    def test_persistent_session_deletion(self):
        """Test that session deletion is persisted."""
        psm = PersistentSessionManager(30, self.storage_file)
        psm.create_session("rider_456")
        
        # Verify session exists
        self.assertTrue(psm.is_session_active("rider_456"))
        
        # Delete session
        result = psm.delete_session("rider_456")
        self.assertEqual(result, "Deleted")
        
        # Create new instance to test persistence of deletion
        psm2 = PersistentSessionManager(30, self.storage_file)
        self.assertFalse(psm2.is_session_active("rider_456"))
    
    def test_load_expired_sessions(self):
        """Test that expired sessions are cleaned up on load."""
        # Create sessions file with expired session
        expired_time = time.time() - 100  # 100 seconds ago
        sessions_data = {
            "expired_session": expired_time,
            "active_session": time.time()
        }
        
        with open(self.storage_file, 'w') as f:
            json.dump(sessions_data, f)
        
        # Load sessions - expired one should be cleaned up
        psm = PersistentSessionManager(30, self.storage_file)
        
        self.assertFalse(psm.is_session_active("expired_session"))
        self.assertTrue(psm.is_session_active("active_session"))
    
    def test_file_error_handling(self):
        """Test handling of file I/O errors."""
        # Test with invalid file path
        invalid_path = "/invalid/path/sessions.json"
        
        # Should not crash, just log error and continue
        psm = PersistentSessionManager(30, invalid_path)
        self.assertEqual(len(psm.sessions), 0)
        
        # Creating session should still work (just won't persist)
        psm.create_session("test_session")
        self.assertTrue(psm.is_session_active("test_session"))


class TestSlidingSessionManager(unittest.TestCase):
    """Test cases for the SlidingSessionManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sliding_sm = SlidingSessionManager(2)  # 2 second expiry
    
    def test_sliding_expiration(self):
        """Test that sessions are refreshed when accessed."""
        session_id = "sliding_driver"
        self.sliding_sm.create_session(session_id)
        
        # Get initial timestamp
        initial_time = self.sliding_sm.sessions[session_id]
        
        # Wait half the expiry time
        time.sleep(1)
        
        # Access the session (should refresh it)
        self.assertTrue(self.sliding_sm.is_session_active(session_id))
        
        # Timestamp should be updated
        refreshed_time = self.sliding_sm.sessions[session_id]
        self.assertGreater(refreshed_time, initial_time)
        
        # Wait another half expiry time (total would exceed original expiry)
        time.sleep(1)
        
        # Should still be active due to sliding expiration
        self.assertTrue(self.sliding_sm.is_session_active(session_id))
    
    def test_sliding_expiration_no_access(self):
        """Test that unused sessions still expire."""
        session_id = "unused_driver"
        self.sliding_sm.create_session(session_id)
        
        # Wait for full expiry without accessing
        time.sleep(2.1)
        
        # Should be expired
        self.assertFalse(self.sliding_sm.is_session_active(session_id))
        self.assertNotIn(session_id, self.sliding_sm.sessions)
    
    def test_multiple_sliding_sessions(self):
        """Test multiple sessions with sliding expiration."""
        sessions = ["driver_1", "driver_2", "driver_3"]
        
        # Create all sessions
        for session_id in sessions:
            self.sliding_sm.create_session(session_id)
        
        # Wait a bit
        time.sleep(1)
        
        # Access only two sessions
        self.assertTrue(self.sliding_sm.is_session_active("driver_1"))
        self.assertTrue(self.sliding_sm.is_session_active("driver_2"))
        # Don't access driver_3
        
        # Wait until driver_3 should expire
        time.sleep(1.1)
        
        # driver_1 and driver_2 should still be active (refreshed)
        # driver_3 should be expired (not refreshed)
        self.assertTrue(self.sliding_sm.is_session_active("driver_1"))
        self.assertTrue(self.sliding_sm.is_session_active("driver_2"))
        self.assertFalse(self.sliding_sm.is_session_active("driver_3"))


class TestSessionManagerIntegration(unittest.TestCase):
    """Integration tests for real-world scenarios."""
    
    def test_ride_sharing_workflow(self):
        """Test a complete ride-sharing workflow."""
        # Create session manager for 30-second sessions
        sm = SessionManager(30)
        
        # Driver logs in
        driver_id = "driver_abc123"
        sm.create_session(driver_id)
        self.assertTrue(sm.is_session_active(driver_id))
        
        # Rider logs in
        rider_id = "rider_xyz789"
        sm.create_session(rider_id)
        self.assertTrue(sm.is_session_active(rider_id))
        
        # Both should be active
        self.assertEqual(sm.get_active_session_count(), 2)
        
        # Driver completes ride and logs out
        result = sm.delete_session(driver_id)
        self.assertEqual(result, "Deleted")
        
        # Only rider should be active
        self.assertEqual(sm.get_active_session_count(), 1)
        self.assertFalse(sm.is_session_active(driver_id))
        self.assertTrue(sm.is_session_active(rider_id))
        
        # Rider finishes and app closes (session expires naturally)
        sm.sessions[rider_id] = time.time() - 35  # Simulate 35 seconds ago
        self.assertFalse(sm.is_session_active(rider_id))
        self.assertEqual(sm.get_active_session_count(), 0)
    
    def test_delivery_platform_workflow(self):
        """Test a food delivery platform workflow with sliding sessions."""
        # Use sliding sessions for delivery drivers who need to stay online
        sm = SlidingSessionManager(10)  # 10 second expiry
        
        # Delivery driver starts shift
        driver_id = "delivery_driver_001"
        sm.create_session(driver_id)
        
        # Simulate periodic app activity (GPS updates, order checks)
        for i in range(5):
            time.sleep(0.5)  # 0.5 second intervals
            
            # Each check refreshes the session
            active = sm.is_session_active(driver_id)
            self.assertTrue(active)
        
        # Driver should still be active after 2.5 seconds due to refreshing
        self.assertTrue(sm.is_session_active(driver_id))
        
        # If driver stops using app, session should eventually expire
        time.sleep(10.1)  # Wait longer than expiry time
        self.assertFalse(sm.is_session_active(driver_id))


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)