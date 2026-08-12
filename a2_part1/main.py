from __future__ import annotations

import random

import pygame

from frog import Frog
from grid import TerrainGrid
from pathfinding import AStarResult, find_path, path_cost_breakdown
from settings import (
    COLOR_BG,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT,
    FONT_SIZE,
    FPS,
    FROG_SPRITE,
    GRASS_TEXTURE,
    GRID_COLS,
    GRID_ROWS,
    KEYBINDS,
    MUD_TEXTURE,
    REVEAL_CELLS_PER_FRAME,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TERRAIN_COST,
    TILE_SIZE,
    WALL_TEXTURE,
    WATER_TEXTURE,
    Terrain,
)


IDLE = "idle"
REVEALING = "revealing"
FOLLOWING = "following"


def build_grid() -> TerrainGrid:
    grid = TerrainGrid(GRID_COLS, GRID_ROWS)
    return grid


def load_surface(path):
    try:
        if path.exists():
            return pygame.image.load(str(path)).convert_alpha()
    except Exception as exc:
        print(f"Failed to load {path.name}: {exc}")
    return None


def choose_random_grass_start(grid: TerrainGrid) -> tuple[int, int]:
    grass_cells = grid.grass_cells()
    if not grass_cells:
        raise RuntimeError("No grass cells available for frog spawn")
    return random.choice(grass_cells)


def invalidate_current_path(grid: TerrainGrid, frog: Frog):
    grid.reset_search_state()
    grid.goal_cell = None
    frog.velocity.update(0, 0)
    frog.set_path([])


def summarize_path_terrain(grid: TerrainGrid, path: list[tuple[int, int]]) -> dict[str, int]:
    counts = {Terrain.GRASS: 0, Terrain.MUD: 0, Terrain.WATER: 0}
    for col, row in path:
        cell = grid.get_cell(col, row)
        if cell is None:
            continue
        if cell.terrain in counts:
            counts[cell.terrain] += 1
    return counts


def main() -> int:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("A* over a weighted-cost grid")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, FONT_SIZE)

    frog_sprite = load_surface(FROG_SPRITE)
    terrain_textures = {
        Terrain.GRASS: load_surface(GRASS_TEXTURE),
        Terrain.MUD: load_surface(MUD_TEXTURE),
        Terrain.WATER: load_surface(WATER_TEXTURE),
        Terrain.WALL: load_surface(WALL_TEXTURE),
    }
    if frog_sprite is None:
        print("Running with frog fallback drawing because frog sprite could not be loaded.")
        frog_sprite = None
    if any(texture is None for texture in terrain_textures.values()):
        missing = [terrain for terrain, texture in terrain_textures.items() if texture is None]
        print(f"Using per-terrain fallback colors for missing textures: {', '.join(missing)}")

    grid = build_grid()
    start_cell = choose_random_grass_start(grid)
    grid.set_start_cell(*start_cell)
    start_center = grid.cell_to_world_center(*start_cell)
    frog = Frog(*start_center, sprite_path=FROG_SPRITE if frog_sprite is not None else None)

    state = IDLE
    result: AStarResult | None = None
    reveal_cursor = 0
    show_final_path = False
    allow_diagonal = True
    show_heatmap = False
    show_cost_labels = True
    hud_message = ""
    hud_message_time = 0.0
    goal_cell: tuple[int, int] | None = None
    last_path_breakdown: list[tuple[tuple[int, int], float, float]] = []

    grid.goal_cell = None

    def reset_world() -> None:
        nonlocal grid, frog, state, result, reveal_cursor, show_final_path, goal_cell, hud_message, hud_message_time
        nonlocal start_cell
        nonlocal last_path_breakdown
        grid = build_grid()
        start_cell = choose_random_grass_start(grid)
        grid.set_start_cell(*start_cell)
        invalidate_current_path(grid, frog)
        frog.pos = pygame.Vector2(*grid.cell_to_world_center(*start_cell))
        frog.velocity.update(0, 0)
        frog.set_path([])
        state = IDLE
        result = None
        reveal_cursor = 0
        show_final_path = False
        goal_cell = None
        last_path_breakdown = []
        hud_message = ""
        hud_message_time = 0.0

    def set_message(text: str, duration: float = 1.5) -> None:
        nonlocal hud_message, hud_message_time
        hud_message = text
        hud_message_time = duration

    def handle_right_click(mouse_pos: tuple[int, int]) -> None:
        nonlocal state, result, reveal_cursor, show_final_path, goal_cell, start_cell
        nonlocal last_path_breakdown
        if state != IDLE:
            return

        start_cell = grid.world_to_cell(frog.pos.x, frog.pos.y)
        grid.set_start_cell(*start_cell)

        col, row = grid.world_to_cell(*mouse_pos)
        if not grid.in_bounds(col, row):
            set_message("Target outside the grid")
            return
        if grid.cost(col, row) == float("inf"):
            set_message("Target is a wall")
            return
        if not grid.is_reachable(col, row):
            set_message("Target unreachable from the frog", duration=2.5)
            return

        goal_cell = (col, row)
        grid.goal_cell = goal_cell
        grid.reset_search_state()
        result = find_path(grid, start_cell, goal_cell, allow_diagonal)
        last_path_breakdown = path_cost_breakdown(grid, result.path)
        reveal_cursor = 0
        show_final_path = False
        state = REVEALING
        if not result.reachable:
            set_message("Target unreachable", duration=2.5)

    def handle_left_click(mouse_pos: tuple[int, int]) -> None:
        nonlocal state, result, reveal_cursor, show_final_path, goal_cell, start_cell, last_path_breakdown
        col, row = grid.world_to_cell(*mouse_pos)
        if not grid.in_bounds(col, row):
            return

        frog_cell = grid.world_to_cell(frog.pos.x, frog.pos.y)
        if (col, row) == frog_cell:
            grid.set_terrain(col, row, Terrain.GRASS)
            grid.set_start_cell(*frog_cell)
            set_message("Cannot place wall on frog", duration=1.8)
            return

        cell = grid.get_cell(col, row)
        if cell is None:
            return

        new_terrain = Terrain.GRASS if cell.terrain == Terrain.WALL else Terrain.WALL
        if not grid.set_terrain(col, row, new_terrain):
            return

        state = IDLE
        result = None
        reveal_cursor = 0
        show_final_path = False
        goal_cell = None
        last_path_breakdown = []
        start_cell = frog_cell
        grid.set_start_cell(*start_cell)
        invalidate_current_path(grid, frog)

    def update(dt: float) -> None:
        nonlocal state, reveal_cursor, show_final_path, result, hud_message_time, hud_message, start_cell
        if hud_message_time > 0.0:
            hud_message_time = max(0.0, hud_message_time - dt)
            if hud_message_time == 0.0:
                hud_message = ""

        if state == REVEALING and result is not None:
            reveal_cursor = min(reveal_cursor + REVEAL_CELLS_PER_FRAME, len(result.explored_order))
            if reveal_cursor >= len(result.explored_order):
                if result.reachable:
                    show_final_path = True
                    world_path = [grid.cell_to_world_center(*cell) for cell in result.path]
                    frog.set_path(world_path)
                    state = FOLLOWING
                else:
                    state = IDLE
            return

        if state == FOLLOWING:
            frog.follow_path(dt)
            if frog.is_path_complete():
                start_cell = grid.world_to_cell(frog.pos.x, frog.pos.y)
                grid.set_start_cell(*start_cell)
                state = IDLE

    def draw() -> None:
        screen.fill(COLOR_BG)
        revealed_cells = set(result.explored_order[:reveal_cursor]) if result is not None else set()
        grid.draw(screen, terrain_textures, revealed_cells, show_final_path, show_heatmap, show_cost_labels, font)
        frog.draw(screen)

        y = GRID_ROWS * TILE_SIZE + 10
        lines = [
            f"Diagonal: {'ON' if allow_diagonal else 'OFF'}   Heatmap: {'ON' if show_heatmap else 'OFF'}   Cost Labels: {'ON' if show_cost_labels else 'OFF'}",
            "Right-click a reachable non-wall cell to run cost-weighted A*.",
            "Left-click toggles Wall/Grass (cannot edit frog cell).",
            "Legend: Grass=1  Mud=3  Water=5  Wall=impassable",
        ]
        if result is not None and result.reachable:
            lines.insert(1, f"Total Cost: {result.total_cost:.1f}")
        elif result is not None and not result.reachable:
            lines.insert(1, "Target unreachable")
        if hud_message:
            lines.insert(0, hud_message)

        for line in lines:
            label = font.render(line, True, COLOR_TEXT)
            screen.blit(label, (12, y))
            y += 22

        panel_width = 280
        panel_x = SCREEN_WIDTH - panel_width - 16
        panel_y = 12
        panel_height = 152
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, COLOR_PANEL_BG, panel_rect)
        pygame.draw.rect(screen, COLOR_PANEL_BORDER, panel_rect, 2)

        panel_lines = ["PATH COST"]
        if result is not None and result.reachable and last_path_breakdown:
            terrain_counts = summarize_path_terrain(grid, result.path)
            panel_lines.append(f"Total: {result.total_cost:.1f}")
            panel_lines.append(f"Path length: {len(result.path)} cells")
            panel_lines.append(f"Grass: {terrain_counts[Terrain.GRASS]} cells x {TERRAIN_COST[Terrain.GRASS]}")
            panel_lines.append(f"Mud:   {terrain_counts[Terrain.MUD]} cells x {TERRAIN_COST[Terrain.MUD]}")
            panel_lines.append(f"Water: {terrain_counts[Terrain.WATER]} cells x {TERRAIN_COST[Terrain.WATER]}")
        else:
            panel_lines.append("Total: --")
            panel_lines.append("Path length: --")
            panel_lines.append(f"Grass: -- cells x {TERRAIN_COST[Terrain.GRASS]}")
            panel_lines.append(f"Mud:   -- cells x {TERRAIN_COST[Terrain.MUD]}")
            panel_lines.append(f"Water: -- cells x {TERRAIN_COST[Terrain.WATER]}")

        text_y = panel_y + 10
        for index, panel_line in enumerate(panel_lines):
            color = (255, 255, 255) if index == 0 else COLOR_TEXT
            label = font.render(panel_line, True, color)
            screen.blit(label, (panel_x + 10, text_y))
            text_y += 24

        pygame.display.flip()

    running = True
    while running:
        dt = clock.tick(FPS) / 1500.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == getattr(pygame, f"K_{KEYBINDS['toggle_diagonal']}"):
                    allow_diagonal = not allow_diagonal
                elif event.key == getattr(pygame, f"K_{KEYBINDS['toggle_heatmap']}"):
                    show_heatmap = not show_heatmap
                elif event.key == getattr(pygame, f"K_{KEYBINDS['toggle_cost_labels']}"):
                    show_cost_labels = not show_cost_labels
                elif event.key == getattr(pygame, f"K_{KEYBINDS['restart']}"):
                    reset_world()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_left_click(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                handle_right_click(event.pos)

        update(dt)
        draw()

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())