from collections import OrderedDict

class LRUCache:
    """
    Basic LRU (Least Recently Used) cache using OrderedDict.
    Methods:
        get(key): Retrieve value and mark key as recently used.
        put(key, value): Add/update value, evict least recently used if full.
    """
    def __init__(self, capacity):
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("Capacity must be a positive integer")
        self.capacity = capacity
        self.cache = OrderedDict()  # key -> value, maintains order

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key, value):
        if key in self.cache:
            self.cache[key] = value
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)  # Remove least recently used
            self.cache[key] = value
