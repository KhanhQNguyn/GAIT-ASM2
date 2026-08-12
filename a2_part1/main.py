from __future__ import annotations

import pygame

from frog import Frog
from grid import TerrainGrid
from pathfinding import AStarResult, find_path
from settings import (
    COLOR_BG,
    COLOR_TEXT,
    FONT_SIZE,
    FPS,
    FROG_SPRITE,
    GRID_COLS,
    GRID_ROWS,
    KEYBINDS,
    REVEAL_CELLS_PER_FRAME,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILESET,
)


IDLE = "idle"
REVEALING = "revealing"
FOLLOWING = "following"


def build_demo_layout() -> list[str]:
    rows = [["." for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

    for row_index in range(1, 4):
        for col_index in range(2, 6):
            rows[row_index][col_index] = "m"

    for row_index in range(8, 12):
        for col_index in range(12, 17):
            rows[row_index][col_index] = "m"

    for row_index in range(4, 7):
        for col_index in range(7, 14):
            rows[row_index][col_index] = "w"

    for row_index in range(0, 11):
        if row_index != 5:
            rows[row_index][10] = "#"

    for row_index in range(10, 13):
        rows[row_index][15] = "#"
        rows[row_index][16] = "#"

    for col_index in range(0, 4):
        rows[7][col_index] = "w"

    rows[1][1] = "."
    rows[1][2] = "."
    rows[2][1] = "."
    rows[2][2] = "."

    return ["".join(row) for row in rows]


def build_grid() -> TerrainGrid:
    layout = build_demo_layout()
    grid = TerrainGrid(GRID_COLS, GRID_ROWS, layout=layout)
    grid.set_start_cell(0, 0)
    return grid


def load_surface(path):
    try:
        if path.exists():
            return pygame.image.load(str(path)).convert_alpha()
    except Exception as exc:
        print(f"Failed to load {path.name}: {exc}")
    return None


def main() -> int:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("A* over a weighted-cost grid")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, FONT_SIZE)

    frog_sprite = load_surface(FROG_SPRITE)
    tileset = load_surface(TILESET)
    use_sprites = frog_sprite is not None and tileset is not None
    if not use_sprites:
        print("Running with fallback drawing because sprite assets could not be loaded.")
        frog_sprite = None
        tileset = None

    grid = build_grid()
    start_cell = (0, 0)
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

    grid.goal_cell = None

    def reset_world() -> None:
        nonlocal grid, frog, state, result, reveal_cursor, show_final_path, goal_cell, hud_message, hud_message_time
        nonlocal start_cell
        grid = build_grid()
        start_cell = (0, 0)
        grid.goal_cell = None
        grid.set_start_cell(*start_cell)
        frog.pos = pygame.Vector2(*grid.cell_to_world_center(*start_cell))
        frog.velocity.update(0, 0)
        frog.set_path([])
        state = IDLE
        result = None
        reveal_cursor = 0
        show_final_path = False
        goal_cell = None
        hud_message = ""
        hud_message_time = 0.0

    def set_message(text: str, duration: float = 1.5) -> None:
        nonlocal hud_message, hud_message_time
        hud_message = text
        hud_message_time = duration

    def handle_right_click(mouse_pos: tuple[int, int]) -> None:
        nonlocal state, result, reveal_cursor, show_final_path, goal_cell, start_cell
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
        reveal_cursor = 0
        show_final_path = False
        state = REVEALING
        if not result.reachable:
            set_message("Target unreachable", duration=2.5)

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
        grid.draw(screen, tileset, revealed_cells, show_final_path, show_heatmap, show_cost_labels, font)
        frog.draw(screen)

        y = GRID_ROWS * 48 + 10
        lines = [
            f"Diagonal: {'ON' if allow_diagonal else 'OFF'}   Heatmap: {'ON' if show_heatmap else 'OFF'}   Cost Labels: {'ON' if show_cost_labels else 'OFF'}",
            "Right-click a reachable non-wall cell to run cost-weighted A*.",
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

        pygame.display.flip()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                handle_right_click(event.pos)

        update(dt)
        draw()

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())