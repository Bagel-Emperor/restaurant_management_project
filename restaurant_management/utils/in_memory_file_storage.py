class InMemoryFileStorage:
    """
    Simulates a file storage system in memory using a Python dictionary.
    Enforces a 10MB total storage limit and reasonable per-file size/text caps.
    Methods:
        save(key, content): Store a file with the given key and content (rejects if over limits).
        read(key): Retrieve the content of a file by key.
        delete(key): Delete a file by key.
        exists(key): Check if a file exists by key.
        list_files(): List all stored file keys.
    """
    MAX_TOTAL_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE = 2 * 1024 * 1024    # 2MB per file
    MAX_TEXT_LENGTH = 100_000          # 100,000 characters for text files

    def __init__(self):
        self.storage = {}
        self.total_size = 0

    def save(self, key, content):
        # Determine content size
        if isinstance(content, str):
            size = len(content.encode('utf-8'))
            if size > self.MAX_FILE_SIZE:
                raise ValueError(f"Text file too large (>{self.MAX_FILE_SIZE} bytes when UTF-8 encoded)")
        elif isinstance(content, bytes):
            size = len(content)
        else:
            raise TypeError("Content must be str or bytes")

        # Already checked for text files above; for bytes, check here
        if isinstance(content, bytes) and size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large (>{self.MAX_FILE_SIZE} bytes)")

        # Calculate new total size
        prev_size = 0
        if key in self.storage:
            prev = self.storage[key]
            prev_size = len(prev.encode('utf-8')) if isinstance(prev, str) else len(prev)
        new_total = self.total_size - prev_size + size
        if new_total > self.MAX_TOTAL_SIZE:
            raise MemoryError(f"Storage limit exceeded (>{self.MAX_TOTAL_SIZE} bytes)")

        self.storage[key] = content
        self.total_size = new_total

    def read(self, key):
        if key not in self.storage:
            raise FileNotFoundError(f"No such file: '{key}'")
        return self.storage[key]

    def delete(self, key):
        if key in self.storage:
            content = self.storage[key]
            size = len(content.encode('utf-8')) if isinstance(content, str) else len(content)
            del self.storage[key]
            self.total_size -= size
            return True
        return False

    def exists(self, key):
        return key in self.storage

    def list_files(self):
        return list(self.storage.keys())
