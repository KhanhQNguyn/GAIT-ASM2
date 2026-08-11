from pathlib import Path
import pygame

# 1. Window & Grid Configuration
TILE_SIZE = 48
GRID_COLS = 20
GRID_ROWS = 14
SIDEBAR_WIDTH = 320

GRID_WIDTH = GRID_COLS * TILE_SIZE
GRID_HEIGHT = GRID_ROWS * TILE_SIZE

SCREEN_WIDTH = GRID_WIDTH + SIDEBAR_WIDTH
SCREEN_HEIGHT = GRID_HEIGHT
FPS = 60

# 2. Terrain Definition and Cost Table
class Terrain:
    GRASS = "grass"
    MUD = "mud"
    WATER = "water"
    WALL = "wall"

TERRAIN_COST = {
    Terrain.GRASS: 1.0,
    Terrain.MUD: 3.0,
    Terrain.WATER: 5.0,
    Terrain.WALL: float("inf"),
}

TERRAIN_COLOR = {  # Fallback colors if sprite tileset fails to load
    Terrain.GRASS: (86, 168, 82),
    Terrain.MUD: (120, 84, 51),
    Terrain.WATER: (58, 122, 199),
    Terrain.WALL: (40, 40, 40),
}

# 3. Pathfinding & Steering Constants
PATH_RADIUS = 10.0            # px tolerance before steering correction kicks in
WAYPOINT_ARRIVAL_RADIUS = 6.0 # px radius to consider waypoint reached
FROG_MAX_SPEED = 220.0        # px/sec
FROG_MAX_FORCE = 900.0        # steering force limit
FROG_SLOW_RADIUS = 60.0       # px slowing radius for arrival behavior
FROG_PREDICT_DIST = 25.0      # ahead prediction distance for Reynolds path following

# 4. Color Palette
COLOR_EXPLORED = (255, 215, 0, 90)   # Translucent gold for heatmap
COLOR_FRONTIER = (255, 140, 0, 90)   # Translucent orange for frontier
COLOR_PATH = (0, 230, 90)            # Vivid green for shortest path
COLOR_TEXT = (240, 240, 240)
COLOR_BG = (18, 18, 24)
COLOR_SIDEBAR_BG = (28, 28, 38)
COLOR_GRID_LINE = (50, 50, 60, 100)

# 5. Asset Paths
ASSETS_DIR = Path(__file__).parent / "assets"
FROG_SPRITE = ASSETS_DIR / "frog_sprite.png"
TERRAIN_TILESET = ASSETS_DIR / "terrain_tiles.png"
C4_BOARD_SPRITE = ASSETS_DIR / "c4_board.png"
TOKEN_ASSETS = {
    "red": ASSETS_DIR / "tokens" / "token_red.png",
    "yellow": ASSETS_DIR / "tokens" / "token_yellow.png",
    "empty": ASSETS_DIR / "tokens" / "token_empty.png",
}

# 6. MCTS Tuning Constants
MCTS_ITERATIONS = 4000
MCTS_TIME_LIMIT_SEC = 2.0
MCTS_C_PARAM = 1.4
MCTS_DIFFICULTIES = {
    "easy": 400,
    "medium": 2000,
    "hard": 8000,
}

# 7. Reveal Animation Constants
REVEAL_CELLS_PER_FRAME = 6
REVEAL_FONT_SIZE = 14

# 8. Keybindings Dictionary
KEYBINDS = {
    "toggle_diagonal": pygame.K_g,
    "toggle_heatmap": pygame.K_o,
    "toggle_cost_labels": pygame.K_n,
    "restart": pygame.K_r,
    "menu": pygame.K_ESCAPE,
}
