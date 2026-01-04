import time
from cachetools import TTLCache

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        """
        :param max_requests: Maximum number of requests allowed in the time window.
        :param time_window: Time window in seconds.
        """
        self.max_requests = max_requests
        self.time_window = time_window
        # Cache stores the list of timestamps for each key
        # When an entry is accessed/updated, its TTL is reset (if using TTLCache correctly)
        # However, standard TTLCache expires based on insertion time by default unless updated.
        self.cache = TTLCache(maxsize=10000, ttl=time_window)

    def is_allowed(self, key: str) -> bool:
        """
        Check if the request is allowed for the given key.
        """
        current_time = time.time()
        
        # Get existing timestamps or empty list
        timestamps = self.cache.get(key, [])
        
        # Filter out timestamps older than the window
        valid_timestamps = [t for t in timestamps if current_time - t < self.time_window]
        
        if len(valid_timestamps) >= self.max_requests:
            # Update cache with cleaned timestamps to keep it fresh but don't add new one
            self.cache[key] = valid_timestamps
            return False

        # Add new timestamp
        valid_timestamps.append(current_time)
        self.cache[key] = valid_timestamps
        return True
