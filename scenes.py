from typing import Optional, List, Dict, Tuple, Union
import math
import queue
import pygame
from settings import (
    TILE_SIZE,
    GRID_COLS,
    GRID_ROWS,
    SIDEBAR_WIDTH,
    GRID_WIDTH,
    GRID_HEIGHT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    KEYBINDS,
    REVEAL_CELLS_PER_FRAME,
    REVEAL_FONT_SIZE,
    COLOR_BG,
    COLOR_SIDEBAR_BG,
    COLOR_TEXT,
    COLOR_PATH,
    TERRAIN_COST,
    Terrain,
)
from grid import TerrainGrid
from pathfinding import find_path, AStarResult
from frog import Frog
from mcts import Connect4State, MCTSResult, AIWorker, COLS, ROWS, PLAYER1, PLAYER2

def draw_stats_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    result: Optional[MCTSResult],
    board_state: Connect4State,
    font: pygame.font.Font,
    small_font: pygame.font.Font
):
    # Fill sidebar panel background
    pygame.draw.rect(surface, COLOR_SIDEBAR_BG, rect)
    pygame.draw.line(surface, (60, 60, 80), (rect.left, rect.top), (rect.left, rect.bottom), 2)

    padding = 16
    x = rect.left + padding
    y = rect.top + padding

    # Header title
    title_surf = font.render("MCTS STATS PANEL", True, (255, 215, 0))
    surface.blit(title_surf, (x, y))
    y += 30

    if result is None:
        info_surf = small_font.render("Waiting for AI calculation...", True, (160, 160, 160))
        surface.blit(info_surf, (x, y))
        return

    # Iterations summary header
    iter_text = f"{result.iterations_run} iterations in {result.elapsed_sec:.2f}s"
    iter_surf = small_font.render(iter_text, True, (200, 200, 220))
    surface.blit(iter_surf, (x, y))
    y += 26

    # Column statistics table header
    col_hdr = small_font.render("COL  VISITS  WIN%    UCB SCORE", True, (150, 150, 170))
    surface.blit(col_hdr, (x, y))
    y += 22

    # Render each column (0-6)
    for col in range(COLS):
        stat = result.stats.get(col)
        if stat is None:
            continue

        is_chosen = (col == result.chosen_column)
        row_bg_color = (45, 65, 45) if is_chosen else (34, 34, 46)

        row_rect = pygame.Rect(x - 4, y - 2, rect.width - (padding * 2) + 8, 30)
        pygame.draw.rect(surface, row_bg_color, row_rect, border_radius=4)
        if is_chosen:
            pygame.draw.rect(surface, (0, 230, 90), row_rect, width=1, border_radius=4)

        col_str = f" #{col} "
        col_color = (0, 255, 120) if is_chosen else (220, 220, 220)
        col_surf = small_font.render(col_str, True, col_color)
        surface.blit(col_surf, (x, y + 4))

        visits_str = f"{stat.visits:5d}"
        visits_surf = small_font.render(visits_str, True, (200, 200, 200))
        surface.blit(visits_surf, (x + 45, y + 4))

        # Win-rate progress bar (Gradient from red to green)
        bar_x = x + 105
        bar_y = y + 8
        bar_w = 60
        bar_h = 12
        pygame.draw.rect(surface, (20, 20, 28), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        
        fill_w = int(bar_w * max(0.0, min(1.0, stat.win_rate)))
        if fill_w > 0:
            r_val = int(255 * (1.0 - stat.win_rate))
            g_val = int(255 * stat.win_rate)
            bar_color = (r_val, g_val, 40)
            pygame.draw.rect(surface, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=2)

        # UCB score text
        if stat.ucb_score == float("inf"):
            ucb_str = "  INF"
        else:
            ucb_str = f"{stat.ucb_score:6.2f}"
        ucb_surf = small_font.render(ucb_str, True, (255, 230, 100) if is_chosen else (180, 180, 180))
        surface.blit(ucb_surf, (x + 180, y + 4))

        y += 34

    # Legend / Chosen column callout
    if result.chosen_column is not None:
        y += 10
        chosen_stat = result.stats[result.chosen_column]
        callout_lines = [
            f"CHOSEN ACTION: Column {result.chosen_column}",
            f"UCB Score: {chosen_stat.ucb_score:.3f}",
            f"Visits: {chosen_stat.visits} | Win Rate: {chosen_stat.win_rate * 100:.1f}%",
        ]
        for line in callout_lines:
            c_surf = small_font.render(line, True, (0, 230, 90))
            surface.blit(c_surf, (x, y))
            y += 20

class PathfindingScene:
    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font, tileset: Optional[pygame.Surface] = None):
        self.font = font
        self.small_font = small_font
        self.tileset = tileset

        self.grid = TerrainGrid(GRID_COLS, GRID_ROWS)
        self.start_cell = (1, 1)
        self.goal_cell = (GRID_COLS - 2, GRID_ROWS - 2)

        frog_world = self.grid.cell_to_world_center(*self.start_cell)
        self.frog = Frog(frog_world[0], frog_world[1])

        self.allow_diagonal = True
        self.show_heatmap = True
        self.show_cost_labels = True

        self.state = "IDLE"  # IDLE -> REVEALING -> FOLLOWING -> IDLE
        self.result: Optional[AStarResult] = None
        self.reveal_cursor = 0

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == KEYBINDS["toggle_diagonal"]:
                self.allow_diagonal = not self.allow_diagonal
            elif event.key == KEYBINDS["toggle_heatmap"]:
                self.show_heatmap = not self.show_heatmap
            elif event.key == KEYBINDS["toggle_cost_labels"]:
                self.show_cost_labels = not self.show_cost_labels
            elif event.key == KEYBINDS["restart"]:
                self.grid = TerrainGrid(GRID_COLS, GRID_ROWS)
                self.state = "IDLE"
                self.result = None
                frog_world = self.grid.cell_to_world_center(*self.start_cell)
                self.frog = Frog(frog_world[0], frog_world[1])

        elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "IDLE":
            mx, my = event.pos
            if mx < GRID_WIDTH and my < GRID_HEIGHT:
                col, row = self.grid.world_to_cell(mx, my)
                if event.button == 1:  # Left-click set goal
                    if self.grid.in_bounds(col, row) and self.grid.cost(col, row) < float("inf"):
                        self.goal_cell = (col, row)
                        self._trigger_search()
                elif event.button == 3:  # Right-click set start
                    if self.grid.in_bounds(col, row) and self.grid.cost(col, row) < float("inf"):
                        self.start_cell = (col, row)
                        frog_world = self.grid.cell_to_world_center(*self.start_cell)
                        self.frog.pos = pygame.Vector2(frog_world[0], frog_world[1])
                        self._trigger_search()

    def _trigger_search(self):
        self.result = find_path(self.grid, self.start_cell, self.goal_cell, self.allow_diagonal)
        self.reveal_cursor = 0
        self.state = "REVEALING"

    def update(self, dt: float):
        if self.state == "REVEALING":
            if self.result:
                self.reveal_cursor += REVEAL_CELLS_PER_FRAME
                if self.reveal_cursor >= len(self.result.explored_order):
                    self.reveal_cursor = len(self.result.explored_order)
                    if self.result.reachable:
                        self.frog.set_path(self.result.path)
                        self.state = "FOLLOWING"
                    else:
                        self.state = "IDLE"
        elif self.state == "FOLLOWING":
            self.frog.follow_path(dt)
            if self.frog.is_path_complete():
                self.state = "IDLE"

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)

        # Draw Grid
        self.grid.draw(surface, self.tileset, self.show_heatmap, self.show_cost_labels, self.small_font)

        # Draw Start and Goal markers
        sx, sy = self.grid.cell_to_world_center(*self.start_cell)
        gx, gy = self.grid.cell_to_world_center(*self.goal_cell)

        pygame.draw.circle(surface, (0, 255, 255), (int(sx), int(sy)), 12, 3)  # Start cyan
        pygame.draw.circle(surface, (255, 50, 50), (int(gx), int(gy)), 12, 3)  # Goal red

        # Draw Frog
        self.frog.draw(surface)

        # Draw HUD Panel on sidebar area
        sidebar_rect = pygame.Rect(GRID_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(surface, COLOR_SIDEBAR_BG, sidebar_rect)
        pygame.draw.line(surface, (60, 60, 80), (GRID_WIDTH, 0), (GRID_WIDTH, SCREEN_HEIGHT), 2)

        x = GRID_WIDTH + 16
        y = 16

        title = self.font.render("A* PATHFINDING", True, (255, 215, 0))
        surface.blit(title, (x, y))
        y += 32

        hud_lines = [
            f"State: {self.state}",
            f"Diagonal (G): {'ON' if self.allow_diagonal else 'OFF'}",
            f"Heatmap  (O): {'ON' if self.show_heatmap else 'OFF'}",
            f"Cost Lbl (N): {'ON' if self.show_cost_labels else 'OFF'}",
            "",
            "CONTROLS:",
            " L-Click: Set Goal",
            " R-Click: Set Start",
            " R Key: Regenerate Grid",
            " ESC: Return to Menu",
            "",
        ]
        for line in hud_lines:
            txt = self.small_font.render(line, True, COLOR_TEXT)
            surface.blit(txt, (x, y))
            y += 20

        # Path metrics display
        if self.result:
            cost_str = f"{self.result.total_cost:.1f}" if self.result.reachable else "UNREACHABLE"
            cost_color = COLOR_PATH if self.result.reachable else (255, 80, 80)
            cost_txt = self.font.render(f"Total Cost: {cost_str}", True, cost_color)
            surface.blit(cost_txt, (x, y))
            y += 30

        # Terrain Cost Legend Table
        y += 10
        leg_hdr = self.small_font.render("TERRAIN COST LEGEND:", True, (200, 200, 220))
        surface.blit(leg_hdr, (x, y))
        y += 22

        legend_items = [
            ("Grass", TERRAIN_COST[Terrain.GRASS], (86, 168, 82)),
            ("Mud", TERRAIN_COST[Terrain.MUD], (120, 84, 51)),
            ("Water", TERRAIN_COST[Terrain.WATER], (58, 122, 199)),
            ("Wall", "INF", (40, 40, 40)),
        ]
        for name, c_val, col in legend_items:
            sq = pygame.Rect(x, y + 2, 14, 14)
            pygame.draw.rect(surface, col, sq)
            pygame.draw.rect(surface, (255, 255, 255), sq, 1)
            
            l_txt = self.small_font.render(f"{name:6s} -> Cost {c_val}", True, COLOR_TEXT)
            surface.blit(l_txt, (x + 22, y))
            y += 22

class Connect4Scene:
    def __init__(
        self,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
        vs_ai: bool = True,
        difficulty: str = "medium",
        board_sprite: Optional[pygame.Surface] = None,
        token_sprites: Optional[Dict[str, pygame.Surface]] = None
    ):
        self.font = font
        self.small_font = small_font
        self.vs_ai = vs_ai
        self.difficulty = difficulty
        self.board_sprite = board_sprite
        self.token_sprites = token_sprites or {}

        self.state = Connect4State()
        self.result_queue = queue.Queue()
        self.worker: Optional[AIWorker] = None
        self.last_result: Optional[MCTSResult] = None
        self.auto_play = False

        if not self.vs_ai:
            # AI vs AI starts worker immediately for Player 1
            self._spawn_worker()

    def _spawn_worker(self):
        if self.worker is None and not self.state.is_terminal():
            self.worker = AIWorker(self.state, self.difficulty, self.result_queue)
            self.worker.start()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == KEYBINDS["restart"]:
                self.state = Connect4State()
                self.worker = None
                self.last_result = None
                self.auto_play = False
                if not self.vs_ai:
                    self._spawn_worker()
            elif event.key == pygame.K_SPACE and not self.vs_ai:
                self.auto_play = not self.auto_play

        elif event.type == pygame.MOUSEBUTTONDOWN and self.vs_ai:
            if self.worker is None and not self.state.is_terminal() and self.state.current_player == PLAYER1:
                mx, my = event.pos
                if mx < GRID_WIDTH:
                    col = int(mx // (GRID_WIDTH / COLS))
                    if 0 <= col < COLS and col in self.state.get_legal_moves():
                        self.state.make_move(col)
                        if not self.state.is_terminal():
                            self._spawn_worker()

    def update(self, dt: float):
        # Poll result queue
        if self.worker is not None:
            try:
                res = self.result_queue.get_nowait()
                if isinstance(res, MCTSResult):
                    self.last_result = res
                    if res.chosen_column is not None:
                        self.state.make_move(res.chosen_column)
                self.worker = None

                # If AI vs AI or vs_ai AI turn, spawn next worker
                if not self.state.is_terminal():
                    if not self.vs_ai or (self.vs_ai and self.state.current_player == PLAYER2):
                        if not self.vs_ai and not self.auto_play:
                            pass # Wait for space key step
                        else:
                            self._spawn_worker()
            except queue.Empty:
                pass

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)

        # Draw Connect 4 Board Area
        cell_w = GRID_WIDTH / COLS
        cell_h = GRID_HEIGHT / ROWS

        board_rect = pygame.Rect(0, 0, GRID_WIDTH, GRID_HEIGHT)
        pygame.draw.rect(surface, (0, 60, 170), board_rect)

        # Draw tokens and grid cutouts
        for r in range(ROWS):
            for c in range(COLS):
                cx = int(c * cell_w + cell_w / 2)
                cy = int(r * cell_h + cell_h / 2)
                radius = int(min(cell_w, cell_h) * 0.4)

                val = self.state.board[r][c]
                if val == PLAYER1:
                    pygame.draw.circle(surface, (220, 40, 40), (cx, cy), radius)
                elif val == PLAYER2:
                    pygame.draw.circle(surface, (230, 210, 40), (cx, cy), radius)
                else:
                    pygame.draw.circle(surface, COLOR_BG, (cx, cy), radius)

        # Draw thinking indicator
        if self.worker is not None:
            think_surf = self.font.render("AI THINKING...", True, (255, 215, 0))
            think_rect = think_surf.get_rect(center=(GRID_WIDTH // 2, 30))
            bg_rect = think_rect.inflate(20, 10)
            pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect, border_radius=6)
            surface.blit(think_surf, think_rect)

        # Draw terminal game winner banner
        if self.state.is_terminal():
            winner = self.state.check_winner()
            if winner == PLAYER1:
                w_str = "PLAYER 1 (RED) WINS!"
                w_col = (255, 80, 80)
            elif winner == PLAYER2:
                w_str = "PLAYER 2 (YELLOW) WINS!"
                w_col = (255, 230, 80)
            else:
                w_str = "GAME DRAW!"
                w_col = (200, 200, 200)

            win_surf = self.font.render(w_str, True, w_col)
            win_rect = win_surf.get_rect(center=(GRID_WIDTH // 2, GRID_HEIGHT // 2))
            bg_rect = win_rect.inflate(40, 20)
            pygame.draw.rect(surface, (10, 10, 20), bg_rect, border_radius=8)
            pygame.draw.rect(surface, w_col, bg_rect, width=2, border_radius=8)
            surface.blit(win_surf, win_rect)

        # Draw Stats Panel on sidebar
        sidebar_rect = pygame.Rect(GRID_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        draw_stats_panel(surface, sidebar_rect, self.last_result, self.state, self.font, self.small_font)

class MenuScene:
    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font):
        self.font = font
        self.small_font = small_font
        self.difficulty = "medium"
        self.difficulties = ["easy", "medium", "hard"]

        self.buttons = [
            ("A* Pathfinding (Weighted Terrain)", "PATHFINDING"),
            ("Connect 4: Human vs AI", "C4_VS_AI"),
            ("Connect 4: AI vs AI", "C4_AI_VS_AI"),
        ]

    def handle_event(self, event: pygame.event.Event) -> Tuple[Optional[str], str]:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Difficulty selector toggle
            diff_y = 440
            for i, d in enumerate(self.difficulties):
                bx = SCREEN_WIDTH // 2 - 150 + i * 105
                rect = pygame.Rect(bx, diff_y, 90, 36)
                if rect.collidepoint(mx, my):
                    self.difficulty = d
                    return None, self.difficulty

            # Main menu scene buttons
            start_y = 200
            for i, (label, mode) in enumerate(self.buttons):
                rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, start_y + i * 70, 400, 50)
                if rect.collidepoint(mx, my):
                    return mode, self.difficulty

        return None, self.difficulty

    def update(self, dt: float):
        pass

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BG)

        # Title
        t_surf = self.font.render("GAIT ASSIGNMENT 2: A* & THREADED MCTS", True, (255, 215, 0))
        t_rect = t_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
        surface.blit(t_surf, t_rect)

        # Mode buttons
        start_y = 200
        for i, (label, mode) in enumerate(self.buttons):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, start_y + i * 70, 400, 50)
            pygame.draw.rect(surface, (35, 35, 50), rect, border_radius=8)
            pygame.draw.rect(surface, (80, 80, 110), rect, width=2, border_radius=8)
            
            lbl_surf = self.font.render(label, True, COLOR_TEXT)
            lbl_rect = lbl_surf.get_rect(center=rect.center)
            surface.blit(lbl_surf, lbl_rect)

        # Difficulty Selector
        diff_y = 440
        lbl = self.small_font.render("MCTS DIFFICULTY LEVEL:", True, (180, 180, 200))
        surface.blit(lbl, (SCREEN_WIDTH // 2 - 150, diff_y - 24))

        for i, d in enumerate(self.difficulties):
            bx = SCREEN_WIDTH // 2 - 150 + i * 105
            rect = pygame.Rect(bx, diff_y, 90, 36)
            is_sel = (d == self.difficulty)
            
            bg = (0, 180, 90) if is_sel else (40, 40, 55)
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            pygame.draw.rect(surface, (255, 255, 255) if is_sel else (80, 80, 100), rect, width=1, border_radius=6)

            d_surf = self.small_font.render(d.upper(), True, (255, 255, 255))
            d_rect = d_surf.get_rect(center=rect.center)
            surface.blit(d_surf, d_rect)
