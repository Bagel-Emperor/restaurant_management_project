class LRUCache:
    """
    Basic LRU (Least Recently Used) cache using lists and dictionaries.
    Methods:
        get(key): Retrieve value and mark key as recently used.
        put(key, value): Add/update value, evict least recently used if full.
    """
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}  # key -> value
        self.order = []  # list of keys, most recent at end

    def get(self, key):
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return None

    def put(self, key, value):
        if key in self.cache:
            self.cache[key] = value
            self.order.remove(key)
            self.order.append(key)
        else:
            if len(self.cache) >= self.capacity:
                lru = self.order.pop(0)
                del self.cache[lru]
            self.cache[key] = value
            self.order.append(key)
