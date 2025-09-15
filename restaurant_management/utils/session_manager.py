import time
import uuid

class SessionManager:
    """
    Simulates session expiry management using in-memory storage.
    
    Session IDs are generated as 32-character hex strings using uuid.uuid4().hex, which closely matches Django's default session key format. This approach provides strong randomness and security, making it suitable for authentication simulation.

    Args:
        expiry_seconds (int): Lifetime of each session in seconds.
    
    Attributes:
        expiry_seconds (int): Session lifetime in seconds.
        _sessions (dict): Maps session_id to expiry timestamp.
    """
    def __init__(self, expiry_seconds=60):
        if not isinstance(expiry_seconds, int) or expiry_seconds <= 0:
            raise ValueError("expiry_seconds must be a positive integer")
        self.expiry_seconds = expiry_seconds
        self._sessions = {}

    def create_session(self):
        """
        Creates a new session with a unique 32-character hex ID and sets its expiry.
        
        Returns:
            str: The session ID.
        """
        session_id = uuid.uuid4().hex
        expiry = time.time() + self.expiry_seconds
        self._sessions[session_id] = expiry
        return session_id

    def is_session_active(self, session_id):
        """
        Checks if the session is active (not expired). Automatically deletes expired sessions.
        
        Args:
            session_id (str): The session ID to validate.
        Returns:
            bool: True if session is active, False otherwise.
        """
        self._cleanup_expired()
        expiry = self._sessions.get(session_id)
        if expiry is None:
            return False
        return True

    def _cleanup_expired(self):
        """
        Removes all expired sessions from the internal session store.
        """
        now = time.time()
        expired = (sid for sid, exp in self._sessions.items() if exp < now)
        for sid in expired:
            del self._sessions[sid]
