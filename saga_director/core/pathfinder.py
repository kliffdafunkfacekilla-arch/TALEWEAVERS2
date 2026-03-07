import heapq
import math
from typing import List, Tuple, Dict, Any

class Pathfinder:
    """Handles movement calculations across the 4-layer hierarchy."""

    @staticmethod
    def get_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """Simple Euclidean distance for heuristics."""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    @staticmethod
    def a_star(grid: List[List[str]], start: Tuple[int, int], end: Tuple[int, int], costs: Dict[str, float]) -> List[Tuple[int, int]]:
        """Standard A* implementation for 2D grids."""
        height = len(grid)
        width = len(grid[0])
        
        # Priority queue stores (priority, current_cost, current_node, path)
        pq = [(0, 0, start, [start])]
        visited = {}

        while pq:
            _, g, current, path = heapq.heappop(pq)

            if current == end:
                return path

            if current in visited and visited[current] <= g:
                continue
            visited[current] = g

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nx, ny = current[0] + dx, current[1] + dy
                
                if 0 <= nx < width and 0 <= ny < height:
                    cell_type = grid[ny][nx]
                    # Default cost 1.0, otherwise use provided cost map
                    step_cost = costs.get(cell_type, 1.0)
                    
                    # Diagonal movement check
                    if abs(dx) + abs(dy) == 2:
                        step_cost *= 1.414
                    
                    new_g = g + step_cost
                    priority = new_g + Pathfinder.get_distance((nx, ny), end)
                    
                    heapq.heappush(pq, (priority, new_g, (nx, ny), path + [(nx, ny)]))
        
        return []

    @classmethod
    def plan_regional_path(cls, grid_data: Dict[str, Any], start: Tuple[int, int], end: Tuple[int, int]) -> Dict[str, Any]:
        """Layer 2 Pathfinding (20x20). 1 day per space."""
        grid = grid_data["grid"]
        # Regional costs: Settlements/Outposts are easy, wilderness is standard.
        costs = {
            "WILDERNESS": 1.0,
            "SETTLEMENT": 0.5,
            "RUIN": 1.5,
            "DANGER_ZONE": 3.0
        }
        path = cls.a_star(grid, start, end, costs)
        
        # Calculate time: Total cost in days
        total_days = 0
        for i in range(len(path) - 1):
            p1, p2 = path[i], path[i+1]
            cell_type = grid[p2[1]][p2[0]]
            cost = costs.get(cell_type, 1.0)
            if abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]) == 2:
                cost *= 1.414
            total_days += cost

        return {
            "path": path,
            "total_time_days": round(total_days, 2),
            "layer": "REGIONAL"
        }

    @classmethod
    def plan_local_path(cls, grid_data: Dict[str, Any], start: Tuple[int, int], end: Tuple[int, int]) -> Dict[str, Any]:
        """Layer 3 Pathfinding (100x100). 15 mins per space."""
        grid = grid_data["grid"]
        costs = {
            "CLEAR": 1.0,
            "THICKET": 2.5,
            "POND": 5.0,
            "RUINED_WALL": 2.0,
            "CAVE_ENTRANCE": 1.5
        }
        path = cls.a_star(grid, start, end, costs)
        
        # Calculate time: Total cost in 15-min intervals
        total_intervals = 0
        for i in range(len(path) - 1):
            p1, p2 = path[i], path[i+1]
            cell_type = grid[p2[1]][p2[0]]
            cost = costs.get(cell_type, 1.0)
            if abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]) == 2:
                cost *= 1.414
            total_intervals += cost

        total_minutes = total_intervals * 15
        return {
            "path": path,
            "total_time_minutes": round(total_minutes, 1),
            "layer": "LOCAL"
        }
