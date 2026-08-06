# ============================================================================
# pathfinding.py
# Purpose
#   A* search over a uniform grid baked from the World's obstacle rects,
#   plus path smoothing (string-pulling) so the returned route looks
#   natural instead of grid-staircased.
# Mathematics
#   f(n) = g(n) + h(n). Cardinal step cost = 1.0, diagonal step cost = sqrt(2).
#   h(n) = octile distance (admissible for this cost model -> A* is optimal).
#   Diagonal moves are only legal if both adjacent cardinal cells are open
#   ("corner-cut guard") so the path never grazes an obstacle corner.
# ============================================================================

import heapq
import math
from pygame.math import Vector2 as V2
from utils import circlecast_hits_any_rect

SQRT2 = math.sqrt(2)


class Grid:
    """
    Uniform grid over the arena, rasterized once from a list of pygame.Rect
    obstacles. Each obstacle is inflated by `padding` (agent radius + a
    small margin) before rasterizing, so a path computed on this grid keeps
    the WHOLE agent body clear of walls, not just its center point.
    """

    def __init__(self, width, height, cell_size, obstacles, padding=0):
        self.cell_size = cell_size
        self.cols = math.ceil(width / cell_size)
        self.rows = math.ceil(height / cell_size)
        self.blocked = [[False] * self.cols for _ in range(self.rows)]
        self._rasterize(obstacles, padding)

    def _rasterize(self, obstacles, padding):
        for rect in obstacles:
            inflated = rect.inflate(padding * 2, padding * 2)
            c0 = max(0, inflated.left // self.cell_size)
            c1 = min(self.cols - 1, inflated.right // self.cell_size)
            r0 = max(0, inflated.top // self.cell_size)
            r1 = min(self.rows - 1, inflated.bottom // self.cell_size)
            for r in range(int(r0), int(r1) + 1):
                for c in range(int(c0), int(c1) + 1):
                    self.blocked[r][c] = True

    def in_bounds(self, cell):
        c, r = cell
        return 0 <= c < self.cols and 0 <= r < self.rows

    def walkable(self, cell):
        c, r = cell
        return self.in_bounds(cell) and not self.blocked[r][c]

    def world_to_cell(self, pos):
        return (int(pos.x // self.cell_size), int(pos.y // self.cell_size))

    def cell_to_world(self, cell):
        c, r = cell
        return V2(c * self.cell_size + self.cell_size / 2,
                  r * self.cell_size + self.cell_size / 2)

    def nearest_walkable(self, cell, max_radius=8):
        """Ring-search outward from `cell` for the closest open cell. Used
        when a click lands inside/behind an obstacle."""
        if self.walkable(cell):
            return cell
        c0, r0 = cell
        for radius in range(1, max_radius + 1):
            for dc in range(-radius, radius + 1):
                for dr in range(-radius, radius + 1):
                    if max(abs(dc), abs(dr)) != radius:
                        continue  # only test the ring's edge, not its interior again
                    cand = (c0 + dc, r0 + dr)
                    if self.walkable(cand):
                        return cand
        return None

    def neighbors(self, cell, allow_diagonal=True):
        """
        Yields (neighbor_cell, step_cost).
        Cardinal cost = 1.0. Diagonal cost = sqrt(2), and a diagonal is only
        yielded if BOTH flanking cardinal cells are walkable (corner-cut guard).
        """
        c, r = cell
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c + dc, r + dr)
            if self.walkable(n):
                yield n, 1.0

        if allow_diagonal:
            for dc, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = (c + dc, r + dr)
                side_a = (c + dc, r)
                side_b = (c, r + dr)
                if self.walkable(n) and self.walkable(side_a) and self.walkable(side_b):
                    yield n, SQRT2


def octile_heuristic(a, b):
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return (dx + dy) + (SQRT2 - 2) * min(dx, dy)


def astar(grid, start_cell, goal_cell, allow_diagonal=True):
    """
    Returns:
        {
          "path_cells": [cell, ...] or None if unreachable,
          "explored_order": [cell, ...],  # order cells were POPPED (settled)
          "g_cost": {cell: g_value, ...},  # cost of every explored cell
          "total_cost": float or None,
        }
    """
    if not grid.walkable(start_cell) or not grid.walkable(goal_cell):
        return {"path_cells": None, "explored_order": [], "g_cost": {}, "total_cost": None}

    open_heap = []
    counter = 0  # tie-breaker so heapq never has to compare cell tuples
    heapq.heappush(open_heap, (0.0, counter, start_cell))

    g_cost = {start_cell: 0.0}
    parent = {start_cell: None}
    closed = set()
    explored_order = []

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)
        explored_order.append(current)

        if current == goal_cell:
            return {
                "path_cells": _reconstruct(parent, current),
                "explored_order": explored_order,
                "g_cost": g_cost,
                "total_cost": g_cost[current],
            }

        for neighbor, step_cost in grid.neighbors(current, allow_diagonal):
            if neighbor in closed:
                continue
            tentative_g = g_cost[current] + step_cost
            if neighbor not in g_cost or tentative_g < g_cost[neighbor]:
                g_cost[neighbor] = tentative_g
                parent[neighbor] = current
                f = tentative_g + octile_heuristic(neighbor, goal_cell)
                counter += 1
                heapq.heappush(open_heap, (f, counter, neighbor))

    return {"path_cells": None, "explored_order": explored_order, "g_cost": g_cost, "total_cost": None}


def _reconstruct(parent, node):
    path = [node]
    while parent[node] is not None:
        node = parent[node]
        path.append(node)
    path.reverse()
    return path


def line_of_sight(p0, p1, obstacles, radius):
    """True if a circle of `radius` can travel straight from p0 to p1
    without touching any obstacle rect."""
    return not circlecast_hits_any_rect(p0, p1, radius, obstacles)


def smooth_path(world_points, obstacles, radius):
    """
    String-pulling: from each kept waypoint, jump directly to the FURTHEST
    waypoint still in a straight line-of-sight, skipping every grid-forced
    zig-zag point in between. This is what turns a jagged, grid-aligned
    A* path into a natural-looking route, and reduces how many corners the
    steering code has to actually turn through.
    """
    if len(world_points) <= 2:
        return list(world_points)

    smoothed = [world_points[0]]
    i = 0
    n = len(world_points)
    while i < n - 1:
        furthest = i + 1
        for j in range(n - 1, i, -1):
            if line_of_sight(world_points[i], world_points[j], obstacles, radius):
                furthest = j
                break
        smoothed.append(world_points[furthest])
        i = furthest
    return smoothed


def find_path(grid, start_world, goal_world, obstacles, agent_radius, allow_diagonal=True):
    """
    High-level entry point used by main.py.
    1. snap start/goal to the nearest walkable grid cell
    2. run A*
    3. convert the cell path to world-space points
    4. smooth it

    Returns a dict ready for both frog.set_path() and the HUD/visualization:
        raw_world_path        - list[V2] or None
        smoothed_world_path   - list[V2] or None
        explored_world        - list[V2] (for drawing, in visit order)
        explored_cells        - list[cell] (for indexing g_cost, in visit order)
        g_cost_by_cell         - {cell: g}
        total_cost              - float or None
    """
    start_cell = grid.world_to_cell(start_world)
    goal_cell = grid.world_to_cell(goal_world)

    snapped_start = grid.nearest_walkable(start_cell)
    snapped_goal = grid.nearest_walkable(goal_cell)
    start_cell = snapped_start if snapped_start else start_cell
    goal_cell = snapped_goal if snapped_goal else goal_cell

    result = astar(grid, start_cell, goal_cell, allow_diagonal)

    world_path = None
    smoothed_world_path = None
    if result["path_cells"]:
        world_path = [grid.cell_to_world(c) for c in result["path_cells"]]
        smoothed_world_path = smooth_path(world_path, obstacles, agent_radius)

    return {
        "raw_world_path": world_path,
        "smoothed_world_path": smoothed_world_path,
        "explored_world": [grid.cell_to_world(c) for c in result["explored_order"]],
        "explored_cells": result["explored_order"],
        "g_cost_by_cell": result["g_cost"],
        "total_cost": result["total_cost"],
    }
