from __future__ import annotations

import math
import random
from collections import deque

import pygame

from settings import COLOR_EXPLORED, COLOR_FRONTIER, COLOR_PATH, TERRAIN_COLOR, TERRAIN_COST, TILE_SIZE, Terrain


class Cell:
    __slots__ = ("col", "row", "terrain", "g_cost", "explored", "in_path")

    def __init__(self, col: int, row: int, terrain: str):
        self.col = col
        self.row = row
        self.terrain = terrain
        self.g_cost = None
        self.explored = False
        self.in_path = False


class TerrainGrid:
    def __init__(self, cols: int, rows: int, layout: list[str] | None = None, seed: int | None = None):
        self.cols = cols
        self.rows = rows
        self.start_cell: tuple[int, int] | None = None
        self.goal_cell: tuple[int, int] | None = None
        self.final_path: list[tuple[int, int]] = []
        self._scaled_texture_cache: dict[tuple[int, str], pygame.Surface] = {}
        self._reachable: set[tuple[int, int]] = set()
        self._rng = random.Random(seed)
        self.cells = self._build_cells(layout)

    def _build_cells(self, layout: list[str] | None) -> list[list[Cell]]:
        cells: list[list[Cell]] = []
        if layout is not None:
            if len(layout) != self.rows:
                raise ValueError("layout row count does not match grid rows")
            for row_index, row_text in enumerate(layout):
                if len(row_text) != self.cols:
                    raise ValueError("layout column count does not match grid cols")
                row_cells: list[Cell] = []
                for col_index, char in enumerate(row_text):
                    terrain = self._terrain_from_layout_char(char)
                    row_cells.append(Cell(col_index, row_index, terrain))
                cells.append(row_cells)
            return cells

        for row_index in range(self.rows):
            row_cells = []
            for col_index in range(self.cols):
                row_cells.append(Cell(col_index, row_index, Terrain.GRASS))
            cells.append(row_cells)

        for _ in range(6):
            self._stamp_blob(cells, Terrain.MUD, radius=2)
        for _ in range(5):
            self._stamp_blob(cells, Terrain.WATER, radius=2)
        for _ in range(6):
            self._stamp_blob(cells, Terrain.WALL, radius=1)

        # Keep a mostly-grass map while preserving visible weighted patches.
        for row_cells in cells:
            for cell in row_cells:
                if cell.terrain == Terrain.GRASS:
                    continue
                roll = self._rng.random()
                if cell.terrain == Terrain.WALL and roll < 0.35:
                    cell.terrain = Terrain.GRASS
                elif cell.terrain == Terrain.WATER and roll < 0.24:
                    cell.terrain = Terrain.GRASS
                elif cell.terrain == Terrain.MUD and roll < 0.18:
                    cell.terrain = Terrain.GRASS

        has_grass = any(cell.terrain == Terrain.GRASS for row_cells in cells for cell in row_cells)
        if not has_grass:
            cells[0][0].terrain = Terrain.GRASS
        return cells

    def _stamp_blob(self, cells: list[list[Cell]], terrain: str, radius: int) -> None:
        center_col = self._rng.randrange(self.cols)
        center_row = self._rng.randrange(self.rows)
        for row_index in range(max(0, center_row - radius), min(self.rows, center_row + radius + 1)):
            for col_index in range(max(0, center_col - radius), min(self.cols, center_col + radius + 1)):
                if self._rng.random() < 0.55:
                    cells[row_index][col_index].terrain = terrain

    def grass_cells(self) -> list[tuple[int, int]]:
        cells: list[tuple[int, int]] = []
        for row_cells in self.cells:
            for cell in row_cells:
                if cell.terrain == Terrain.GRASS:
                    cells.append((cell.col, cell.row))
        return cells

    def set_terrain(self, col: int, row: int, terrain: str) -> bool:
        cell = self.get_cell(col, row)
        if cell is None:
            return False
        cell.terrain = terrain
        return True

    @staticmethod
    def _terrain_from_layout_char(char: str) -> str:
        if char == ".":
            return Terrain.GRASS
        if char == "m":
            return Terrain.MUD
        if char == "w":
            return Terrain.WATER
        if char == "#":
            return Terrain.WALL
        raise ValueError(f"unknown terrain layout character: {char!r}")

    def set_start_cell(self, col: int, row: int) -> None:
        self.start_cell = (col, row)
        self._reachable = self._flood_fill(col, row)

    def _flood_fill(self, start_col: int, start_row: int) -> set[tuple[int, int]]:
        if not self.in_bounds(start_col, start_row):
            return set()
        if self.cost(start_col, start_row) == float("inf"):
            return set()

        reachable: set[tuple[int, int]] = set()
        queue = deque([(start_col, start_row)])
        reachable.add((start_col, start_row))

        while queue:
            col, row = queue.popleft()
            for next_col, next_row in self.neighbors(col, row, allow_diagonal=False):
                if (next_col, next_row) not in reachable and self.cost(next_col, next_row) != float("inf"):
                    reachable.add((next_col, next_row))
                    queue.append((next_col, next_row))

        return reachable

    def is_reachable(self, col: int, row: int) -> bool:
        return (col, row) in self._reachable

    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def get_cell(self, col: int, row: int) -> Cell | None:
        if not self.in_bounds(col, row):
            return None
        return self.cells[row][col]

    def cost(self, col: int, row: int) -> float:
        cell = self.get_cell(col, row)
        if cell is None:
            return float("inf")
        return TERRAIN_COST[cell.terrain]

    def neighbors(self, col: int, row: int, allow_diagonal: bool) -> list[tuple[int, int]]:
        result: list[tuple[int, int]] = []
        cardinal_offsets = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        for delta_col, delta_row in cardinal_offsets:
            next_col = col + delta_col
            next_row = row + delta_row
            if self.in_bounds(next_col, next_row) and self.cost(next_col, next_row) != float("inf"):
                result.append((next_col, next_row))

        if not allow_diagonal:
            return result

        diagonal_offsets = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        for delta_col, delta_row in diagonal_offsets:
            next_col = col + delta_col
            next_row = row + delta_row
            orthogonal_a = (col + delta_col, row)
            orthogonal_b = (col, row + delta_row)
            if not self.in_bounds(next_col, next_row):
                continue
            if self.cost(next_col, next_row) == float("inf"):
                continue
            if self.cost(*orthogonal_a) == float("inf") or self.cost(*orthogonal_b) == float("inf"):
                continue
            result.append((next_col, next_row))

        return result

    def movement_cost(self, from_cell: Cell, to_cell: Cell) -> float:
        diagonal = from_cell.col != to_cell.col and from_cell.row != to_cell.row
        multiplier = math.sqrt(2) if diagonal else 1.0
        return TERRAIN_COST[to_cell.terrain] * multiplier

    def reset_search_state(self) -> None:
        self.final_path = []
        for row_cells in self.cells:
            for cell in row_cells:
                cell.g_cost = None
                cell.explored = False
                cell.in_path = False

    def world_to_cell(self, x: float, y: float) -> tuple[int, int]:
        return int(x // TILE_SIZE), int(y // TILE_SIZE)

    def cell_to_world_center(self, col: int, row: int) -> tuple[float, float]:
        return col * TILE_SIZE + TILE_SIZE / 2.0, row * TILE_SIZE + TILE_SIZE / 2.0

    def draw(
        self,
        surface: pygame.Surface,
        terrain_textures: dict[str, pygame.Surface],
        revealed_cells: set[tuple[int, int]],
        show_final_path: bool,
        show_heatmap: bool,
        show_cost_labels: bool,
        font: pygame.font.Font,
    ) -> None:
        for row_cells in self.cells:
            for cell in row_cells:
                rect = pygame.Rect(cell.col * TILE_SIZE, cell.row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                self._draw_base_tile(surface, rect, cell.terrain, terrain_textures.get(cell.terrain))

                if show_heatmap and cell.terrain != Terrain.WALL:
                    heat_color = self._heat_color_for_terrain(cell.terrain)
                    overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    overlay.fill((*heat_color, 72))
                    surface.blit(overlay, rect.topleft)

                if (cell.col, cell.row) in revealed_cells:
                    overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    overlay.fill((*COLOR_EXPLORED, 72))
                    surface.blit(overlay, rect.topleft)
                    pygame.draw.rect(surface, COLOR_FRONTIER, rect, 1)

                    if show_cost_labels and cell.g_cost is not None:
                        label = font.render(f"{cell.g_cost:.2f}", True, (255, 255, 255))
                        label_rect = label.get_rect(center=rect.center)
                        shadow = font.render(f"{cell.g_cost:.2f}", True, (0, 0, 0))
                        shadow_rect = shadow.get_rect(center=(rect.centerx + 1, rect.centery + 1))
                        surface.blit(shadow, shadow_rect)
                        surface.blit(label, label_rect)

                if show_final_path and cell.in_path:
                    overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    overlay.fill((*COLOR_PATH, 112))
                    surface.blit(overlay, rect.topleft)

        if show_final_path:
            path_points = [self.cell_to_world_center(col, row) for col, row in self.final_path]
            if len(path_points) >= 2:
                pygame.draw.lines(surface, COLOR_PATH, False, path_points, 4)

        if self.start_cell is not None:
            self._draw_marker(surface, self.start_cell, (80, 220, 255), 10)
        if self.goal_cell is not None:
            self._draw_marker(surface, self.goal_cell, (255, 90, 90), 10)

    def _draw_base_tile(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        terrain: str,
        terrain_texture: pygame.Surface | None,
    ) -> None:
        if terrain_texture is not None:
            try:
                cache_key = (id(terrain_texture), terrain)
                scaled = self._scaled_texture_cache.get(cache_key)
                if scaled is None:
                    scaled = pygame.transform.smoothscale(terrain_texture, (TILE_SIZE, TILE_SIZE))
                    self._scaled_texture_cache[cache_key] = scaled
                surface.blit(scaled, rect.topleft)
                return
            except pygame.error:
                pass

        pygame.draw.rect(surface, TERRAIN_COLOR[terrain], rect)

    @staticmethod
    def _heat_color_for_terrain(terrain: str) -> tuple[int, int, int]:
        mapping = {
            Terrain.GRASS: (74, 180, 92),
            Terrain.MUD: (182, 117, 52),
            Terrain.WATER: (80, 132, 227),
            Terrain.WALL: (0, 0, 0),
        }
        return mapping[terrain]

    def _draw_marker(self, surface: pygame.Surface, cell_coord: tuple[int, int], color: tuple[int, int, int], radius: int) -> None:
        center = self.cell_to_world_center(*cell_coord)
        pygame.draw.circle(surface, (20, 20, 20), (int(center[0]), int(center[1])), radius + 2)
        pygame.draw.circle(surface, color, (int(center[0]), int(center[1])), radius)
