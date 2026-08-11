from typing import Optional, List, Tuple, Dict
import heapq
import math
from dataclasses import dataclass, field
from grid import TerrainGrid, Cell

@dataclass
class AStarResult:
    path: List[Tuple[float, float]]       # ordered list of (x, y) world centers, start to goal inclusive
    total_cost: float                     # g_cost of goal cell; float('inf') if unreachable
    explored_order: List[Tuple[int, int]] # (col, row) cells in the order they were POPPED from open set
    reachable: bool

def octile_distance(c1: Tuple[int, int], c2: Tuple[int, int]) -> float:
    dx = abs(c1[0] - c2[0])
    dy = abs(c1[1] - c2[1])
    return (dx + dy) + (math.sqrt(2.0) - 2.0) * min(dx, dy)

def manhattan_distance(c1: Tuple[int, int], c2: Tuple[int, int]) -> float:
    return float(abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]))

def find_path(
    grid: TerrainGrid,
    start: Tuple[int, int],
    goal: Tuple[int, int],
    allow_diagonal: bool
) -> AStarResult:
    grid.reset_search_state()

    start_col, start_row = start
    goal_col, goal_row = goal

    if not grid.in_bounds(start_col, start_row) or not grid.in_bounds(goal_col, goal_row):
        return AStarResult(path=[], total_cost=float("inf"), explored_order=[], reachable=False)

    if grid.cost(start_col, start_row) == float("inf") or grid.cost(goal_col, goal_row) == float("inf"):
        return AStarResult(path=[], total_cost=float("inf"), explored_order=[], reachable=False)

    heuristic_fn = octile_distance if allow_diagonal else manhattan_distance

    # Priority queue storing tuples: (f_score, g_score, col, row)
    # Using small tie-breaker bias on h_score (multiply by 1.001) to favor larger g
    open_set = []
    
    h_start = heuristic_fn(start, goal)
    heapq.heappush(open_set, (h_start * 1.001, 0.0, start_col, start_row))

    g_score = {(start_col, start_row): 0.0}
    came_from = {}
    explored_order = []
    
    # Track frontier nodes for visual rendering overlay
    start_cell = grid.get_cell(start_col, start_row)
    if start_cell:
        start_cell.frontier = True

    reached_goal = False

    while open_set:
        f, current_g, col, row = heapq.heappop(open_set)

        cell = grid.get_cell(col, row)
        if cell is None:
            continue

        # Skip if we already found a cheaper way to this popped node
        if current_g > g_score.get((col, row), float("inf")):
            continue

        cell.frontier = False
        cell.explored = True
        cell.g_cost = current_g
        explored_order.append((col, row))

        if (col, row) == (goal_col, goal_row):
            reached_goal = True
            break

        for nc, nr in grid.neighbors(col, row, allow_diagonal):
            neighbor_cell = grid.get_cell(nc, nr)
            if neighbor_cell is None or neighbor_cell.explored:
                continue

            move_cost = grid.movement_cost(cell, neighbor_cell)
            tentative_g = current_g + move_cost

            if tentative_g < g_score.get((nc, nr), float("inf")):
                came_from[(nc, nr)] = (col, row)
                g_score[(nc, nr)] = tentative_g
                h_val = heuristic_fn((nc, nr), goal)
                f_val = tentative_g + h_val * 1.001
                
                neighbor_cell.frontier = True
                heapq.heappush(open_set, (f_val, tentative_g, nc, nr))

    if not reached_goal:
        return AStarResult(path=[], total_cost=float("inf"), explored_order=explored_order, reachable=False)

    # Reconstruct path from goal to start
    curr = (goal_col, goal_row)
    grid_path = [curr]
    while curr in came_from:
        curr = came_from[curr]
        grid_path.append(curr)

    grid_path.reverse()

    # Convert grid cell coordinates to world center points and mark in_path
    world_path = []
    for c, r in grid_path:
        cell = grid.get_cell(c, r)
        if cell:
            cell.in_path = True
        world_path.append(grid.cell_to_world_center(c, r))

    goal_total_cost = g_score.get((goal_col, goal_row), float("inf"))
    return AStarResult(path=world_path, total_cost=goal_total_cost, explored_order=explored_order, reachable=True)

def path_cost_breakdown(grid: TerrainGrid, grid_coords: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], float, float]]:
    """Returns a list of ((col, row), step_cost, cumulative_cost) for narration / debugging."""
    breakdown = []
    cum_cost = 0.0
    for i, (c, r) in enumerate(grid_coords):
        cell = grid.get_cell(c, r)
        if i == 0:
            step_cost = 0.0
        else:
            prev_c, prev_r = grid_coords[i-1]
            prev_cell = grid.get_cell(prev_c, prev_r)
            step_cost = grid.movement_cost(prev_cell, cell) if prev_cell and cell else 0.0
        cum_cost += step_cost
        breakdown.append(((c, r), step_cost, cum_cost))
    return breakdown
