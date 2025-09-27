"""
Enhanced Session Manager for Ride-Sharing/Delivery Platform

This module implements a comprehensive session management system designed for
understanding session handling in stateless environments. Perfect for
ride-sharing, food delivery, or any real-time application requiring
user session management with expiration.

Features:
- In-memory session storage with timestamp tracking  
- Automatic session expiration and cleanup
- Manual session deletion (logout scenarios)
- Bonus: Sliding expiration and persistent storage options
"""

import time
import uuid
import json
import os
from typing import Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """
    A lightweight session manager for handling user sessions with expiration.
    
    This class provides session management functionality for ride-sharing/delivery platforms:
    - Creating sessions with automatic timestamps using time.time()
    - Validating session activity based on expiration time
    - Automatic cleanup of expired sessions  
    - Manual session deletion for logout scenarios
    
    Perfect for understanding session management in ride-sharing platforms
    where drivers and riders need to maintain active sessions.
    
    Args:
        expiry_seconds (int): How long a session should remain active in seconds
    
    Attributes:
        expiry_seconds (int): Session lifetime in seconds
        sessions (dict): Maps session_id to creation timestamp (using time.time())
    
    Example:
        >>> sm = SessionManager(expiry_seconds=1800)  # 30 minute sessions
        >>> sm.create_session("driver_123")
        >>> sm.is_session_active("driver_123")  # True
        >>> sm.delete_session("driver_123")     # "Deleted"
    """
    
    def __init__(self, expiry_seconds: Union[int, float]):
        """
        Initialize the session manager.
        
        Args:
            expiry_seconds (Union[int, float]): How long a session should remain active in seconds
            
        Raises:
            ValueError: If expiry_seconds is not a positive number or contains fractional values
        """
        if not isinstance(expiry_seconds, (int, float)) or expiry_seconds <= 0 or expiry_seconds != int(expiry_seconds):
            raise ValueError("expiry_seconds must be a positive integer or whole number float")
        
        self.expiry_seconds = expiry_seconds
        self.sessions: Dict[str, float] = {}  # Maps session_id to creation timestamp
        
        logger.info(f"SessionManager initialized with {expiry_seconds}s expiry")

    def create_session(self, session_id: str) -> None:
        """
        Create a new session with the current timestamp.
        
        This simulates what happens when a user (driver or rider) logs in
        to the ride-sharing platform. Uses time.time() as specified in requirements.
        
        Args:
            session_id (str): Unique identifier for the session
            
        Raises:
            ValueError: If session_id is not a non-empty string
        """
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id must be a non-empty string")
        
        current_time = time.time()
        self.sessions[session_id] = current_time
        
        logger.info(f"Session created: {session_id} at {current_time}")
    
    def generate_session_id(self) -> str:
        """
        Generate a unique session ID (utility method for backwards compatibility).
        
        Returns:
            str: Unique 32-character hex session ID
        """
        return uuid.uuid4().hex

    def is_session_active(self, session_id: str) -> bool:
        """
        Check if a session is still active based on expiration time.
        
        This method automatically removes expired sessions to keep the
        sessions dictionary clean. Perfect for validating if a driver
        or rider's session is still valid during API requests.
        Uses time.time() as specified in requirements.
        
        Args:
            session_id (str): The session ID to check
        
        Returns:
            bool: True if session exists and is not expired, False otherwise
        """
        if not isinstance(session_id, str) or not session_id or session_id not in self.sessions:
            logger.debug(f"Session not found: {session_id}")
            return False
        
        current_time = time.time()
        session_start_time = self.sessions[session_id]
        
        # Check if session has expired
        if current_time - session_start_time > self.expiry_seconds:
            logger.info(f"Session expired: {session_id} (age: {current_time - session_start_time:.2f}s)")
            # Automatically delete expired session
            del self.sessions[session_id]
            return False
        
        logger.debug(f"Session active: {session_id} (age: {current_time - session_start_time:.2f}s)")
        return True

    def delete_session(self, session_id: str) -> str:
        """
        Manually delete a session.
        
        This simulates manual logout or force logout scenarios in a
        ride-sharing app (e.g., when a driver goes offline).
        Returns strings as specified in requirements.
        
        Args:
            session_id (str): The session ID to delete
        
        Returns:
            str: "Deleted" if session was found and removed, "Not Found" otherwise
        """
        if not isinstance(session_id, str):
            logger.debug(f"Session not found for deletion: {session_id}")
            return "Not Found"
        
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session manually deleted: {session_id}")
            return "Deleted"
        else:
            logger.debug(f"Session not found for deletion: {session_id}")
            return "Not Found"
    
    def end_session(self, session_id: str) -> bool:
        """
        Backwards compatibility method for existing code.
        
        Args:
            session_id (str): The session ID to end
        
        Returns:
            bool: True if session was ended, False if not found
        """
        return self.delete_session(session_id) == "Deleted"

    def get_active_session_count(self) -> int:
        """
        Get the number of currently active sessions.
        
        This utility method also performs cleanup of expired sessions.
        Useful for monitoring how many drivers/riders are currently online.
        
        Returns:
            int: Number of active sessions
        """
        # Clean up expired sessions first
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, start_time in self.sessions.items()
            if current_time - start_time > self.expiry_seconds
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.debug(f"Auto-cleaned expired session: {session_id}")
        
        return len(self.sessions)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Union[str, float, int]]]:
        """
        Get detailed information about a session.
        
        Useful for debugging or providing session status to users.
        
        Args:
            session_id (str): The session ID to get info for
        
        Returns:
            Optional[Dict]: Session info including age and remaining time, or None if not found
        """
        if not self.is_session_active(session_id):
            return None
        
        current_time = time.time()
        start_time = self.sessions[session_id]
        age = current_time - start_time
        remaining = self.expiry_seconds - age
        
        return {
            'session_id': session_id,
            'start_time': start_time,
            'age_seconds': round(age, 2),
            'remaining_seconds': round(remaining, 2),
            'expires_at': start_time + self.expiry_seconds
        }
    
    def cleanup_expired_sessions(self) -> int:
        """
        Manually trigger cleanup of expired sessions.
        
        Returns:
            int: Number of sessions that were cleaned up
        """
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, start_time in self.sessions.items()
            if current_time - start_time > self.expiry_seconds
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
        
        return len(expired_sessions)


class PersistentSessionManager(SessionManager):
    """
    Extended session manager that persists sessions to a file.
    
    Bonus implementation that saves sessions to disk for persistence
    across application restarts. Perfect for production environments
    where you don't want users to lose their sessions during deployments.
    """
    
    def __init__(self, expiry_seconds: int, storage_file: str = "sessions.json"):
        """
        Initialize persistent session manager.
        
        Args:
            expiry_seconds (int): Session expiry time in seconds
            storage_file (str): Path to file for storing sessions
        """
        super().__init__(expiry_seconds)
        self.storage_file = storage_file
        self._load_sessions()
    
    def _load_sessions(self) -> None:
        """Load sessions from storage file."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    self.sessions = json.load(f)
                logger.info(f"Loaded {len(self.sessions)} sessions from {self.storage_file}")
                # Clean up any sessions that expired while app was down
                self.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            self.sessions = {}
    
    def _save_sessions(self) -> None:
        """Save sessions to storage file."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
            logger.debug(f"Saved {len(self.sessions)} sessions to {self.storage_file}")
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def create_session(self, session_id: str) -> None:
        """Create session and persist to file."""
        super().create_session(session_id)
        self._save_sessions()
    
    def delete_session(self, session_id: str) -> str:
        """Delete session and update persistent storage."""
        result = super().delete_session(session_id)
        if result == "Deleted":
            self._save_sessions()
        return result


class SlidingSessionManager(SessionManager):
    """
    Session manager with sliding expiration (bonus challenge).
    
    Sessions are refreshed each time they're accessed, extending their lifetime.
    Perfect for ride-sharing apps where active drivers should stay logged in
    as long as they're actively using the app.
    """
    
    def is_session_active(self, session_id: str) -> bool:
        """
        Check if session is active and refresh its expiration time.
        
        This implements "sliding expiration" where each access to the session
        resets the expiration timer. Great for keeping active drivers online.
        
        Args:
            session_id (str): The session ID to check
        
        Returns:
            bool: True if session exists and is refreshed, False if expired/not found
        """
        if not isinstance(session_id, str) or not session_id or session_id not in self.sessions:
            return False
        
        current_time = time.time()
        session_start_time = self.sessions[session_id]
        
        # Check if session has expired
        if current_time - session_start_time > self.expiry_seconds:
            logger.info(f"Sliding session expired: {session_id}")
            del self.sessions[session_id]
            return False
        
        # Refresh the session timestamp (sliding expiration)
        self.sessions[session_id] = current_time
        logger.debug(f"Sliding session refreshed: {session_id}")
        return True
