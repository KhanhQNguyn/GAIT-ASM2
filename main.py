import sys
import pygame
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    COLOR_BG,
    KEYBINDS,
    FROG_SPRITE,
    TERRAIN_TILESET,
    C4_BOARD_SPRITE,
    TOKEN_ASSETS,
)
from scenes import MenuScene, PathfindingScene, Connect4Scene

def main():
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("GAIT Assignment 2: A* & Threaded MCTS Connect 4")
    clock = pygame.time.Clock()

    # Load Fonts
    font = pygame.font.SysFont("Helvetica", 18, bold=True)
    small_font = pygame.font.SysFont("Monospace", 13)

    # Asset loading and graceful fallback detector
    loaded_assets = {
        "frog": None,
        "tileset": None,
        "board": None,
        "tokens": {},
    }

    if FROG_SPRITE.exists():
        try:
            loaded_assets["frog"] = str(FROG_SPRITE)
            print(f"[ASSETS] Loaded Frog sprite: {FROG_SPRITE}")
        except Exception as e:
            print(f"[ASSETS] Failed to load Frog sprite: {e}")

    if TERRAIN_TILESET.exists():
        try:
            loaded_assets["tileset"] = pygame.image.load(str(TERRAIN_TILESET)).convert_alpha()
            print(f"[ASSETS] Loaded Terrain tileset: {TERRAIN_TILESET}")
        except Exception as e:
            print(f"[ASSETS] Failed to load Terrain tileset: {e}")

    menu_scene = MenuScene(font, small_font)
    current_scene = menu_scene
    current_mode = "MENU"
    difficulty = "medium"

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # seconds delta time

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN and event.key == KEYBINDS["menu"]:
                current_scene = menu_scene
                current_mode = "MENU"
                continue

            if current_mode == "MENU":
                selected_mode, selected_diff = current_scene.handle_event(event)
                difficulty = selected_diff
                if selected_mode is not None:
                    current_mode = selected_mode
                    if selected_mode == "PATHFINDING":
                        current_scene = PathfindingScene(font, small_font, loaded_assets["tileset"])
                    elif selected_mode == "C4_VS_AI":
                        current_scene = Connect4Scene(font, small_font, vs_ai=True, difficulty=difficulty)
                    elif selected_mode == "C4_AI_VS_AI":
                        current_scene = Connect4Scene(font, small_font, vs_ai=False, difficulty=difficulty)
            else:
                current_scene.handle_event(event)

        current_scene.update(dt)

        screen.fill(COLOR_BG)
        current_scene.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
