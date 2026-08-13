# GAIT A2 PART 2 — FINAL IMPLEMENTATION PLAN (MCTS CONNECT4)

**DO NOT INVENT IMPLEMENTATION DETAILS. FOLLOW THE CODE BLOCKS AND CONTRACTS IN THIS DOCUMENT.**

This document is the complete, standalone implementation contract for Part 2 of the GAIT assignment. It is generated directly from inspection of the actual supplied codebase (`connect4_mcts.py`) and the official assignment/rubric requirements. It supersedes any prior plan or patch — implement from this document alone.

---

## 0. Scope of Inspection

The supplied codebase contains exactly one file: **`connect4_mcts.py`**. No `assets/` directory and no asset files were present in the supplied files. No Part 1 (A*/frog) files were present in the supplied files — if such files exist elsewhere in the real project, they are **out of scope for this plan**: do not create, guess at, modify, or import from them. This plan touches `connect4_mcts.py` only.

`connect4_mcts.py` currently implements a working **2-human-player** Connect4 game with an MCTS-computed "hint" marker (not an actual AI opponent), organized into six `PART` comment blocks:

- **PART 1** — constants/colors/screen size.
- **PART 2** — `Connect4State` class (board rules).
- **PART 3** — explanatory docstring only, no code.
- **PART 4** — `MCTSNode` class, `rollout()`, `mcts_search()`.
- **PART 5** — `draw_board()`.
- **PART 6** — `main()` (2-human loop with hint marker).

### A. Code that MUST NOT be modified

- `Connect4State.__init__`, `.clone()`, `.get_legal_moves()`, `.make_move()`, `.check_winner()`, `.is_full()`, `.is_terminal()` — verified correct, full rules coverage (horizontal, vertical, both diagonals, draw, full-column rejection).
- `MCTSNode.__init__`, `.is_fully_expanded()`, `.best_child()`, `.most_visited_child()` — verified correct UCT implementation.
- `rollout(state, root_player)` — verified correct, scores strictly from `root_player`'s perspective.
- `mcts_search()`'s **iteration loop body** (selection → expansion → simulation → backpropagation, lines currently between `for _ in range(n_iter):` and the loop's end) — verified correct control flow.

### B. Code that MUST be extended (wrapped, not rewritten)

- `mcts_search()`'s **signature and return statement only** (Phase 2).
- `draw_board()` — gains new optional parameters for stats overlay, winning-line highlight, last-move marker, animated disc (Phases 3, 6, 9, 10) — its existing board/message/disc-drawing behavior must still work with no new arguments supplied.

### C. Code that MUST be replaced

- `main()` — the entire function body is replaced (Phase 13). The current 2-human-player behavior with a decorative hint is explicitly not required by the assignment and is superseded by mode-based Human vs AI / AI vs AI play. `HEIGHT`'s formula (currently `(ROWS + 2) * SQUARESIZE`, "extra 2 rows for message and hint") is widened, not renamed (Phase 1).

### D. New code that MUST be added

Listed function-by-function in the phases below. Every new function name, signature, and body given in this document is to be implemented **exactly as written** — do not redesign.

---

## 1. MCTS Mathematical Contract (reference for every later phase)

Using the actual existing implementation's own conventions, verified from the code:

- `node.visits` (int): number of times this node was passed through during backpropagation across the `n_iter` iterations of one `mcts_search` call.
- `node.wins` (float): cumulative reward, **from the fixed `root_player`'s perspective** (`root_player = root_state.current_player`, captured once at the top of `mcts_search`), summed over every backpropagation pass through this node. This does **not** flip sign per depth — it stays fixed to the same `root_player` at every level, which is correct and must remain so.
- `rollout(state, root_player)` returns `1.0` if `root_player` wins the random playout, `0.0` if the opponent wins, `0.5` on a draw.
- **UCT formula actually used by `MCTSNode.best_child`** (copy this exactly anywhere else a UCB value is computed for display):

```
exploit = child.wins / child.visits
explore = sqrt( 2 * ln(parent.visits) / child.visits )
score   = exploit + c_param * explore
```

with `c_param = 1.4` as the existing default, and `score = float('inf')` for any child with `visits == 0`. Note the factor of `2` inside the square root — any statistics-display code that omits this factor will show a UCB value inconsistent with what tree selection actually used, which is not acceptable.

- **Final move selection**: `root_node.most_visited_child().move` — the child with the highest visit count. This is unchanged and must remain the selection rule. The UCB value shown in the UI for the chosen column is a **diagnostic report**, computed with the same formula above, of what that already-chosen child's UCB happened to be — it is never used to pick the move.
- **Root state representation**: `Connect4State` cloned once into `MCTSNode(root_state.clone())` at the top of `mcts_search`.
- **Legal move generation / move application / terminal detection**: `Connect4State.get_legal_moves()`, `.make_move()`, `.is_terminal()` — unchanged, called only.

---

## 2. Phase-by-Phase Implementation

### PHASE 1 — Constants, Screen Sizing, and Protective Comments

**Objective:** Establish every new named constant up front (no magic numbers introduced later), widen the screen to fit the new UI regions, and mark the protected algorithmic regions with comments so no later phase accidentally edits them.

**Files affected:** `connect4_mcts.py`, PART 1 block only.

**Exact code — append immediately after the existing `FPS = 60` line, before the blank lines that lead into PART 2:**

```python
# ==========================================
#     PART 1B - PART 2 ASSIGNMENT CONSTANTS
# ==========================================

# --- Layout ---
BOARD_HEIGHT = ROWS * SQUARESIZE          # pixel height of the playable grid only
STATUS_BAND_HEIGHT = 40                   # turn indicator / thinking status text
STATS_BAND_HEIGHT = 110                   # per-column win-rate/visits bar chart
EXPLANATION_BAND_HEIGHT = 26              # "why this move" text line
LEGEND_BAND_HEIGHT = 90                   # always-visible keybind legend (multi-line)
DEBUG_BAND_HEIGHT = 130                   # toggleable debug panel, reserved space

UI_REGION_HEIGHT = (STATUS_BAND_HEIGHT + STATS_BAND_HEIGHT
                     + EXPLANATION_BAND_HEIGHT + LEGEND_BAND_HEIGHT
                     + DEBUG_BAND_HEIGHT)

# Overwrite the starter's HEIGHT/SIZE with room for the full UI region below the board.
HEIGHT = BOARD_HEIGHT + UI_REGION_HEIGHT
SIZE = (WIDTH, HEIGHT)

STATUS_BAND_Y = BOARD_HEIGHT
STATS_BAND_Y = STATUS_BAND_Y + STATUS_BAND_HEIGHT
EXPLANATION_BAND_Y = STATS_BAND_Y + STATS_BAND_HEIGHT
LEGEND_BAND_Y = EXPLANATION_BAND_Y + EXPLANATION_BAND_HEIGHT
DEBUG_BAND_Y = LEGEND_BAND_Y + LEGEND_BAND_HEIGHT

# --- MCTS search parameters ---
MCTS_EXPLORATION_C = 1.4                  # matches MCTSNode.best_child's existing default

# --- AI personalities / difficulty (Phase 12) ---
AI_CONFIGS = {
    "aggressive": {"name": "AI Aggressive", "n_iter": 1200, "c_param": 0.8},
    "balanced":   {"name": "AI Balanced",   "n_iter": 800,  "c_param": 1.4},
    "cautious":   {"name": "AI Cautious",   "n_iter": 600,  "c_param": 2.0},
}
DEFAULT_AI_CONFIG_KEY = "balanced"

# --- Timing ---
MIN_THINKING_DISPLAY_MS = 400             # minimum visible "AI thinking" duration
AI_VS_AI_MOVE_PAUSE_MS = 900              # pause between AI vs AI moves
DROP_ANIMATION_MS = 300                   # piece-drop animation duration

# --- Extra colors for new UI (existing colors are not modified) ---
PANEL_BG_COLOR = (20, 20, 20)
PANEL_ALPHA = 170
LAST_MOVE_RING_COLOR = (255, 255, 255)
WINNING_LINE_COLOR = (255, 215, 0)
CHOSEN_COLUMN_EMPHASIS_COLOR = (255, 255, 255)
UNEXPLORED_COLUMN_COLOR = (90, 90, 90)

# --- Assets (Phase 5) ---
ASSET_DIR = "assets"

# --- Fonts (created once in main(), Phase 13) ---
FONT_SIZE_HEADER = 30
FONT_SIZE_BODY = 22
FONT_SIZE_SMALL = 16
```

**Protective comment banners — insert exactly where shown, do not alter the code beneath them:**

Immediately above `class Connect4State:`:
```python
# =====================================================================
# PROTECTED CORE — DO NOT MODIFY THE LOGIC BELOW.
# Connect4State is algorithmically verified correct (rules engine).
# Later phases may only ADD new functions that READ this state;
# never alter make_move/check_winner/is_terminal logic.
# =====================================================================
```

Immediately above `class MCTSNode:`:
```python
# =====================================================================
# PROTECTED CORE — DO NOT MODIFY.
# MCTSNode + rollout() + mcts_search()'s iteration loop are the
# verified-correct MCTS algorithm (selection/expansion/simulation/
# backprop + UCT). Phase 2 wraps mcts_search's RETURN value only —
# never its loop body.
# =====================================================================
```

**Integration point:** These constants are consumed by every later phase; nothing downstream should redefine `HEIGHT`, `BOARD_HEIGHT`, or any band constant.

**Expected behavior:** The file still runs (via the still-unmodified `main()` from the starter) with a taller window; the extra space below the board is blank/unused until later phases draw into it.

**Verification checklist:**
- [ ] File runs with no `NameError`/`ImportError`.
- [ ] Window height visibly increased versus the original starter.
- [ ] `WIDTH` and the existing `x // SQUARESIZE` column math are unchanged.

---

### PHASE 2 — Root Statistics Extraction + UCB Snapshot Contract

**Objective:** Add the single source of truth for per-column statistics, and change `mcts_search`'s return contract so the chosen column's UCB is captured before the move is ever applied to the real board — the core fix that makes the UCB survive an immediate winning move.

**Files affected:** `connect4_mcts.py`, PART 4 block only (append after `mcts_search`; modify only `mcts_search`'s signature and return statement).

**Exact code — add `import` at top of file (with the other imports) if not already present:**

```python
from math import log as _log, sqrt as _sqrt  # avoid clobbering math module usage elsewhere; math is already imported
```

(If preferred, use the already-imported `math` module directly — `math.log`, `math.sqrt` — instead of a separate import, to avoid two names for the same function. Use **one** approach consistently; the code below uses `math.log`/`math.sqrt` to match the existing file's style, which already does `import math`.)

**New function — insert directly below `mcts_search` (which is modified below):**

```python
def extract_root_stats(root_node, c_param):
    """
    Reads root_node.children (a finished MCTS search tree) and returns
    per-column statistics for every legal column at the root, INCLUDING
    columns that never received a child (visits == 0).

    Read-only: does not mutate root_node or any child.

    Returns:
        dict: {col: {"visits": int, "win_rate": float, "ucb": float or None}}
        "ucb" is None only for visits == 0 columns (displayed as "unexplored"
        in the UI, never as a fabricated number).
    """
    stats = {}
    legal_columns = root_node.state.get_legal_moves()
    children_by_move = {child.move: child for child in root_node.children}

    for col in legal_columns:
        child = children_by_move.get(col)
        if child is None or child.visits == 0:
            stats[col] = {"visits": 0, "win_rate": 0.0, "ucb": None}
            continue
        win_rate = child.wins / child.visits
        ucb = win_rate + c_param * math.sqrt(2 * math.log(root_node.visits) / child.visits)
        stats[col] = {"visits": child.visits, "win_rate": win_rate, "ucb": ucb}

    return stats
```

**Modify `mcts_search`'s signature and return statement ONLY — the loop body between them is untouched:**

Replace:
```python
def mcts_search(root_state, n_iter=400):
    ...
    if root_state.is_terminal():
        return None
    ...
    best_child = root_node.most_visited_child()
    if best_child is None:
        return None
    return best_child.move
```

With:
```python
def mcts_search(root_state, n_iter=400, c_param=MCTS_EXPLORATION_C):
    """
    Run MCTS from the given root_state and return (best_move, stats, chosen_ucb).

    best_move:   root_node.most_visited_child().move, or None if terminal/no moves.
    stats:       dict from extract_root_stats(root_node, c_param) — ALL legal
                 columns, captured BEFORE any move is applied to the real board.
    chosen_ucb:  stats[best_move]["ucb"], or None if best_move is None.

    This return contract exists so the UI can display the chosen column's UCB
    even if that move immediately wins the game — the value is captured here,
    while root_node still exists, independent of what happens after the move
    is applied by the caller.
    """
    if root_state.is_terminal():
        return None, {}, None

    root_player = root_state.current_player
    root_node = MCTSNode(root_state.clone())

    for _ in range(n_iter):
        # === SELECTION / EXPANSION / SIMULATION / BACKPROPAGATION ===
        # PROTECTED CORE — UNCHANGED FROM STARTER. DO NOT EDIT THIS BLOCK.
        node = root_node
        state = root_state.clone()

        while node.children and node.is_fully_expanded() and not state.is_terminal():
            node = node.best_child()
            if node.move is not None:
                state.make_move(node.move)

        if not state.is_terminal():
            legal_moves = state.get_legal_moves()
            existing_moves = {child.move for child in node.children}
            untried_moves = [m for m in legal_moves if m not in existing_moves]
            if untried_moves:
                move = random.choice(untried_moves)
                state.make_move(move)
                child_node = MCTSNode(state.clone(), parent=node, move=move)
                node.children.append(child_node)
                node = child_node

        reward = rollout(state, root_player)

        while node is not None:
            node.visits += 1
            node.wins += reward
            node = node.parent
        # === END PROTECTED CORE ===

    best_child_node = root_node.most_visited_child()
    if best_child_node is None:
        return None, {}, None

    best_move = best_child_node.move
    stats = extract_root_stats(root_node, c_param)
    chosen_ucb = stats[best_move]["ucb"]
    return best_move, stats, chosen_ucb
```

**Update the only existing call site (inside the current `main()`):** it is fine for this phase to leave that call site functionally simplified (unpack all 3 values, ignore `stats`/`chosen_ucb` for now) since `main()` is fully replaced in Phase 13 — the only requirement here is that it does not crash:

```python
# temporary, inside starter main() only, until Phase 13 replaces main() entirely:
hint_col, _stats, _ucb = mcts_search(state, n_iter=400)
```

**Integration point:** Every later phase that needs statistics/UCB reads them from this return contract — no other function may recompute or fabricate them.

**Expected behavior:** `mcts_search` returns a 3-tuple; the file still runs with no crash; the (temporary) hint marker still appears correctly using `hint_col`.

**Verification checklist:**
- [ ] `extract_root_stats` never raises `ZeroDivisionError` for any `visits == 0` child.
- [ ] `stats` dict includes every legal column, even ones with no child.
- [ ] `mcts_search` returns exactly 3 values at its only call site; no unpack errors.
- [ ] Loop body between `for _ in range(n_iter):` and the final `best_child_node = ...` line is byte-for-byte identical to the original starter's loop body.

---

### PHASE 3 — Winning-Cell Detection (Tied to the Actual Final Move)

**Objective:** Add a helper that returns the exact four winning cells, specifically the line that passes through the most recently placed piece — not an arbitrary earlier-found line elsewhere on the board.

**Files affected:** `connect4_mcts.py`, new function appended after PART 2 (near `Connect4State`, since it reads board state directly) or in PART 4/5 area — place it directly after `Connect4State` class, before PART 3's docstring.

**Exact code:**

```python
def find_winning_cells(state, last_move):
    """
    Given the (row, col) of the most recently placed piece, return the list
    of exactly 4 (row, col) tuples forming the winning line THROUGH that piece,
    or None if the piece at last_move is not part of a winning line.

    Checks all four orientations centered on last_move:
    horizontal, vertical, diagonal \\ (down-right), diagonal / (down-left/up-right).

    Does not scan the whole board for an arbitrary winning line elsewhere —
    the returned line always contains last_move, so the highlight always
    corresponds to the move that actually ended the game.
    """
    if last_move is None:
        return None
    row, col = last_move
    player = state.board[row][col]
    if player == EMPTY:
        return None

    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for dr, dc in directions:
        cells = [(row, col)]

        r, c = row - dr, col - dc
        while 0 <= r < ROWS and 0 <= c < COLS and state.board[r][c] == player:
            cells.insert(0, (r, c))
            r, c = r - dr, c - dc

        r, c = row + dr, col + dc
        while 0 <= r < ROWS and 0 <= c < COLS and state.board[r][c] == player:
            cells.append((r, c))
            r, c = r + dr, c + dc

        if len(cells) >= 4:
            idx = cells.index((row, col))
            start = max(0, idx - 3)
            for offset in range(start, idx + 1):
                window = cells[offset:offset + 4]
                if len(window) == 4:
                    return window

    return None
```

**Integration point:** Called once, immediately after `state.check_winner()` returns a non-`None` winner, in both mode controllers (Phases 7/8), passing the coordinate of the piece that was just placed. Do not call `Connect4State.check_winner` differently or duplicate its scan logic elsewhere — this function is additive.

**Expected behavior:** Returns exactly 4 coordinates whenever the last move won; `None` otherwise (e.g. if `check_winner()` found a winner through some other pre-existing line without the last move being part of it — should not normally happen in Connect4 since only the just-placed piece can complete a new line, but the function is still defined safely relative to `last_move`).

**Verification checklist:**
- [ ] Constructed test board, horizontal win: returns the 4 cells including `last_move`.
- [ ] Constructed test board, vertical win: same.
- [ ] Constructed test board, diagonal `\` win: same.
- [ ] Constructed test board, diagonal `/` win: same.
- [ ] Returns `None` on a non-winning `last_move`.

---

### PHASE 4 — Turn Coordinate Tracking on `make_move`

**Objective:** `Connect4State.make_move` does not currently report *where* (row, col) the piece landed — only that it succeeded. Rather than modifying the protected `make_move`, add a small wrapper used by the controllers so `last_move`/`find_winning_cells`/drop-animation all have the exact landing coordinate.

**Files affected:** `connect4_mcts.py`, new function near `find_winning_cells`.

**Exact code:**

```python
def apply_move_and_get_coordinate(state, col):
    """
    Applies col as a move on state (using the existing, unmodified make_move),
    and returns the (row, col) where the piece actually landed, or None if
    the move was illegal (column full / out of range).

    Does not alter Connect4State.make_move. Only wraps it to recover the
    landing row, by comparing the top-most non-EMPTY cell in that column
    before/after — implemented here by re-deriving it from the same
    bottom-up scan make_move itself uses, BEFORE calling make_move, since
    after make_move the column's fill level has already changed.
    """
    if col not in state.get_legal_moves():
        return None
    landing_row = None
    for r in range(ROWS - 1, -1, -1):
        if state.board[r][col] == EMPTY:
            landing_row = r
            break
    success = state.make_move(col)
    if not success or landing_row is None:
        return None
    return (landing_row, col)
```

**Integration point:** Every place a controller currently calls `state.make_move(col)` directly (Phases 7, 8) must instead call `apply_move_and_get_coordinate(state, col)` and store the returned coordinate as `last_move`.

**Expected behavior:** Identical game behavior to calling `make_move` directly, plus a coordinate available for `last_move`/`find_winning_cells`/animation.

**Verification checklist:**
- [ ] Returns the correct `(row, col)` for a piece dropped into an empty column (should land at `row = ROWS - 1`).
- [ ] Returns the correct `(row, col)` for a piece dropped into a partially-filled column.
- [ ] Returns `None` for a full column, and the board is unchanged in that case (matches `make_move`'s existing False-return behavior).

---

### PHASE 5 — Asset Loading Layer (Safe, No Invented Filenames)

**Objective:** Add an asset-loading function with safe fallback, without assuming any filenames — the supplied codebase has no `assets/` directory or files at all.

**Files affected:** `connect4_mcts.py`, new function in PART 5 area (near `draw_board`).

**Exact code:**

```python
import os  # add to the existing import block at the top of the file if not already present

def load_assets():
    """
    Attempts to load optional disc images from ASSET_DIR ("assets").
    No assets were found in the supplied codebase at inspection time, so
    every slot below defaults to None (procedural pygame.draw.circle
    fallback, exactly as the current draw_board already does).

    IMPORTANT: If real asset files are later added to the assets/ directory,
    add their EXACT filenames to the `expected_files` list below — do not
    invent or guess names, and do not rename/move any user-provided file.
    Loading happens exactly once, at startup, never per-frame.
    """
    assets = {
        "player1": None,
        "player2": None,
        "ai_alpha": None,
        "ai_beta": None,
    }

    # expected_files maps asset slot -> filename. Empty until real files
    # are confirmed to exist in ASSET_DIR; do not populate with guesses.
    expected_files = {
        # "player1": "<exact_filename_found_in_assets_dir>",
        # "player2": "<exact_filename_found_in_assets_dir>",
        # "ai_alpha": "<exact_filename_found_in_assets_dir>",
        # "ai_beta": "<exact_filename_found_in_assets_dir>",
    }

    for slot, filename in expected_files.items():
        path = os.path.join(ASSET_DIR, filename)
        try:
            img = pygame.image.load(path).convert_alpha()
            assets[slot] = pygame.transform.smoothscale(img, (RADIUS * 2, RADIUS * 2))
        except (pygame.error, FileNotFoundError):
            assets[slot] = None

    return assets
```

**Integration point:** Called exactly once in `main()` (Phase 13) before the loop starts; the returned dict is threaded into `draw_board` (Phase 6) for optional disc rendering.

**Expected behavior:** With no `assets/` directory present, `load_assets()` returns all-`None` slots and the game renders identically to the current procedural circles — zero visual change until real files are added and their filenames are filled into `expected_files`.

**Verification checklist:**
- [ ] Runs with no `assets/` directory present — no crash.
- [ ] If a real `assets/` directory with confirmed filenames is added later, populating `expected_files` with the exact names causes those images to load and scale correctly.
- [ ] No existing file inside `assets/` (if present) is renamed, moved, or overwritten by this function.

---

### PHASE 6 — Extend `draw_board` (Stats Overlay Hooks, Winning Line, Last Move, Assets, Animated Disc)

**Objective:** Extend the existing `draw_board` with new **optional** parameters so all later visual features route through one rendering function, without breaking its current basic-call signature.

**Files affected:** `connect4_mcts.py`, PART 5, `draw_board` function.

**Exact code — replace the function signature and body as shown (existing message/hint/board-drawing lines are preserved, new blocks are added):**

```python
def draw_board(screen, state, font, hint_col=None, message="",
                assets=None, winning_cells=None, last_move=None,
                drop_animation=None, chosen_move=None):
    """
    Draw the entire game screen. Extends the starter's draw_board with
    optional overlays; all new parameters default to None/no-op so any
    existing call with only (screen, state, font, hint_col, message)
    behaves exactly as before.

    New parameters:
        assets: dict from load_assets(), or None.
        winning_cells: list of 4 (row, col) from find_winning_cells(), or None.
        last_move: (row, col) of the most recent move, or None.
        drop_animation: {"row", "col", "player", "start_ms"} or None — the
                         cell currently mid drop-animation; its static piece
                         is skipped this frame in favor of the animated draw.
        chosen_move: column index of the AI's last chosen move, for a
                     subtle board-side emphasis (kept minimal here; the
                     main chosen-column display lives in the stats panel).
    """
    screen.fill(BG_COLOR)

    text_surface = font.render(message, True, TEXT_COLOR)
    screen.blit(text_surface, (10, 5))

    if hint_col is not None:
        x_center = hint_col * SQUARESIZE + SQUARESIZE // 2
        pygame.draw.circle(screen, HINT_COLOR, (x_center, SQUARESIZE), RADIUS // 2)

    # Board + holes (unchanged geometry; note board is drawn at (r * SQUARESIZE)
    # directly now — Phase 1 removed the "+2 extra rows" offset convention
    # because the status/message text now lives in its own STATUS band below
    # the board rather than above it. See Phase 13 for the message relocation.)
    for c in range(COLS):
        for r in range(ROWS):
            pygame.draw.rect(
                screen, BOARD_COLOR,
                (c * SQUARESIZE, r * SQUARESIZE, SQUARESIZE, SQUARESIZE),
            )
            pygame.draw.circle(
                screen, BG_COLOR,
                (c * SQUARESIZE + SQUARESIZE // 2, r * SQUARESIZE + SQUARESIZE // 2),
                RADIUS,
            )

    # Pieces (skip the cell currently mid drop-animation; drawn separately below)
    animating_cell = None
    if drop_animation is not None:
        animating_cell = (drop_animation["row"], drop_animation["col"])

    for c in range(COLS):
        for r in range(ROWS):
            if (r, c) == animating_cell:
                continue
            piece = state.board[r][c]
            if piece == PLAYER1:
                color = PLAYER1_COLOR
                asset_key = "player1"
            elif piece == PLAYER2:
                color = PLAYER2_COLOR
                asset_key = "player2"
            else:
                continue
            center = (c * SQUARESIZE + SQUARESIZE // 2, r * SQUARESIZE + SQUARESIZE // 2)
            _draw_disc(screen, assets, asset_key, center, color)

    # Animated (falling) disc, drawn on top
    if drop_animation is not None:
        now_ms = pygame.time.get_ticks()
        t = min(1.0, (now_ms - drop_animation["start_ms"]) / DROP_ANIMATION_MS)
        target_y = drop_animation["row"] * SQUARESIZE + SQUARESIZE // 2
        start_y = 0 - SQUARESIZE // 2
        current_y = start_y + (target_y - start_y) * t
        center_x = drop_animation["col"] * SQUARESIZE + SQUARESIZE // 2
        color = PLAYER1_COLOR if drop_animation["player"] == PLAYER1 else PLAYER2_COLOR
        asset_key = "player1" if drop_animation["player"] == PLAYER1 else "player2"
        _draw_disc(screen, assets, asset_key, (center_x, int(current_y)), color)

    # Last-move ring (distinct from winning-line highlight)
    if last_move is not None and (winning_cells is None or last_move not in winning_cells):
        r, c = last_move
        center = (c * SQUARESIZE + SQUARESIZE // 2, r * SQUARESIZE + SQUARESIZE // 2)
        pygame.draw.circle(screen, LAST_MOVE_RING_COLOR, center, RADIUS + 4, width=3)

    # Winning-line highlight
    if winning_cells:
        for (r, c) in winning_cells:
            center = (c * SQUARESIZE + SQUARESIZE // 2, r * SQUARESIZE + SQUARESIZE // 2)
            pygame.draw.circle(screen, WINNING_LINE_COLOR, center, RADIUS + 6, width=4)

    # NOTE: pygame.display.update() call REMOVED from here — Phase 13's main()
    # calls pygame.display.flip() once per frame after all draw_* functions
    # (board + stats panel + debug panel + legend) have run, so overlays are
    # not wiped by a mid-frame update. This is the one behavioral change to
    # draw_board's existing contract; every caller must stop expecting this
    # function to flip the display itself.


def _draw_disc(screen, assets, asset_key, center, fallback_color):
    img = assets.get(asset_key) if assets else None
    if img is not None:
        rect = img.get_rect(center=center)
        screen.blit(img, rect)
    else:
        pygame.draw.circle(screen, fallback_color, center, RADIUS)
```

**Integration point:** Called every frame by both mode controllers (Phases 7/8) with the current `state`, animation/highlight state, and `assets`. `main()` (Phase 13) is now responsible for the single `pygame.display.flip()` call per frame — remove the `pygame.display.update()` that currently lives inside `draw_board`.

**Expected behavior:** With all new parameters left at their defaults (`None`), the board renders with no message-position regression versus before, minus the display-flip change (handled centrally in Phase 13). With real values supplied, discs animate, the last move rings, and the winning line glows.

**Verification checklist:**
- [ ] Calling `draw_board(screen, state, font)` with no new arguments does not crash and renders the board+message correctly.
- [ ] `winning_cells` highlight renders on exactly 4 correct cells for all 4 orientations (reuses Phase 3's tests).
- [ ] `drop_animation` never causes a duplicate disc to render in the same cell (static draw is skipped for the animating cell every frame it's active).
- [ ] Removing `pygame.display.update()` from inside `draw_board` does not cause a blank/unflipped screen once Phase 13's `main()` adds the single `pygame.display.flip()`.

---

### PHASE 7 — Human vs AI Controller (Synchronous First Pass)

**Objective:** Build a fully correct, playable Human vs AI mode using a synchronous `mcts_search` call, to validate correctness before adding threading (Phase 9).

**Files affected:** `connect4_mcts.py`, new controller-state block and functions, placed after `draw_board`/`_draw_disc`, before the old PART 6.

**Exact code:**

```python
# ============================================================
#         PART 7 - HUMAN VS AI CONTROLLER STATE
# ============================================================

HUMAN_PLAYER = PLAYER1
AI_PLAYER = PLAYER2

# Controller state (re-initialized by reset_game_state(), Phase 11)
state = None
game_over = False
winner = None
last_move = None
winning_cells = None
ai_thinking = False
drop_animation = None
last_ai_stats = {}
last_chosen_move = None
chosen_ucb = None
explanation_text = ""
selected_hvai_config_key = DEFAULT_AI_CONFIG_KEY


def handle_human_vs_ai_click(event):
    """
    Applies a human move ONLY if the click is a left-click strictly inside
    the board region (never the UI bands below it), it is currently the
    human's turn, the game is not over, and the AI is not thinking.
    """
    global last_move, winning_cells, drop_animation, game_over, winner

    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return
    if game_over or ai_thinking:
        return
    if state.current_player != HUMAN_PLAYER:
        return

    mouse_x, mouse_y = event.pos
    if not (0 <= mouse_x < WIDTH and 0 <= mouse_y < BOARD_HEIGHT):
        return  # click was on a UI band — ignore

    col = mouse_x // SQUARESIZE
    if col not in state.get_legal_moves():
        return

    coord = apply_move_and_get_coordinate(state, col)
    if coord is None:
        return

    last_move = coord
    drop_animation = {"row": coord[0], "col": coord[1], "player": HUMAN_PLAYER,
                       "start_ms": pygame.time.get_ticks()}

    result_winner = state.check_winner()
    if result_winner is not None:
        winner = result_winner
        winning_cells = find_winning_cells(state, last_move)
        game_over = True
    elif state.is_full():
        winner = None
        game_over = True
```

**Integration point:** `handle_human_vs_ai_click` is called once per `MOUSEBUTTONDOWN` event inside `main()`'s event loop (Phase 13), only while `mode == GameMode.HUMAN_VS_AI`.

**Expected behavior:** Human moves apply only on valid board clicks during the human's own turn; AI turn triggering is added in Phase 9 (threaded) — for this phase's isolated verification, a temporary synchronous AI call (below) may be used and then deleted once Phase 9 lands:

```python
# TEMPORARY — for isolated Phase 7 testing only, replaced by Phase 9's threaded version:
def _debug_run_ai_turn_sync():
    global last_move, winning_cells, drop_animation, game_over, winner
    global last_ai_stats, last_chosen_move, chosen_ucb
    cfg = AI_CONFIGS[selected_hvai_config_key]
    best_move, stats, ucb = mcts_search(state, n_iter=cfg["n_iter"], c_param=cfg["c_param"])
    last_ai_stats, last_chosen_move, chosen_ucb = stats, best_move, ucb
    if best_move is None:
        return
    coord = apply_move_and_get_coordinate(state, best_move)
    last_move = coord
    drop_animation = {"row": coord[0], "col": coord[1], "player": AI_PLAYER,
                       "start_ms": pygame.time.get_ticks()}
    result_winner = state.check_winner()
    if result_winner is not None:
        winner = result_winner
        winning_cells = find_winning_cells(state, last_move)
        game_over = True
    elif state.is_full():
        game_over = True
```

**Verification checklist:**
- [ ] Clicking outside the board (e.g. `mouse_y >= BOARD_HEIGHT`) never applies a move.
- [ ] Right/middle-click never applies a move.
- [ ] Clicking a full column does nothing.
- [ ] Clicking during the AI's conceptual turn does nothing.
- [ ] `last_ai_stats`/`chosen_ucb` are correctly populated after `_debug_run_ai_turn_sync` and remain visible after `game_over` becomes `True`.

---

### PHASE 8 — AI vs AI Controller (Synchronous First Pass)

**Objective:** Build the fully automatic AI-vs-AI turn sequence, synchronous for now, verified in isolation before threading (Phase 9).

**Files affected:** `connect4_mcts.py`, new controller block after Phase 7's.

**Exact code:**

```python
# ============================================================
#         PART 8 - AI VS AI CONTROLLER STATE
# ============================================================

selected_ai_vs_ai_config_keys = {PLAYER1: DEFAULT_AI_CONFIG_KEY, PLAYER2: DEFAULT_AI_CONFIG_KEY}
pending_pause_until_ms = None


def config_for(player, mode):
    """
    SINGLE SOURCE OF TRUTH for (n_iter, c_param). No gameplay call site may
    pass literal n_iter=/c_param= values — always resolve through this.
    """
    if mode == "human_vs_ai":
        key = selected_hvai_config_key
    else:
        key = selected_ai_vs_ai_config_keys[player]
    cfg = AI_CONFIGS[key]
    return cfg["n_iter"], cfg["c_param"], cfg["name"]


def _debug_run_ai_vs_ai_turn_sync():
    """TEMPORARY synchronous version for isolated Phase 8 testing only —
    replaced by Phase 9's threaded update_ai_vs_ai_frame."""
    global last_move, winning_cells, drop_animation, game_over, winner
    global last_ai_stats, last_chosen_move, chosen_ucb

    player = state.current_player
    n_iter, c_param, _name = config_for(player, "ai_vs_ai")
    best_move, stats, ucb = mcts_search(state, n_iter=n_iter, c_param=c_param)
    last_ai_stats, last_chosen_move, chosen_ucb = stats, best_move, ucb
    if best_move is None:
        return
    coord = apply_move_and_get_coordinate(state, best_move)
    last_move = coord
    drop_animation = {"row": coord[0], "col": coord[1], "player": player,
                       "start_ms": pygame.time.get_ticks()}
    result_winner = state.check_winner()
    if result_winner is not None:
        winner = result_winner
        winning_cells = find_winning_cells(state, last_move)
        game_over = True
    elif state.is_full():
        game_over = True
```

**Integration point:** Called from a temporary test loop for this phase only; Phase 9 replaces it with the threaded, paced version.

**Expected behavior:** Calling `_debug_run_ai_vs_ai_turn_sync()` repeatedly (e.g. bound to a temporary keypress) alternates `PLAYER1`/`PLAYER2` correctly and ends the game correctly on win/draw.

**Verification checklist:**
- [ ] Alternation is correct (`state.current_player` flips every call).
- [ ] AI never selects a full column (inherits correctness from `mcts_search`/`get_legal_moves`).
- [ ] Game halts correctly on win/draw; `winning_cells` set correctly.

---

### PHASE 9 — Threaded Search (Replaces Both Debug-Sync Helpers)

**Objective:** Replace the temporary synchronous AI calls from Phases 7–8 with a background-thread version, safe generation-token invalidation, and a strict `ai_thinking` invariant.

**Files affected:** `connect4_mcts.py`, new threading block; deletes `_debug_run_ai_turn_sync` and `_debug_run_ai_vs_ai_turn_sync`.

**Exact code:**

```python
import threading  # add to the existing import block at the top of the file

# ============================================================
#         PART 9 - THREADED MCTS SEARCH
# ============================================================

search_generation = 0
_ai_result_slot = None       # [ (best_move, stats, chosen_ucb) ] once populated, else None
_ai_result_generation = None
thinking_started_ms = None
last_search_iterations = 0
last_search_duration_ms = 0.0
_search_start_ms = None


def _run_search_worker(state_clone, n_iter, c_param, result_slot):
    """
    WORKER THREAD ONLY. Touches only the cloned state passed in — never the
    live game-state object, never any pygame drawing call.
    """
    result = mcts_search(state_clone, n_iter=n_iter, c_param=c_param)
    result_slot[0] = result


def start_ai_search(player, mode):
    """
    Starts exactly one MCTS worker for `player`. Refuses to start a second
    worker while one is already active (ai_thinking must be False).
    Sets ai_thinking = True as its final step — this is the ONLY place in
    the whole program allowed to set ai_thinking = True.
    """
    global ai_thinking, _ai_result_slot, _ai_result_generation
    global thinking_started_ms, _search_start_ms, last_search_iterations

    assert not ai_thinking, "start_ai_search called while a search is already active"

    n_iter, c_param, _name = config_for(player, mode)
    last_search_iterations = n_iter

    _ai_result_slot = [None]
    _ai_result_generation = search_generation
    thinking_started_ms = pygame.time.get_ticks()
    _search_start_ms = thinking_started_ms

    clone = state.clone()
    t = threading.Thread(
        target=_run_search_worker,
        args=(clone, n_iter, c_param, _ai_result_slot),
        daemon=True,
    )
    t.start()
    ai_thinking = True


def poll_ai_search(now_ms):
    """
    Call every frame while ai_thinking is True.
    Returns (best_move, stats, chosen_ucb) once ready AND the minimum
    thinking-display duration has elapsed AND the generation still matches;
    returns None otherwise (including when the result is stale — it is
    silently discarded, never applied).
    """
    global last_search_duration_ms

    if _ai_result_slot is None or _ai_result_slot[0] is None:
        return None
    if _ai_result_generation != search_generation:
        return None  # stale — a restart/mode-switch happened; discard silently
    if now_ms - thinking_started_ms < MIN_THINKING_DISPLAY_MS:
        return None  # keep the thinking animation visible a little longer
    last_search_duration_ms = now_ms - _search_start_ms
    return _ai_result_slot[0]


def apply_ai_result(best_move, stats, ucb, player):
    """
    Applies best_move to the real board on the MAIN THREAD only.
    Defensive validation guards against a corrupt/invalid move (should never
    trigger if the MCTS core is correct; if it does, it is logged, not hidden).
    """
    global last_move, winning_cells, drop_animation, game_over, winner
    global last_ai_stats, last_chosen_move, chosen_ucb, explanation_text

    legal = state.get_legal_moves()
    if best_move is None or best_move not in range(COLS) or best_move not in legal:
        explanation_text = f"WARNING: MCTS returned invalid move {best_move}; using fallback."
        best_move = legal[0] if legal else None
        if best_move is None:
            return

    last_ai_stats = stats
    last_chosen_move = best_move
    chosen_ucb = ucb

    coord = apply_move_and_get_coordinate(state, best_move)
    if coord is None:
        return
    last_move = coord
    drop_animation = {"row": coord[0], "col": coord[1], "player": player,
                       "start_ms": pygame.time.get_ticks()}

    explanation_text = build_explanation_text(stats, best_move, ucb)

    result_winner = state.check_winner()
    if result_winner is not None:
        winner = result_winner
        winning_cells = find_winning_cells(state, last_move)
        game_over = True
    elif state.is_full():
        game_over = True


def build_explanation_text(stats, chosen_move, ucb):
    if chosen_move is None or chosen_move not in stats:
        return "No move statistics available."
    entry = stats[chosen_move]
    ucb_text = "inf" if ucb in (None, float("inf")) else f"{ucb:.2f}"
    return (f"Column {chosen_move} chosen — {entry['visits']} visits, "
            f"{entry['win_rate']*100:.1f}% win rate, UCB {ucb_text}")
```

**Integration point:** Replaces the two temporary `_debug_run_*` helpers from Phases 7–8 entirely — delete them once this phase is implemented. `start_ai_search`/`poll_ai_search`/`apply_ai_result` are called from both mode-update functions (Phases 10/11 below, which restate the full per-mode frame logic using these primitives).

**Expected behavior:** No frozen window during search; `ai_thinking` flips `False→True` only in `start_ai_search`, and `True→False` only at the point a result is consumed (Phase 10/11).

**Verification checklist:**
- [ ] `assert not ai_thinking` in `start_ai_search` never fires during normal play (i.e. nothing ever tries to double-start a search).
- [ ] A restart mid-search (Phase 11) correctly causes the eventual worker result to be discarded (`_ai_result_generation != search_generation`).
- [ ] `apply_ai_result`'s fallback path, when manually forced with an invalid test move, does not crash or corrupt the board.

---

### PHASE 10 — Human vs AI: Final Frame-Update Function (Threaded)

**Objective:** Replace Phase 7's temporary synchronous AI trigger with the real per-frame update function using Phase 9's threaded primitives, including the full `ai_thinking`/game-over lifecycle.

**Files affected:** `connect4_mcts.py`, replaces the temporary debug helper from Phase 7.

**Exact code:**

```python
def update_human_vs_ai_frame(now_ms):
    global ai_thinking

    if game_over:
        return

    if ai_thinking:
        result = poll_ai_search(now_ms)
        if result is not None and not game_over:
            best_move, stats, ucb = result
            apply_ai_result(best_move, stats, ucb, AI_PLAYER)
            ai_thinking = False
        return

    if state.current_player == AI_PLAYER:
        start_ai_search(AI_PLAYER, "human_vs_ai")
```

**Integration point:** Called every frame from `main()` (Phase 13) while `mode == GameMode.HUMAN_VS_AI`, immediately after event handling (which calls `handle_human_vs_ai_click`) and before `draw_board`.

**Expected behavior:** After the human's move switches `state.current_player` to `AI_PLAYER`, the next frame automatically starts a search; subsequent frames poll until ready; the move is applied and control returns to the human, or the game ends.

**Verification checklist:**
- [ ] AI turn always eventually resolves to exactly one applied move (no double-application, no stuck state).
- [ ] `game_over` becoming `True` inside `apply_ai_result` (via a winning AI move) correctly prevents any further search from starting on subsequent frames (top `if game_over: return` guard).

---

### PHASE 11 — AI vs AI: Final Frame-Update Function (Threaded, Paced)

**Objective:** Replace Phase 8's temporary synchronous alternation with the real, paced, threaded version.

**Files affected:** `connect4_mcts.py`, replaces the temporary debug helper from Phase 8.

**Exact code:**

```python
def update_ai_vs_ai_frame(now_ms):
    global ai_thinking, pending_pause_until_ms

    if game_over:
        return

    if ai_thinking:
        result = poll_ai_search(now_ms)
        if result is not None and not game_over:
            best_move, stats, ucb = result
            player = state.current_player
            apply_ai_result(best_move, stats, ucb, player)
            ai_thinking = False
            if not game_over:
                pending_pause_until_ms = now_ms + AI_VS_AI_MOVE_PAUSE_MS
        return

    if pending_pause_until_ms is not None:
        if now_ms >= pending_pause_until_ms:
            pending_pause_until_ms = None
            start_ai_search(state.current_player, "ai_vs_ai")
        return

    start_ai_search(state.current_player, "ai_vs_ai")
```

**Integration point:** Called every frame from `main()` while `mode == GameMode.AI_VS_AI`. No human input applies moves in this mode — only `QUIT`/`R`/`Esc`/`Tab` are handled by `main()`'s event loop regardless of mode.

**Expected behavior:** Fully automatic alternation with a visible, non-blocking pause between moves; never gets stuck in "thinking" because every branch either polls, schedules, or starts — never silently returns without progressing.

**Verification checklist:**
- [ ] A full automatic game completes to win/draw with no manual intervention.
- [ ] The `AI_VS_AI_MOVE_PAUSE_MS` pause is visibly observable (not an instant unreadable burst).
- [ ] `ai_thinking` never remains `True` indefinitely (bounded by search completion + `MIN_THINKING_DISPLAY_MS`).

---

### PHASE 12 — Reset Contract (`R`) and AI Personality Selection

**Objective:** One centralized reset function clearing all gameplay/search/visual state (used by `R` and by fresh menu-entry into a mode), plus wiring `AI_CONFIGS` (already defined in Phase 1) into menu-time selection.

**Files affected:** `connect4_mcts.py`, new function near the controller-state declarations.

**Exact code:**

```python
def reset_game_state():
    """
    Single reset contract. Called on R and on every fresh menu-entry into
    a mode. Resets ALL gameplay/search/visual state in one place — no
    partial resets scattered elsewhere. Bumps search_generation so any
    in-flight worker's eventual result is discarded, never applied to the
    fresh game.
    """
    global state, game_over, winner, last_move, winning_cells
    global ai_thinking, _ai_result_slot, _ai_result_generation, search_generation
    global pending_pause_until_ms, last_ai_stats, last_chosen_move, chosen_ucb
    global last_search_iterations, last_search_duration_ms
    global drop_animation, thinking_started_ms, explanation_text

    state = Connect4State()
    game_over = False
    winner = None
    last_move = None
    winning_cells = None
    ai_thinking = False
    _ai_result_slot = None
    _ai_result_generation = None
    search_generation += 1
    pending_pause_until_ms = None
    last_ai_stats = {}
    last_chosen_move = None
    chosen_ucb = None
    last_search_iterations = 0
    last_search_duration_ms = 0.0
    drop_animation = None
    thinking_started_ms = None
    explanation_text = ""
```

**AI personality selection state (menu-time, used by `config_for` from Phase 8):**

```python
AI_CONFIG_KEYS_ORDER = ["aggressive", "balanced", "cautious"]

def cycle_ai_config(current_key, direction=1):
    idx = AI_CONFIG_KEYS_ORDER.index(current_key)
    idx = (idx + direction) % len(AI_CONFIG_KEYS_ORDER)
    return AI_CONFIG_KEYS_ORDER[idx]
```

**Integration point:** `reset_game_state()` is called: (a) on `K_r` at any point during either game mode, (b) immediately when entering `HUMAN_VS_AI`/`AI_VS_AI` from the menu (Phase 13). `cycle_ai_config` is called from the menu's input handling (Phase 13) to let the presenter pick personalities before starting a game.

**Expected behavior:** After `R`, every visual/stat/animation trace of the previous game is gone on the very next frame; a stale worker from before the reset cannot mutate the new game (generation mismatch, Phase 9).

**Verification checklist:**
- [ ] Mid-game `R` clears board, stats, last move, winning highlight, thinking flag, pending pause — all in the same frame the key is pressed.
- [ ] A worker started just before `R` and finishing just after does not apply its move to the reset board.
- [ ] Selected AI config(s) persist correctly into the new game and are not silently reset to defaults unless the presenter changed them via the menu.

---

### PHASE 13 — Menu, Mode Dispatch, and the Real `main()`

**Objective:** Replace the starter's `main()` entirely with a mode-dispatching loop: `MENU` → `HUMAN_VS_AI` / `AI_VS_AI`, wiring every prior phase together, plus the stats panel/debug panel/legend calls (Phases 14–16 define those draw functions, referenced here).

**Files affected:** `connect4_mcts.py`, PART 6 — entire `main()` function body replaced.

**Exact code:**

```python
# ============================================================
#         PART 13 - GAME MODE / MENU / MAIN LOOP
# ============================================================

class GameMode:
    MENU = "menu"
    HUMAN_VS_AI = "human_vs_ai"
    AI_VS_AI = "ai_vs_ai"


def draw_menu(screen, fonts, hvai_key, ai1_key, ai2_key):
    screen.fill(BG_COLOR)
    header, body, small = fonts
    lines = [
        ("MCTS CONNECT 4 — PART 2", header),
        ("", small),
        (f"Human vs AI (1)   [AI: {AI_CONFIGS[hvai_key]['name']}]", body),
        (f"AI vs AI (2)   [P1: {AI_CONFIGS[ai1_key]['name']}  P2: {AI_CONFIGS[ai2_key]['name']}]", body),
        ("", small),
        ("Left/Right: cycle Human-vs-AI opponent difficulty", small),
        ("A/D: cycle AI-vs-AI Player 1 difficulty   J/L: cycle Player 2 difficulty", small),
        ("Esc: Quit", small),
    ]
    y = 40
    for text, font in lines:
        if text:
            screen.blit(font.render(text, True, TEXT_COLOR), (30, y))
        y += font.get_height() + 10


def handle_menu_keydown(event, hvai_key, ai1_key, ai2_key):
    """Returns (new_mode, hvai_key, ai1_key, ai2_key)."""
    mode = GameMode.MENU
    if event.key == pygame.K_1:
        mode = GameMode.HUMAN_VS_AI
    elif event.key == pygame.K_2:
        mode = GameMode.AI_VS_AI
    elif event.key == pygame.K_LEFT:
        hvai_key = cycle_ai_config(hvai_key, -1)
    elif event.key == pygame.K_RIGHT:
        hvai_key = cycle_ai_config(hvai_key, 1)
    elif event.key == pygame.K_a:
        ai1_key = cycle_ai_config(ai1_key, -1)
    elif event.key == pygame.K_d:
        ai1_key = cycle_ai_config(ai1_key, 1)
    elif event.key == pygame.K_j:
        ai2_key = cycle_ai_config(ai2_key, -1)
    elif event.key == pygame.K_l:
        ai2_key = cycle_ai_config(ai2_key, 1)
    return mode, hvai_key, ai1_key, ai2_key


def get_status_text():
    if game_over:
        if winner is None:
            return "Game Over — Draw"
        return f"Game Over — Player {winner} wins"
    if ai_thinking:
        return "AI thinking..."
    if state.current_player == HUMAN_PLAYER:
        return "Your turn"
    return f"AI (Player {AI_PLAYER}) turn"


def main():
    global selected_hvai_config_key, selected_ai_vs_ai_config_keys, debug_visible

    pygame.init()
    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption("MCTS Connect 4 — Part 2")
    clock = pygame.time.Clock()

    fonts = (
        pygame.font.SysFont("arial", FONT_SIZE_HEADER),
        pygame.font.SysFont("arial", FONT_SIZE_BODY),
        pygame.font.SysFont("arial", FONT_SIZE_SMALL),
    )
    assets = load_assets()

    mode = GameMode.MENU
    hvai_key = DEFAULT_AI_CONFIG_KEY
    ai1_key = DEFAULT_AI_CONFIG_KEY
    ai2_key = DEFAULT_AI_CONFIG_KEY
    debug_visible = False

    running = True
    while running:
        now_ms = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if mode == GameMode.MENU:
                        running = False
                    else:
                        mode = GameMode.MENU
                        reset_game_state()
                elif event.key == pygame.K_TAB:
                    debug_visible = not debug_visible
                elif event.key == pygame.K_r and mode != GameMode.MENU:
                    reset_game_state()
                elif mode == GameMode.MENU:
                    mode, hvai_key, ai1_key, ai2_key = handle_menu_keydown(
                        event, hvai_key, ai1_key, ai2_key)
                    if mode != GameMode.MENU:
                        selected_hvai_config_key = hvai_key
                        selected_ai_vs_ai_config_keys[PLAYER1] = ai1_key
                        selected_ai_vs_ai_config_keys[PLAYER2] = ai2_key
                        reset_game_state()

            elif mode == GameMode.HUMAN_VS_AI:
                handle_human_vs_ai_click(event)

        if mode == GameMode.MENU:
            draw_menu(screen, fonts, hvai_key, ai1_key, ai2_key)
        elif mode == GameMode.HUMAN_VS_AI:
            update_human_vs_ai_frame(now_ms)
            draw_board(screen, state, fonts[1], assets=assets,
                       winning_cells=winning_cells, last_move=last_move,
                       drop_animation=drop_animation, chosen_move=last_chosen_move)
            draw_status_and_panels(screen, fonts, mode, now_ms)
        elif mode == GameMode.AI_VS_AI:
            update_ai_vs_ai_frame(now_ms)
            draw_board(screen, state, fonts[1], assets=assets,
                       winning_cells=winning_cells, last_move=last_move,
                       drop_animation=drop_animation, chosen_move=last_chosen_move)
            draw_status_and_panels(screen, fonts, mode, now_ms)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
```

**Integration point:** `draw_status_and_panels` is defined in Phases 14–16 (stats panel, debug panel, legend, status text) and called here as one consolidated call for layout consistency.

**Expected behavior:** Menu → mode selection with difficulty cycling → full game → `Esc` back to menu (with reset) → `Esc` again quits from menu. `R` resets mid-game. `Tab` toggles debug.

**Verification checklist:**
- [ ] Program starts directly into `MENU`, no crash.
- [ ] `1`/`2` enter the two modes with a freshly reset game each time.
- [ ] `Esc` from a game mode returns to menu with a clean reset; `Esc` from menu quits.
- [ ] `R` works in both modes.
- [ ] `Tab` toggles `debug_visible` without affecting game state.
- [ ] No duplicate `pygame.display.update()`/`flip()` calls anywhere (only the one in `main()`, since Phase 6 removed `draw_board`'s internal call).

---

### PHASE 14 — Stats Panel (Win Rate / Visits per Column)

**Objective:** Always-visible, non-overlapping bar chart for all 7 columns, sourced only from `last_ai_stats`.

**Files affected:** `connect4_mcts.py`, new draw function.

**Exact code:**

```python
def draw_stats_panel(screen, font, stats, chosen_move):
    x0, y0 = 0, STATS_BAND_Y
    col_width = WIDTH // COLS
    bar_max_height = STATS_BAND_HEIGHT - 40

    for col in range(COLS):
        entry = stats.get(col, {"visits": 0, "win_rate": 0.0, "ucb": None})
        cx = x0 + col * col_width
        is_chosen = (col == chosen_move)

        if entry["visits"] == 0:
            label = font.render("unexplored", True, UNEXPLORED_COLUMN_COLOR)
            screen.blit(label, (cx + 4, y0 + STATS_BAND_HEIGHT - 20))
            continue

        bar_height = int(bar_max_height * entry["win_rate"])
        bar_rect = pygame.Rect(cx + 4, y0 + (bar_max_height - bar_height),
                                col_width - 8, bar_height)
        pygame.draw.rect(screen, HINT_COLOR, bar_rect)
        if is_chosen:
            pygame.draw.rect(screen, CHOSEN_COLUMN_EMPHASIS_COLOR, bar_rect, width=2)

        pct_label = font.render(f"{entry['win_rate']*100:.0f}%", True, TEXT_COLOR)
        visits_label = font.render(f"{entry['visits']:,}", True, (200, 200, 200))
        screen.blit(pct_label, (cx + 4, y0 + STATS_BAND_HEIGHT - 36))
        screen.blit(visits_label, (cx + 4, y0 + STATS_BAND_HEIGHT - 18))
```

**Integration point:** Called from `draw_status_and_panels` (Phase 16) with `last_ai_stats`/`last_chosen_move`.

**Expected behavior:** One entry per column, x-aligned to the board's columns, unexplored columns visually distinct, chosen column emphasized. Persists through game-over (data source `last_ai_stats` only changes on the next AI decision or on reset).

**Verification checklist:**
- [ ] All 7 columns always rendered, even with an empty `stats` dict (all show "unexplored").
- [ ] Bar heights proportional to `win_rate`, never negative/overflowing `STATS_BAND_HEIGHT`.
- [ ] Panel confined to `STATS_BAND_Y`..`STATS_BAND_Y + STATS_BAND_HEIGHT`, never overlapping the board.

---

### PHASE 15 — Debug Panel and Keybind Legend

**Objective:** Toggleable diagnostic panel (read-only) plus the always-visible keybind legend, both confined to their own layout bands.

**Files affected:** `connect4_mcts.py`, new draw functions.

**Exact code:**

```python
debug_visible = False  # module-level, toggled in main()'s event loop (Phase 13)


def draw_debug_panel(screen, font, mode, now_ms):
    if not debug_visible:
        return
    overlay = pygame.Surface((WIDTH, DEBUG_BAND_HEIGHT), pygame.SRCALPHA)
    overlay.fill((*PANEL_BG_COLOR, PANEL_ALPHA))
    screen.blit(overlay, (0, DEBUG_BAND_Y))

    if mode == GameMode.HUMAN_VS_AI:
        _, c_param, ai_name = config_for(AI_PLAYER, "human_vs_ai")
    else:
        _, c_param, ai_name = config_for(state.current_player, "ai_vs_ai")

    selected_entry = last_ai_stats.get(last_chosen_move, {"visits": 0, "win_rate": 0.0})
    ucb_text = "inf" if chosen_ucb in (None, float("inf")) else f"{chosen_ucb:.3f}"

    lines = [
        f"Mode: {mode}   Active AI: {ai_name}",
        f"Iterations: {last_search_iterations}   Search time: {last_search_duration_ms:.0f} ms",
        f"Chosen column: {last_chosen_move}",
        f"Selected win rate: {selected_entry['win_rate']*100:.1f}%   Visits: {selected_entry['visits']}",
        f"Selected UCB: {ucb_text}   Exploration C: {c_param}",
        f"Status: {'Searching...' if ai_thinking else 'Idle'}",
    ]
    for i, line in enumerate(lines):
        screen.blit(font.render(line, True, TEXT_COLOR), (10, DEBUG_BAND_Y + 8 + i * 20))


def draw_keybind_legend(screen, font):
    legend = [
        "Human vs AI (1)   AI vs AI (2)",
        "Restart (R)   Debug (TAB)   Back (ESC)",
    ]
    for i, line in enumerate(legend):
        screen.blit(font.render(line, True, (200, 200, 200)),
                     (10, LEGEND_BAND_Y + 8 + i * 20))
```

**Integration point:** Both called from `draw_status_and_panels` (Phase 16). `draw_debug_panel` is strictly read-only — it must never call `mcts_search`, `state.make_move`, or reassign any controller-state global.

**Expected behavior:** Debug panel renders only when `debug_visible` is `True`, confined to `DEBUG_BAND_Y`..`DEBUG_BAND_Y + DEBUG_BAND_HEIGHT`; legend always visible in its own band.

**Verification checklist:**
- [ ] `Tab` toggles the debug panel with zero effect on `state`/`ai_thinking`/stats.
- [ ] Debug panel content matches `last_ai_stats[last_chosen_move]`/`chosen_ucb` exactly (no recomputation).
- [ ] Legend and debug panel never overlap each other or the stats panel.

---

### PHASE 16 — Status Text, Explanation Text, and the Consolidated Panel Call

**Objective:** Tie together the turn/status indicator, "why this move" explanation, and Phases 14–15's panels into the single `draw_status_and_panels` function referenced by Phase 13's `main()`.

**Files affected:** `connect4_mcts.py`, new function.

**Exact code:**

```python
def draw_status_and_panels(screen, fonts, mode, now_ms):
    header_font, body_font, small_font = fonts

    status_text = get_status_text()
    screen.blit(body_font.render(status_text, True, TEXT_COLOR), (10, STATUS_BAND_Y + 6))

    if ai_thinking:
        dots = "." * ((now_ms // 300) % 4)
        thinking_label = body_font.render(f"AI THINKING{dots}", True, HINT_COLOR)
        screen.blit(thinking_label, (WIDTH - 220, STATUS_BAND_Y + 6))

    draw_stats_panel(screen, small_font, last_ai_stats, last_chosen_move)

    screen.blit(small_font.render(explanation_text, True, (220, 220, 220)),
                 (10, EXPLANATION_BAND_Y + 4))

    draw_keybind_legend(screen, small_font)
    draw_debug_panel(screen, small_font, mode, now_ms)
```

**Integration point:** This is the single call `main()` makes per frame (in both game modes) after `draw_board`, as already wired in Phase 13's code block.

**Expected behavior:** Every UI element renders in its own non-overlapping band below the board; the board itself is never drawn into by any of these calls.

**Verification checklist:**
- [ ] Full visual pass: Menu → Human vs AI → forced win (all 4 orientations, using Phase 3's test boards live in-game) → AI vs AI → forced win — confirm every band renders correctly and nothing overlaps at any point, including immediately after a winning move.

---

## 3. File-by-File Implementation Plan (Consolidated)

# FILE: connect4_mcts.py

## A. Existing responsibility
Single-file Pygame + MCTS Connect4 program; previously a 2-human-player demo with a decorative MCTS hint.

## B. What must remain unchanged
`Connect4State` (all methods), `MCTSNode` (all methods), `rollout()`, `mcts_search()`'s iteration loop body — see Section 0.A.

## C. What must be removed/replaced
`main()`'s entire body (Phase 13). `draw_board`'s internal `pygame.display.update()` call (Phase 6 — display flip is centralized in `main()`). The starter's `HEIGHT`/`SIZE` values (Phase 1 — widened, not renamed).

## D. What must be added
Every function introduced in Phases 1–16 above: `extract_root_stats`, `find_winning_cells`, `apply_move_and_get_coordinate`, `load_assets`, `_draw_disc`, controller state + `handle_human_vs_ai_click`, `config_for`, `_run_search_worker`, `start_ai_search`, `poll_ai_search`, `apply_ai_result`, `build_explanation_text`, `reset_game_state`, `cycle_ai_config`, `GameMode`, `draw_menu`, `handle_menu_keydown`, `get_status_text`, `draw_stats_panel`, `draw_debug_panel`, `draw_keybind_legend`, `draw_status_and_panels`, the new `main()`.

## E. Exact implementation
See Phases 1–16 in full above — every code block is to be implemented verbatim.

## F. Integration points
`mcts_search` (Phase 2) is the sole algorithmic entry point, called only from `_run_search_worker` (Phase 9), which runs only on a background thread. `draw_board` (Phase 6) is the sole rendering entry point for the grid, called once per frame from `main()`. `reset_game_state` (Phase 12) is the sole state-reset entry point, called from `R`, `Esc`, and fresh mode-entry.

## G. Expected runtime behavior
Menu-driven Human vs AI and AI vs AI Connect4, fully MCTS-driven (no heuristic/minimax substitution), responsive during search (threaded), with a persistent, correctly-captured win-rate/visits/UCB display that survives immediate wins in all four orientations, plus animations, personality selection, and a toggleable debug panel.

## H. Verification checklist
The union of every phase's individual checklist above, plus Section 4's consolidated tests below.

---

## 4. Testing — Concrete, Not Vague

### MCTS tests
- [ ] `get_legal_moves()` excludes full columns in all cases; AI never selects a full column (verify via `apply_ai_result`'s defensive check never actually triggering during normal play).
- [ ] `extract_root_stats` returns all legal root columns, including `visits == 0` ones, with `ucb=None` for those and never raises `ZeroDivisionError`.
- [ ] `MCTSNode.best_child`'s formula and `extract_root_stats`'s UCB formula agree exactly (both use `c_param * sqrt(2 * ln(parent.visits) / child.visits)`).
- [ ] `most_visited_child().move` remains the sole final-move policy; no code path substitutes a UCB-based pick.
- [ ] `rollout` reward is always scored against the fixed `root_player` captured at the top of `mcts_search`, never flipped per depth.
- [ ] Sum of all root children's `visits` plus the root's own pass equals `n_iter` (manual trace/print during isolated testing, removed afterward).

### Connect4 tests
- [ ] Horizontal, vertical, diagonal `\`, diagonal `/` wins all detected correctly (reuses `check_winner`, unmodified).
- [ ] Draw detected correctly on a full board with no winner.
- [ ] Full column cannot be clicked by a human or selected by the AI.
- [ ] Game ends immediately on a winning move; `game_over` blocks all further input (Phase 10/11's top guard).
- [ ] Turns strictly alternate in both modes.

### UCB / winning-move tests (construct all four explicitly)
For each of horizontal, vertical, diagonal `\`, diagonal `/`:
- [ ] Play/construct toward that exact winning pattern.
- [ ] Confirm `chosen_ucb` was captured in `mcts_search`'s return (Phase 2) **before** `apply_ai_result` applied the move.
- [ ] Confirm the stats panel and debug panel both still show the correct win-rate/visits/UCB for the winning column immediately after the win, and continue to show it indefinitely until `R`/`Esc`.
- [ ] Confirm `winning_cells` (Phase 3) highlights exactly the 4 cells of that specific orientation's line, and that the line contains `last_move`.

### UI / UX tests
- [ ] Human vs AI fully playable start-to-finish, restart works.
- [ ] AI vs AI runs fully automatically, restart works, pacing is visibly observable.
- [ ] Window remains responsive (can still close it, see thinking animation move) during every AI search.
- [ ] Clicking any UI band (stats/debug/legend/status) never places a piece (Phase 7's board-region guard).
- [ ] Right/middle-click never places a piece.
- [ ] `Tab` toggles debug panel with zero gameplay side effects.
- [ ] `Esc` returns to menu cleanly from either mode, with `reset_game_state()` applied.
- [ ] Drop animation never duplicates a disc in the same cell (Phase 6's `animating_cell` skip logic).
- [ ] Missing `assets/` directory does not crash `load_assets()` or the game.
- [ ] No two UI bands ever overlap, at any screen state (menu, mid-game, debug on/off, game-over).

---

## 5. Performance

- All iteration counts (`AI_CONFIGS[...]["n_iter"]`) and the exploration constant are named constants (Phase 1) — never literals at call sites (Phase 8's `config_for` is the only place that resolves them).
- Profile actual search duration via `last_search_duration_ms` (Phase 9); if any configured `n_iter` regularly exceeds roughly 1–1.5 seconds of wall-clock search time on the target machine, lower that config's `n_iter` in `AI_CONFIGS` — do not change the algorithm to compensate.
- The worker thread (Phase 9) touches only a cloned `Connect4State`; the main thread owns all Pygame calls — no cross-thread Pygame access anywhere.
- Assets load exactly once (Phase 5, called once in `main()`), never per-frame.

---

## 6. Final Acceptance Checklist

### Assignment
- [ ] Human vs AI implemented and fully playable.
- [ ] AI vs AI implemented and fully playable.

### MCTS
- [ ] Selection / Expansion / Simulation / Backpropagation all present, unmodified from the verified-correct starter.
- [ ] UCB1 formula (`exploit + c_param * sqrt(2*ln(N)/n)`) correct and consistent between `best_child` and `extract_root_stats`.
- [ ] Correct root-player reward perspective throughout.
- [ ] Correct visit accounting; correct win-rate arithmetic.

### Statistics
- [ ] Win rate shown for columns 0–6.
- [ ] Visits shown for columns 0–6.
- [ ] Final chosen column's UCB shown.
- [ ] UCB remains visible after an immediate win — verified for horizontal, vertical, diagonal `\`, and diagonal `/`.

### Connect4
- [ ] Horizontal / vertical / diagonal `\` / diagonal `/` win detection correct.
- [ ] Draw detection correct.
- [ ] Full-column rejection correct, both for human clicks and AI move selection.

### Game feel
- [ ] AI thinking animation present and logically consistent with `ai_thinking`.
- [ ] Piece-drop animation present, no duplicate discs.
- [ ] Last-move highlight present and visually distinct from the winning-line highlight.
- [ ] Winning-line animation correctly tied to the actual final move (Phase 3/7).
- [ ] Turn indicator always accurate (`Your turn` / `AI thinking...` / `AI (Player 2) turn` / game-over text).

### Creativity
- [ ] AI personality/difficulty (Phase 1's `AI_CONFIGS`), algorithmically meaningful (differs by `n_iter`/`c_param`, not cosmetics).
- [ ] Live confidence visualization (Phase 14's bar chart).
- [ ] "Why this move?" explanation (Phase 9's `build_explanation_text`), sourced only from real stats.
- [ ] AI identity distinction (personality names shown in menu/debug panel; asset-based visuals if/when real files are added, Phase 5).
- [ ] Search telemetry (iteration count, search duration) in the debug panel.

### Assets
- [ ] `load_assets()` present, safe, called once; no invented filenames; game runs identically with or without an `assets/` directory.

### Performance
- [ ] UI remains responsive during every search (threaded, Phase 9).
- [ ] No unsafe cross-thread Pygame access.
- [ ] Iteration budgets are reasonable and named, not arbitrary/unbounded.

### Regression
- [ ] `Connect4State`, `MCTSNode`, `rollout`, and `mcts_search`'s loop body are byte-for-byte unmodified in control flow from the verified starter.
- [ ] No circular imports, no duplicate game-state systems.
- [ ] No new third-party dependencies (only stdlib `threading`/`os` added beyond the starter's `pygame`, `sys`, `math`, `random`).
- [ ] Any Part 1 (A*/frog) files that exist in the real project (outside this file's scope) remain completely untouched by this plan.

### Demo readiness
- [ ] Keybind legend always visible.
- [ ] A presenter can show Human vs AI, AI vs AI, per-column stats, chosen-column UCB, an actual winning move with its line highlighted, and at least one creativity feature — entirely from the running program, without reading source code.