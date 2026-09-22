"""A* shortest-path implementation."""


class AStar:
    """A minimal A* search class."""

    def __init__(self, graph, heuristic):
        self.graph = graph
        self.heuristic = heuristic

    def search(self, start, goal):
        """Search the shortest path from start to goal."""
        if start == goal:
            return [start]

        open_set = {start}
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}

        while open_set:
            current = min(open_set, key=lambda node: f_score.get(node, float("inf")))
            if current == goal:
                return self._reconstruct_path(came_from, current)

            open_set.remove(current)
            for edge in self.graph.edges.get(current, []):
                neighbor = edge["target"]
                tentative = g_score.get(current, float("inf")) + edge["weight"]
                if tentative < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative
                    f_score[neighbor] = tentative + self.heuristic(neighbor, goal)
                    open_set.add(neighbor)

        return []

    def _reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path
