from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

from settings import MIN_TERRAIN_COST


@dataclass
class AStarResult:
    path: list[tuple[int, int]]
    total_cost: float
    explored_order: list[tuple[int, int]]
    reachable: bool


def _manhattan(current: tuple[int, int], goal: tuple[int, int]) -> float:
    dx = abs(goal[0] - current[0])
    dy = abs(goal[1] - current[1])
    return float(dx + dy)


def _octile(current: tuple[int, int], goal: tuple[int, int]) -> float:
    dx = abs(goal[0] - current[0])
    dy = abs(goal[1] - current[1])
    return float((dx + dy) + (math.sqrt(2) - 2.0) * min(dx, dy))


def _heuristic(current: tuple[int, int], goal: tuple[int, int], allow_diagonal: bool) -> float:
    distance = _octile(current, goal) if allow_diagonal else _manhattan(current, goal)
    return MIN_TERRAIN_COST * distance


def _reconstruct_path(came_from: dict[tuple[int, int], tuple[int, int]], goal: tuple[int, int], start: tuple[int, int]) -> list[tuple[int, int]]:
    current = goal
    path = [current]
    while current != start:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def find_path(grid, start: tuple[int, int], goal: tuple[int, int], allow_diagonal: bool) -> AStarResult:
    start_cell = grid.get_cell(*start)
    goal_cell = grid.get_cell(*goal)
    if start_cell is None or goal_cell is None:
        return AStarResult(path=[], total_cost=float("inf"), explored_order=[], reachable=False)

    if start == goal:
        start_cell.g_cost = 0.0
        start_cell.explored = True
        start_cell.in_path = True
        grid.final_path = [start]
        return AStarResult(path=[start], total_cost=0.0, explored_order=[start], reachable=True)

    open_heap: list[tuple[float, int, float, int, int]] = []
    tie_break = 0
    best_g: dict[tuple[int, int], float] = {start: 0.0}
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    explored_order: list[tuple[int, int]] = []

    start_f = _heuristic(start, goal, allow_diagonal)
    heapq.heappush(open_heap, (start_f, tie_break, 0.0, start[0], start[1]))

    while open_heap:
        _, _, g, col, row = heapq.heappop(open_heap)
        current = (col, row)
        if g > best_g.get(current, float("inf")):
            continue

        cell = grid.get_cell(col, row)
        if cell is None:
            continue

        cell.g_cost = g
        cell.explored = True
        explored_order.append(current)

        if current == goal:
            path = _reconstruct_path(came_from, goal, start)
            grid.final_path = path
            for path_col, path_row in path:
                path_cell = grid.get_cell(path_col, path_row)
                if path_cell is not None:
                    path_cell.in_path = True
            return AStarResult(path=path, total_cost=g, explored_order=explored_order, reachable=True)

        for next_col, next_row in grid.neighbors(col, row, allow_diagonal):
            next_cell = grid.get_cell(next_col, next_row)
            if next_cell is None:
                continue
            tentative_g = g + grid.movement_cost(cell, next_cell)
            neighbor = (next_col, next_row)
            if tentative_g < best_g.get(neighbor, float("inf")):
                best_g[neighbor] = tentative_g
                came_from[neighbor] = current
                tie_break += 1
                f_score = tentative_g + _heuristic(neighbor, goal, allow_diagonal)
                heapq.heappush(open_heap, (f_score, tie_break, tentative_g, next_col, next_row))

    return AStarResult(path=[], total_cost=float("inf"), explored_order=explored_order, reachable=False)


def path_cost_breakdown(grid, path: list[tuple[int, int]]) -> list[tuple[tuple[int, int], float, float]]:
    breakdown: list[tuple[tuple[int, int], float, float]] = []
    if not path:
        return breakdown

    cumulative_cost = 0.0
    breakdown.append((path[0], 0.0, 0.0))
    for previous, current in zip(path, path[1:]):
        previous_cell = grid.get_cell(*previous)
        current_cell = grid.get_cell(*current)
        if previous_cell is None or current_cell is None:
            step_cost = float("inf")
        else:
            step_cost = grid.movement_cost(previous_cell, current_cell)
        cumulative_cost += step_cost
        breakdown.append((current, step_cost, cumulative_cost))
    return breakdown
