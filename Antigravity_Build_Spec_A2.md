# Antigravity Build Spec — GAIT Assignment 2 (Refined)
**Target:** A* Pathfinding (Weighted Terrain) + Threaded MCTS Connect 4
**Codebase state:** Fresh scaffold. No Assignment 1 code (no flies, snakes, health, obstacles) survives.
**Consumer:** Antigravity code-generation agent. Each section below is a self-contained prompt targeting exactly one file. Feed them in order — later prompts assume earlier files already exist and import from them.

---

## 0. Why this structure maps to the rubric

| Rubric line | Where it's satisfied |
|---|---|
| "Display the cost of each explored path" | `grid.py` g-cost storage + `main.py` reveal animation |
| "Show all explored areas on the map before the frog can follow the path" | `main.py` `REVEALING` state |
| "Display the followed/shortest path's total cost" | `pathfinding.py` returns `total_cost`; HUD in `main.py` |
| "Win rate per column" | `mcts.py` `mcts_search` stats dict |
| "Visits per column" | same dict |
| "UCB score of final chosen column" | same dict, frozen at decision time |
| "Design and color choice / smart features / creativity" | sprite assets, heatmap toggle, difficulty levels, themed stats panel |

Keep this table in mind — every prompt below exists to check one of these boxes, not to add unrelated polish.

---

## 1. Fresh Project Scaffold

```
gait_a2/
  settings.py
  grid.py
  pathfinding.py
  frog.py
  mcts.py
  scenes.py
  main.py
  assets/
    frog_sprite.png
    terrain_tiles.png
    c4_board.png
    tokens/
      token_red.png
      token_yellow.png
      token_empty.png
  README.md
```

No `entities/`, no `obstacles.py`, no `health.py`, no `fly.py`, no `snake.py`. If Antigravity's scaffolding step proposes any of these, reject and regenerate — this is a hard constraint, not a style preference.

`main.py` owns a top-level mode switch between three scenes: `PATHFINDING`, `C4_VS_AI`, `C4_AI_VS_AI`, selected from a start menu (see `scenes.py`).

---

## 2. `settings.py`

**Prompt for Antigravity:**

> Create `settings.py` as the single source of constants for the whole project. No game logic here — only numbers, colors, paths, and enums. Include:
>
> 1. **Window/grid config:** `TILE_SIZE = 48`, `GRID_COLS = 20`, `GRID_ROWS = 14`, `SIDEBAR_WIDTH = 320` (for the stats panel), computed `SCREEN_WIDTH`/`SCREEN_HEIGHT`, `FPS = 60`.
> 2. **Terrain cost table** as a single dict so `grid.py` and any legend/HUD code share one source of truth:
>    ```python
>    class Terrain:
>        GRASS = "grass"
>        MUD = "mud"
>        WATER = "water"
>        WALL = "wall"
>
>    TERRAIN_COST = {
>        Terrain.GRASS: 1,
>        Terrain.MUD: 3,
>        Terrain.WATER: 5,
>        Terrain.WALL: float("inf"),
>    }
>    TERRAIN_COLOR = {  # fallback if sprites fail to load
>        Terrain.GRASS: (86, 168, 82),
>        Terrain.MUD:   (120, 84, 51),
>        Terrain.WATER: (58, 122, 199),
>        Terrain.WALL:  (40, 40, 40),
>    }
>    ```
> 3. **Path/steering constants:** `PATH_RADIUS = 10` (px tolerance before correction kicks in), `WAYPOINT_ARRIVAL_RADIUS = 6`, `FROG_MAX_SPEED = 220`, `FROG_MAX_FORCE = 900`, `FROG_SLOW_RADIUS = 60`.
> 4. **Colors:** `COLOR_EXPLORED = (255, 215, 0, 90)` (translucent gold for heatmap), `COLOR_PATH = (0, 230, 90)` (the required green), `COLOR_FRONTIER = (255, 140, 0, 90)`, `COLOR_TEXT = (240, 240, 240)`, `COLOR_BG = (18, 18, 24)`.
> 5. **Asset paths**, all relative to an `ASSETS_DIR = Path(__file__).parent / "assets"`:
>    ```python
>    FROG_SPRITE = ASSETS_DIR / "frog_sprite.png"
>    TERRAIN_TILESET = ASSETS_DIR / "terrain_tiles.png"
>    C4_BOARD_SPRITE = ASSETS_DIR / "c4_board.png"
>    TOKEN_ASSETS = {
>        "red": ASSETS_DIR / "tokens" / "token_red.png",
>        "yellow": ASSETS_DIR / "tokens" / "token_yellow.png",
>        "empty": ASSETS_DIR / "tokens" / "token_empty.png",
>    }
>    ```
> 6. **MCTS tuning:** `MCTS_ITERATIONS = 4000`, `MCTS_TIME_LIMIT_SEC = 2.0` (whichever bound hits first), `MCTS_C_PARAM = 1.4`, `MCTS_DIFFICULTIES = {"easy": 400, "medium": 2000, "hard": 8000}`.
> 7. **Reveal animation:** `REVEAL_CELLS_PER_FRAME = 6`, `REVEAL_FONT_SIZE = 14`.
> 8. **Keybindings** as a dict so `main.py` never hardcodes a key literal:
>    ```python
>    KEYBINDS = {
>        "toggle_diagonal": pygame.K_g,
>        "toggle_heatmap": pygame.K_o,
>        "toggle_cost_labels": pygame.K_n,
>        "restart": pygame.K_r,
>        "menu": pygame.K_ESCAPE,
>    }
>    ```
>
> Do not put any Pygame `Surface` creation, drawing, or `pygame.init()` calls in this file — it must be importable before the display is initialized.

---

## 3. `grid.py`

**Prompt for Antigravity:**

> Create `grid.py` defining `TerrainGrid`, a weighted grid independent of any pathfinding or rendering concerns (single-responsibility: it owns terrain data and cell metadata only).
>
> ```python
> class Cell:
>     __slots__ = ("col", "row", "terrain", "g_cost", "explored", "in_path")
>     def __init__(self, col, row, terrain):
>         self.col, self.row, self.terrain = col, row, terrain
>         self.g_cost = None      # set by A* when explored; used for the reveal HUD
>         self.explored = False   # was this cell popped from the open set?
>         self.in_path = False    # is this cell part of the final returned path?
> ```
>
> `TerrainGrid` responsibilities:
> - `__init__(self, cols, rows)`: build a `cols x rows` array of `Cell`s. Procedurally seed terrain with `random.random()` thresholds (~65% grass, ~18% mud, ~12% water, ~5% wall clusters) OR load from an optional `layout: list[str]` where each character maps to a `Terrain` constant (`'.'`=grass, `'m'`=mud, `'w'`=water, `'#'`=wall). Support both so a fixed demo layout can be swapped in for reproducible cost explanations on camera.
> - `in_bounds(self, col, row) -> bool`
> - `cost(self, col, row) -> float`: returns `TERRAIN_COST[cell.terrain]`, `inf` for walls or out-of-bounds.
> - `neighbors(self, col, row, allow_diagonal: bool) -> list[tuple[int,int]]`:
>   - Cardinal-only when `allow_diagonal=False`: 4 neighbors.
>   - When `allow_diagonal=True`: add the 4 diagonals, **and explicitly prevent corner-cutting** — a diagonal move from `(c,r)` to `(c+dc,r+dr)` is only legal if both orthogonal cells `(c+dc, r)` and `(c, r+dr)` are not walls. This is the detail most students miss and is what makes diagonal paths look "natural" instead of clipping through wall corners.
>   - Skip any neighbor that is out of bounds or has `cost() == inf`.
> - `movement_cost(self, from_cell, to_cell) -> float`: base terrain cost of `to_cell`, multiplied by `1.4142` if the move is diagonal (so diagonal steps aren't unrealistically cheap relative to two cardinal steps).
> - `reset_search_state(self)`: clears `explored`, `in_path`, `g_cost` on every cell — call this before each new A* run so old runs don't bleed into the reveal animation.
> - `world_to_cell(self, x, y)` / `cell_to_world_center(self, col, row)`: conversions using `TILE_SIZE`, used by both `pathfinding.py` (click → target cell) and `frog.py` (path cell → steering waypoint).
> - `draw(self, surface, tileset: pygame.Surface | None, show_heatmap: bool, show_cost_labels: bool, font: pygame.font.Font)`:
>   - Draw each cell's terrain tile (blit from `tileset` sub-rect if provided, else flat-fill with `TERRAIN_COLOR`).
>   - If `show_heatmap`, overlay `COLOR_EXPLORED` on every cell where `cell.explored` and `COLOR_FRONTIER` on cells that are in the current open set but not yet popped (track a separate `frontier` bool if useful).
>   - If `show_cost_labels`, blit the `g_cost` (rounded to 1 decimal) centered in every explored cell — this directly satisfies "display the cost of each explored path."
>   - Draw a thin grid line grid over everything for readability.
>
> Keep `Cell.g_cost` as the field the reveal animation and A* both write to — do not duplicate cost state in a separate dict.

---

## 4. `pathfinding.py`

**Prompt for Antigravity:**

> Create `pathfinding.py` implementing A* over a `TerrainGrid`. This module has no Pygame drawing calls — it only computes and returns data; `grid.py`/`main.py` render it. Keep it pure so its correctness can be reasoned about independently of the animation layer.
>
> ```python
> import heapq
> from dataclasses import dataclass, field
>
> @dataclass
> class AStarResult:
>     path: list[tuple[int, int]]        # ordered list of (col, row) grid-cell CENTERS, start to goal, inclusive
>     total_cost: float                  # g_cost of the goal node; float('inf') if unreachable
>     explored_order: list[tuple[int, int]]  # cells in the order they were POPPED from the open set — this order drives the reveal animation
>     reachable: bool
> ```
>
> `def find_path(grid: TerrainGrid, start: tuple[int,int], goal: tuple[int,int], allow_diagonal: bool) -> AStarResult:`
>
> Implementation requirements:
> - Standard A* with a binary heap (`heapq`) open set: `f = g + h`.
> - Heuristic `h`: octile distance when `allow_diagonal` is True (`dx, dy = abs(...)`; `h = (dx+dy) + (sqrt(2)-2)*min(dx,dy)`), Manhattan distance when False. Using the wrong heuristic for the neighbor mode is the classic bug that makes diagonal paths look wrong — be deliberate about this branch.
> - `g_cost[start] = 0`; every popped node writes `cell.g_cost = g` and `cell.explored = True` directly onto the `TerrainGrid` cells (this is what `main.py`'s reveal loop iterates over) and appends `(col,row)` to `explored_order`.
> - Tie-breaking: when two nodes have equal `f`, prefer the one with the larger `g` (multiply `h` by `1.0 + 1e-3` internally) — this reduces the "which of several equal-cost paths gets drawn" flakiness and gives consistent, explainable demo runs.
> - Reconstruct the path via a `came_from` dict once `goal` is popped; **do not smooth or string-pull** — return literal grid-cell centers in `path`, one entry per cell the path passes through, using `grid.cell_to_world_center`.
> - Mark every cell on the reconstructed path with `cell.in_path = True` so `grid.draw()` can render it green without `pathfinding.py` touching Pygame.
> - If the open set empties before reaching `goal`, return `AStarResult(path=[], total_cost=float('inf'), explored_order=..., reachable=False)`.
> - Also export `def path_cost_breakdown(grid, path) -> list[tuple[tuple[int,int], float, float]]`: for each cell in `path`, return `(coord, step_cost, cumulative_cost)`. This is what you narrate in the demo when explaining "here's why this path costs 23, cell by cell" — build it once instead of recomputing on the fly during Q&A.

---

## 5. `frog.py`

**Prompt for Antigravity:**

> Create `frog.py` with a single `Frog` class using **Reynolds-style path following**, not simple waypoint-seek. This is the steering behaviour the assignment explicitly wants: the frog should look glued to the green line through corners, not lurch node-to-node.
>
> ```python
> class Frog:
>     def __init__(self, x, y, sprite_path):
>         self.pos = pygame.Vector2(x, y)
>         self.velocity = pygame.Vector2(0, 0)
>         self.path: list[pygame.Vector2] = []
>         self.path_index = 0
>         self.sprite = self._load_sprite(sprite_path)  # pygame.image.load(...).convert_alpha()
>         self.angle = 0.0
> ```
>
> Core method — call every frame once a path exists:
>
> ```python
> def follow_path(self, dt):
>     if not self.path:
>         return
>     # 1. Advance path_index if we've arrived at the current waypoint
>     target = self.path[self.path_index]
>     if self.pos.distance_to(target) < WAYPOINT_ARRIVAL_RADIUS and self.path_index < len(self.path) - 1:
>         self.path_index += 1
>         target = self.path[self.path_index]
>
>     # 2. Predict future position (Reynolds' classic "look ahead")
>     future_pos = self.pos + self.velocity.normalize() * PREDICT_DIST if self.velocity.length() > 0 else self.pos
>
>     # 3. Find the point on the CURRENT PATH SEGMENT nearest to future_pos, by projection
>     seg_start = self.path[max(self.path_index - 1, 0)]
>     seg_end = target
>     projected = project_point_on_segment(future_pos, seg_start, seg_end)
>
>     # 4. If we've drifted beyond PATH_RADIUS from the line, steer back onto it;
>     #    otherwise keep steering toward the next waypoint (arrive behaviour, so it decelerates smoothly into corners)
>     distance_off_line = future_pos.distance_to(projected)
>     if distance_off_line > PATH_RADIUS:
>         seek_target = projected + (seg_end - seg_start).normalize() * PREDICT_DIST
>         steering = self._seek(seek_target)
>     else:
>         steering = self._arrive(target)
>
>     self._apply_steering(steering, dt)
>     self._update_facing_angle()
> ```
>
> Also implement:
> - `_seek(self, target) -> Vector2`: `desired = (target - pos).normalize() * MAX_SPEED; return (desired - velocity).limit(MAX_FORCE)`.
> - `_arrive(self, target) -> Vector2`: like seek but scale `desired`'s magnitude down linearly inside `FROG_SLOW_RADIUS` of `target`, floor at 0 — this is what prevents overshoot/corner-clipping at the final waypoint.
> - `project_point_on_segment(p, a, b)` as a free function (pure vector math, reusable/testable): clamp the projection scalar `t` to `[0, 1]` so the projected point never falls outside the actual segment.
> - `_apply_steering(self, force, dt)`: `velocity += force * dt`, clamp to `MAX_SPEED`, `pos += velocity * dt`.
> - `_update_facing_angle(self)`: `angle = velocity.angle_to((1,0))` when speed > small epsilon, else keep last angle — used to `pygame.transform.rotate` the sprite so the frog visibly faces its direction of travel.
> - `set_path(self, world_points: list[tuple[float,float]])`: replaces `self.path`, resets `path_index = 0`. Called once per A* result — never mutate the path while `follow_path` is mid-frame.
> - `is_path_complete(self) -> bool`: `path_index == len(path) - 1` and within `WAYPOINT_ARRIVAL_RADIUS` of the final point.
> - `draw(self, surface)`: blit the rotated sprite centered on `self.pos`. If sprite load failed, fall back to drawing a green circle + direction wedge so the game never crashes on a missing asset.
>
> Keep all tunable numbers (`PREDICT_DIST`, arrival radii, speeds) imported from `settings.py` — nothing hardcoded here.

---

## 6. `mcts.py`

**Prompt for Antigravity:**

> Create `mcts.py`. Reuse the game-state logic pattern from the provided starter (`Connect4State`: `clone`, `get_legal_moves`, `make_move`, `check_winner`, `is_full`, `is_terminal`) — port it in cleanly, it's already correct. The new work is: (a) return **rich per-column statistics**, not just a move, and (b) run **off the main thread** so the UI never freezes mid-search.
>
> ```python
> @dataclass
> class ColumnStat:
>     column: int
>     visits: int
>     win_rate: float      # wins / visits from the perspective of root_player, 0.0 if visits == 0
>     ucb_score: float     # UCT score AS COMPUTED AT THE FINAL ITERATION for this child of the root
>
> @dataclass
> class MCTSResult:
>     chosen_column: int | None
>     stats: dict[int, ColumnStat]   # every legal column, even ones MCTS barely visited
>     iterations_run: int
>     elapsed_sec: float
> ```
>
> `MCTSNode`: identical fields to the starter (`state, parent, move, children, visits, wins`), plus keep `best_child(c_param)` and `is_fully_expanded()` as given. Add `def uct_score(self, c_param) -> float` as a method on the node itself (refactor the inline formula out of `best_child` so it can be called standalone on any root child to fill `ColumnStat.ucb_score` after the search loop ends — the rubric explicitly wants the UCB score of the *chosen* column reported, so it must survive past the selection loop, not just live inside `best_child`).
>
> `def mcts_search(root_state, n_iter=None, time_limit_sec=None, c_param=MCTS_C_PARAM, progress_cb=None) -> MCTSResult:`
> - Loop bounded by `n_iter` OR `time_limit_sec`, whichever is passed (support both so "easy/medium/hard" can use iteration counts while a background worker can also enforce a wall-clock cap).
> - Each iteration: Selection (walk `best_child` while fully expanded & non-terminal) → Expansion (pick one untried legal move, `state.clone().make_move(...)`, create child) → Simulation (`rollout`, same logic as the starter: 1.0 win / 0.0 loss / 0.5 draw from `root_player`'s perspective) → Backpropagation (walk back to root incrementing `visits`, adding reward to `wins`; **flip the reward when the node's mover differs from root_player** — verify the starter's `rollout` reward convention is applied consistently at every backprop level, this is the single most common MCTS bug).
> - If `progress_cb` is given, call it every ~50 iterations with `(iterations_so_far, total)` so a threaded caller can update a progress indicator without touching Pygame objects directly.
> - After the loop, for every child of the root build a `ColumnStat`: `visits = child.visits`, `win_rate = child.wins / child.visits if child.visits else 0.0`, `ucb_score = child.uct_score(c_param)` computed against the **final** `root_node.visits`. Also fill in any legal column that was never expanded at all (rare, but possible under a tight time limit) with `visits=0, win_rate=0.0, ucb_score=float('inf')`.
> - `chosen_column = most_visited_child(root_node).move` (visits, not raw win rate — this matches standard MCTS practice and is worth explaining on camera).
> - Return the populated `MCTSResult`.
>
> `class AIWorker(threading.Thread):`
> - `__init__(self, state, difficulty: str, result_queue: queue.Queue)`: stores a **cloned** state (never share a mutable board with the main thread), looks up iteration count from `MCTS_DIFFICULTIES[difficulty]`.
> - `run(self)`: calls `mcts_search(...)`, puts the `MCTSResult` on `result_queue`. Wrap in try/except and put an exception sentinel on the queue on failure so the main loop never hangs waiting on a dead thread.
> - Main-thread side (documented here, implemented in `scenes.py`): poll `result_queue.get_nowait()` inside the event loop each frame; while a worker is alive, render a "thinking…" indicator and ignore board clicks.
>
> Keep `mcts.py` free of any `pygame` import — it's pure game logic + threading, which also makes it unit-testable in isolation.

---

## 7. `scenes.py`

**Prompt for Antigravity:**

> Create `scenes.py` holding three scene classes, each exposing `handle_event(event)`, `update(dt)`, `draw(surface)` so `main.py`'s loop stays a thin dispatcher.
>
> **`PathfindingScene`**
> - Owns a `TerrainGrid`, a `Frog`, current `allow_diagonal` bool, `show_heatmap`, `show_cost_labels` bools, and a small state machine: `IDLE → REVEALING → FOLLOWING → IDLE`.
> - `handle_event`: right-click while `IDLE` → `grid.reset_search_state()`, run `pathfinding.find_path(...)`, store the `AStarResult`, switch to `REVEALING`, reset a `reveal_cursor = 0`. Keybinds from `settings.KEYBINDS` toggle `allow_diagonal`/`show_heatmap`/`show_cost_labels` at any time (toggling diagonal mid-`REVEALING` should **not** mutate the in-flight result — only affects the *next* click).
> - `update`: while `REVEALING`, advance `reveal_cursor` by `REVEAL_CELLS_PER_FRAME` per frame through `explored_order` (cells are already flagged `explored`/`g_cost` from the A* call itself, so this loop is purely pacing the *visual* reveal, not recomputing anything) — once `reveal_cursor` reaches the end, call `frog.set_path(...)` from the result's `path` and switch to `FOLLOWING`. While `FOLLOWING`, call `frog.follow_path(dt)`; once `frog.is_path_complete()`, switch to `IDLE`.
> - `draw`: `grid.draw(...)`, then frog, then a HUD box (top-left) showing: current mode, `allow_diagonal` state, and once a path exists, `Total Cost: {result.total_cost:.1f}` plus a small legend mapping terrain color → cost number (Grass 1 / Mud 3 / Water 5 / Wall ∞) — this is what makes "cost of each cell" explainable at a glance during the demo instead of you reciting numbers from memory.
>
> **`Connect4Scene`** — shared base for both MCTS modes (`vs_ai: bool` flag differentiates human-vs-AI from AI-vs-AI so you don't duplicate board/render code):
> - Owns `Connect4State`, a `result_queue`, current `AIWorker | None`, last `MCTSResult | None`, and a `difficulty` string.
> - `handle_event`: in `vs_ai` mode, human clicks a column only when it's the human's turn and no worker is running → `state.make_move(col)`, then immediately spawn an `AIWorker` for the AI's turn. In `AI vs AI` mode, ignore board clicks; instead a "Step"/"Auto-play" control (space bar or on-screen button) spawns the next `AIWorker` for whichever player is due to move.
> - `update`: poll `result_queue`; when a result arrives, store it as `last_result`, apply `state.make_move(last_result.chosen_column)`, clear the worker. If `state.is_terminal()`, freeze input and show the winner banner.
> - `draw`: board via `c4_board.png` (or fallback blue rounded-rect grid if the sprite is missing), tokens via `TOKEN_ASSETS` sprites, and the **stats panel** (below) whenever `last_result` is not None. Also draw a "thinking…" spinner over the board while a worker is alive.
>
> `def draw_stats_panel(surface, rect, result: MCTSResult, board_state) -> None`:
> - Draw within the reserved `SIDEBAR_WIDTH` region so it never overlaps the board.
> - One row per legal column 0–6: column index, a horizontal win-rate bar (`ColumnStat.win_rate`, 0–100%, colored on a red→green gradient by rate), visit count as a right-aligned number, and UCB score to 2 decimals.
> - Bold/highlight the chosen column's row — it must be visually obvious this is "the UCB score of the final chosen column" the rubric asks for, without you pointing at code.
> - Header line: `f"{result.iterations_run} iterations in {result.elapsed_sec:.2f}s"` so the demo narration ties directly to what's on screen.
> - Use a small monospace-ish font for numeric alignment; theme colors from `settings.py`, not hardcoded here.
>
> **`MenuScene`**: three buttons (`A* Pathfinding`, `Connect4: vs AI`, `Connect4: AI vs AI`) plus, for the two Connect4 options, a difficulty selector (`easy/medium/hard` from `MCTS_DIFFICULTIES`). Returns the chosen scene name + difficulty to `main.py` on confirm.

---

## 8. `main.py`

**Prompt for Antigravity:**

> Create `main.py` as a thin orchestrator: `pygame.init()`, build the window from `settings.SCREEN_WIDTH/HEIGHT`, load the shared `pygame.font.Font`, instantiate `MenuScene`, then run a single `while running:` loop that:
> 1. Pumps events; on `QUIT` set `running = False`; on `settings.KEYBINDS["menu"]` return to `MenuScene` from any active scene.
> 2. Delegates `handle_event`, `update(dt)`, `draw(screen)` to whichever scene object is currently active (`current_scene` variable swapped based on `MenuScene`'s return value).
> 3. Clears the screen with `COLOR_BG`, calls `current_scene.draw(screen)`, `pygame.display.flip()`, and caps via `clock.tick(FPS)`.
>
> No game logic belongs here — if you find yourself writing an `if terrain == ...` branch or an MCTS loop directly in `main.py`, that's a sign it belongs in `grid.py`/`pathfinding.py`/`mcts.py` instead. `main.py`'s only "state machine" is the *scene* switch; the `IDLE → REVEALING → FOLLOWING` state machine for pathfinding lives inside `PathfindingScene`, not here — keep the reveal-animation ownership in `scenes.py` per the previous prompt, and just call `update`/`draw` on it from this loop.
>
> Also implement graceful asset fallback at startup: attempt to load every path in `settings`'s asset constants once, log (`print`) any that fail, and set a `USE_SPRITES` bool passed down to scenes so missing art degrades to the flat-color/vector fallbacks described in `frog.py`/`grid.py`/`scenes.py` rather than crashing — you want a broken PNG path to never be the reason a live demo fails.

---

## 9. Creativity levers already built into this spec (don't add more without checking the rubric table in §0)

- Sprite-based frog + tokens with graceful vector fallback.
- Diagonal corner-cut prevention (a detail most submissions miss).
- Octile vs Manhattan heuristic switch tied correctly to the diagonal toggle.
- Reynolds projection-based path following instead of naive waypoint-seek.
- Difficulty-tiered MCTS (`easy/medium/hard`) exposed in the menu.
- Threaded search with a live "thinking…" indicator so AI-vs-AI mode is watchable rather than freezing the window.
- Themed, color-graded stats panel with the chosen column visually highlighted.

If you want more creativity points beyond these, the safest additions (each independent, none required) are: (a) an editable terrain brush so you can hand-paint the demo map live, (b) a step-through mode for MCTS that visualizes one simulation's rollout path on the board, (c) a small opening book so `easy` AI doesn't feel randomly cheap. Don't add any of these mid-build — finish and test the seven files above first.

---

## 10. Demo narration checklist (say these out loud on camera, don't just show code)

- [ ] Point at two different terrain cells, state their cost (grass=1, mud=3, water=5, wall=∞), and explain why the A* path detours around water.
- [ ] Toggle the heatmap on, explain explored vs. frontier vs. path coloring.
- [ ] Toggle diagonal movement off/on, show the path shape change, mention corner-cutting prevention.
- [ ] Read the `Total Cost` HUD number and manually add 2–3 step costs from the legend to sanity-check it live.
- [ ] In Connect4, point at the stats panel: read one column's visit count and win rate, then read the chosen column's UCB score specifically, since that's graded as its own line item.
- [ ] Show AI-vs-AI mode running end to end without input.
- [ ] Your face must be visible per the assignment's submission rule — frame the camera before starting.
