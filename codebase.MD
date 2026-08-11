This file is a merged representation of the entire codebase, combined into a single document by Repomix.

<file_summary>
This section contains a summary of this file.

<purpose>
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.
</purpose>

<file_format>
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  - File path as an attribute
  - Full contents of the file
</file_format>

<usage_guidelines>
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.
</usage_guidelines>

<notes>
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)
</notes>

</file_summary>

<directory_structure>
part2/
  connect4_mcts.py
  startercodeassignment2.MD
Antigravity_Build_Spec_A2.md
frog.py
grid.py
main.py
mcts.py
pathfinding.py
README.md
scenes.py
settings.py
</directory_structure>

<files>
This section contains the contents of the repository's files.

<file path="Antigravity_Build_Spec_A2.md">
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
</file>

<file path="frog.py">
from typing import Optional, List, Tuple
import math
import pygame
from settings import (
    PATH_RADIUS,
    WAYPOINT_ARRIVAL_RADIUS,
    FROG_MAX_SPEED,
    FROG_MAX_FORCE,
    FROG_SLOW_RADIUS,
    FROG_PREDICT_DIST,
)

def project_point_on_segment(p: pygame.Vector2, a: pygame.Vector2, b: pygame.Vector2) -> pygame.Vector2:
    """Projects point P onto segment AB, clamping scalar t to [0, 1]."""
    ab = b - a
    if ab.length_squared() == 0:
        return pygame.Vector2(a)
    t = (p - a).dot(ab) / ab.length_squared()
    t = max(0.0, min(1.0, t))
    return a + ab * t

class Frog:
    def __init__(self, x: float, y: float, sprite_path: Optional[str] = None):
        self.pos = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0.0, 0.0)
        self.path: List[pygame.Vector2] = []
        self.path_index = 0
        self.angle = 0.0
        
        self.sprite = None
        if sprite_path:
            try:
                raw_sprite = pygame.image.load(str(sprite_path)).convert_alpha()
                self.sprite = pygame.transform.scale(raw_sprite, (36, 36))
            except Exception:
                self.sprite = None

    def set_path(self, world_points: List[Tuple[float, float]]):
        self.path = [pygame.Vector2(pt[0], pt[1]) for pt in world_points]
        self.path_index = 0

    def is_path_complete(self) -> bool:
        if not self.path:
            return True
        final_target = self.path[-1]
        is_last_index = (self.path_index >= len(self.path) - 1)
        is_close = (self.pos.distance_to(final_target) < WAYPOINT_ARRIVAL_RADIUS)
        return is_last_index and is_close

    def follow_path(self, dt: float):
        if not self.path:
            return

        target = self.path[self.path_index]
        
        # 1. Advance waypoint index if arrived at current target
        if self.pos.distance_to(target) < WAYPOINT_ARRIVAL_RADIUS and self.path_index < len(self.path) - 1:
            self.path_index += 1
            target = self.path[self.path_index]

        # 2. Predict future position (Reynolds' look ahead)
        if self.velocity.length() > 0:
            future_pos = self.pos + self.velocity.normalize() * FROG_PREDICT_DIST
        else:
            future_pos = pygame.Vector2(self.pos)

        # 3. Project future position onto active path segment
        seg_start = self.path[max(self.path_index - 1, 0)]
        seg_end = target
        projected = project_point_on_segment(future_pos, seg_start, seg_end)

        # 4. Steering decision: seek onto line if off-track, else arrive at target
        distance_off_line = future_pos.distance_to(projected)
        seg_dir = (seg_end - seg_start)
        if seg_dir.length() > 0:
            seg_dir = seg_dir.normalize()
        else:
            seg_dir = pygame.Vector2(1, 0)

        if distance_off_line > PATH_RADIUS:
            seek_target = projected + seg_dir * FROG_PREDICT_DIST
            steering = self._seek(seek_target)
        else:
            # Arrive behavior towards current target segment endpoint
            steering = self._arrive(target)

        self._apply_steering(steering, dt)
        self._update_facing_angle()

    def _seek(self, target: pygame.Vector2) -> pygame.Vector2:
        desired = (target - self.pos)
        if desired.length() > 0:
            desired = desired.normalize() * FROG_MAX_SPEED
        else:
            desired = pygame.Vector2(0, 0)
        
        steering = desired - self.velocity
        if steering.length() > FROG_MAX_FORCE:
            steering = steering.normalize() * FROG_MAX_FORCE
        return steering

    def _arrive(self, target: pygame.Vector2) -> pygame.Vector2:
        to_target = target - self.pos
        dist = to_target.length()

        if dist < 0.001:
            desired = pygame.Vector2(0, 0)
        else:
            if dist < FROG_SLOW_RADIUS:
                speed = FROG_MAX_SPEED * (dist / FROG_SLOW_RADIUS)
            else:
                speed = FROG_MAX_SPEED
            desired = to_target.normalize() * speed

        steering = desired - self.velocity
        if steering.length() > FROG_MAX_FORCE:
            steering = steering.normalize() * FROG_MAX_FORCE
        return steering

    def _apply_steering(self, force: pygame.Vector2, dt: float):
        self.velocity += force * dt
        if self.velocity.length() > FROG_MAX_SPEED:
            self.velocity = self.velocity.normalize() * FROG_MAX_SPEED
        
        self.pos += self.velocity * dt

    def _update_facing_angle(self):
        if self.velocity.length() > 5.0:
            # Angle relative to positive X-axis in degrees
            self.angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x))

    def draw(self, surface: pygame.Surface):
        if self.sprite:
            rotated_sprite = pygame.transform.rotate(self.sprite, self.angle)
            rect = rotated_sprite.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            surface.blit(rotated_sprite, rect)
        else:
            # Vector fallback: Green circle with direction indicator line
            center = (int(self.pos.x), int(self.pos.y))
            pygame.draw.circle(surface, (40, 200, 40), center, 14)
            pygame.draw.circle(surface, (255, 255, 255), center, 14, 2)
            
            rad = math.radians(self.angle)
            end_x = self.pos.x + 18 * math.cos(rad)
            end_y = self.pos.y - 18 * math.sin(rad)
            pygame.draw.line(surface, (255, 255, 0), center, (end_x, end_y), 3)
</file>

<file path="grid.py">
from typing import Optional, Union, Dict, List, Tuple
import math
import random
import pygame
from settings import (
    TILE_SIZE,
    Terrain,
    TERRAIN_COST,
    TERRAIN_COLOR,
    COLOR_EXPLORED,
    COLOR_FRONTIER,
    COLOR_PATH,
    COLOR_GRID_LINE,
)

class Cell:
    __slots__ = ("col", "row", "terrain", "g_cost", "explored", "frontier", "in_path")

    def __init__(self, col: int, row: int, terrain: str):
        self.col = col
        self.row = row
        self.terrain = terrain
        self.g_cost = None      # set by A* when explored
        self.explored = False   # popped from open set
        self.frontier = False   # currently in open set
        self.in_path = False    # part of final path

class TerrainGrid:
    def __init__(self, cols: int, rows: int, layout: Optional[List[str]] = None):
        self.cols = cols
        self.rows = rows
        self.grid = [[None for _ in range(rows)] for _ in range(cols)]
        
        if layout:
            self._load_from_layout(layout)
        else:
            self._procedural_generate()

    def _load_from_layout(self, layout: list[str]):
        char_map = {
            '.': Terrain.GRASS,
            'm': Terrain.MUD,
            'w': Terrain.WATER,
            '#': Terrain.WALL,
        }
        for r in range(min(self.rows, len(layout))):
            line = layout[r]
            for c in range(min(self.cols, len(line))):
                char = line[c]
                terrain = char_map.get(char, Terrain.GRASS)
                self.grid[c][r] = Cell(c, r, terrain)

    def _procedural_generate(self):
        # Procedurally seed terrain
        for r in range(self.rows):
            for c in range(self.cols):
                rand = random.random()
                if rand < 0.65:
                    t = Terrain.GRASS
                elif rand < 0.83:
                    t = Terrain.MUD
                elif rand < 0.95:
                    t = Terrain.WATER
                else:
                    t = Terrain.WALL
                self.grid[c][r] = Cell(c, r, t)
        
        # Simple cluster smoothing for walls/water
        for _ in range(2):
            for r in range(1, self.rows - 1):
                for c in range(1, self.cols - 1):
                    current_cell = self.grid[c][r]
                    if current_cell.terrain == Terrain.WALL:
                        wall_neighbors = sum(
                            1 for dc in (-1, 0, 1) for dr in (-1, 0, 1)
                            if (dc != 0 or dr != 0) and self.grid[c+dc][r+dr].terrain == Terrain.WALL
                        )
                        if wall_neighbors < 2:
                            current_cell.terrain = Terrain.GRASS

    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def get_cell(self, col: int, row: int) -> Optional[Cell]:
        if self.in_bounds(col, row):
            return self.grid[col][row]
        return None

    def cost(self, col: int, row: int) -> float:
        cell = self.get_cell(col, row)
        if not cell:
            return float("inf")
        return TERRAIN_COST[cell.terrain]

    def neighbors(self, col: int, row: int, allow_diagonal: bool) -> list[tuple[int, int]]:
        result = []
        cardinals = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        for dc, dr in cardinals:
            nc, nr = col + dc, row + dr
            if self.in_bounds(nc, nr) and self.cost(nc, nr) < float("inf"):
                result.append((nc, nr))

        if allow_diagonal:
            diagonals = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
            for dc, dr in diagonals:
                nc, nr = col + dc, row + dr
                if self.in_bounds(nc, nr) and self.cost(nc, nr) < float("inf"):
                    # Explicitly prevent corner-cutting:
                    # Diagonal move is legal ONLY IF both orthogonal adjacent cells are not walls
                    ortho1_passable = self.cost(col + dc, row) < float("inf")
                    ortho2_passable = self.cost(col, row + dr) < float("inf")
                    if ortho1_passable and ortho2_passable:
                        result.append((nc, nr))

        return result

    def movement_cost(self, from_cell: Cell, to_cell: Cell) -> float:
        base_cost = TERRAIN_COST[to_cell.terrain]
        is_diagonal = (from_cell.col != to_cell.col) and (from_cell.row != to_cell.row)
        return base_cost * (1.4142 if is_diagonal else 1.0)

    def reset_search_state(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[c][r]
                cell.g_cost = None
                cell.explored = False
                cell.frontier = False
                cell.in_path = False

    def world_to_cell(self, x: float, y: float) -> tuple[int, int]:
        col = int(x // TILE_SIZE)
        row = int(y // TILE_SIZE)
        return col, row

    def cell_to_world_center(self, col: int, row: int) -> tuple[float, float]:
        x = col * TILE_SIZE + TILE_SIZE / 2.0
        y = row * TILE_SIZE + TILE_SIZE / 2.0
        return x, y

    def draw(
        self,
        surface: pygame.Surface,
        tileset: Optional[pygame.Surface],
        show_heatmap: bool,
        show_cost_labels: bool,
        font: pygame.font.Font,
    ):
        overlay_explored = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        overlay_explored.fill(COLOR_EXPLORED)

        overlay_frontier = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        overlay_frontier.fill(COLOR_FRONTIER)

        for c in range(self.cols):
            for r in range(self.rows):
                cell = self.grid[c][r]
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)

                # Draw Base Terrain Tile
                if tileset:
                    # Tile index mapping fallback if tileset provided
                    tile_rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
                    surface.blit(tileset, rect, tile_rect)
                else:
                    color = TERRAIN_COLOR[cell.terrain]
                    pygame.draw.rect(surface, color, rect)

                # Draw Path Highlight (Green)
                if cell.in_path:
                    path_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    path_surf.fill((*COLOR_PATH[:3], 150))
                    surface.blit(path_surf, rect)
                # Heatmap / Frontier Overlay
                elif show_heatmap:
                    if cell.explored:
                        surface.blit(overlay_explored, rect)
                    elif cell.frontier:
                        surface.blit(overlay_frontier, rect)

                # Draw Cell Cost Labels
                if show_cost_labels and cell.g_cost is not None:
                    text_str = f"{cell.g_cost:.1f}"
                    txt_surf = font.render(text_str, True, (255, 255, 255))
                    txt_rect = txt_surf.get_rect(center=rect.center)
                    # Small drop shadow for text readability
                    shadow_surf = font.render(text_str, True, (0, 0, 0))
                    surface.blit(shadow_surf, (txt_rect.x + 1, txt_rect.y + 1))
                    surface.blit(txt_surf, txt_rect)

                # Grid Lines
                pygame.draw.rect(surface, COLOR_GRID_LINE, rect, 1)
</file>

<file path="main.py">
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
</file>

<file path="mcts.py">
from typing import Optional, List, Dict
import math
import random
import time
import queue
import threading
from dataclasses import dataclass
from settings import MCTS_C_PARAM, MCTS_DIFFICULTIES

# Connect 4 Constants
ROWS = 6
COLS = 7
EMPTY = 0
PLAYER1 = 1
PLAYER2 = 2

class Connect4State:
    def __init__(self, board=None, current_player=PLAYER1):
        if board is None:
            self.board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        else:
            self.board = [row[:] for row in board]
        self.current_player = current_player

    def clone(self):
        return Connect4State(self.board, self.current_player)

    def get_legal_moves(self) -> List[int]:
        return [c for c in range(COLS) if self.board[0][c] == EMPTY]

    def make_move(self, col: int) -> bool:
        for r in range(ROWS - 1, -1, -1):
            if self.board[r][col] == EMPTY:
                self.board[r][col] = self.current_player
                self.current_player = PLAYER1 if self.current_player == PLAYER2 else PLAYER2
                return True
        return False

    def check_winner(self) -> Optional[int]:
        # Horizontal check
        for r in range(ROWS):
            for c in range(COLS - 3):
                p = self.board[r][c]
                if p != EMPTY and all(self.board[r][c + i] == p for i in range(4)):
                    return p

        # Vertical check
        for c in range(COLS):
            for r in range(ROWS - 3):
                p = self.board[r][c]
                if p != EMPTY and all(self.board[r + i][c] == p for i in range(4)):
                    return p

        # Positive diagonal (top-left to bottom-right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                p = self.board[r][c]
                if p != EMPTY and all(self.board[r + i][c + i] == p for i in range(4)):
                    return p

        # Negative diagonal (bottom-left to top-right)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                p = self.board[r][c]
                if p != EMPTY and all(self.board[r - i][c + i] == p for i in range(4)):
                    return p

        return None

    def is_full(self) -> bool:
        return all(self.board[0][c] != EMPTY for c in range(COLS))

    def is_terminal(self) -> bool:
        return self.check_winner() is not None or self.is_full()

@dataclass
class ColumnStat:
    column: int
    visits: int
    win_rate: float
    ucb_score: float

@dataclass
class MCTSResult:
    chosen_column: Optional[int]
    stats: Dict[int, ColumnStat]
    iterations_run: int
    elapsed_sec: float

class MCTSNode:
    def __init__(self, state: Connect4State, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children: List['MCTSNode'] = []
        self.visits = 0
        self.wins = 0.0

    def is_fully_expanded(self) -> bool:
        if self.state.is_terminal():
            return True
        return len(self.children) == len(self.state.get_legal_moves())

    def uct_score(self, c_param: float) -> float:
        if self.visits == 0:
            return float("inf")
        if self.parent is None or self.parent.visits == 0:
            parent_visits = self.visits
        else:
            parent_visits = self.parent.visits

        exploitation = self.wins / self.visits
        exploration = c_param * math.sqrt(math.log(parent_visits) / self.visits)
        return exploitation + exploration

    def best_child(self, c_param: float = MCTS_C_PARAM):
        return max(self.children, key=lambda child: child.uct_score(c_param))

def mcts_search(
    root_state: Connect4State,
    n_iter: Optional[int] = None,
    time_limit_sec: Optional[float] = None,
    c_param: float = MCTS_C_PARAM,
    progress_cb=None
) -> MCTSResult:
    start_time = time.time()
    root_node = MCTSNode(root_state.clone())
    root_player = root_state.current_player
    legal_moves = root_state.get_legal_moves()

    if not legal_moves or root_state.is_terminal():
        empty_stats = {
            col: ColumnStat(column=col, visits=0, win_rate=0.0, ucb_score=0.0)
            for col in range(COLS)
        }
        return MCTSResult(chosen_column=None, stats=empty_stats, iterations_run=0, elapsed_sec=0.0)

    iterations_so_far = 0

    while True:
        # Check iteration or time limit conditions
        if n_iter is not None and iterations_so_far >= n_iter:
            break
        if time_limit_sec is not None and (time.time() - start_time) >= time_limit_sec:
            break

        iterations_so_far += 1

        # 1. Selection
        node = root_node
        while node.is_fully_expanded() and not node.state.is_terminal():
            node = node.best_child(c_param)

        # 2. Expansion
        if not node.state.is_terminal():
            tried_moves = {child.move for child in node.children}
            untried_moves = [m for m in node.state.get_legal_moves() if m not in tried_moves]
            if untried_moves:
                move = random.choice(untried_moves)
                new_state = node.state.clone()
                new_state.make_move(move)
                child_node = MCTSNode(new_state, parent=node, move=move)
                node.children.append(child_node)
                node = child_node

        # 3. Simulation (Rollout)
        sim_state = node.state.clone()
        while not sim_state.is_terminal():
            moves = sim_state.get_legal_moves()
            sim_state.make_move(random.choice(moves))

        winner = sim_state.check_winner()
        if winner == root_player:
            reward = 1.0
        elif winner is None:
            reward = 0.5
        else:
            reward = 0.0

        # 4. Backpropagation
        curr_node = node
        while curr_node is not None:
            curr_node.visits += 1
            # Check player context: reward from root_player's perspective
            curr_node.wins += reward
            curr_node = curr_node.parent

        if progress_cb and iterations_so_far % 50 == 0:
            progress_cb(iterations_so_far, n_iter or 0)

    elapsed = time.time() - start_time

    # Build per-column statistics
    stats: Dict[int, ColumnStat] = {}
    child_map = {child.move: child for child in root_node.children}

    for col in range(COLS):
        if col in child_map:
            child = child_map[col]
            v = child.visits
            wr = (child.wins / v) if v > 0 else 0.0
            ucb = child.uct_score(c_param)
            stats[col] = ColumnStat(column=col, visits=v, win_rate=wr, ucb_score=ucb)
        else:
            is_legal = col in legal_moves
            ucb_val = float("inf") if is_legal else -1.0
            stats[col] = ColumnStat(column=col, visits=0, win_rate=0.0, ucb_score=ucb_val)

    # Select best column based on most visits
    most_visited_child = max(root_node.children, key=lambda c: c.visits) if root_node.children else None
    chosen = most_visited_child.move if most_visited_child else (legal_moves[0] if legal_moves else None)

    return MCTSResult(
        chosen_column=chosen,
        stats=stats,
        iterations_run=iterations_so_far,
        elapsed_sec=elapsed
    )

class AIWorker(threading.Thread):
    def __init__(self, state: Connect4State, difficulty: str, result_queue: queue.Queue):
        super().__init__(daemon=True)
        self.state_clone = state.clone()
        self.difficulty = difficulty
        self.result_queue = result_queue

    def run(self):
        try:
            n_iter = MCTS_DIFFICULTIES.get(self.difficulty, 2000)
            res = mcts_search(self.state_clone, n_iter=n_iter, time_limit_sec=MCTS_TIME_LIMIT_SEC)
            self.result_queue.put(res)
        except Exception as e:
            self.result_queue.put(e)
</file>

<file path="pathfinding.py">
from typing import Optional, List, Tuple, Dict
import heapq
import math
from dataclasses import dataclass, field
from grid import TerrainGrid, Cell

@dataclass
class AStarResult:
    path: List[Tuple[float, float]]       # ordered list of (x, y) world centers, start to goal inclusive
    total_cost: float                     # g_cost of goal cell; float('inf') if unreachable
    explored_order: List[Tuple[int, int]] # (col, row) cells in the order they were POPPED from open set
    reachable: bool

def octile_distance(c1: Tuple[int, int], c2: Tuple[int, int]) -> float:
    dx = abs(c1[0] - c2[0])
    dy = abs(c1[1] - c2[1])
    return (dx + dy) + (math.sqrt(2.0) - 2.0) * min(dx, dy)

def manhattan_distance(c1: Tuple[int, int], c2: Tuple[int, int]) -> float:
    return float(abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]))

def find_path(
    grid: TerrainGrid,
    start: Tuple[int, int],
    goal: Tuple[int, int],
    allow_diagonal: bool
) -> AStarResult:
    grid.reset_search_state()

    start_col, start_row = start
    goal_col, goal_row = goal

    if not grid.in_bounds(start_col, start_row) or not grid.in_bounds(goal_col, goal_row):
        return AStarResult(path=[], total_cost=float("inf"), explored_order=[], reachable=False)

    if grid.cost(start_col, start_row) == float("inf") or grid.cost(goal_col, goal_row) == float("inf"):
        return AStarResult(path=[], total_cost=float("inf"), explored_order=[], reachable=False)

    heuristic_fn = octile_distance if allow_diagonal else manhattan_distance

    # Priority queue storing tuples: (f_score, g_score, col, row)
    # Using small tie-breaker bias on h_score (multiply by 1.001) to favor larger g
    open_set = []
    
    h_start = heuristic_fn(start, goal)
    heapq.heappush(open_set, (h_start * 1.001, 0.0, start_col, start_row))

    g_score = {(start_col, start_row): 0.0}
    came_from = {}
    explored_order = []
    
    # Track frontier nodes for visual rendering overlay
    start_cell = grid.get_cell(start_col, start_row)
    if start_cell:
        start_cell.frontier = True

    reached_goal = False

    while open_set:
        f, current_g, col, row = heapq.heappop(open_set)

        cell = grid.get_cell(col, row)
        if cell is None:
            continue

        # Skip if we already found a cheaper way to this popped node
        if current_g > g_score.get((col, row), float("inf")):
            continue

        cell.frontier = False
        cell.explored = True
        cell.g_cost = current_g
        explored_order.append((col, row))

        if (col, row) == (goal_col, goal_row):
            reached_goal = True
            break

        for nc, nr in grid.neighbors(col, row, allow_diagonal):
            neighbor_cell = grid.get_cell(nc, nr)
            if neighbor_cell is None or neighbor_cell.explored:
                continue

            move_cost = grid.movement_cost(cell, neighbor_cell)
            tentative_g = current_g + move_cost

            if tentative_g < g_score.get((nc, nr), float("inf")):
                came_from[(nc, nr)] = (col, row)
                g_score[(nc, nr)] = tentative_g
                h_val = heuristic_fn((nc, nr), goal)
                f_val = tentative_g + h_val * 1.001
                
                neighbor_cell.frontier = True
                heapq.heappush(open_set, (f_val, tentative_g, nc, nr))

    if not reached_goal:
        return AStarResult(path=[], total_cost=float("inf"), explored_order=explored_order, reachable=False)

    # Reconstruct path from goal to start
    curr = (goal_col, goal_row)
    grid_path = [curr]
    while curr in came_from:
        curr = came_from[curr]
        grid_path.append(curr)

    grid_path.reverse()

    # Convert grid cell coordinates to world center points and mark in_path
    world_path = []
    for c, r in grid_path:
        cell = grid.get_cell(c, r)
        if cell:
            cell.in_path = True
        world_path.append(grid.cell_to_world_center(c, r))

    goal_total_cost = g_score.get((goal_col, goal_row), float("inf"))
    return AStarResult(path=world_path, total_cost=goal_total_cost, explored_order=explored_order, reachable=True)

def path_cost_breakdown(grid: TerrainGrid, grid_coords: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], float, float]]:
    """Returns a list of ((col, row), step_cost, cumulative_cost) for narration / debugging."""
    breakdown = []
    cum_cost = 0.0
    for i, (c, r) in enumerate(grid_coords):
        cell = grid.get_cell(c, r)
        if i == 0:
            step_cost = 0.0
        else:
            prev_c, prev_r = grid_coords[i-1]
            prev_cell = grid.get_cell(prev_c, prev_r)
            step_cost = grid.movement_cost(prev_cell, cell) if prev_cell and cell else 0.0
        cum_cost += step_cost
        breakdown.append(((c, r), step_cost, cum_cost))
    return breakdown
</file>

<file path="scenes.py">
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
</file>

<file path="settings.py">
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
</file>

<file path="part2/connect4_mcts.py">
"""
Assignment II - Starter Code: Connect 4 in Pygame with MCTS based hint for 2 human players.

This file is meant to be the starter code, it is not a requirement, feel free to ignore it.
In your tasks, you need to implement:
    -  1 human player against an AI agent
    -  2 AI agents playing against each other.

Run this sample codeussing: 
    python connect4_mcts.py

Rememever that you need Pygame installed:
    pip install pygame
"""

import pygame
import sys
import math
import random

# ==========================================
#              PART 1 - GAME CONSTANTS AND COLORS
#             ==========================

# In Connect 4, the board has 6 rows and 7 columns.
ROWS = 6
COLS = 7

# So I use simple integers to represent the content of each cell.
EMPTY = 0      # No piece in this cell
PLAYER1 = 1    # Player 1 piece (red)
PLAYER2 = 2    # Player 2 piece (yellow)

# Visual settings for Pygame. Up to you if you want to tweak these to resiz
SQUARESIZE = 100
RADIUS = SQUARESIZE // 2 - 5

# Colors are given in RGB format (red, green, blue)
BOARD_COLOR = (0, 0, 200)        # Blue board background
BG_COLOR = (0, 0, 0)             # Black background
PLAYER1_COLOR = (200, 0, 0)      # Red discs for player 1
PLAYER2_COLOR = (230, 230, 0)    # Yellow discs for player 2
TEXT_COLOR = (255, 255, 255)     # White text
HINT_COLOR = (0, 200, 0)         # Green hint marker

# Screen size
WIDTH = COLS * SQUARESIZE
# Extra 2 rows of space for messages and hint marker
HEIGHT = (ROWS + 2) * SQUARESIZE
SIZE = (WIDTH, HEIGHT)

FPS = 60


# ====================================
#              PART 2 - CONNECT 4 STATE CLASS
# ====================================

class Connect4State:
    """
    This class represents a Connect 4 game state.

    It contains:
    - The board, a list of lists of integers.
    - The current player who should move next.

    I will keep all the game logic here, but again this is not a requirement so feel free:
    - Getting legal moves
    - Applying a move
    - Checking for a win or a draw
    """

    def __init__(self, board=None, current_player=PLAYER1):
        """
        Constructor for the game state.

        board:
            Either None (start a new empty baord)
            or an existing 2D list to copy.

        current_player:
            Either PLAYER1 or PLAYER2.
        """
        if board is None:
            # Create an empty baord with ROWS x COLS filled with EMPTY
            self.board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        else:
            # Make a deep copy of the baord so we do not modify the original
            self.board = [row[:] for row in board]

        self.current_player = current_player

    def clone(self):
        """
        Create a new Connect4State with the same board and current player.

        Useful in MCTS when we want to simulate moves without
        changing the original game state.
        """
        return Connect4State(self.board, self.current_player)

    def get_legal_moves(self):
        """
        Return a lits of columns (indices from 0 to COLS - 1)
        where a piece can still be dropped.

        A column is legal if its top cell (row 0) is EMPTY !!!! This is very important in the game logic
        """
        moves = []
        for c in range(COLS):
            if self.board[0][c] == EMPTY:
                moves.append(c)
        return moves

    def make_move(self, col):
        """
        Drop a piece for the current player in the given column.

        If the column is valid:
            - The piece will fall to the lowest available row.
            - The current player will switch to the other player.
            - The function returns True.

        If the column is full:
            - The function retunrs False and does nothing.
        """
        for r in range(ROWS - 1, -1, -1):  # Start from bottom row and go up
            if self.board[r][col] == EMPTY:
                self.board[r][col] = self.current_player
                # Switch to the other player
                self.current_player = PLAYER1 if self.current_player == PLAYER2 else PLAYER2
                return True
        return False  # Column was full

    def check_winner(self):
        """
        Check if there is a winner on the baord.

        Right, we need to look for 4 equal, non empty pieces in:
        - Horizontal lines
        - Vertical lines
        - Diagonals from top left to bottom right
        - Diagonals from bottom left to top right\
        This is very important.

        Returns:
            PLAYER1 if player 1 wins
            PLAYER2 if player 2 wins
            None if there is no winner
        """

        # Horizontal check
        for r in range(ROWS):
            for c in range(COLS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r][c + i] == piece for i in range(4)):
                        return piece

        # Vertical check
        for c in range(COLS):
            for r in range(ROWS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r + i][c] == piece for i in range(4)):
                        return piece

        # Diagonal check (top left to bottom right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r + i][c + i] == piece for i in range(4)):
                        return piece

        # Diagonal check (bottom left to top right)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r - i][c + i] == piece for i in range(4)):
                        return piece

        # No winner found
        return None

    def is_full(self):
        """
        Check if the board is full.

        If the top row has no EMPTY cells, then no more moves can be played.
        """
        return all(self.board[0][c] != EMPTY for c in range(COLS))

    def is_terminal(self):
        """
        Check if the game is over.

        The game is terminal if:
        - someone won, or
        - the board is full (draw).
        """
        if self.check_winner() is not None:
            return True
        if self.is_full():
            return True
        return False


# ============================================================
#                 PART 3 - MCTS EXPLANATION
# ============================================================

"""
Let me now explain the Monte Carlo Tree Search (MCTS) algorithm that we will use
to suggest a good move as a hint for the current player.

MCTS is built on 4 main steps that are repeated many times:

1. SELECTION
   - Start from the root node that represents the current game state.
   - If the node has already been visited and fully expanded,
     we use a formula called UCT (Upper Confidence bound applied to Trees)
     to pick the child that balances:
        * Exploitation: children that won more often in the past.
        * Exploration: children that have been visited fewer times.
   - We follow this path of best children until we reach a node that:
        * is not fully expanded, or
        * represents a terminal game state (win, loss, or draw).

2. EXPANSION
   - If the selected node is not terminal, we can add a new child.
   - A child corresponds to playing one of the moves that has not been tried yet.
   - We pick one untried move, apply it to a copy of the game state,
     and create a new child node that stores this new state.

3. SIMULATION (also called ROLLOUT)
   - From the newly created child state, we play a random game until the end.
   - That means we randomly select legal moves until we reach a win, loss, or draw.
   - At the end we know the result:
        * The root player wins, loses, or it is a draw.
   - We convert this result into a numeric reward:
        * 1.0 for a win for the root player
        * 0.0 for a loss for the root player
        * 0.5 for a draw

4. BACKPROPAGATION
   - We then walk back from the simulation node up to the root node.
   - For each node on this path we:
        * Increase the visit count.
        * Add the reward to the node's total wins.
   - This way, each node stores:
        * How many times we visited it.
        * How many wins the root player got through this node.

After doing many iterations of these four steps:
   - The root node will have some children, each corresponding to a possible move.
   - Each child has a visit count and a total win count.
   - We can then pick the child that has the most visits.
   - The move that leads to that child is our suggested move.

The main idea:
   - Random simulations plus statistics guide us to good moves.
   - More iterations usually gives a smarter suggestion.
"""


# ============================================================
#              PART 4 - MCTS DATA STRUCTURES AND CODE
# ============================================================

class MCTSNode:
    """
    Node in the MCTS tree.

    It stores:
    - state: a Connect4State instance
    - parent: parent node in the tree (None for root)
    - move: the move (column index) that led from the parent state to this state
    - children: list of child MCTSNode objects
    - visits: how many times this node was visited in the search
    - wins: total reward from the root player's perspective
    """

    def __init__(self, state, parent=None, move=None):
        self.state = state          # Game state at this node
        self.parent = parent        # Parent node
        self.move = move            # Move that led to this node from parent
        self.children = []          # List of child MCTSNode instances
        self.visits = 0             # Number of times this node has been visited
        self.wins = 0.0             # Sum of rewards from root player's point of view

    def is_fully_expanded(self):
        """
        Check if this node has created children for all legal moves.

        If the state is terminal, we consider it fully expanded,
        because there are no moves to expand.

        Otherwise:
        - We get all legal moves from this state.
        - We compare them with the moves that are already used by children.
        - If every legal move has a child, then the node is fully expanded.
        """
        if self.state.is_terminal():
            return True

        child_moves = {child.move for child in self.children}
        legal_moves = set(self.state.get_legal_moves())
        # Node is fully expanded if:
        # - the number of children matches the number of legal moves
        # - and every legal move already has a child
        return legal_moves.issubset(child_moves) and len(legal_moves) == len(child_moves)

    def best_child(self, c_param=1.4):
        """
        Select a child using the UCT formula.

        UCT score for a child:
            exploit = wins / visits
            explore = sqrt( 2 * ln(parent_visits) / child_visits )
            score = exploit + c_param * explore

        - exploit encourages moves that have good win ratio.
        - explore encourages trying moves that are less visited.

        c_param (exploration constant) controls how much we explore.
        A common choice is around 1.4 (square root of 2).

        If a child has never been visited (visits == 0),
        we treat its score as infinity to ensure it is explored at least once.
        """
        best_score = float("-inf")
        best_children = []

        for child in self.children:
            if child.visits == 0:
                # Encourage at least one visit for every child
                score = float("inf")
            else:
                exploit = child.wins / child.visits
                explore = math.sqrt(2 * math.log(self.visits) / child.visits)
                score = exploit + c_param * explore

            # Keep track of the best score and all children that achieve it
            if score > best_score:
                best_score = score
                best_children = [child]
            elif score == best_score:
                best_children.append(child)

        # If several children tie, pick one at random
        return random.choice(best_children)

    def most_visited_child(self):
        """
        After MCTS finishes, we want to pick the move that was explored the most.

        This function returns the child with the highest visit count.
        If there are no children (no moves), returns None.
        """
        if not self.children:
            return None
        return max(self.children, key=lambda c: c.visits)


def rollout(state, root_player):
    """
    Perform a random simulation (rollout) from the given state until the game ends.

    We work on a cloned state so we do not modify the original.

    At each step:
        - Get the list of legal moves.
        - Pick one move uniformly at random.
        - Apply this move.

    When the game reaches a terminal state:
        - If the winner is the root player, we return 1.0
        - If the winner is the opponent, we return 0.0
        - If there is no winner (draw), we return 0.5

    Arguments:
        state: Connect4State from which to start simulation
        root_player: the player we consider as "our" perspective
    """
    temp_state = state.clone()

    # Play random moves until the game is over
    while not temp_state.is_terminal():
        legal_moves = temp_state.get_legal_moves()
        if not legal_moves:
            break  # No moves left, should be a draw
        move = random.choice(legal_moves)
        temp_state.make_move(move)

    # Game is over, check the result
    winner = temp_state.check_winner()
    if winner is None:
        return 0.5
    if winner == root_player:
        return 1.0
    else:
        return 0.0


def mcts_search(root_state, n_iter=400):
    """
    Run MCTS from the given root_state and return the best move.

    Arguments:
        root_state:
            The current game state from which we search.
        n_iter:
            Number of MCTS iterations. More iterations usually means a better hint
            but it is also slower.

    Returns:
        The column index of the suggested move, or
        None if there is no legal move.

    Steps:
        1. Create a root MCTSNode that holds a copy of root_state.
        2. For n_iter iterations:
            a) Selection
            b) Expansion
            c) Simulation
            d) Backpropagation
        3. Return the move of the most visited child of the root.
    """
    # If the game is already finished, we return no move
    if root_state.is_terminal():
        return None

    # The root player is the player who is about to move in root_state
    root_player = root_state.current_player

    # Create a root node for the MCTS tree
    root_node = MCTSNode(root_state.clone())

    for _ in range(n_iter):
        # 1. Start at the root node and work on a fresh copy of root_state
        node = root_node
        state = root_state.clone()

        # 2. SELECTION
        # While the current node has children, is fully expanded,
        # and the state is not terminal, choose the best child with UCT.
        while node.children and node.is_fully_expanded() and not state.is_terminal():
            node = node.best_child()
            # Apply the move that led to this child to our simulation state
            if node.move is not None:
                state.make_move(node.move)

        # 3. EXPANSION
        # If the state is not terminal, we can expand by creating a new child.
        if not state.is_terminal():
            legal_moves = state.get_legal_moves()
            existing_moves = {child.move for child in node.children}
            # Untried moves are legal moves without a child yet
            untried_moves = [m for m in legal_moves if m not in existing_moves]

            if untried_moves:
                # Pick one untried move at random
                move = random.choice(untried_moves)
                # Apply it to the simulation state
                state.make_move(move)
                # Create the new child node
                child_node = MCTSNode(state.clone(), parent=node, move=move)
                # Attach this new child to the tree
                node.children.append(child_node)
                # And select this new child as the node to simulate from
                node = child_node

        # 4. SIMULATION (ROLLOUT)
        # From this node's state, simulate a random game until the end.
        reward = rollout(state, root_player)

        # 5. BACKPROPAGATION
        # Walk up the tree and update visit and win counts.
        while node is not None:
            node.visits += 1
            node.wins += reward
            node = node.parent

    # After finishing all iterations, pick the child with the most visits.
    best_child = root_node.most_visited_child()
    if best_child is None:
        return None
    return best_child.move


# ============================================================
#             PART 5 - DRAWING THE GAME WITH PYGAME
# ============================================================

def draw_board(screen, state, font, hint_col=None, message=""):
    """
    Draw the entire game screen.

    This includes:
    - A message text at the top (whose turn, winner, instructions).
    - A small green hint marker at the top to show the suggested column.
    - The blue board with circular holes.
    - The pieces for both players.

    Arguments:
        screen: the Pygame surface where we draw
        state: the Connect4State we want to display
        font:  a Pygame font object for rendering text
        hint_col: optional column index for the hint move
        message: text message to display at the top
    """
    # Fill the screen with background color
    screen.fill(BG_COLOR)

    # Draw message area at the top
    text_surface = font.render(message, True, TEXT_COLOR)
    screen.blit(text_surface, (10, 5))

    # Draw hint marker if we have a suggested column
    if hint_col is not None:
        x_center = hint_col * SQUARESIZE + SQUARESIZE // 2
        pygame.draw.circle(
            screen,
            HINT_COLOR,
            (x_center, SQUARESIZE),
            RADIUS // 2,
        )

    # Draw blue board and empty holes
    for c in range(COLS):
        for r in range(ROWS):
            pygame.draw.rect(
                screen,
                BOARD_COLOR,
                (
                    c * SQUARESIZE,
                    (r + 2) * SQUARESIZE,
                    SQUARESIZE,
                    SQUARESIZE,
                ),
            )
            pygame.draw.circle(
                screen,
                BG_COLOR,
                (
                    c * SQUARESIZE + SQUARESIZE // 2,
                    (r + 2) * SQUARESIZE + SQUARESIZE // 2,
                ),
                RADIUS,
            )

    # Draw pieces for player 1 and player 2
    for c in range(COLS):
        for r in range(ROWS):
            piece = state.board[r][c]
            if piece == PLAYER1:
                color = PLAYER1_COLOR
            elif piece == PLAYER2:
                color = PLAYER2_COLOR
            else:
                continue  # Skip empty cells
            pygame.draw.circle(
                screen,
                color,
                (
                    c * SQUARESIZE + SQUARESIZE // 2,
                    (r + 2) * SQUARESIZE + SQUARESIZE // 2,
                ),
                RADIUS,
            )

    # Finally, update the display
    pygame.display.update()


# ============================================================
#              PART 6 - MAIN GAME LOOP WITH PYGAME
# ============================================================

def main():
    """
    Main function that runs the Pygame event loop.

    Game behavior (just for this starter because your assignment behavior is different):
        - 2 human players alternate turns.
        - The MCTS algorithm always computes a hint for the current player.
        - The hint is shown as a small green marker above the suggested column.
        - Players click with the mouse in the column where they want to drop a piece.
        - If a player wins or the board is full, a message is displayed.
        - Press R to restart the game.

    This function does not contain any MCTS logic itself.
    It just calls mcts_search to get the hint move.
    """
    pygame.init()

    # Create the screen and set the title
    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption("MCTS Connect4- 2 human players")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24)

    # Start with a fresh game state
    state = Connect4State()
    game_over = False

    # hint_col will store the column suggested by MCTS
    hint_col = None

    # Message at the top of the screen
    message = "Player 1 turn"

    # Compute the first hint for player 1
    hint_col = mcts_search(state, n_iter=400)

    running = True
    while running:
        # Limit the game loop speed to FPS frames per second
        clock.tick(FPS)

        # Handle events from Pygame (mouse, keyboard, window close)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Window close button clicked
                running = False

            if event.type == pygame.KEYDOWN:
                # If player presses R, reset the game
                if event.key == pygame.K_r:
                    state = Connect4State()
                    game_over = False
                    message = "Player 1 turn"
                    hint_col = mcts_search(state, n_iter=400)

            if event.type == pygame.MOUSEBUTTONDOWN:
                # If mouse is clicked and the game is still running
                if not game_over:
                    # Get mouse position and convert to column index
                    x, _ = event.pos
                    col = x // SQUARESIZE

                    # Check that the chosen column is a legal move
                    legal_moves = state.get_legal_moves()
                    if col in legal_moves:
                        # Apply this move
                        state.make_move(col)

                        # Check if this move wins the game
                        winner = state.check_winner()
                        if winner == PLAYER1:
                            message = "Player 1 wins, press R to restart"
                            game_over = True
                            hint_col = None
                        elif winner == PLAYER2:
                            message = "Player 2 wins, press R to restart"
                            game_over = True
                            hint_col = None
                        elif state.is_full():
                            # No more moves and no winner
                            message = "Draw, press R to restart"
                            game_over = True
                            hint_col = None
                        else:
                            # Game continues, switch message to the next player
                            current = state.current_player
                            message = f"Player {current} turn"

                            # Compute new hint for the new current player
                            hint_col = mcts_search(state, n_iter=400)

        # Draw the current frame
        draw_board(screen, state, font, hint_col, message)

    # When running goes False, quit Pygame and exit the program
    pygame.quit()
    sys.exit()


# This ensures that main() is called only when this file is run directly,
# not when it is imported as a module in another script.
if __name__ == "__main__":
    main()
</file>

<file path="part2/startercodeassignment2.MD">
This file is a merged representation of the entire codebase, combined into a single document by Repomix.

<file_summary>
This section contains a summary of this file.

<purpose>
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.
</purpose>

<file_format>
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  - File path as an attribute
  - Full contents of the file
</file_format>

<usage_guidelines>
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.
</usage_guidelines>

<notes>
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)
</notes>

</file_summary>

<directory_structure>
connect4_mcts.py
</directory_structure>

<files>
This section contains the contents of the repository's files.

<file path="connect4_mcts.py">
"""
Assignment II - Starter Code: Connect 4 in Pygame with MCTS based hint for 2 human players.

This file is meant to be the starter code, it is not a requirement, feel free to ignore it.
In your tasks, you need to implement:
    -  1 human player against an AI agent
    -  2 AI agents playing against each other.

Run this sample codeussing: 
    python connect4_mcts.py

Rememever that you need Pygame installed:
    pip install pygame
"""

import pygame
import sys
import math
import random

# ==========================================
#              PART 1 - GAME CONSTANTS AND COLORS
#             ==========================

# In Connect 4, the board has 6 rows and 7 columns.
ROWS = 6
COLS = 7

# So I use simple integers to represent the content of each cell.
EMPTY = 0      # No piece in this cell
PLAYER1 = 1    # Player 1 piece (red)
PLAYER2 = 2    # Player 2 piece (yellow)

# Visual settings for Pygame. Up to you if you want to tweak these to resiz
SQUARESIZE = 100
RADIUS = SQUARESIZE // 2 - 5

# Colors are given in RGB format (red, green, blue)
BOARD_COLOR = (0, 0, 200)        # Blue board background
BG_COLOR = (0, 0, 0)             # Black background
PLAYER1_COLOR = (200, 0, 0)      # Red discs for player 1
PLAYER2_COLOR = (230, 230, 0)    # Yellow discs for player 2
TEXT_COLOR = (255, 255, 255)     # White text
HINT_COLOR = (0, 200, 0)         # Green hint marker

# Screen size
WIDTH = COLS * SQUARESIZE
# Extra 2 rows of space for messages and hint marker
HEIGHT = (ROWS + 2) * SQUARESIZE
SIZE = (WIDTH, HEIGHT)

FPS = 60


# ====================================
#              PART 2 - CONNECT 4 STATE CLASS
# ====================================

class Connect4State:
    """
    This class represents a Connect 4 game state.

    It contains:
    - The board, a list of lists of integers.
    - The current player who should move next.

    I will keep all the game logic here, but again this is not a requirement so feel free:
    - Getting legal moves
    - Applying a move
    - Checking for a win or a draw
    """

    def __init__(self, board=None, current_player=PLAYER1):
        """
        Constructor for the game state.

        board:
            Either None (start a new empty baord)
            or an existing 2D list to copy.

        current_player:
            Either PLAYER1 or PLAYER2.
        """
        if board is None:
            # Create an empty baord with ROWS x COLS filled with EMPTY
            self.board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        else:
            # Make a deep copy of the baord so we do not modify the original
            self.board = [row[:] for row in board]

        self.current_player = current_player

    def clone(self):
        """
        Create a new Connect4State with the same board and current player.

        Useful in MCTS when we want to simulate moves without
        changing the original game state.
        """
        return Connect4State(self.board, self.current_player)

    def get_legal_moves(self):
        """
        Return a lits of columns (indices from 0 to COLS - 1)
        where a piece can still be dropped.

        A column is legal if its top cell (row 0) is EMPTY !!!! This is very important in the game logic
        """
        moves = []
        for c in range(COLS):
            if self.board[0][c] == EMPTY:
                moves.append(c)
        return moves

    def make_move(self, col):
        """
        Drop a piece for the current player in the given column.

        If the column is valid:
            - The piece will fall to the lowest available row.
            - The current player will switch to the other player.
            - The function returns True.

        If the column is full:
            - The function retunrs False and does nothing.
        """
        for r in range(ROWS - 1, -1, -1):  # Start from bottom row and go up
            if self.board[r][col] == EMPTY:
                self.board[r][col] = self.current_player
                # Switch to the other player
                self.current_player = PLAYER1 if self.current_player == PLAYER2 else PLAYER2
                return True
        return False  # Column was full

    def check_winner(self):
        """
        Check if there is a winner on the baord.

        Right, we need to look for 4 equal, non empty pieces in:
        - Horizontal lines
        - Vertical lines
        - Diagonals from top left to bottom right
        - Diagonals from bottom left to top right\
        This is very important.

        Returns:
            PLAYER1 if player 1 wins
            PLAYER2 if player 2 wins
            None if there is no winner
        """

        # Horizontal check
        for r in range(ROWS):
            for c in range(COLS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r][c + i] == piece for i in range(4)):
                        return piece

        # Vertical check
        for c in range(COLS):
            for r in range(ROWS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r + i][c] == piece for i in range(4)):
                        return piece

        # Diagonal check (top left to bottom right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r + i][c + i] == piece for i in range(4)):
                        return piece

        # Diagonal check (bottom left to top right)
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                piece = self.board[r][c]
                if piece != EMPTY:
                    if all(self.board[r - i][c + i] == piece for i in range(4)):
                        return piece

        # No winner found
        return None

    def is_full(self):
        """
        Check if the board is full.

        If the top row has no EMPTY cells, then no more moves can be played.
        """
        return all(self.board[0][c] != EMPTY for c in range(COLS))

    def is_terminal(self):
        """
        Check if the game is over.

        The game is terminal if:
        - someone won, or
        - the board is full (draw).
        """
        if self.check_winner() is not None:
            return True
        if self.is_full():
            return True
        return False


# ============================================================
#                 PART 3 - MCTS EXPLANATION
# ============================================================

"""
Let me now explain the Monte Carlo Tree Search (MCTS) algorithm that we will use
to suggest a good move as a hint for the current player.

MCTS is built on 4 main steps that are repeated many times:

1. SELECTION
   - Start from the root node that represents the current game state.
   - If the node has already been visited and fully expanded,
     we use a formula called UCT (Upper Confidence bound applied to Trees)
     to pick the child that balances:
        * Exploitation: children that won more often in the past.
        * Exploration: children that have been visited fewer times.
   - We follow this path of best children until we reach a node that:
        * is not fully expanded, or
        * represents a terminal game state (win, loss, or draw).

2. EXPANSION
   - If the selected node is not terminal, we can add a new child.
   - A child corresponds to playing one of the moves that has not been tried yet.
   - We pick one untried move, apply it to a copy of the game state,
     and create a new child node that stores this new state.

3. SIMULATION (also called ROLLOUT)
   - From the newly created child state, we play a random game until the end.
   - That means we randomly select legal moves until we reach a win, loss, or draw.
   - At the end we know the result:
        * The root player wins, loses, or it is a draw.
   - We convert this result into a numeric reward:
        * 1.0 for a win for the root player
        * 0.0 for a loss for the root player
        * 0.5 for a draw

4. BACKPROPAGATION
   - We then walk back from the simulation node up to the root node.
   - For each node on this path we:
        * Increase the visit count.
        * Add the reward to the node's total wins.
   - This way, each node stores:
        * How many times we visited it.
        * How many wins the root player got through this node.

After doing many iterations of these four steps:
   - The root node will have some children, each corresponding to a possible move.
   - Each child has a visit count and a total win count.
   - We can then pick the child that has the most visits.
   - The move that leads to that child is our suggested move.

The main idea:
   - Random simulations plus statistics guide us to good moves.
   - More iterations usually gives a smarter suggestion.
"""


# ============================================================
#              PART 4 - MCTS DATA STRUCTURES AND CODE
# ============================================================

class MCTSNode:
    """
    Node in the MCTS tree.

    It stores:
    - state: a Connect4State instance
    - parent: parent node in the tree (None for root)
    - move: the move (column index) that led from the parent state to this state
    - children: list of child MCTSNode objects
    - visits: how many times this node was visited in the search
    - wins: total reward from the root player's perspective
    """

    def __init__(self, state, parent=None, move=None):
        self.state = state          # Game state at this node
        self.parent = parent        # Parent node
        self.move = move            # Move that led to this node from parent
        self.children = []          # List of child MCTSNode instances
        self.visits = 0             # Number of times this node has been visited
        self.wins = 0.0             # Sum of rewards from root player's point of view

    def is_fully_expanded(self):
        """
        Check if this node has created children for all legal moves.

        If the state is terminal, we consider it fully expanded,
        because there are no moves to expand.

        Otherwise:
        - We get all legal moves from this state.
        - We compare them with the moves that are already used by children.
        - If every legal move has a child, then the node is fully expanded.
        """
        if self.state.is_terminal():
            return True

        child_moves = {child.move for child in self.children}
        legal_moves = set(self.state.get_legal_moves())
        # Node is fully expanded if:
        # - the number of children matches the number of legal moves
        # - and every legal move already has a child
        return legal_moves.issubset(child_moves) and len(legal_moves) == len(child_moves)

    def best_child(self, c_param=1.4):
        """
        Select a child using the UCT formula.

        UCT score for a child:
            exploit = wins / visits
            explore = sqrt( 2 * ln(parent_visits) / child_visits )
            score = exploit + c_param * explore

        - exploit encourages moves that have good win ratio.
        - explore encourages trying moves that are less visited.

        c_param (exploration constant) controls how much we explore.
        A common choice is around 1.4 (square root of 2).

        If a child has never been visited (visits == 0),
        we treat its score as infinity to ensure it is explored at least once.
        """
        best_score = float("-inf")
        best_children = []

        for child in self.children:
            if child.visits == 0:
                # Encourage at least one visit for every child
                score = float("inf")
            else:
                exploit = child.wins / child.visits
                explore = math.sqrt(2 * math.log(self.visits) / child.visits)
                score = exploit + c_param * explore

            # Keep track of the best score and all children that achieve it
            if score > best_score:
                best_score = score
                best_children = [child]
            elif score == best_score:
                best_children.append(child)

        # If several children tie, pick one at random
        return random.choice(best_children)

    def most_visited_child(self):
        """
        After MCTS finishes, we want to pick the move that was explored the most.

        This function returns the child with the highest visit count.
        If there are no children (no moves), returns None.
        """
        if not self.children:
            return None
        return max(self.children, key=lambda c: c.visits)


def rollout(state, root_player):
    """
    Perform a random simulation (rollout) from the given state until the game ends.

    We work on a cloned state so we do not modify the original.

    At each step:
        - Get the list of legal moves.
        - Pick one move uniformly at random.
        - Apply this move.

    When the game reaches a terminal state:
        - If the winner is the root player, we return 1.0
        - If the winner is the opponent, we return 0.0
        - If there is no winner (draw), we return 0.5

    Arguments:
        state: Connect4State from which to start simulation
        root_player: the player we consider as "our" perspective
    """
    temp_state = state.clone()

    # Play random moves until the game is over
    while not temp_state.is_terminal():
        legal_moves = temp_state.get_legal_moves()
        if not legal_moves:
            break  # No moves left, should be a draw
        move = random.choice(legal_moves)
        temp_state.make_move(move)

    # Game is over, check the result
    winner = temp_state.check_winner()
    if winner is None:
        return 0.5
    if winner == root_player:
        return 1.0
    else:
        return 0.0


def mcts_search(root_state, n_iter=400):
    """
    Run MCTS from the given root_state and return the best move.

    Arguments:
        root_state:
            The current game state from which we search.
        n_iter:
            Number of MCTS iterations. More iterations usually means a better hint
            but it is also slower.

    Returns:
        The column index of the suggested move, or
        None if there is no legal move.

    Steps:
        1. Create a root MCTSNode that holds a copy of root_state.
        2. For n_iter iterations:
            a) Selection
            b) Expansion
            c) Simulation
            d) Backpropagation
        3. Return the move of the most visited child of the root.
    """
    # If the game is already finished, we return no move
    if root_state.is_terminal():
        return None

    # The root player is the player who is about to move in root_state
    root_player = root_state.current_player

    # Create a root node for the MCTS tree
    root_node = MCTSNode(root_state.clone())

    for _ in range(n_iter):
        # 1. Start at the root node and work on a fresh copy of root_state
        node = root_node
        state = root_state.clone()

        # 2. SELECTION
        # While the current node has children, is fully expanded,
        # and the state is not terminal, choose the best child with UCT.
        while node.children and node.is_fully_expanded() and not state.is_terminal():
            node = node.best_child()
            # Apply the move that led to this child to our simulation state
            if node.move is not None:
                state.make_move(node.move)

        # 3. EXPANSION
        # If the state is not terminal, we can expand by creating a new child.
        if not state.is_terminal():
            legal_moves = state.get_legal_moves()
            existing_moves = {child.move for child in node.children}
            # Untried moves are legal moves without a child yet
            untried_moves = [m for m in legal_moves if m not in existing_moves]

            if untried_moves:
                # Pick one untried move at random
                move = random.choice(untried_moves)
                # Apply it to the simulation state
                state.make_move(move)
                # Create the new child node
                child_node = MCTSNode(state.clone(), parent=node, move=move)
                # Attach this new child to the tree
                node.children.append(child_node)
                # And select this new child as the node to simulate from
                node = child_node

        # 4. SIMULATION (ROLLOUT)
        # From this node's state, simulate a random game until the end.
        reward = rollout(state, root_player)

        # 5. BACKPROPAGATION
        # Walk up the tree and update visit and win counts.
        while node is not None:
            node.visits += 1
            node.wins += reward
            node = node.parent

    # After finishing all iterations, pick the child with the most visits.
    best_child = root_node.most_visited_child()
    if best_child is None:
        return None
    return best_child.move


# ============================================================
#             PART 5 - DRAWING THE GAME WITH PYGAME
# ============================================================

def draw_board(screen, state, font, hint_col=None, message=""):
    """
    Draw the entire game screen.

    This includes:
    - A message text at the top (whose turn, winner, instructions).
    - A small green hint marker at the top to show the suggested column.
    - The blue board with circular holes.
    - The pieces for both players.

    Arguments:
        screen: the Pygame surface where we draw
        state: the Connect4State we want to display
        font:  a Pygame font object for rendering text
        hint_col: optional column index for the hint move
        message: text message to display at the top
    """
    # Fill the screen with background color
    screen.fill(BG_COLOR)

    # Draw message area at the top
    text_surface = font.render(message, True, TEXT_COLOR)
    screen.blit(text_surface, (10, 5))

    # Draw hint marker if we have a suggested column
    if hint_col is not None:
        x_center = hint_col * SQUARESIZE + SQUARESIZE // 2
        pygame.draw.circle(
            screen,
            HINT_COLOR,
            (x_center, SQUARESIZE),
            RADIUS // 2,
        )

    # Draw blue board and empty holes
    for c in range(COLS):
        for r in range(ROWS):
            pygame.draw.rect(
                screen,
                BOARD_COLOR,
                (
                    c * SQUARESIZE,
                    (r + 2) * SQUARESIZE,
                    SQUARESIZE,
                    SQUARESIZE,
                ),
            )
            pygame.draw.circle(
                screen,
                BG_COLOR,
                (
                    c * SQUARESIZE + SQUARESIZE // 2,
                    (r + 2) * SQUARESIZE + SQUARESIZE // 2,
                ),
                RADIUS,
            )

    # Draw pieces for player 1 and player 2
    for c in range(COLS):
        for r in range(ROWS):
            piece = state.board[r][c]
            if piece == PLAYER1:
                color = PLAYER1_COLOR
            elif piece == PLAYER2:
                color = PLAYER2_COLOR
            else:
                continue  # Skip empty cells
            pygame.draw.circle(
                screen,
                color,
                (
                    c * SQUARESIZE + SQUARESIZE // 2,
                    (r + 2) * SQUARESIZE + SQUARESIZE // 2,
                ),
                RADIUS,
            )

    # Finally, update the display
    pygame.display.update()


# ============================================================
#              PART 6 - MAIN GAME LOOP WITH PYGAME
# ============================================================

def main():
    """
    Main function that runs the Pygame event loop.

    Game behavior (just for this starter because your assignment behavior is different):
        - 2 human players alternate turns.
        - The MCTS algorithm always computes a hint for the current player.
        - The hint is shown as a small green marker above the suggested column.
        - Players click with the mouse in the column where they want to drop a piece.
        - If a player wins or the board is full, a message is displayed.
        - Press R to restart the game.

    This function does not contain any MCTS logic itself.
    It just calls mcts_search to get the hint move.
    """
    pygame.init()

    # Create the screen and set the title
    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption("MCTS Connect4- 2 human players")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24)

    # Start with a fresh game state
    state = Connect4State()
    game_over = False

    # hint_col will store the column suggested by MCTS
    hint_col = None

    # Message at the top of the screen
    message = "Player 1 turn"

    # Compute the first hint for player 1
    hint_col = mcts_search(state, n_iter=400)

    running = True
    while running:
        # Limit the game loop speed to FPS frames per second
        clock.tick(FPS)

        # Handle events from Pygame (mouse, keyboard, window close)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Window close button clicked
                running = False

            if event.type == pygame.KEYDOWN:
                # If player presses R, reset the game
                if event.key == pygame.K_r:
                    state = Connect4State()
                    game_over = False
                    message = "Player 1 turn"
                    hint_col = mcts_search(state, n_iter=400)

            if event.type == pygame.MOUSEBUTTONDOWN:
                # If mouse is clicked and the game is still running
                if not game_over:
                    # Get mouse position and convert to column index
                    x, _ = event.pos
                    col = x // SQUARESIZE

                    # Check that the chosen column is a legal move
                    legal_moves = state.get_legal_moves()
                    if col in legal_moves:
                        # Apply this move
                        state.make_move(col)

                        # Check if this move wins the game
                        winner = state.check_winner()
                        if winner == PLAYER1:
                            message = "Player 1 wins, press R to restart"
                            game_over = True
                            hint_col = None
                        elif winner == PLAYER2:
                            message = "Player 2 wins, press R to restart"
                            game_over = True
                            hint_col = None
                        elif state.is_full():
                            # No more moves and no winner
                            message = "Draw, press R to restart"
                            game_over = True
                            hint_col = None
                        else:
                            # Game continues, switch message to the next player
                            current = state.current_player
                            message = f"Player {current} turn"

                            # Compute new hint for the new current player
                            hint_col = mcts_search(state, n_iter=400)

        # Draw the current frame
        draw_board(screen, state, font, hint_col, message)

    # When running goes False, quit Pygame and exit the program
    pygame.quit()
    sys.exit()


# This ensures that main() is called only when this file is run directly,
# not when it is imported as a module in another script.
if __name__ == "__main__":
    main()
</file>

</files>
</file>

<file path="README.md">
# GAIT Assignment 2: Pathfinding & Threaded MCTS Connect 4

## Overview
This codebase is a clean Python/Pygame implementation for **GAIT Assignment 2**, featuring:
1. **Weighted A* Pathfinding**: Supports octile vs Manhattan heuristics, corner-cut prevention, step-by-step visual reveal, g-cost visualization overlays, heatmap toggle, and a Reynolds path-following frog steering agent.
2. **Threaded MCTS Connect 4**: Supports Human vs AI and AI vs AI modes with multi-threaded non-blocking searches, customizable difficulty levels (`easy`, `medium`, `hard`), and a detailed sidebar stats panel reporting Visits, Win Rates, and UCB Scores for each column.

## Project Structure
```
gait_a2/
├── settings.py      # Global constants, colors, keybinds, asset paths
├── grid.py          # Cell structure & TerrainGrid with corner-cutting logic
├── pathfinding.py   # Pure A* algorithm & path cost breakdown utilities
├── frog.py          # Reynolds path-following steering agent
├── mcts.py          # Connect 4 state, MCTS search, & AIWorker thread
├── scenes.py        # MenuScene, PathfindingScene, Connect4Scene & Stats Panel
└── main.py          # Main application loop & scene orchestrator
```

## Running the Application
Ensure Pygame is installed:
```bash
pip install pygame
```

Launch the main application:
```bash
python3 main.py
```

## Controls & Keybindings
- `G`: Toggle diagonal movement in pathfinding
- `O`: Toggle heatmap overlay
- `N`: Toggle g-cost label overlay
- `R`: Reset grid layout or Connect 4 board
- `Space`: Step / Auto-play toggle in Connect 4 (AI vs AI mode)
- `ESC`: Return to Main Menu
</file>

</files>
