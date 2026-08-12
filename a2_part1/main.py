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
    GRID_PIXEL_WIDTH,
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

import io
import struct
import math

def create_wav_sound(freq=440.0, duration=0.1, volume=0.5):
    if not pygame.mixer.get_init():
        return None
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    max_amp = int(32767 * volume)
    audio_data = bytearray()
    for i in range(n_samples):
        env = 1.0
        if i < 441: env = i / 441.0
        elif i > n_samples - 441: env = (n_samples - i) / 441.0
        val = int(max_amp * env * math.sin(2 * math.pi * freq * i / sample_rate))
        audio_data.extend(struct.pack('<h', val))
        audio_data.extend(struct.pack('<h', val)) # stereo
    
    wav_header = b'RIFF'
    wav_header += struct.pack('<I', 36 + len(audio_data))
    wav_header += b'WAVEfmt '
    wav_header += struct.pack('<I', 16)
    wav_header += struct.pack('<H', 1)
    wav_header += struct.pack('<H', 2)
    wav_header += struct.pack('<I', sample_rate)
    wav_header += struct.pack('<I', sample_rate * 4)
    wav_header += struct.pack('<H', 4)
    wav_header += struct.pack('<H', 16)
    wav_header += b'data'
    wav_header += struct.pack('<I', len(audio_data))
    
    try:
        return pygame.mixer.Sound(io.BytesIO(wav_header + audio_data))
    except:
        return None


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
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("A* over a weighted-cost grid")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, FONT_SIZE)

    sound_step = create_wav_sound(400, 0.05, 0.05)
    sound_think = create_wav_sound(800, 0.02, 0.02)
    sound_goal = create_wav_sound(500, 0.3, 0.1)
    sound_error = create_wav_sound(150, 0.2, 0.1)

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

    particles = []
    frog_step_dist = 0.0
    think_timer = 0.0

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
            if sound_error: sound_error.play()
            return
        if grid.cost(col, row) == float("inf"):
            set_message("Target is a wall")
            if sound_error: sound_error.play()
            return
        if not grid.is_reachable(col, row):
            set_message("Target unreachable from the frog", duration=2.5)
            if sound_error: sound_error.play()
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
            if sound_error: sound_error.play()

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
            if sound_error: sound_error.play()
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
        nonlocal frog_step_dist, think_timer

        if hud_message_time > 0.0:
            hud_message_time = max(0.0, hud_message_time - dt)
            if hud_message_time == 0.0:
                hud_message = ""

        # Update particles
        for p in particles[:]:
            p["pos"] += p["vel"] * dt
            p["life"] -= dt
            if p["life"] <= 0:
                particles.remove(p)

        if state == REVEALING and result is not None:
            think_timer += dt
            if think_timer > 0.1:
                think_timer = 0
                if sound_think: sound_think.play()
            
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
            speed = frog.velocity.length()
            if speed > 10:
                if random.random() < 0.3:
                    particles.append({
                        "pos": pygame.Vector2(frog.pos),
                        "vel": pygame.Vector2(random.uniform(-20, 20), random.uniform(-20, 20)),
                        "life": random.uniform(0.2, 0.4),
                        "color": (150, 200, 150)
                    })
                frog_step_dist += speed * dt
                if frog_step_dist > TILE_SIZE * 0.8:
                    frog_step_dist -= TILE_SIZE * 0.8
                    if sound_step: sound_step.play()

            frog.follow_path(dt)
            if frog.is_path_complete():
                start_cell = grid.world_to_cell(frog.pos.x, frog.pos.y)
                grid.set_start_cell(*start_cell)
                state = IDLE
                frog_step_dist = 0
                if sound_goal: sound_goal.play()
                for _ in range(15):
                    particles.append({
                        "pos": pygame.Vector2(frog.pos),
                        "vel": pygame.Vector2(random.uniform(-80, 80), random.uniform(-80, 80)),
                        "life": random.uniform(0.3, 0.6),
                        "color": (255, 215, 0)
                    })

    def draw() -> None:
        screen.fill(COLOR_BG)
        revealed_cells = set(result.explored_order[:reveal_cursor]) if result is not None else set()
        grid.draw(screen, terrain_textures, revealed_cells, show_final_path, show_heatmap, show_cost_labels, font)
        frog.draw(screen)

        # Draw particles
        for p in particles:
            alpha = int(255 * max(0, p["life"] / 0.6))
            surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p["color"], alpha), (3, 3), 3)
            screen.blit(surf, (int(p["pos"].x - 3), int(p["pos"].y - 3)))

        if state == REVEALING:
            blink = int((pygame.time.get_ticks() / 150) % 2)
            if blink:
                think_surf = font.render("THINKING...", True, (255, 255, 0))
                screen.blit(think_surf, (frog.pos.x - 40, frog.pos.y - 40))

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

        # This panel must never share pixel space with the grid canvas — it lives in the sidebar only.
        panel_width = SCREEN_WIDTH - GRID_PIXEL_WIDTH - 32
        panel_x = GRID_PIXEL_WIDTH + 16
        panel_y = 12
        panel_height = SCREEN_HEIGHT - 24
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