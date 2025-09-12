import time

class SimpleRateLimiter:
    """
    Simulates a basic rate limiter for user requests.
    Allows up to `max_requests` per user in a rolling `window_seconds` time window.
    Methods:
        allow_request(user_id): Returns True if request is allowed, False if rate-limited.
    """
    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests = {}  # user_id -> list of request timestamps

    def allow_request(self, user_id):
        """
        Checks if the user can make a request based on rate limits.
        Args:
            user_id: Unique identifier for the user/client.
        Returns:
            True if request is allowed, False if rate-limited.
        """
        now = time.time()
        window_start = now - self.window_seconds
        requests = self.user_requests.get(user_id, [])

        # Remove requests outside the window
        requests = [t for t in requests if t > window_start]

        if len(requests) < self.max_requests:
            requests.append(now)
            self.user_requests[user_id] = requests
            return True  # Allow request
        else:
            self.user_requests[user_id] = requests
            return False  # Block request

    def cleanup(self):
        """
        Removes users with no recent requests from the user_requests dictionary.
        Call this periodically to prevent memory leaks in long-running applications.
        """
        now = time.time()
        window_start = now - self.window_seconds
        to_delete = [user_id for user_id, requests in self.user_requests.items()
                     if not any(t > window_start for t in requests)]
        for user_id in to_delete:
            del self.user_requests[user_id]
