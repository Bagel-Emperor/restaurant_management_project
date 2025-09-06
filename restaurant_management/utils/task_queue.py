class TaskQueue:
    """
    Simple FIFO task queue using a Python list.
    Methods:
        enqueue(task): Add a task to the end of the queue.
        dequeue(): Remove and return the first task in the queue.
        peek(): View the first task without removing it.
        is_empty(): Check if the queue is empty.
        size(): Return the number of tasks in the queue.
    """
    def __init__(self):
        self.queue = []

    def enqueue(self, task):
        self.queue.append(task)

    def dequeue(self):
        if self.queue:
            return self.queue.pop(0)
        return None

    def peek(self):
        if self.queue:
            return self.queue[0]
        return None

    def is_empty(self):
        return len(self.queue) == 0

    def size(self):
        return len(self.queue)
