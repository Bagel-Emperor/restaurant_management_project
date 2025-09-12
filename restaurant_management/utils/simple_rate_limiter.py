import time

class SimpleRateLimiter:
    """
    Simulates a basic rate limiter for user requests.
    Allows up to `max_requests` per user in a rolling `window_seconds` time window.

    Args:
        max_requests (int): Maximum allowed requests per user in the time window.
        window_seconds (float): Length of the rolling time window in seconds.

    Attributes:
        max_requests (int): Maximum allowed requests per user.
        window_seconds (float): Time window in seconds.
        __user_requests (dict): Maps user_id to list of request timestamps.
    """
    def __init__(self, max_requests, window_seconds):
        if not isinstance(max_requests, int):
            raise TypeError("max_requests must be int")
        if not isinstance(window_seconds, (int, float)):
            raise TypeError("window_seconds must be int or float")
        if max_requests < 0:
            raise ValueError("max_requests must be non-negative")
        if window_seconds < 0:
            raise ValueError("window_seconds must be non-negative")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.__user_requests = {}  # user_id -> list of request timestamps

    def allow_request(self, user_id):
        """
        Checks if the user can make a request based on rate limits.

        Args:
            user_id (Any): Unique identifier for the user/client.

        Returns:
            bool: True if request is allowed, False if rate-limited.
        """
        now = time.time()
        window_start = now - self.window_seconds
        requests = self.__user_requests.get(user_id, [])

        # Remove requests outside the window
        requests = [timestamp for timestamp in requests if timestamp > window_start]

        allowed = len(requests) < self.max_requests
        if allowed:
            requests.append(now)
        self.__user_requests[user_id] = requests
        return allowed

    def cleanup(self):
        """
        Removes users with no recent requests from the internal user request dictionary.
        Call this periodically to prevent memory leaks in long-running applications.

        Returns:
            None
        """
        now = time.time()
        window_start = now - self.window_seconds
        to_delete = [user_id for user_id, requests in self.__user_requests.items()
                     if not any(timestamp > window_start for timestamp in requests)]
        for user_id in to_delete:
            del self.__user_requests[user_id]
