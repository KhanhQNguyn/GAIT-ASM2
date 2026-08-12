from pathlib import Path


GRID_COLS = 20
GRID_ROWS = 14
TILE_SIZE = 48

SCREEN_WIDTH = GRID_COLS * TILE_SIZE
SCREEN_HEIGHT = GRID_ROWS * TILE_SIZE + 112
FPS = 60


class Terrain:
    GRASS = "grass"
    MUD = "mud"
    WATER = "water"
    WALL = "wall"


TERRAIN_COST = {
    Terrain.GRASS: 1,
    Terrain.MUD: 3,
    Terrain.WATER: 5,
    Terrain.WALL: float("inf"),
}

MIN_TERRAIN_COST = min(value for value in TERRAIN_COST.values() if value != float("inf"))

TERRAIN_COLOR = {
    Terrain.GRASS: (66, 145, 73),
    Terrain.MUD: (123, 85, 42),
    Terrain.WATER: (56, 111, 184),
    Terrain.WALL: (47, 49, 57),
}

FROG_SPEED = 220.0

COLOR_EXPLORED = (90, 140, 255)
COLOR_FRONTIER = (255, 200, 70)
COLOR_PATH = (0, 230, 90)
COLOR_TEXT = (240, 240, 240)
COLOR_BG = (18, 20, 26)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
FROG_SPRITE = ASSETS_DIR / "frog_sprite.png"
GRASS_TEXTURE = ASSETS_DIR / "tileset.png"
MUD_TEXTURE = ASSETS_DIR / "mud.png"
WATER_TEXTURE = ASSETS_DIR / "water.png"
WALL_TEXTURE = ASSETS_DIR / "stone.png"

REVEAL_CELLS_PER_FRAME = 5
FONT_SIZE = 20

COLOR_PANEL_BG = (12, 14, 18)
COLOR_PANEL_BORDER = (88, 97, 116)

KEYBINDS = {
    "toggle_diagonal": "d",
    "toggle_heatmap": "h",
    "toggle_cost_labels": "c",
    "restart": "r",
}