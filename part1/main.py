# ============================================================================
# main.py
# Purpose
#   Entry point and game loop. Handles input, updates agents, and draws frames.
# Mental model
#   Each frame: measure dt, process input, update world and agents, draw UI.
#   Agents do not draw themselves until update is finished for the frame.
# Controls
#   Left click sets a target for the frog. Space shoots a bubble. R restarts.
# ============================================================================

from utils import circle_rect_intersect, draw_heart, draw_explored_heatmap, draw_astar_path
import sys, random, math
import pygame
from settings import *
from utils import draw_grid, draw_debug_overlay, nearest_point_on_rect
from world import World
from entities.frog import Frog
from entities.fly import Fly
from entities.snake import Snake, SnakeState
from pathfinding import find_path
import debug_state
from pygame.math import Vector2 as V2

class Particle:
    def __init__(self, pos, color):
        self.pos = V2(pos)
        raw_dir = V2(random.uniform(-1, 1), random.uniform(-1, 1))
        direction = raw_dir.normalize() if raw_dir.length_squared() > 0 else V2(1, 0)
        self.vel = direction * random.uniform(50, 150)
        self.lifetime = PARTICLE_LIFETIME
        self.age = 0.0
        self.color = color

    def update(self, dt):
        self.pos += self.vel * dt
        self.age += dt

    def draw(self, surf):
        if self.age < self.lifetime:
            radius = max(1, int(5 * (1 - self.age / self.lifetime)))
            pygame.draw.circle(surf, self.color, self.pos, radius)

class KeySlider:
    def __init__(self, x, y, min_v, max_v, step, initial, label, key_dec, key_inc, key_names):
        self.x = x
        self.y = y
        self.min_v = min_v
        self.max_v = max_v
        self.step = step
        self.val = initial
        self.label = label
        self.key_dec = key_dec
        self.key_inc = key_inc
        self.key_names = key_names

    def handle_event(self, e):

        if e.type == pygame.KEYDOWN:
            if e.key == self.key_dec:
                self.val = max(self.min_v, self.val - self.step)
            elif e.key == self.key_inc:
                self.val = min(self.max_v, self.val + self.step)

    def draw(self, surf, font):
        txt = font.render(f"[{self.key_names}] {self.label}: {self.val:.1f}", True, (230, 230, 255))
        bg_rect = txt.get_rect(topleft=(self.x, self.y))
        bg_rect.inflate_ip(12, 6)
        
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, 160), bg_surf.get_rect(), border_radius=4)
        surf.blit(bg_surf, bg_rect.topleft)
        
        surf.blit(txt, (self.x, self.y))

def resolve_fly_overlaps(flies, iterations=2):
    """
    Hard position-based separation: guarantees no two flies end up visually
    overlapping, regardless of how the steering forces balance out. Runs after
    all flies have moved for the frame. Cheap: O(n^2) with n=30 is trivial.
    """
    for _ in range(iterations):
        for i in range(len(flies)):
            a = flies[i]
            for j in range(i + 1, len(flies)):
                b = flies[j]
                diff = a.pos - b.pos
                dist = diff.length()
                min_dist = a.radius + b.radius
                if dist == 0:
                    # Perfectly stacked (rare) — nudge apart along a fixed axis
                    push = V2(1, 0) * (min_dist * 0.5)
                    a.pos += push
                    b.pos -= push
                elif dist < min_dist:
                    overlap = min_dist - dist
                    push = diff.normalize() * (overlap * 0.5)
                    a.pos += push
                    b.pos -= push

def main():
    # Initialize Pygame and create a window and a clock
    pygame.init()
    pygame.display.set_caption("Frog, Flies, and Snakes")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Fonts for text and overlay
    font = pygame.font.SysFont("consolas", 22)
    bigfont = pygame.font.SysFont("consolas", 48, bold=True)
    font_small = pygame.font.SysFont("consolas", 12)   # small labels for the A* cost heatmap

    def reset():
        """
        Create a fresh world and agents. Called at start and when the player restarts.
        Returns a tuple of (world, frog, flies, snakes).
        """
        world = World(WIDTH, HEIGHT)

        # Helper to push spawn/target points out of obstacles
        def get_safe_point(x, y, radius):
            p = V2(x, y)
            for _ in range(5): # Iteratively push out of overlapping obstacles
                hit = False
                for rect in world.obstacles:
                    if circle_rect_intersect(p, radius, rect):
                        hit = True
                        nearest = nearest_point_on_rect(p, rect)
                        diff = p - nearest
                        if diff.length_squared() > 0:
                            p = nearest + diff.normalize() * (radius + 10)
                        else:
                            # Fallback push if perfectly centered
                            p += V2(0, -1) * (radius + 10)
                if not hit:
                    break
            
            # Clamp the final point to ensure it wasn't pushed off-screen
            p.x = max(radius, min(WIDTH - radius, p.x))
            p.y = max(radius, min(HEIGHT - radius, p.y))
            return p.x, p.y

        # Spawn Frog safely
        fx, fy = get_safe_point(WIDTH * 0.5, HEIGHT * 0.5, FROG_RADIUS)
        frog = Frog((fx, fy), world.obstacles)

        # Generate cluster centers for flies
        centers = []
        while len(centers) < FLY_CLUSTER_COUNT:
            cx = random.randint(60, WIDTH - 60)
            cy = random.randint(60, HEIGHT - 60)
            candidate = V2(cx, cy)
            if all((candidate - c).length() >= 250 for c in centers):
                centers.append(candidate)
            
        flies = []
        for i in range(NUM_FLIES):
            center = centers[i % FLY_CLUSTER_COUNT]
            radius = FLY_CLUSTER_SPAWN_RADIUS * math.sqrt(random.random())
            angle = random.uniform(0, 2 * math.pi)
            fly_x = center.x + radius * math.cos(angle)
            fly_y = center.y + radius * math.sin(angle)
            fly_x = max(FLY_RADIUS + 4, min(WIDTH - (FLY_RADIUS + 4), fly_x))
            fly_y = max(FLY_RADIUS + 4, min(HEIGHT - (FLY_RADIUS + 4), fly_y))
            flies.append(Fly((fly_x, fly_y)))

        # Create snakes with safely adjusted patrol and home points
        snakes = []
        for i in range(NUM_SNAKES):
            px = 140 + i * 320
            py = 120 if i % 2 == 0 else HEIGHT - 140
            
            # Ensure both the spawn (home) point and the patrol point are safe
            home_x, home_y = get_safe_point(px, py, SNAKE_RADIUS)
            patrol_x, patrol_y = get_safe_point(WIDTH - px, HEIGHT - py, SNAKE_RADIUS)
            
            snakes.append(Snake((home_x, home_y), (patrol_x, patrol_y), world.obstacles))

        return world, frog, flies, snakes

    # Build initial state
    world, frog, flies, snakes = reset()

    import settings
    sliders = [
        KeySlider(20, 100, 0.0, 5.0, 0.1, settings.SEP_WEIGHT, "SEP_WEIGHT", pygame.K_1, pygame.K_2, "1/2"),
        KeySlider(20, 130, 0.0, 5.0, 0.1, settings.COH_WEIGHT, "COH_WEIGHT", pygame.K_3, pygame.K_4, "3/4"),
        KeySlider(20, 160, 0.0, 5.0, 0.1, settings.ALI_WEIGHT, "ALI_WEIGHT", pygame.K_5, pygame.K_6, "5/6"),
        KeySlider(20, 190, 50.0, 500.0, 10.0, settings.AGGRO_RANGE, "AGGRO_RANGE", pygame.K_7, pygame.K_8, "7/8"),
    ]

    DEFAULT_SLIDER_VALS = [sl.val for sl in sliders]

    particles = []
    red_flash_timer = 0.0
    avg_close_speed = 0.0
    last_aggro_dist = None

    # A* pathfinding visualization state (Assignment 2, Part 1)
    last_path_info = None       # dict returned by find_path(), or None
    path_reveal_progress = 0    # how many explored cells have been "revealed" so far
    path_ready = False          # True once the reveal animation finishes and the frog can move
    diagonal_enabled = True     # toggled with G

    # Click-to-inspect state for debug mode
    inspected_entity = None

    # Game state for health, scoring, and endings
    health = START_HEALTH
    fly_count = 0
    game_over = False
    win = False

    running = True
    while running:
        # ---------------- Measure dt ----------------
        # Convert milliseconds to seconds for frame rate independent movement
        dt = clock.tick(FPS) / 1000.0

        # ---------------- Input ----------------
        for e in pygame.event.get():
            if debug_state.DEBUG:
                for sl in sliders:
                    sl.handle_event(e)
                settings.SEP_WEIGHT = sliders[0].val
                settings.COH_WEIGHT = sliders[1].val
                settings.ALI_WEIGHT = sliders[2].val
                settings.AGGRO_RANGE = sliders[3].val

            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False

                if e.key == pygame.K_F1:
                    # F1 toggles debug overlay; clear inspect selection when turning off
                    debug_state.DEBUG = not debug_state.DEBUG
                    if not debug_state.DEBUG:
                        inspected_entity = None

                if not game_over and e.key == pygame.K_SPACE:
                    # Space shoots a bubble from the frog mouth
                    frog.shoot()

                if game_over and e.key == pygame.K_r:
                    # R restarts the whole scene
                    world, frog, flies, snakes = reset()
                    health = START_HEALTH
                    fly_count = 0
                    game_over = False
                    win = False
                    last_path_info = None
                    path_reveal_progress = 0
                    path_ready = False
                    for sl, default_val in zip(sliders, DEFAULT_SLIDER_VALS):
                        sl.val = default_val
                    settings.SEP_WEIGHT = DEFAULT_SLIDER_VALS[0]
                    settings.COH_WEIGHT = DEFAULT_SLIDER_VALS[1]
                    settings.ALI_WEIGHT = DEFAULT_SLIDER_VALS[2]
                    settings.AGGRO_RANGE = DEFAULT_SLIDER_VALS[3]

            if not game_over and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # Left click: legacy direct-Arrive move (Assignment 1 behaviour,
                # kept so you can demo it side-by-side against A*)
                frog.path = []
                frog.set_target(pygame.mouse.get_pos())

            if not game_over and e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                # Right click (Assignment 2 requirement): compute an A* path
                # from the frog to the clicked point and have the frog follow it
                goal = V2(pygame.mouse.get_pos())
                last_path_info = find_path(
                    world.grid, frog.pos, goal, world.obstacles,
                    FROG_RADIUS, allow_diagonal=diagonal_enabled,
                )
                path_reveal_progress = 0
                path_ready = False

            if debug_state.DEBUG and e.type == pygame.MOUSEBUTTONDOWN and e.button == 2:
                # Middle-click: click-to-inspect (moved off right-click, which
                # now drives A* pathfinding)
                mx, my = pygame.mouse.get_pos()
                click_pos = V2(mx, my)
                best = None
                best_dist = float('inf')
                candidates = list(flies) + list(snakes) + [frog]
                for agent in candidates:
                    d = (agent.pos - click_pos).length()
                    if d <= agent.radius and d < best_dist:
                        best_dist = d
                        best = agent
                inspected_entity = best  # None if nothing clicked = clear selection

            if e.type == pygame.KEYDOWN and e.key == pygame.K_g:
                # Toggle diagonal neighbours and re-run the last query, so you
                # can compare cardinal-only vs diagonal-enabled paths live
                # (reproduces the two panels of Figure 2 in the brief)
                diagonal_enabled = not diagonal_enabled
                if last_path_info is not None:
                    goal = (last_path_info["smoothed_world_path"][-1]
                            if last_path_info["smoothed_world_path"] else frog.pos)
                    last_path_info = find_path(
                        world.grid, frog.pos, goal, world.obstacles,
                        FROG_RADIUS, allow_diagonal=diagonal_enabled,
                    )
                    path_reveal_progress = 0
                    path_ready = False

        # ---------------- Update ----------------
        if not game_over:
            # A* explored-area reveal animation: shows the searched region
            # growing outward before the frog is allowed to start moving,
            # so the whole explored area is visible before path-following begins.
            if (last_path_info is not None
                    and last_path_info["smoothed_world_path"] is not None
                    and not path_ready):
                path_reveal_progress += PATH_REVEAL_CELLS_PER_FRAME
                if path_reveal_progress >= len(last_path_info["explored_cells"]):
                    path_reveal_progress = len(last_path_info["explored_cells"])
                    path_ready = True
                    frog.set_path(
                        last_path_info["smoothed_world_path"],
                        cost=last_path_info["total_cost"],
                    )

            # Update frog first since other agents may query frog position
            frog.update(dt)

            # Precompute neighbor counts for catch-up detection
# Precompute each fly's neighbor list (positions+velocities) and neighbor-id
            # set ONCE per frame, in a single O(N^2) pass. This replaces the previous
            # separate neighbor-counting pass plus the redundant per-fly neighbor rebuilds
            # that used to happen again inside Fly.update()'s Flock branch, Fleeing branch,
            # and has_nearby_flockmate check. Note: like the old neighbor_counts pass, this
            # snapshot is taken before any fly moves this frame, so behavior (which flies
            # count as neighbors of which) is unchanged from before — just computed once.
            fly_neighbors = {}
            fly_neighbor_ids = {}
            for f in flies:
                f_neighbors = []
                f_neighbor_ids = set()
                for g in flies:
                    if g is f:
                        continue
                    if (g.pos - f.pos).length_squared() <= NEIGHBOR_RADIUS ** 2:
                        f_neighbors.append((g.pos, g.vel))
                        f_neighbor_ids.add(id(g))
                fly_neighbors[id(f)] = f_neighbors
                fly_neighbor_ids[id(f)] = f_neighbor_ids
            neighbor_counts = {fid: len(nbrs) for fid, nbrs in fly_neighbors.items()}

            # Update flies and check if any fly gets caught by the frog
            for f in list(flies):
                f.update(
                    dt, flies, frog, world.rect, frog.bubbles,
                    neighbor_counts=neighbor_counts,
                    neighbors=fly_neighbors.get(id(f), []),
                    neighbor_ids=fly_neighbor_ids.get(id(f), set()),
                )

                # Eat a fly when close enough to the frog center
                if (f.pos - frog.pos).length_squared() <= (f.radius + FROG_RADIUS) ** 2:
                    for _ in range(8):
                        particles.append(Particle(f.pos, YELLOW))
                    flies.remove(f)
                    fly_count += 1
                    if fly_count >= FLIES_TO_WIN:
                        game_over = True
                        win = True

            # Hard positional correction — guarantee no two flies visually overlap
            resolve_fly_overlaps(flies)

            # Update snakes and their FSM decisions
            for s in snakes:
                s.update(dt, frog)

            # ------------- Bubble hit logic -------------
            for s in snakes:
                for b in frog.bubbles:
                    if (b.pos - s.pos).length_squared() <= (BUBBLE_RADIUS + s.radius) ** 2:
                        b.alive = False
                        if s.state == SnakeState.Aggro:
                            for _ in range(8):
                                particles.append(Particle(s.pos, (200, 200, 255)))
                            # Transition exactly as required: Aggro -> Harmless -> Confused
                            s.set_state(SnakeState.Harmless)

            # Bubbles also pop early if they hit an obstacle rect (optional per brief)
                for b in frog.bubbles:
                        for rect in world.obstacles:
                            if circle_rect_intersect(b.pos, BUBBLE_RADIUS, rect):
                                b.alive = False
                                for _ in range(4):
                                    particles.append(Particle(b.pos, (200, 200, 255)))
                                break

            # ------------- Damage logic -------------
            for s in snakes:
                if s.state == SnakeState.Aggro and (s.pos - frog.pos).length_squared() <= (s.radius + FROG_RADIUS) ** 2:
                    if frog.can_be_hurt():
                        health -= 1
                        red_flash_timer = HURT_FLASH_DURATION
                        frog.start_hurt()
                        s.set_state(SnakeState.Harmless)
                        
                        if health <= 0:
                            game_over = True
                            win = False

            # Particles
            for p in list(particles):
                p.update(dt)
                if p.age >= p.lifetime:
                    particles.remove(p)

            # Red flash
            if red_flash_timer > 0:
                red_flash_timer -= dt

            # HUD Counter
            if debug_state.DEBUG:
                aggro_snakes = [s for s in snakes if s.state == SnakeState.Aggro]
                if aggro_snakes:
                    nearest = min(aggro_snakes, key=lambda s: (s.pos - frog.pos).length_squared())
                    dist = (nearest.pos - frog.pos).length()
                    if last_aggro_dist is not None and dt > 0:
                        close_speed = (last_aggro_dist - dist) / dt
                        avg_close_speed = avg_close_speed * 0.95 + close_speed * 0.05
                    last_aggro_dist = dist
                else:
                    last_aggro_dist = None
                    avg_close_speed = 0.0

        # ---------------- Draw ----------------
        screen.fill(BG)           # clear background
        draw_grid(screen)         # draw a soft grid
        world.draw(screen)        # draw obstacles

        # A* visualization: explored-cost heatmap, then the green path
        if last_path_info is not None:
            if last_path_info["smoothed_world_path"] is not None:
                shown_cells = (
                    last_path_info["explored_cells"][:path_reveal_progress]
                    if not path_ready else last_path_info["explored_cells"]
                )
                draw_explored_heatmap(screen, world.grid, shown_cells,
                                       last_path_info["g_cost_by_cell"], font_small)
                if path_ready:
                    draw_astar_path(screen, last_path_info["smoothed_world_path"])
            else:
                no_path_txt = font.render("No path found to that location", True, RED)
                screen.blit(no_path_txt, (16, 96))

        for f in flies:           # draw flies
            f.draw(screen)
        for s in snakes:          # draw snakes
            s.draw(screen)
        frog.draw(screen)         # draw frog and bubbles

        # Draw particles
        for p in particles:
            p.draw(screen)

        # Draw Red Flash
        if red_flash_timer > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha = min(255, max(0, int(255 * (red_flash_timer / HURT_FLASH_DURATION))))
            pygame.draw.rect(flash_surf, (255, 0, 0, alpha), flash_surf.get_rect(), width=10)
            screen.blit(flash_surf, (0, 0))

        # Draw hearts for health
        for i in range(START_HEALTH):
            color = RED if i < health else (80, 60, 60)
            draw_heart(screen, 16 + i * 26, 18, color)

        # Draw fly counter and control hint
        txt = font.render(f"Flies: {fly_count}/{FLIES_TO_WIN}", True, (240, 240, 240))
        screen.blit(txt, (16, 42))
        tips = font.render(
            "Left-click: direct move | Right-click: A* move | Space: bubble | G: toggle diagonal | R: restart",
            True, MUTED)
        screen.blit(tips, (16, 68))

        if last_path_info is not None and last_path_info["smoothed_world_path"] is not None:
            cost_txt = font.render(
                f"A* path cost: {last_path_info['total_cost']:.1f} px  |  "
                f"explored: {len(last_path_info['explored_cells'])} cells  |  "
                f"diagonal: {'ON' if diagonal_enabled else 'OFF'}",
                True, GREEN)
            screen.blit(cost_txt, (16, 96))

        if debug_state.DEBUG:
            from entities.fly import FlyState
            from entities.snake import SnakeState as _SnakeState

            for sl in sliders:
                sl.draw(screen, font)
            if last_aggro_dist is not None:
                hud_txt = font.render(f"Pursue closing speed: {avg_close_speed:.1f} px/s", True, (255, 150, 150))
                screen.blit(hud_txt, (20, 220))

            #-- Transition log (bottom-left corner) ---
            # log_y_start = HEIGHT - 20 - len(debug_state.TRANSITION_LOG) * 22
            # for i, (ts, kind, idx, old_st, new_st) in enumerate(debug_state.TRANSITION_LOG):
            #     entry = f"{ts} {kind}#{idx} {old_st} -> {new_st}"
            #     log_surf = font.render(entry, True, (200, 230, 200))
            #     screen.blit(log_surf, (16, log_y_start + i * 22))

            # --- Stats panel (top-right corner) ---
            # fps_val   = clock.get_fps()
            # fly_flock   = sum(1 for f in flies if f.state == FlyState.Flock)
            # fly_flee    = sum(1 for f in flies if f.state == FlyState.Fleeing)
            # fly_idle    = sum(1 for f in flies if f.state == FlyState.Idle)
            # sn_counts   = {st: sum(1 for s in snakes if s.state == st) for st in _SnakeState}
            # stats_lines = [
            #     f"FPS: {fps_val:.1f}",
            #     f"Flies: Flock {fly_flock} | Fleeing {fly_flee} | Idle {fly_idle}",
            #     f"Snakes: Patrol {sn_counts[_SnakeState.PatrolAway]+sn_counts[_SnakeState.PatrolHome]}"
            #     f" | Aggro {sn_counts[_SnakeState.Aggro]}"
            #     f" | Harmless {sn_counts[_SnakeState.Harmless]}"
            #     f" | Confused {sn_counts[_SnakeState.Confused]}",
            #     f"Bubbles: {len(frog.bubbles)}",
            #     f"Particles: {len(particles)}",
            # # ]
            # panel_w = 480
            # panel_h = len(stats_lines) * 22 + 10
            # panel_x = WIDTH - panel_w - 10
            # panel_y = 10
            # panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            # panel_surf.fill((0, 0, 0, 140))
            # screen.blit(panel_surf, (panel_x, panel_y))
            # for li, line in enumerate(stats_lines):
            #     ls = font.render(line, True, (220, 220, 255))
            #     screen.blit(ls, (panel_x + 6, panel_y + 5 + li * 22))

            # --- Click-to-inspect floating info box ---
            # Clear selection if the inspected fly was caught
            if inspected_entity in flies or inspected_entity is None or inspected_entity is frog or inspected_entity in snakes:
                pass  # still valid
            else:
                inspected_entity = None

            if inspected_entity is not None:
                from entities.fly import Fly as _Fly
                from entities.snake import Snake as _Snake
                from entities.frog import Frog as _Frog
                ent = inspected_entity
                if isinstance(ent, _Fly):
                    etype = "Fly"
                elif isinstance(ent, _Snake):
                    etype = "Snake"
                else:
                    etype = "Frog"

                info_lines = [
                    f"{etype}#{id(ent) % 1000}",
                    f"Pos: ({int(ent.pos.x)}, {int(ent.pos.y)})",
                    f"Speed: {ent.vel.length():.1f} px/s",
                ]
                if isinstance(ent, _Fly):
                    info_lines.append(f"State: {ent.state.name}")
                    if ent.state == FlyState.Fleeing:
                        info_lines.append(f"scare_timer: {ent.scare_timer:.2f}s")
                    elif ent.state == FlyState.Idle:
                        info_lines.append(f"idle_timer: {ent.idle_timer:.2f}s")
                elif isinstance(ent, _Snake):
                    info_lines.append(f"State: {ent.state.name}")
                    if ent.state == _SnakeState.Confused:
                        info_lines.append(f"confused_timer: {ent.confused_timer:.2f}s")

                ibox_w = 220
                ibox_h = len(info_lines) * 22 + 10
                ibox_x = int(ent.pos.x) + ent.radius + 8
                ibox_y = int(ent.pos.y) - ibox_h - 8
                # Clamp to screen
                ibox_x = min(ibox_x, WIDTH - ibox_w - 4)
                ibox_y = max(ibox_y, 4)
                ibox_surf = pygame.Surface((ibox_w, ibox_h), pygame.SRCALPHA)
                ibox_surf.fill((0, 0, 0, 180))
                screen.blit(ibox_surf, (ibox_x, ibox_y))
                pygame.draw.rect(screen, (100, 200, 255), (ibox_x, ibox_y, ibox_w, ibox_h), 1)
                for li, line in enumerate(info_lines):
                    ls = font.render(line, True, (230, 230, 255))
                    screen.blit(ls, (ibox_x + 6, ibox_y + 5 + li * 22))

        # If game over, dim the screen and show a message
        if game_over:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 160))
            screen.blit(shade, (0, 0))
            msg = "You won!" if win else "You died!"
            col = (90, 220, 120) if win else RED
            text = bigfont.render(msg, True, col)
            hint = font.render("Press R to restart", True, (240, 240, 240))
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10))
            screen.blit(text, rect)
            screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 44)))

        # Present the frame
        pygame.display.flip()

    # Clean shutdown
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
