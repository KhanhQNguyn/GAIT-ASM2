# FINAL IMPLEMENTATION PLAN — A2 Part 1: A* Over a Weighted-Cost Grid & Path-Following Frog

**Status:** Implementation-ready. Self-contained — no other document needs to be read alongside this one. Written for an AI coding agent (e.g. Antigravity).
## 0. EXECUTION INSTRUCTION — IMPLEMENT THIS IN THE EXISTING `a2_part1/` FOLDER

You are working directly inside the existing assignment repository.

Your first task is to locate and open the `a2_part1/` folder in the current workspace.

IMPORTANT:
- `a2_part1/` is the ONLY folder you are allowed to modify for Part 1.
- Implement the entire Part 1 assignment inside `a2_part1/`.
- Do NOT create the implementation in the repository root.
- Do NOT implement Part 1 in another folder with a different name.
- Do NOT modify Part 2 / Connect4 / MCTS code.
- Before writing code, inspect the existing contents of `a2_part1/` and determine whether there is an existing Part 1 implementation that should be replaced or refactored.
- If an existing Part 1 implementation conflicts with this specification, modify/remove the conflicting Part 1 code inside `a2_part1/` so that the final implementation conforms to this specification.
- You may create, modify, rename, or delete files INSIDE `a2_part1/` as necessary.
- Do not touch files outside `a2_part1/` unless absolutely required for the project to run, and if such a change is unavoidable, explain it before making it.
- The final runnable entry point MUST be:

    a2_part1/main.py

- The final application MUST be runnable with:

    cd a2_part1
    python main.py

Execution order:
1. Locate `a2_part1/`.
2. Inspect its existing files and assets.
3. Inspect any existing Part 1 code before modifying it.
4. Implement/refactor the complete Part 1 solution according to this specification.
5. Run/test the implementation from inside `a2_part1/`.
6. Fix any runtime, import, pathfinding, movement, or visualization errors found during testing.
7. Verify the final file structure and acceptance checklist before considering the task complete.

Do not merely provide code snippets or an implementation plan. Actually implement the solution in the `a2_part1/` folder.
---

## 1. Scope

**In scope:** a grid where each cell has a traversal cost, A* search over that weighted-cost grid (toggleable 8-directional movement), a reveal-before-move visualization, a green final path, total-cost and per-cell-cost display, and a frog that follows the resulting path continuously via an explicit Seek steering behaviour.

**Out of scope / must not be present anywhere in this project:**
- Any Assignment 1 code, class, asset, or system (flies, snakes, health, hiding, or any other A1 gameplay mechanic). This project is built entirely from scratch; nothing imports, extends, or assumes any A1 source exists.
- Connect 4, MCTS, any shared `scenes.py`, menu, or mode switch.
- Predictive look-ahead steering, path-radius drift correction, mass/acceleration/force-limited physics.
- Independent obstacle avoidance that would let the frog deviate from the A* route — the route is decided once by A* and never renegotiated by the movement layer.

**Terminology note:** this project does **not** implement "Weighted A*" in the formal algorithmic sense (`f(n) = g(n) + w·h(n)` with `w > 1`). It implements standard `f(n) = g(n) + h(n)` A* search over a grid whose edges carry **terrain-dependent movement costs**. Refer to this everywhere — code comments, README, demo narration — as **"A* over a weighted-cost grid"** or **"cost-weighted A*"**, never as "Weighted A*".

The project must run standalone via `python main.py` from inside `a2_part1/`.

---

## 2. Coordinate systems — grid space vs. world space

Two coordinate systems exist in this project and must never be mixed:

- **Grid space:** `(col, row)`, integer, zero-indexed, `col` increasing rightward, `row` increasing downward. This is the only coordinate system A* and the grid's internal data structures operate in.
- **World space:** `pygame.Vector2` / `(x, y)` float pixel coordinates. This is the only coordinate system the frog operates in.

**Conversion happens in exactly two places, both owned by `grid.py`:**
- `world_to_cell(x, y) -> (col, row)` — used only when handling a mouse click.
- `cell_to_world_center(col, row) -> (x, y)` — used only when converting a finished A* path into waypoints for the frog.

`pathfinding.py` works exclusively in grid space and never imports pygame. `main.py` is the only file that converts an `AStarResult.path` (grid space) into a world-space waypoint list, immediately before calling `frog.set_path(...)`. No other file performs this conversion.

---

## 3. Grid & terrain

- **Grid dimensions:** `GRID_COLS = 20`, `GRID_ROWS = 14`, `TILE_SIZE = 48` px. *(Engineering default — adjust freely; the only functional requirement is that the grid stay large enough to make weighted-terrain detours visible on camera.)*
- A cell's world-space center: `(col * TILE_SIZE + TILE_SIZE / 2, row * TILE_SIZE + TILE_SIZE / 2)`. Every waypoint the frog ever targets is a cell **center**, never a corner.
- **Terrain types and costs** (finite costs only — only `WALL` is structurally impassable):

  | Terrain | Cost | Meaning |
  |---|---|---|
  | `GRASS` | `1` | Cheapest, default terrain |
  | `MUD` | `3` | Costly but legal detour |
  | `WATER` | `5` | Most costly legal terrain |
  | `WALL` | `float('inf')` | Structurally impassable — excluded from the graph entirely |

  `MIN_TERRAIN_COST = min(cost for cost in TERRAIN_COST.values() if cost != float('inf'))`, computed once from the live cost table. **Never hardcode `1` as this value anywhere else in the codebase** — the heuristic in §4.3 depends on this being derived, not assumed.
- **Layout:** support both procedural generation (weighted random terrain, mostly grass with mud/water pockets and modest wall density) and an optional fixed `layout: list[str]` (`'.'`=grass, `'m'`=mud, `'w'`=water, `'#'`=wall) for a reproducible demo map.
- **Connectivity:** after generation, run a flood-fill (4-connected, over all non-`WALL` cells) from the frog's start cell, exposed as `is_reachable(col, row) -> bool`, so an unreachable right-click can be rejected with a clear message instead of producing a confusing dead end.
- **Start/target:** the frog's current position is always the A* start. The target is whatever cell the user right-clicks. Right-clicking a `WALL` cell, or a cell `is_reachable()` reports `False` for, is rejected before A* ever runs — show a brief on-screen message instead.

---

## 4. A* specification (pure algorithm, no pygame)

### 4.1 Node representation

Each grid cell `(col, row)` is a node. No separate node class exists — `pathfinding.py` keeps its own internal search bookkeeping (`best_g`, `came_from`) as local dictionaries scoped to a single `find_path()` call, and writes onto the grid's `Cell` objects (`g_cost`, `explored`, `in_path`) **only at finalization time** (§4.5) — never during relaxation.

### 4.2 Priority queue, tie-breaking, and stale entries

- **Open set:** a binary min-heap (`heapq`) holding `(f_score, tie_break, col, row)` tuples.
- **Tie-breaking:** `tie_break` is a strictly increasing integer counter, incremented on every push, used purely to keep heap tuples fully ordered without ever comparing `(col, row)` pairs directly. This does not alter `f_score` and introduces no inadmissibility.
- **Duplicate heap entries:** the same `(col, row)` may be pushed multiple times as cheaper routes to it are discovered. This is expected and handled via the `best_g` dict, not prevented at push time.
- **Stale-entry detection:** maintain `best_g: dict[(col,row), float]`, initialized with `best_g[start] = 0`. On every relaxation that improves a neighbor's cost, update `best_g[neighbor]` and push a new heap entry — do not attempt to decrease-key an existing heap entry (not supported by `heapq`). When popping `(f, tie_break, col, row)` from the heap, first compare its embedded `g` against `best_g[(col, row)]`; if the popped entry's `g` is worse (larger) than the current `best_g` value for that cell, this entry is stale — discard it and continue the loop without processing it further. This is standard lazy-deletion A* and requires no explicit closed-set container.

### 4.3 Cost function and heuristic

```
g(start) = 0
g(neighbor) = g(current) + movement_cost(current, neighbor)

movement_cost(a, b) = TERRAIN_COST[b.terrain] * (sqrt(2) if diagonal(a, b) else 1)

f(n) = g(n) + h(n)

h(n) = MIN_TERRAIN_COST * distance(n, goal)

  distance(n, goal) =
      octile(n, goal)    if allow_diagonal
      manhattan(n, goal) if not allow_diagonal

  octile(n, goal):
      dx, dy = abs(goal.col - n.col), abs(goal.row - n.row)
      return (dx + dy) + (sqrt(2) - 2) * min(dx, dy)

  manhattan(n, goal):
      dx, dy = abs(goal.col - n.col), abs(goal.row - n.row)
      return dx + dy
```

Terrain weighting belongs entirely in `movement_cost` / `g(n)`. The heuristic scales the *geometric* distance by `MIN_TERRAIN_COST` only — it must never itself branch on individual terrain types, and it must never be inflated by any factor greater than `MIN_TERRAIN_COST` (no artificial `w > 1` multiplier of any kind — that would be actual Weighted A* and would risk suboptimal paths).

**Admissibility/consistency:** the cheapest possible real transition, cardinal or diagonal, costs `MIN_TERRAIN_COST * 1` or `MIN_TERRAIN_COST * sqrt(2)` respectively — that is the definition of `MIN_TERRAIN_COST`. `octile()`/`manhattan()` compute the exact geometric shortest distance under those same unit assumptions. Scaling that geometric distance by `MIN_TERRAIN_COST` therefore produces the cost of the cheapest theoretically possible path to the goal, ignoring obstacles — always `<=` the true optimal cost, since obstacles and non-minimum-cost terrain can only make a real path longer, never shorter (admissibility). Consistency follows because `octile`/`manhattan` are proper distance metrics (they satisfy the triangle inequality) and a positive constant scale factor preserves that property.

### 4.4 Neighbor generation & corner-cutting

- `neighbors(col, row, allow_diagonal) -> list[(col, row)]`:
  - Cardinal neighbors: included if in-bounds and `cost(neighbor) != inf`.
  - Diagonal neighbors (only if `allow_diagonal`): a diagonal transition
    ```
    (c, r) -> (c + dc, r + dr)        where dc, dr in {-1, +1}
    ```
    is **rejected** if either orthogonal neighbor is impassable:
    ```
    cost(c + dc, r) == inf   OR   cost(c, r + dr) == inf
    ```
    This is an exact boolean condition, evaluated on the grid directly — never approximated with a distance check.

### 4.5 Finalization, path reconstruction, and output

- A node's `g_cost`/`explored` fields on its `Cell` object are written **exactly once**, at the moment it is popped from the heap and confirmed not stale (§4.2) — this is "finalization." They are never written during relaxation/pushing, so `Cell.g_cost` always reflects the true finalized cost, never a since-superseded candidate value. `explored_order` (a plain list) gets this cell's `(col, row)` appended at the same moment, in pop order.
- On finalizing `goal`: reconstruct the path via `came_from: dict[(col,row), (col,row)]`, walking from `goal` back to `start`, then reversing. **No smoothing, no string-pulling, no waypoint pruning.** Mark every cell on the reconstructed path with `cell.in_path = True`.
- **Canonical path representation — grid coordinates only:**
  ```python
  @dataclass
  class AStarResult:
      path: list[tuple[int, int]]          # GRID coordinates (col, row), start -> goal inclusive
      total_cost: float                     # g_cost of goal; float('inf') if unreachable
      explored_order: list[tuple[int, int]] # GRID coordinates, in POP/finalization order
      reachable: bool
  ```
  `path` is never world-space and never converted to pixels inside `pathfinding.py`. World-space conversion happens only in `main.py` (§2, §7).
- **Start equals goal:** finalize `start` directly (`g_cost = 0`, `explored = True`, `in_path = True`), return `path=[start]`, `total_cost=0.0`, `explored_order=[start]`, `reachable=True` — no heap loop required.
- **Unreachable target:** if the heap empties before `goal` is finalized, return `path=[]`, `total_cost=float('inf')`, `explored_order=<everything actually finalized>`, `reachable=False`. Never raise or crash on this case.
- **`path_cost_breakdown(grid, path) -> list[tuple[tuple[int,int], float, float]]`:** given `path` (grid coordinates, exactly as returned by `find_path`, never pre-converted to world space), return `(coord, step_cost, cumulative_cost)` for every cell on the path, computed once after the search completes.

---

## 5. Reveal state machine & visualization

### 5.1 Two distinct layers of state — do not conflate them

1. **Search state** (finalized instantly, the moment `find_path()` returns): `Cell.g_cost`, `Cell.explored`, `Cell.in_path`. Because A* runs synchronously to completion in a single call, every explored cell already has `explored = True` the instant `find_path()` returns — **before any visual reveal has happened.**
2. **Visual reveal state** (paced frame-by-frame by `main.py`, entirely separate from #1): a `reveal_cursor: int`, advanced by `REVEAL_CELLS_PER_FRAME` cells per frame through `result.explored_order`.

**The rendering layer must key off the visual reveal state, never off `Cell.explored`/`Cell.in_path` directly** — since those are already `True` for the entire explored region immediately after the search, rendering conditioned on them alone would show every explored cell (and the finished green path) instantly, defeating the reveal animation entirely. Concretely:

- Each frame during `REVEALING`, `main.py` computes `revealed_cells = set(result.explored_order[:reveal_cursor])` and passes it into `grid.draw(...)`.
- `grid.draw()` renders the explored-overlay and `g_cost` label for a cell **only if that cell's `(col, row)` is in the `revealed_cells` set it was given** — not by checking `cell.explored`.
- `main.py` also tracks a `show_final_path: bool`, `False` for the entirety of `IDLE`→`REVEALING`, and set `True` only once `reveal_cursor` has consumed the entire `explored_order` list (i.e. reveal is complete). `grid.draw()` renders the green final-path overlay only when `show_final_path` is `True` — not by unconditionally checking `cell.in_path`.

### 5.2 Required visual states

| State | Rendering | Gated by |
|---|---|---|
| Unexplored | Base terrain tile only | (default) |
| Explored (revealed) | Terrain tile + overlay + `g_cost` label | `(col,row) in revealed_cells` |
| Frontier (optional) | Distinct overlay from explored | Engineering default — optional, aids narration |
| Final path | Solid **green** overlay/line | `show_final_path is True` |
| Start / goal | Distinct marker | Drawn independently of reveal state |
| Wall | Distinct terrain tile/color, never overlaid with explored/path coloring | (default) |

### 5.3 State machine

```
IDLE --(right-click valid target)--> REVEALING --(reveal_cursor exhausts explored_order)--> FOLLOWING --(frog.is_path_complete())--> IDLE
```

| Current state | Trigger | Action | Next state |
|---|---|---|---|
| `IDLE` | Right-click on a valid (in-bounds, non-`WALL`, reachable) cell | `grid.reset_search_state()`; run `pathfinding.find_path(...)`; store `result`; `reveal_cursor = 0`; `show_final_path = False` | `REVEALING` |
| `IDLE` | Right-click on an invalid cell | Show a brief on-HUD rejection message | `IDLE` (unchanged) |
| `REVEALING` | Every frame | `reveal_cursor = min(reveal_cursor + REVEAL_CELLS_PER_FRAME, len(result.explored_order))`; recompute `revealed_cells` | `REVEALING` (unchanged) until exhausted |
| `REVEALING` | `reveal_cursor == len(result.explored_order)` | `show_final_path = True`; convert `result.path` (grid coords) to world-space waypoints via `grid.cell_to_world_center`; call `frog.set_path(world_path)` | `FOLLOWING` |
| `FOLLOWING` | Every frame | `frog.follow_path(dt)` | `FOLLOWING` (unchanged) until complete |
| `FOLLOWING` | `frog.is_path_complete()` | — | `IDLE` |
| any state | `restart` keybind | Rebuild grid; reset frog to a start cell; clear `result`, `reveal_cursor`, `show_final_path` | `IDLE` |
| any state | toggle diagonal/heatmap/cost-label keybind | Flip the corresponding boolean; must not mutate any field of an in-flight `result` — affects only the *next* right-click | unchanged |
| `REVEALING` or `FOLLOWING` | right-click | Ignored — right-clicks are only accepted in `IDLE` | unchanged |

If `result.reachable is False`: skip `REVEALING`'s transition into `FOLLOWING` entirely (there is no path to follow); still run the reveal animation over whatever was explored so the demo can show *why* it failed; display an explicit "target unreachable" message; return to `IDLE` once the reveal finishes instead of proceeding to `FOLLOWING`.

---

## 6. Frog movement — explicit Seek steering

### 6.1 Behaviour

The frog uses an explicit **Seek** steering computation, applied with **no force limit and no smoothing**, so that velocity is fully redirected toward the current target every frame — this keeps the code and vocabulary recognizably a steering behaviour (not plain teleport/index-jump between cells) while guaranteeing the frog can never drift off the straight segment between its current and next waypoint, since there is no inertia for it to drift with.

```
desired_velocity = normalize(target - position) * FROG_SPEED
steering = desired_velocity - velocity
velocity = velocity + steering        # == velocity = desired_velocity  (unlimited responsiveness)
position += velocity * dt
```

**Explicitly not implemented:** mass, acceleration limits, accumulated force summation, max-force clamping, predictive look-ahead, path-line projection/drift-correction, arrival deceleration blending, or any obstacle avoidance. None of these constants (`MAX_FORCE`, `SLOW_RADIUS`, `PREDICT_DIST`, `PATH_RADIUS`) exist anywhere in this project.

### 6.2 Overshoot-safe waypoint traversal

If, in a single frame, `FROG_SPEED * dt` exceeds the remaining distance to the current waypoint, the frog must not overshoot past it. Traverse with a **bounded loop** (never recursion):

```
remaining_distance = FROG_SPEED * dt
loop (bounded to at most len(path)+1 iterations):
    if no current waypoint or path already complete: exit loop
    target = current waypoint
    dist_to_target = distance(position, target)
    recompute velocity via the Seek formula in §6.1, toward target

    if dist_to_target <= remaining_distance:
        position = target                          # snap exactly onto the waypoint
        remaining_distance -= dist_to_target
        if there is a next waypoint:
            advance to next waypoint                # loop continues, carrying leftover distance
        else:
            velocity = (0, 0)
            remaining_distance = 0                  # path complete, stop
    else:
        position += velocity.normalized() * remaining_distance
        remaining_distance = 0                      # step fully consumed, exit loop
```

This guarantees: one frame's movement can correctly cross multiple short path segments in a single update (e.g. an unusually high `FROG_SPEED` or a large `dt` spike), the frog never overshoots any waypoint, and the loop is bounded and cannot hang even on a pathological zero-length final segment.

### 6.3 API

```python
class Frog:
    def __init__(self, x, y, sprite_path=None): ...
        # pos: Vector2, velocity: Vector2 (0,0), path: list[Vector2] = [],
        # path_index: int = 0, angle: float = 0.0, sprite: Surface | None

    def set_path(self, world_points: list[tuple[float, float]]) -> None: ...
        # world_points are WORLD-SPACE pixel coordinates (already converted by main.py from
        # AStarResult.path via grid.cell_to_world_center). Resets path_index = 0.

    def follow_path(self, dt: float) -> None: ...
        # Implements §6.1/§6.2 exactly. No-op if path is empty or already complete.

    def is_path_complete(self) -> bool: ...
        # True if path_index is at the final waypoint and position is within a small
        # floating-point epsilon of it.

    def draw(self, surface) -> None: ...
        # Rotates the sprite to face `angle` (derived from velocity direction); falls back to
        # a filled circle + direction line if the sprite failed to load, so a missing PNG
        # never crashes the demo.
```

---

## 7. File architecture & implementation prompts

```
a2_part1/
  settings.py
  grid.py
  pathfinding.py
  frog.py
  main.py
  assets/
    frog_sprite.png
    tileset.png
  README.md
```

No `scenes.py`, no `mcts.py`, no Connect4/menu imports, no Assignment 1 imports anywhere in this tree.

### `settings.py`
**Responsibility:** constants only. **Must NOT contain:** `pygame.init()`, `Surface` creation, or any game logic.

**Implementation Prompt:**
```text
You are implementing settings.py for a standalone A*-over-a-weighted-cost-grid demo, built
entirely from scratch (no Assignment 1 dependency of any kind).

Define, as module-level constants with no side effects:
- GRID_COLS=20, GRID_ROWS=14, TILE_SIZE=48, derived SCREEN_WIDTH/HEIGHT, FPS=60.
- class Terrain with GRASS/MUD/WATER/WALL string constants.
- TERRAIN_COST = {GRASS: 1, MUD: 3, WATER: 5, WALL: float('inf')}.
- MIN_TERRAIN_COST = min(v for v in TERRAIN_COST.values() if v != float('inf')). Every other
  file must import and use this constant — never hardcode 1 as the heuristic scale elsewhere.
- TERRAIN_COLOR fallback colors per terrain (used if tileset.png fails to load).
- FROG_SPEED (px/sec) — the only motion-speed constant this project uses.
- COLOR_EXPLORED, COLOR_FRONTIER, COLOR_PATH=(0,230,90) [green — mandatory for the final path],
  COLOR_TEXT, COLOR_BG.
- ASSETS_DIR, FROG_SPRITE = ASSETS_DIR/"frog_sprite.png", TILESET = ASSETS_DIR/"tileset.png".
- REVEAL_CELLS_PER_FRAME (int, paces the visual reveal — independent of search timing, since
  the search itself already completes synchronously in one call).
- FONT_SIZE (HUD text and in-cell g-cost labels).
- KEYBINDS = {"toggle_diagonal": ..., "toggle_heatmap": ..., "toggle_cost_labels": ...,
  "restart": ...}.

Do NOT define MAX_FORCE, SLOW_RADIUS, PREDICT_DIST, or PATH_RADIUS — this project's frog uses
unlimited-responsiveness Seek steering (see frog.py spec), not force-limited physics, so none
of these constants have any use here.

Constraints: no pygame.init(), no Surface objects, no drawing code, no game logic, no
Assignment 1 import of any kind.
```

### `grid.py`
**Responsibility:** `Cell` and `TerrainGrid` — terrain data, cell search-state fields, neighbor generation, connectivity, coordinate conversion, and drawing (including the reveal/final-path gating from §5.1). No A* algorithm, no frog logic here.

**Implementation Prompt:**
```text
You are implementing grid.py from scratch (no Assignment 1 dependency).

Define:
- Cell (col, row, terrain, g_cost=None, explored=False, in_path=False), using __slots__.
- TerrainGrid(cols, rows): builds a cols x rows array of Cells, either procedurally (weighted
  random terrain) or from an optional layout: list[str] ('.'=grass,'m'=mud,'w'=water,'#'=wall).
- After generation, flood-fill connectivity (4-connected, non-WALL cells) from a given start
  cell; expose is_reachable(col, row) -> bool.

Required API (exact signatures):
- in_bounds(col, row) -> bool
- get_cell(col, row) -> Cell | None            # returns None if out of bounds; used by
                                                  pathfinding.py and main.py instead of indexing
                                                  the internal array directly
- cost(col, row) -> float                       # TERRAIN_COST[terrain]; inf for wall/OOB
- neighbors(col, row, allow_diagonal: bool) -> list[tuple[int,int]]
    - cardinal: included if in-bounds and cost != inf
    - diagonal (only if allow_diagonal): included only if in-bounds, cost != inf, AND both
      orthogonal cells (c+dc, r) and (c, r+dr) have cost != inf — exact boolean check, per the
      Part 1 spec section 4.4, never a distance-based approximation
- movement_cost(from_cell, to_cell) -> float    # TERRAIN_COST[to_cell.terrain] * (sqrt(2) if
                                                   diagonal else 1)
- reset_search_state() -> None                  # clears explored/in_path/g_cost on every cell
- world_to_cell(x, y) -> tuple[int,int]
- cell_to_world_center(col, row) -> tuple[float,float]
- draw(surface, tileset_or_none, revealed_cells: set[tuple[int,int]], show_final_path: bool,
       show_heatmap: bool, show_cost_labels: bool, font) -> None
    - Draws base terrain for every cell always.
    - Draws the explored overlay and g_cost label ONLY for cells whose (col,row) is a member of
      revealed_cells — NOT by checking cell.explored directly (cell.explored is already True
      for the whole explored region the instant the search finishes, well before the reveal
      animation has played; revealed_cells is what paces the animation — see spec section 5.1).
    - Draws the green final-path overlay ONLY when show_final_path is True — NOT by
      unconditionally checking cell.in_path (same reasoning as above).
    - Must clearly visually distinguish: unexplored, explored/revealed, frontier (optional),
      final path (green), wall, start, goal.

Constraints:
- No pathfinding algorithm (no heap, no A* loop) lives here — that belongs in pathfinding.py.
- No frog/steering code here.

Do not:
- Key any rendering decision off cell.explored or cell.in_path directly — always go through the
  revealed_cells set / show_final_path flag supplied by the caller.
- Special-case WALL vs MUD/WATER anywhere except via the shared cost()/TERRAIN_COST lookup.
- Reference, import, or assume any Assignment 1 module.
```

### `pathfinding.py`
**Responsibility:** pure A* over the weighted-cost grid, entirely in grid-space coordinates. No pygame import.

**Implementation Prompt:**
```text
You are implementing pathfinding.py from scratch. No pygame import anywhere in this file — it
must be fully testable without a display. No Assignment 1 dependency.

Required API (exact signatures):

@dataclass
class AStarResult:
    path: list[tuple[int, int]]            # GRID coordinates only — never world-space here
    total_cost: float
    explored_order: list[tuple[int, int]]  # GRID coordinates, in finalization/pop order
    reachable: bool

def find_path(grid, start: tuple[int,int], goal: tuple[int,int], allow_diagonal: bool) -> AStarResult

def path_cost_breakdown(grid, path: list[tuple[int,int]]) -> list[tuple[tuple[int,int], float, float]]
    # path is GRID coordinates, exactly as returned by find_path — never pre-converted to
    # world-space before calling this. Returns (coord, step_cost, cumulative_cost) per cell.

Algorithm — implement exactly as specified in Part 1 spec section 4:
1. If start == goal: finalize start immediately (g_cost=0, explored=True, in_path=True on its
   Cell via grid.get_cell), return path=[start], total_cost=0.0, explored_order=[start],
   reachable=True. No heap loop.
2. Otherwise, run a heapq-based open set of (f_score, tie_break_counter, col, row) tuples, an
   internal best_g dict (best_g[start] = 0.0), and an internal came_from dict.
3. h(n) = grid.MIN_TERRAIN_COST * octile_or_manhattan_distance(n, goal), branching on
   allow_diagonal exactly as in spec section 4.3. Never hardcode the scale factor to 1.
4. On each pop: if the popped entry's g exceeds the current best_g for that cell (i.e. this
   entry is stale because a cheaper route was found and pushed after this entry), discard it and
   continue the loop without processing it further.
5. Otherwise finalize this cell: write cell.g_cost = g and cell.explored = True onto its Cell
   object via grid.get_cell (this write happens ONLY here, at finalization — never during
   relaxation in step 6), and append (col,row) to explored_order.
6. If this cell is goal: reconstruct the path via came_from (grid coordinates, no smoothing, no
   pruning), mark cell.in_path = True on every path cell, and return the AStarResult.
7. Otherwise, for each neighbor from grid.neighbors(col, row, allow_diagonal): compute
   tentative_g = g + grid.movement_cost(current_cell, neighbor_cell); if this improves on
   best_g.get(neighbor, inf), update best_g[neighbor], came_from[neighbor] = current, and push a
   new heap entry — do not attempt to modify an existing heap entry in place.
8. If the heap empties without finalizing goal: return path=[], total_cost=float('inf'),
   explored_order=<everything finalized so far>, reachable=False. Never raise/crash.

Do not:
- Import pygame or perform any drawing.
- Return or accept world-space coordinates anywhere in this file's public API.
- Smooth, prune, or otherwise simplify the returned path.
- Reference, import, or assume any Assignment 1 module.
```

### `frog.py`
**Responsibility:** explicit Seek steering, entirely in world-space, per §6. No pathfinding, no grid logic.

**Implementation Prompt:**
```text
You are implementing frog.py from scratch (no Assignment 1 dependency).

Required API (exact signatures):
class Frog:
    def __init__(self, x, y, sprite_path=None): ...
    def set_path(self, world_points: list[tuple[float, float]]) -> None: ...
    def follow_path(self, dt: float) -> None: ...
    def is_path_complete(self) -> bool: ...
    def draw(self, surface) -> None: ...

Internal state: pos (Vector2), velocity (Vector2, starts at (0,0)), path (list[Vector2]),
path_index (int), angle (float, degrees), sprite (Surface|None).

Algorithm — implement exactly as specified in Part 1 spec section 6:
- set_path(world_points): store as a list of Vector2, reset path_index = 0. world_points are
  already world-space pixel coordinates (converted by main.py — this file never converts grid
  coordinates itself).
- follow_path(dt): if path is empty or is_path_complete() is already True, set velocity to (0,0)
  and return. Otherwise run the BOUNDED LOOP from spec section 6.2 (never recursion): each
  iteration computes velocity via the Seek formula in section 6.1 (desired_velocity =
  normalize(target - pos) * FROG_SPEED; velocity = desired_velocity directly, no force limit),
  checks whether this frame's remaining movement distance reaches or passes the current
  waypoint, and either snaps onto the waypoint and carries over leftover distance into the next
  segment (advancing path_index), or consumes the remaining distance moving toward the current
  waypoint and stops. Cap loop iterations at len(path)+1 to guarantee termination.
- is_path_complete(): True if path_index is at the last waypoint and pos is within a small
  epsilon of it.
- draw(): rotate sprite to face `angle` (derived from velocity's direction, updated only while
  velocity is non-zero); fall back to a filled circle + short direction line if the sprite
  failed to load.

Do not:
- Add MAX_FORCE, SLOW_RADIUS, PREDICT_DIST, or PATH_RADIUS constants or any force-limiting logic
  — velocity is always set directly to desired_velocity, with no clamping or smoothing.
- Implement any predictive look-ahead or path-line projection/drift-correction.
- Use recursion for the overshoot/leftover-distance handling — use the bounded loop specified.
- Let the frog's position ever leave the straight segment between its current and next waypoint.
- Reference, import, or assume any Assignment 1 module, class, or asset.
```

### `main.py`
**Responsibility:** the sole entry point. Owns `pygame.init()`, the window, the `IDLE/REVEALING/FOLLOWING` state machine (§5.3), event handling, the grid-to-world path conversion (§2), and HUD drawing.

**Implementation Prompt:**
```text
You are implementing main.py, the sole entry point for this standalone project. No Assignment 1
import of any kind.

Responsibilities:
- pygame.init(), build window at settings.SCREEN_WIDTH x SCREEN_HEIGHT, load a shared
  pygame.font.Font(None, settings.FONT_SIZE).
- Attempt to load settings.FROG_SPRITE and settings.TILESET once; on failure, log via print and
  set USE_SPRITES=False so grid.draw()/frog.draw() use their flat-color/shape fallbacks.
- Build a TerrainGrid, pick a starting grass cell, construct Frog at that cell's center.
- Own state machine variables directly: state (IDLE/REVEALING/FOLLOWING), result (AStarResult |
  None), reveal_cursor (int), show_final_path (bool), plus allow_diagonal, show_heatmap,
  show_cost_labels toggles — implement every transition in the table in Part 1 spec section 5.3
  exactly, including: right-clicks are only ever accepted while state == IDLE; on a valid
  right-click, call grid.reset_search_state(), run pathfinding.find_path(...), store result,
  reset reveal_cursor = 0 and show_final_path = False, switch to REVEALING.
- update(dt):
    - REVEALING: reveal_cursor = min(reveal_cursor + settings.REVEAL_CELLS_PER_FRAME,
      len(result.explored_order)). Once reveal_cursor == len(result.explored_order): if
      result.reachable, set show_final_path = True, convert result.path (grid coordinates) to
      world-space via [grid.cell_to_world_center(*c) for c in result.path], call
      frog.set_path(world_path), switch to FOLLOWING. If not result.reachable, switch back to
      IDLE instead (there is no path to follow) and keep showing an "unreachable" HUD message.
    - FOLLOWING: call frog.follow_path(dt); once frog.is_path_complete(), switch to IDLE.
- draw(screen):
    - clear with COLOR_BG.
    - compute revealed_cells = set(result.explored_order[:reveal_cursor]) if result else set().
    - grid.draw(screen, tileset_or_none, revealed_cells, show_final_path, show_heatmap,
      show_cost_labels, font) — exactly this signature, per grid.py's spec.
    - frog.draw(screen).
    - HUD: diagonal/heatmap/cost-label toggle states; once result exists and is reachable,
      "Total Cost: {result.total_cost:.1f}"; if not reachable, "Target unreachable"; a small
      legend (Grass=1, Mud=3, Water=5, Wall=impassable).
- Handle settings.KEYBINDS["restart"] in any state: rebuild the grid, reset the frog to a start
  cell, clear result/reveal_cursor/show_final_path, return to IDLE.

Constraints:
- No terrain/A*/movement algorithm code belongs here — if you find an `if terrain == ...` branch
  or a heap/priority-queue here, move it to grid.py/pathfinding.py.
- This file is the ONLY place that converts AStarResult.path (grid coordinates) into world-space
  waypoints — no other file performs this conversion.

Do not:
- Add a menu, a scene-switch enum, or any Connect4/MCTS import.
- Let the frog begin FOLLOWING before reveal_cursor has consumed the entire explored_order list.
- Reference, import, or assume any Assignment 1 module.
```

---

## 8. Edge cases

| Case | Required behavior |
|---|---|
| Start equals goal | `path=[start]`, `total_cost=0`, `reachable=True`; frog performs no unnecessary movement |
| Target on a wall | Rejected before `find_path` is ever called |
| Target outside the grid | Rejected at the click-handling stage (`world_to_cell` result fails `in_bounds`) before `find_path` is called |
| Target unreachable (sealed off) | `find_path` terminates normally with `reachable=False`; explored region still visualized via the reveal animation; no crash; state returns to `IDLE` after the reveal instead of proceeding to `FOLLOWING` |
| Diagonal disabled | Path uses only 4-directional steps; heuristic uses Manhattan distance |
| Diagonal enabled | Path may use 8-directional steps; heuristic uses octile distance; corner-cutting rule (§4.4) enforced |
| Blocked diagonal corner | Diagonal transition rejected per the exact boolean rule in §4.4 |
| Repeated target (same cell clicked twice) | `grid.reset_search_state()` runs before every new search — no stale `explored`/`g_cost`/`in_path` bleeds from a previous run |
| Empty path (`reachable=False`) | Handled explicitly — see "Target unreachable" row above |
| One-cell path (start == goal) | Handled explicitly — see "Start equals goal" row above |
| Very high `FROG_SPEED` / large `dt` spike crossing multiple waypoints in one frame | Handled by the bounded loop in §6.2 — leftover distance carries through consecutive waypoints within the same `follow_path(dt)` call |
| Right-click during `REVEALING` | Ignored — only `IDLE` accepts right-clicks |
| Right-click during `FOLLOWING` | Ignored — only `IDLE` accepts right-clicks |
| Restart during any state | Clears grid, frog path, `result`, `reveal_cursor`, `show_final_path`; returns cleanly to `IDLE` |

---

## 9. Testing checklist

### A* correctness
- [ ] start == goal returns immediately, cost 0, single-point path, no heap loop needed
- [ ] direct unobstructed path is a straight line at minimal cost
- [ ] weighted terrain: a mud/water patch causes a visible detour when cheaper than crossing it
- [ ] diagonal disabled uses only 4-directional steps; diagonal enabled uses 8-directional steps
- [ ] diagonal corner-cutting is rejected at a concave wall corner (verify by hand-deriving that cell's would-be g-cost)
- [ ] target unreachable: `reachable=False`, no crash, explored region still populated
- [ ] target on a wall is rejected before `find_path` runs at all
- [ ] boundary cells (`col=0`, `row=0`, `col=GRID_COLS-1`, `row=GRID_ROWS-1`) produce no out-of-bounds errors
- [ ] repeated runs on the same grid/start/goal/diagonal-flag produce an identical path (determinism)
- [ ] `AStarResult.path` is always `list[tuple[int,int]]` (grid coordinates) — verify no float/pixel values ever appear in it
- [ ] `total_cost` matches a hand-computed sum on a small (e.g. 4x4) fixed-layout grid
- [ ] `g(start) = 0`; `g(neighbor) = g(current) + movement_cost(current, neighbor)` for several sampled cells
- [ ] a node's `Cell.g_cost`/`Cell.explored` are set only once, at finalization — confirm by checking a cell that was relaxed more than once before being popped still ends with the correct, final (lowest) `g_cost`

### Visualization
- [ ] immediately after `find_path()` returns, `revealed_cells` (main.py's, at `reveal_cursor=0`) is empty even though every explored `Cell.explored` is already `True` — confirms the reveal doesn't leak the whole result instantly
- [ ] the number of cells actually drawn as "explored" each frame during `REVEALING` matches `len(revealed_cells)`, growing by `REVEAL_CELLS_PER_FRAME` per frame
- [ ] the green final path is never drawn while `show_final_path` is `False`
- [ ] the green final path appears at the exact frame `reveal_cursor` reaches `len(explored_order)`
- [ ] cost labels shown per cell match that cell's `g_cost` exactly
- [ ] toggling heatmap/cost-labels mid-`REVEALING` or mid-`FOLLOWING` does not corrupt `result` or the reveal progress

### Frog
- [ ] no teleportation — position changes continuously frame to frame except the deliberate snap-onto-waypoint case
- [ ] velocity is computed via the explicit Seek formula every frame (verify by logging `velocity` and confirming it always points directly at the current waypoint at full `FROG_SPEED` magnitude, never smoothed)
- [ ] no drift — frog's position never leaves the straight segment between its current and next waypoint
- [ ] no waypoint skipping — every path cell is visited in order
- [ ] overshoot-safe: an artificially large `dt` (simulating a frame hitch) never causes the frog to pass beyond a waypoint before snapping onto it, and correctly carries leftover distance into subsequent segments within the same call
- [ ] frog stops exactly on the final waypoint; `is_path_complete()` becomes `True` at that moment
- [ ] facing direction (`angle`) updates correctly as the frog turns at each waypoint

### State / input
- [ ] right-clicks are accepted only in `IDLE`; ignored during `REVEALING`/`FOLLOWING`
- [ ] invalid targets (wall, out-of-bounds, unreachable) are all rejected with the correct corresponding behavior from §8
- [ ] restart clears grid, frog, result, reveal_cursor, and show_final_path cleanly from any state
- [ ] `IDLE → REVEALING → FOLLOWING → IDLE` transitions occur exactly per the table in §5.3, with no skipped or extra transitions

---

## 10. Final Acceptance Checklist

### Specification compliance
- [ ] Right-click runs A* from the frog's current position to the clicked cell
- [ ] Final path is rendered in green, only after the reveal completes
- [ ] Diagonal (8-directional) neighbors are supported and toggleable
- [ ] Frog moves via an explicit Seek steering computation, never teleports between cells
- [ ] Clear, tested "reached waypoint" logic exists (§6.2)
- [ ] Corner collisions are prevented at the pathfinding level (§4.4), not patched at the movement level
- [ ] All explored cells are shown, with their `g_cost`, progressively, before the frog starts moving
- [ ] Total path cost is displayed

### Coordinate-system discipline
- [ ] `AStarResult.path` and `explored_order` are `list[tuple[int,int]]` grid coordinates everywhere, with no exceptions
- [ ] World-space conversion happens only in `main.py`, only at the `REVEALING → FOLLOWING` transition
- [ ] `pathfinding.py` contains no pygame import and no world-space coordinate anywhere in its public API

### Algorithm correctness
- [ ] Heuristic is `MIN_TERRAIN_COST * (octile or manhattan)`, never a bare unscaled distance, never inflated by `w > 1`
- [ ] Diagonal cost is `terrain_cost(destination) * sqrt(2)`
- [ ] Stale heap entries are correctly detected and discarded via the `best_g` comparison at pop time
- [ ] `Cell.g_cost`/`Cell.explored` are written only once, at finalization — never during relaxation
- [ ] Unreachable targets are handled without crashing

### Visualization correctness
- [ ] `grid.draw()` renders explored/reveal state from the `revealed_cells` set it is given, never from `cell.explored` directly
- [ ] `grid.draw()` renders the final path only when `show_final_path` is `True`, never from `cell.in_path` directly

### Frog / steering correctness
- [ ] Seek formula (`desired_velocity - velocity`, applied with no force limit) is implemented exactly as specified
- [ ] No `MAX_FORCE`/`SLOW_RADIUS`/`PREDICT_DIST`/`PATH_RADIUS` constant or logic exists anywhere in the project
- [ ] Overshoot handling uses a bounded loop, never recursion

### Independence from Assignment 1
- [ ] No file imports, references, or assumes any Assignment 1 code, class, or asset
- [ ] The project runs standalone via `python main.py` from an otherwise-empty `a2_part1/` directory

### Edge cases & testing
- [ ] Every row of §8 handled and tested
- [ ] Every checkbox in §9 has been manually run at least once

### Submission hygiene
- [ ] No Connect4/MCTS/menu code anywhere under `a2_part1/`
- [ ] No Assignment 1 files, imports, or assets anywhere in the submitted tree
- [ ] Any previous/obsolete Part 1 attempt removed or clearly archived outside the submission zip
