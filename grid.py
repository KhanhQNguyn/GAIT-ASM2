from typing import Optional, Union, Dict, List, Tuple
import math
import random
import pygame
from settings import (
    TILE_SIZE,
    Terrain,
    TERRAIN_COST,
    TERRAIN_COLOR,
    COLOR_EXPLORED,
    COLOR_FRONTIER,
    COLOR_PATH,
    COLOR_GRID_LINE,
)

class Cell:
    __slots__ = ("col", "row", "terrain", "g_cost", "explored", "frontier", "in_path")

    def __init__(self, col: int, row: int, terrain: str):
        self.col = col
        self.row = row
        self.terrain = terrain
        self.g_cost = None      # set by A* when explored
        self.explored = False   # popped from open set
        self.frontier = False   # currently in open set
        self.in_path = False    # part of final path

class TerrainGrid:
    def __init__(self, cols: int, rows: int, layout: Optional[List[str]] = None):
        self.cols = cols
        self.rows = rows
        self.grid = [[None for _ in range(rows)] for _ in range(cols)]
        
        if layout:
            self._load_from_layout(layout)
        else:
            self._procedural_generate()

    def _load_from_layout(self, layout: list[str]):
        char_map = {
            '.': Terrain.GRASS,
            'm': Terrain.MUD,
            'w': Terrain.WATER,
            '#': Terrain.WALL,
        }
        for r in range(min(self.rows, len(layout))):
            line = layout[r]
            for c in range(min(self.cols, len(line))):
                char = line[c]
                terrain = char_map.get(char, Terrain.GRASS)
                self.grid[c][r] = Cell(c, r, terrain)

    def _procedural_generate(self):
        # Procedurally seed terrain
        for r in range(self.rows):
            for c in range(self.cols):
                rand = random.random()
                if rand < 0.65:
                    t = Terrain.GRASS
                elif rand < 0.83:
                    t = Terrain.MUD
                elif rand < 0.95:
                    t = Terrain.WATER
                else:
                    t = Terrain.WALL
                self.grid[c][r] = Cell(c, r, t)
        
        # Simple cluster smoothing for walls/water
        for _ in range(2):
            for r in range(1, self.rows - 1):
                for c in range(1, self.cols - 1):
                    current_cell = self.grid[c][r]
                    if current_cell.terrain == Terrain.WALL:
                        wall_neighbors = sum(
                            1 for dc in (-1, 0, 1) for dr in (-1, 0, 1)
                            if (dc != 0 or dr != 0) and self.grid[c+dc][r+dr].terrain == Terrain.WALL
                        )
                        if wall_neighbors < 2:
                            current_cell.terrain = Terrain.GRASS

    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def get_cell(self, col: int, row: int) -> Optional[Cell]:
        if self.in_bounds(col, row):
            return self.grid[col][row]
        return None

    def cost(self, col: int, row: int) -> float:
        cell = self.get_cell(col, row)
        if not cell:
            return float("inf")
        return TERRAIN_COST[cell.terrain]

    def neighbors(self, col: int, row: int, allow_diagonal: bool) -> list[tuple[int, int]]:
        result = []
        cardinals = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        for dc, dr in cardinals:
            nc, nr = col + dc, row + dr
            if self.in_bounds(nc, nr) and self.cost(nc, nr) < float("inf"):
                result.append((nc, nr))

        if allow_diagonal:
            diagonals = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
            for dc, dr in diagonals:
                nc, nr = col + dc, row + dr
                if self.in_bounds(nc, nr) and self.cost(nc, nr) < float("inf"):
                    # Explicitly prevent corner-cutting:
                    # Diagonal move is legal ONLY IF both orthogonal adjacent cells are not walls
                    ortho1_passable = self.cost(col + dc, row) < float("inf")
                    ortho2_passable = self.cost(col, row + dr) < float("inf")
                    if ortho1_passable and ortho2_passable:
                        result.append((nc, nr))

        return result

    def movement_cost(self, from_cell: Cell, to_cell: Cell) -> float:
        base_cost = TERRAIN_COST[to_cell.terrain]
        is_diagonal = (from_cell.col != to_cell.col) and (from_cell.row != to_cell.row)
        return base_cost * (1.4142 if is_diagonal else 1.0)

    def reset_search_state(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[c][r]
                cell.g_cost = None
                cell.explored = False
                cell.frontier = False
                cell.in_path = False

    def world_to_cell(self, x: float, y: float) -> tuple[int, int]:
        col = int(x // TILE_SIZE)
        row = int(y // TILE_SIZE)
        return col, row

    def cell_to_world_center(self, col: int, row: int) -> tuple[float, float]:
        x = col * TILE_SIZE + TILE_SIZE / 2.0
        y = row * TILE_SIZE + TILE_SIZE / 2.0
        return x, y

    def draw(
        self,
        surface: pygame.Surface,
        tileset: Optional[pygame.Surface],
        show_heatmap: bool,
        show_cost_labels: bool,
        font: pygame.font.Font,
    ):
        overlay_explored = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        overlay_explored.fill(COLOR_EXPLORED)

        overlay_frontier = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        overlay_frontier.fill(COLOR_FRONTIER)

        for c in range(self.cols):
            for r in range(self.rows):
                cell = self.grid[c][r]
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)

                # Draw Base Terrain Tile
                if tileset:
                    # Tile index mapping fallback if tileset provided
                    tile_rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
                    surface.blit(tileset, rect, tile_rect)
                else:
                    color = TERRAIN_COLOR[cell.terrain]
                    pygame.draw.rect(surface, color, rect)

                # Draw Path Highlight (Green)
                if cell.in_path:
                    path_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    path_surf.fill((*COLOR_PATH[:3], 150))
                    surface.blit(path_surf, rect)
                # Heatmap / Frontier Overlay
                elif show_heatmap:
                    if cell.explored:
                        surface.blit(overlay_explored, rect)
                    elif cell.frontier:
                        surface.blit(overlay_frontier, rect)

                # Draw Cell Cost Labels
                if show_cost_labels and cell.g_cost is not None:
                    text_str = f"{cell.g_cost:.1f}"
                    txt_surf = font.render(text_str, True, (255, 255, 255))
                    txt_rect = txt_surf.get_rect(center=rect.center)
                    # Small drop shadow for text readability
                    shadow_surf = font.render(text_str, True, (0, 0, 0))
                    surface.blit(shadow_surf, (txt_rect.x + 1, txt_rect.y + 1))
                    surface.blit(txt_surf, txt_rect)

                # Grid Lines
                pygame.draw.rect(surface, COLOR_GRID_LINE, rect, 1)
