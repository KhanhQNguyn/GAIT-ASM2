"""
tools/generate_placeholder_assets.py
Run once from the part2/ directory to generate placeholder disc PNGs so
the asset pipeline can be verified end-to-end before real artwork is added.

Usage:
    python3 tools/generate_placeholder_assets.py

Output: assets/player1_disc.png, assets/player2_disc.png
        assets/ai_alpha_avatar.png, assets/ai_beta_avatar.png
"""

import os
import sys

# Must be run from part2/ directory
ASSET_DIR = "assets"

try:
    import pygame
except ImportError:
    print("pygame not found — install with: pip install pygame")
    sys.exit(1)

pygame.init()

RADIUS = 45  # 90x90 disc


def make_disc(size, base_color, highlight_color, filename):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    r = size // 2 - 2

    # Base disc
    pygame.draw.circle(surf, base_color, (cx, cy), r)

    # Darkened rim
    rim = tuple(max(0, c - 40) for c in base_color[:3])
    pygame.draw.circle(surf, (*rim, 255), (cx, cy), r, width=3)

    # Glossy highlight ellipse (top-left)
    hl_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    hl_w = r
    hl_h = int(r * 0.5)
    hl_x = cx - hl_w // 2
    hl_y = cy - r + 8
    pygame.draw.ellipse(hl_surf, (*highlight_color, 110), (hl_x, hl_y, hl_w, hl_h))
    surf.blit(hl_surf, (0, 0))

    path = os.path.join(ASSET_DIR, filename)
    pygame.image.save(surf, path)
    print(f"  Saved: {path}")


def make_avatar(size, base_color, filename):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    r = size // 2 - 2
    pygame.draw.circle(surf, base_color, (size // 2, size // 2), r)
    # Simple "AI" marker — small inner ring
    pygame.draw.circle(surf, (255, 255, 255, 160), (size // 2, size // 2), r // 2, width=2)
    path = os.path.join(ASSET_DIR, filename)
    pygame.image.save(surf, path)
    print(f"  Saved: {path}")


os.makedirs(ASSET_DIR, exist_ok=True)
print("Generating placeholder assets...")

# Coral disc (Player 1)
make_disc(90, (204, 120, 92, 255), (224, 164, 140), "player1_disc.png")

# Amber disc (Player 2)
make_disc(90, (232, 165, 90, 255), (240, 192, 132), "player2_disc.png")

# Avatar icons
make_avatar(32, (204, 120, 92, 255), "ai_alpha_avatar.png")
make_avatar(32, (232, 165, 90, 255), "ai_beta_avatar.png")


# ── Prompt 5 additions ─────────────────────────────────────────────────────
# BOARD_COLOR / BOARD_HOLE_COLOR hardcoded below (matching connect4_mcts.py)
# to keep this script standalone — never import connect4_mcts.py here.

def make_board_texture(width, height, filename):
    """Subtle dark-navy gradient texture for the board area."""
    surf = pygame.Surface((width, height))
    BOARD_COLOR      = (24, 23, 21)
    BOARD_HOLE_COLOR = (31, 30, 27)
    for y in range(height):
        t = y / height
        r = int(BOARD_COLOR[0] + (BOARD_HOLE_COLOR[0] - BOARD_COLOR[0]) * t)
        g = int(BOARD_COLOR[1] + (BOARD_HOLE_COLOR[1] - BOARD_COLOR[1]) * t)
        b = int(BOARD_COLOR[2] + (BOARD_HOLE_COLOR[2] - BOARD_COLOR[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
    path = os.path.join(ASSET_DIR, filename)
    pygame.image.save(surf, path)
    print(f"  Saved: {path}")


def make_menu_background(width, height, filename):
    """Cream canvas background with faint concentric hairline circles."""
    CANVAS_COLOR   = (250, 249, 245)  # colors.canvas
    HAIRLINE_COLOR = (230, 223, 216)  # colors.hairline
    surf = pygame.Surface((width, height))
    surf.fill(CANVAS_COLOR)
    cx, cy = width // 2, height // 2
    for radius in range(80, max(width, height), 80):
        pygame.draw.circle(surf, HAIRLINE_COLOR, (cx, cy), radius, width=1)
    path = os.path.join(ASSET_DIR, filename)
    pygame.image.save(surf, path)
    print(f"  Saved: {path}")


make_board_texture(700, 600, "board_texture.png")
make_menu_background(700, 1010, "menu_background.png")

print("Done. Run the game to verify assets load correctly.")
pygame.quit()

