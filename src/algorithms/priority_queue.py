"""Priority queue helper for A* search."""


class PriorityQueue:
    """Simple min-priority queue implementation."""

    def __init__(self):
        self.items = []

    def push(self, item, priority):
        self.items.append((priority, item))
        self.items.sort(key=lambda x: x[0])

    def pop(self):
        if not self.items:
            raise IndexError("pop from empty priority queue")
        return self.items.pop(0)[1]

    def empty(self):
        return len(self.items) == 0
