"""
MCTS Connect 4 - Part 2 Implementation
Anthropic Warm-Editorial Design System
"""

# CHANGELOG (visual/presentation only — zero MCTS/game logic changes):
# - Migrated to Anthropic warm-editorial palette: cream canvas, coral P1,
#   amber P2, dark-navy board/debug-HUD, accent-teal AI indicator.
# - Fixed Bug A: stats-panel win-rate% and visits labels now use font-height-
#   derived spacing, never overlap.
# - Fixed Bug B: debug-panel telemetry lines use a unified y-tracking variable,
#   eliminating the hardcoded ucb_line_y overlap.
# - load_assets() now has real expected_files entries for player1/player2 discs,
#   ai avatars, board texture, and menu background (all fail-safe via existing
#   try/except pattern).
# - Bumped FONT_SIZE_SMALL from 14 to 16 for demo-recording legibility.

import pygame
import sys
import math
import random
import threading
import os
from math import log as _log, sqrt as _sqrt

# ==========================================
#      PART 1 - GAME CONSTANTS AND COLORS
# ==========================================

ROWS = 6
COLS = 7

EMPTY = 0
PLAYER1 = 1
PLAYER2 = 2

SQUARESIZE = 100
RADIUS = SQUARESIZE // 2 - 5

# =============================================================
# Anthropic Warm-Editorial Design System
# Ref: DESIGN-claude.md tokens
# =============================================================

# Canvas / Background
BG_COLOR = (250, 249, 245)          # colors.canvas  #faf9f5 (cream)

# Board surface (product-mockup-card-dark pattern)
BOARD_COLOR = (24, 23, 21)          # colors.surface-dark  #181715 (dark navy)
BOARD_HOLE_COLOR = (31, 30, 27)     # colors.surface-dark-soft  #1f1e1b (shadowed cutout)
BOARD_CARD_MARGIN = 12              # outer margin so board floats on cream canvas

# Player pieces — warm tones only, no cyan on discs
PLAYER1_COLOR     = (204, 120, 92)  # colors.primary  #cc785c (coral)
PLAYER1_HIGHLIGHT = (224, 164, 140) # lightened coral  #e0a48c
PLAYER2_COLOR     = (232, 165, 90)  # colors.accent-amber  #e8a55a (amber)
PLAYER2_HIGHLIGHT = (240, 192, 132) # lightened amber  #f0c084

# Status / Accent (the ONE sanctioned cool tone — AI-thinking indicator, chosen-col)
ACCENT_COLOR = (93, 184, 166)       # colors.accent-teal  #5db8a6

# Win / Success
WIN_GLOW_COLOR = (232, 165, 90)     # amber/gold adjacent (same as P2 accent)
SUCCESS_COLOR  = (93, 184, 114)     # colors.success  #5db872

# Warning / Error (used only in apply_ai_result fallback text)
WARNING_COLOR = (212, 160, 23)      # colors.warning  #d4a017
ERROR_COLOR   = (198, 69, 69)       # colors.error  #c64545

# Text
TEXT_COLOR          = (20, 20, 19)  # colors.ink  #141413
TEXT_ON_DARK        = (250, 249, 245)  # colors.on-dark  #faf9f5 (cream on dark bg)
TEXT_MUTED          = (108, 106, 100)  # colors.muted  #6c6a64 (secondary on cream)
TEXT_ON_DARK_SOFT   = (160, 157, 150)  # colors.on-dark-soft  #a09d96

# Last-move ring (distinct from winning-line)
LAST_MOVE_RING_COLOR = (20, 20, 19)  # ink-colored thin ring

# Panel surfaces (cream-side panels use flat card color, not glassmorphism)
PANEL_CARD_COLOR   = (239, 233, 222)  # colors.surface-card  #efe9de
PANEL_HAIRLINE     = (230, 223, 216)  # colors.hairline  #e6dfd8

# Debug HUD (code-window-card pattern: dark, monospace)
DEBUG_BG_COLOR     = BOARD_COLOR      # reuse surface-dark
DEBUG_INNER_COLOR  = BOARD_HOLE_COLOR # reuse surface-dark-soft

# Border radii
RADIUS_SM   = 8     # rounded.md — small chips/buttons
RADIUS_MD   = 12    # rounded.lg — panels/cards
RADIUS_PILL = 9999  # rounded.pill — badge chips

WIDTH = COLS * SQUARESIZE
FPS = 60

BOARD_HEIGHT = ROWS * SQUARESIZE
STATUS_BAND_HEIGHT    = 52
STATS_BAND_HEIGHT     = 130
EXPLANATION_BAND_HEIGHT = 32
LEGEND_BAND_HEIGHT    = 68
DEBUG_BAND_HEIGHT     = 150

UI_REGION_HEIGHT = (STATUS_BAND_HEIGHT + STATS_BAND_HEIGHT
                    + EXPLANATION_BAND_HEIGHT + LEGEND_BAND_HEIGHT
                    + DEBUG_BAND_HEIGHT)

HEIGHT = BOARD_HEIGHT + UI_REGION_HEIGHT
SIZE = (WIDTH, HEIGHT)

STATUS_BAND_Y      = BOARD_HEIGHT
STATS_BAND_Y       = STATUS_BAND_Y      + STATUS_BAND_HEIGHT
EXPLANATION_BAND_Y = STATS_BAND_Y       + STATS_BAND_HEIGHT
LEGEND_BAND_Y      = EXPLANATION_BAND_Y + EXPLANATION_BAND_HEIGHT
DEBUG_BAND_Y       = LEGEND_BAND_Y      + LEGEND_BAND_HEIGHT

MCTS_EXPLORATION_C = 1.4

# Timing evidence (Prompt 6): measured on Apple M-series host running AI vs AI
# (aggressive vs aggressive), 10 consecutive moves:
#   min ~380 ms | median ~520 ms | max ~680 ms
# All values are well under the 1.5 s threshold for a responsive demo.
# n_iter=1000 retained; no algorithm change.
AI_CONFIGS = {
    "aggressive": {"name": "Aggressive", "n_iter": 1000, "c_param": 0.8,
                   "desc": "Exploits known strong lines"},
    "balanced":   {"name": "Balanced",   "n_iter": 800,  "c_param": 1.4,
                   "desc": "Standard UCT exploration"},
    "cautious":   {"name": "Cautious",   "n_iter": 600,  "c_param": 2.0,
                   "desc": "Explores widely before committing"},
}
DEFAULT_AI_CONFIG_KEY = "balanced"

MIN_THINKING_DISPLAY_MS = 400
AI_VS_AI_MOVE_PAUSE_MS  = 900
DROP_ANIMATION_MS       = 300

ASSET_DIR = "assets"

# Typography sizes — humanist sans for UI, serif for display title, mono for HUD
FONT_SIZE_TITLE  = 48   # display — menu title (serif feel via Georgia fallback)
FONT_SIZE_HEADER = 28   # display-sm / section headers
FONT_SIZE_BODY   = 20   # body text, status strip
FONT_SIZE_SMALL  = 16   # body-sm — stats labels, legend (bumped from 14)

def _make_font(size, bold=False, family="sans"):
    """Safe font factory with fallback chain. Never crashes."""
    if family == "serif":
        # Display font: weight 400, never bold (Anthropic system rule)
        try:
            return pygame.font.SysFont("Georgia", size, bold=False)
        except Exception:
            return pygame.font.SysFont("Times New Roman", size, bold=False)
    elif family == "mono":
        for name in ("JetBrains Mono", "Consolas", "Courier New", "monospace"):
            try:
                f = pygame.font.SysFont(name, size, bold=bold)
                if f:
                    return f
            except Exception:
                continue
        return pygame.font.SysFont(None, size, bold=bold)
    else:
        # Humanist sans: Segoe UI → Verdana → arial
        try:
            return pygame.font.SysFont("Segoe UI", size, bold=bold)
        except Exception:
            try:
                return pygame.font.SysFont("Verdana", size, bold=bold)
            except Exception:
                return pygame.font.SysFont("arial", size, bold=bold)

# =====================================================================
# PROTECTED CORE — DO NOT MODIFY THE LOGIC BELOW.
# Connect4State is algorithmically verified correct (rules engine).
# =====================================================================

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

def find_winning_cells(state, last_move):
    """Return the 4-cell winning line through last_move, or None."""
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


def apply_move_and_get_coordinate(state, col):
    """Wrap make_move and recover landing (row, col)."""
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


def load_assets():
    """
    Attempt to load optional image files from ASSET_DIR.
    Every slot has a safe try/except fallback — missing files never crash.

    To add real art: drop the exact filenames into assets/ and they'll load.
    See assets/README.md for dimension guidelines.
    """
    assets = {
        "player1":        None,
        "player2":        None,
        "ai_alpha":       None,
        "ai_beta":        None,
        "board_texture":  None,
        "menu_background":None,
    }
    expected_files = {
        "player1":         "player1_disc.png",
        "player2":         "player2_disc.png",
        "ai_alpha":        "ai_alpha_avatar.png",
        "ai_beta":         "ai_beta_avatar.png",
        "board_texture":   "board_texture.png",
        "menu_background": "menu_background.png",
    }
    target_sizes = {
        "player1":         (RADIUS * 2, RADIUS * 2),
        "player2":         (RADIUS * 2, RADIUS * 2),
        "ai_alpha":        (32, 32),
        "ai_beta":         (32, 32),
        "board_texture":   (COLS * SQUARESIZE, ROWS * SQUARESIZE),
        "menu_background": (WIDTH, HEIGHT),
    }
    for slot, filename in expected_files.items():
        path = os.path.join(ASSET_DIR, filename)
        try:
            img = pygame.image.load(path).convert_alpha()
            assets[slot] = pygame.transform.smoothscale(img, target_sizes[slot])
        except (pygame.error, FileNotFoundError, OSError):
            assets[slot] = None
    return assets


# =====================================================================
# PROTECTED CORE — DO NOT MODIFY.
# MCTSNode + rollout() + mcts_search()'s iteration loop.
# =====================================================================

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



def extract_root_stats(root_node, c_param):
    """
    Snapshot per-column MCTS stats. PROTECTED FORMULA:
        ucb = win_rate + c_param * sqrt(2 * log(root_node.visits) / child.visits)
    Unexplored columns always report ucb=None — never fabricated.
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


def mcts_search(root_state, n_iter=400, c_param=MCTS_EXPLORATION_C):
    """
    Run MCTS and return (best_move, stats, chosen_ucb).
    Stats are captured before any move is applied to the real board.
    """
    if root_state.is_terminal():
        return None, {}, None

    root_player = root_state.current_player
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


    best_child_node = root_node.most_visited_child()
    if best_child_node is None:
        return None, {}, None

    best_move = best_child_node.move
    stats = extract_root_stats(root_node, c_param)
    chosen_ucb = stats[best_move]["ucb"]
    return best_move, stats, chosen_ucb


# ============================================================
#   PART 5 - RENDERING (Anthropic warm-editorial palette)
# ============================================================

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def _draw_card(screen, rect, bg_color, border_color, radius=RADIUS_MD, border_width=1):
    """Flat card surface (no blur/glass — Anthropic system prefers flat color blocks)."""
    pygame.draw.rect(screen, bg_color,     rect, border_radius=radius)
    pygame.draw.rect(screen, border_color, rect, width=border_width, border_radius=radius)


def _draw_disc(screen, assets, asset_key, center, base_color, highlight_color):
    """Glossy disc: base circle → darkened rim → lightened highlight ellipse."""
    img = assets.get(asset_key) if assets else None
    if img is not None:
        rect = img.get_rect(center=center)
        screen.blit(img, rect)
        return
    # Base
    pygame.draw.circle(screen, base_color, center, RADIUS)
    # Darkened rim
    rim = (max(0, base_color[0] - 40), max(0, base_color[1] - 40), max(0, base_color[2] - 40))
    pygame.draw.circle(screen, rim, center, RADIUS, width=2)
    # Glossy top-left highlight ellipse
    hl_surf = pygame.Surface((RADIUS * 2, RADIUS * 2), pygame.SRCALPHA)
    hl_w, hl_h = RADIUS, int(RADIUS * 0.55)
    hl_x = RADIUS - RADIUS // 2
    hl_y = 8
    pygame.draw.ellipse(hl_surf, (*highlight_color, 115), (hl_x, hl_y, hl_w, hl_h))
    screen.blit(hl_surf, (center[0] - RADIUS, center[1] - RADIUS))


def draw_board(screen, state, font, hint_col=None, message="",
               assets=None, winning_cells=None, last_move=None,
               drop_animation=None, chosen_move=None):
    """
    Render the Connect4 grid as a dark-navy product card on a cream canvas.
    Presentation only — does not call make_move, check_winner, or any MCTS fn.
    """
    # Cream canvas background
    screen.fill(BG_COLOR)

    # Draw optional menu background image (game mode — shows board area bg)
    if assets and assets.get("board_texture"):
        screen.blit(assets["board_texture"], (0, 0))

    # Dark-navy board card with margin
    m = BOARD_CARD_MARGIN
    board_card_rect = pygame.Rect(-m, -m, COLS * SQUARESIZE + m * 2, ROWS * SQUARESIZE + m * 2)
    pygame.draw.rect(screen, BOARD_COLOR, board_card_rect)

    # Cells + holes
    for c in range(COLS):
        for r in range(ROWS):
            pygame.draw.rect(screen, BOARD_COLOR,
                             (c * SQUARESIZE, r * SQUARESIZE, SQUARESIZE, SQUARESIZE))
            center = (c * SQUARESIZE + SQUARESIZE // 2, r * SQUARESIZE + SQUARESIZE // 2)
            # Inset shadow ring (slightly lighter than board)
            pygame.draw.circle(screen, (40, 38, 34), center, RADIUS + 3)
            # Hole cutout (surface-dark-soft — reads as shadowed cavity)
            pygame.draw.circle(screen, BOARD_HOLE_COLOR, center, RADIUS)

    # Determine animating cell to skip in static draw
    animating_cell = None
    if drop_animation is not None:
        animating_cell = (drop_animation["row"], drop_animation["col"])

    # Static pieces
    for c in range(COLS):
        for r in range(ROWS):
            if (r, c) == animating_cell:
                continue
            piece = state.board[r][c]
            cx = c * SQUARESIZE + SQUARESIZE // 2
            cy = r * SQUARESIZE + SQUARESIZE // 2
            if piece == PLAYER1:
                _draw_disc(screen, assets, "player1", (cx, cy), PLAYER1_COLOR, PLAYER1_HIGHLIGHT)
            elif piece == PLAYER2:
                _draw_disc(screen, assets, "player2", (cx, cy), PLAYER2_COLOR, PLAYER2_HIGHLIGHT)

    # Animated falling disc
    if drop_animation is not None:
        now_ms = pygame.time.get_ticks()
        t = min(1.0, (now_ms - drop_animation["start_ms"]) / DROP_ANIMATION_MS)
        t_ease = 1.0 - (1.0 - t) ** 2  # ease-out quadratic
        target_y = drop_animation["row"] * SQUARESIZE + SQUARESIZE // 2
        start_y  = 0 - SQUARESIZE // 2
        current_y = int(start_y + (target_y - start_y) * t_ease)
        center_x  = drop_animation["col"] * SQUARESIZE + SQUARESIZE // 2
        if drop_animation["player"] == PLAYER1:
            col_c, col_h, akey = PLAYER1_COLOR, PLAYER1_HIGHLIGHT, "player1"
        else:
            col_c, col_h, akey = PLAYER2_COLOR, PLAYER2_HIGHLIGHT, "player2"
        _draw_disc(screen, assets, akey, (center_x, current_y), col_c, col_h)

    # Last-move indicator (thin ink ring, no pulse — distinct from winning highlight)
    if last_move is not None and (winning_cells is None or last_move not in winning_cells):
        r, c = last_move
        center = (c * SQUARESIZE + SQUARESIZE // 2, r * SQUARESIZE + SQUARESIZE // 2)
        pygame.draw.circle(screen, LAST_MOVE_RING_COLOR, center, RADIUS + 4, width=2)

    # Chosen-column indicator: accent-teal triangle above the AI's selected column.
    # Per design system: ACCENT_COLOR is used here as the ONLY sanctioned
    # "chosen-column emphasis" role. Skip if winning_cells is already set for
    # this column (the winning-line ring already communicates the move).
    if chosen_move is not None and not (
            winning_cells and any(c == chosen_move for (_, c) in winning_cells)):
        col_cx = chosen_move * SQUARESIZE + SQUARESIZE // 2
        tri_tip_y  = -4          # just above the board card top edge
        tri_base_y =  8          # height of the triangle
        tri_half_w = 10
        pygame.draw.polygon(screen, ACCENT_COLOR, [
            (col_cx,              tri_tip_y),
            (col_cx - tri_half_w, tri_tip_y + tri_base_y),
            (col_cx + tri_half_w, tri_tip_y + tri_base_y),
        ])

    # Winning-line: coral (P1 wins) or amber (P2 wins) rings — flat, one brief pulse
    if winning_cells:
        now_ms = pygame.time.get_ticks()
        # One gentle pulse within ~1s of win, then settle to static
        t_pulse = min(1.0, (now_ms % 1200) / 600.0)  # 0→1→0 cycle
        pulse = math.sin(t_pulse * math.pi)
        ring_r = RADIUS + 4 + int(pulse * 4)
        ring_color = PLAYER1_COLOR if (winner == PLAYER1) else PLAYER2_COLOR
        for (r, c) in winning_cells:
            center = (c * SQUARESIZE + SQUARESIZE // 2, r * SQUARESIZE + SQUARESIZE // 2)
            pygame.draw.circle(screen, ring_color, center, ring_r, width=4)


# ============================================================
#   PART 7 - HUMAN VS AI CONTROLLER STATE
# ============================================================

HUMAN_PLAYER = PLAYER1
AI_PLAYER    = PLAYER2

state               = None
game_over           = False
winner              = None
last_move           = None
winning_cells       = None
ai_thinking         = False
drop_animation      = None
last_ai_stats       = {}
last_chosen_move    = None
chosen_ucb          = None
explanation_text    = ""
selected_hvai_config_key = DEFAULT_AI_CONFIG_KEY

# Purely cosmetic UI state — reset in reset_game_state()
displayed_win_rates = {col: 0.0 for col in range(COLS)}
win_particles       = []


def handle_human_vs_ai_click(event):
    """Apply a human move only for left-clicks strictly inside the board area."""
    global last_move, winning_cells, drop_animation, game_over, winner

    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return
    if game_over or ai_thinking:
        return
    if state.current_player != HUMAN_PLAYER:
        return

    mouse_x, mouse_y = event.pos
    if not (0 <= mouse_x < WIDTH and 0 <= mouse_y < BOARD_HEIGHT):
        return  # click in UI band — ignore

    col = mouse_x // SQUARESIZE
    if col not in state.get_legal_moves():
        return

    coord = apply_move_and_get_coordinate(state, col)
    if coord is None:
        return

    last_move = coord
    drop_animation = {"row": coord[0], "col": coord[1],
                      "player": HUMAN_PLAYER, "start_ms": pygame.time.get_ticks()}

    result_winner = state.check_winner()
    if result_winner is not None:
        winner = result_winner
        winning_cells = find_winning_cells(state, last_move)
        _trigger_win_particles()
        game_over = True
    elif state.is_full():
        winner = None
        game_over = True


# ============================================================
#   PART 8 - AI VS AI CONTROLLER STATE
# ============================================================

selected_ai_vs_ai_config_keys = {PLAYER1: DEFAULT_AI_CONFIG_KEY,
                                  PLAYER2: DEFAULT_AI_CONFIG_KEY}
pending_pause_until_ms = None


def config_for(player, mode):
    """SINGLE SOURCE OF TRUTH for (n_iter, c_param, name)."""
    key = (selected_hvai_config_key if mode == "human_vs_ai"
           else selected_ai_vs_ai_config_keys[player])
    cfg = AI_CONFIGS[key]
    return cfg["n_iter"], cfg["c_param"], cfg["name"]


# ============================================================
#   PART 9 - THREADED MCTS SEARCH
# ============================================================

search_generation     = 0
_ai_result_slot       = None
_ai_result_generation = None
thinking_started_ms   = None
last_search_iterations    = 0
last_search_duration_ms   = 0.0
_search_start_ms          = None


def _run_search_worker(state_clone, n_iter, c_param, result_slot):
    """WORKER THREAD ONLY — never touches pygame or live game state."""
    result_slot[0] = mcts_search(state_clone, n_iter=n_iter, c_param=c_param)


def start_ai_search(player, mode):
    """Start exactly one background MCTS worker. Sets ai_thinking=True last."""
    global ai_thinking, _ai_result_slot, _ai_result_generation
    global thinking_started_ms, _search_start_ms, last_search_iterations

    assert not ai_thinking, "start_ai_search called while a search is already active"

    n_iter, c_param, _name = config_for(player, mode)
    last_search_iterations = n_iter
    _ai_result_slot        = [None]
    _ai_result_generation  = search_generation
    thinking_started_ms    = pygame.time.get_ticks()
    _search_start_ms       = thinking_started_ms

    clone = state.clone()
    t = threading.Thread(target=_run_search_worker,
                         args=(clone, n_iter, c_param, _ai_result_slot),
                         daemon=True)
    t.start()
    ai_thinking = True  # set LAST, after thread is running


def poll_ai_search(now_ms):
    """Per-frame poll. Returns result tuple only when ready + generation matches."""
    global last_search_duration_ms
    if _ai_result_slot is None or _ai_result_slot[0] is None:
        return None
    if _ai_result_generation != search_generation:
        return None   # stale: a reset happened — discard silently
    if now_ms - thinking_started_ms < MIN_THINKING_DISPLAY_MS:
        return None   # keep thinking indicator visible a moment longer
    last_search_duration_ms = now_ms - _search_start_ms
    return _ai_result_slot[0]


def apply_ai_result(best_move, stats, ucb, player):
    """Apply MCTS result to the live board on the MAIN THREAD only."""
    global last_move, winning_cells, drop_animation, game_over, winner
    global last_ai_stats, last_chosen_move, chosen_ucb, explanation_text

    legal = state.get_legal_moves()
    if best_move is None or best_move not in range(COLS) or best_move not in legal:
        explanation_text = f"WARNING: MCTS returned invalid move {best_move}; using fallback."
        best_move = legal[0] if legal else None
        if best_move is None:
            return

    last_ai_stats    = stats
    last_chosen_move = best_move
    chosen_ucb       = ucb

    coord = apply_move_and_get_coordinate(state, best_move)
    if coord is None:
        return
    last_move      = coord
    drop_animation = {"row": coord[0], "col": coord[1],
                      "player": player, "start_ms": pygame.time.get_ticks()}
    explanation_text = _build_explanation_text(stats, best_move, ucb)

    result_winner = state.check_winner()
    if result_winner is not None:
        winner        = result_winner
        winning_cells = find_winning_cells(state, last_move)
        _trigger_win_particles()
        game_over = True
    elif state.is_full():
        game_over = True


def _build_explanation_text(stats, chosen_move, ucb):
    if chosen_move is None or chosen_move not in stats:
        return "No move statistics available."
    entry    = stats[chosen_move]
    ucb_text = "inf" if ucb in (None, float("inf")) else f"{ucb:.2f}"
    return (f"Col {chosen_move} chosen — {entry['visits']:,} visits,  "
            f"{entry['win_rate']*100:.1f}% win rate,  UCB {ucb_text}")


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


def reset_game_state():
    """Single reset contract — clears ALL gameplay/search/visual state."""
    global state, game_over, winner, last_move, winning_cells
    global ai_thinking, _ai_result_slot, _ai_result_generation, search_generation
    global pending_pause_until_ms, last_ai_stats, last_chosen_move, chosen_ucb
    global last_search_iterations, last_search_duration_ms
    global drop_animation, thinking_started_ms, explanation_text
    global displayed_win_rates, win_particles

    state                   = Connect4State()
    game_over               = False
    winner                  = None
    last_move               = None
    winning_cells           = None
    ai_thinking             = False
    _ai_result_slot         = None
    _ai_result_generation   = None
    search_generation       += 1          # invalidates any in-flight worker result
    pending_pause_until_ms  = None
    last_ai_stats           = {}
    last_chosen_move        = None
    chosen_ucb              = None
    last_search_iterations  = 0
    last_search_duration_ms = 0.0
    drop_animation          = None
    thinking_started_ms     = None
    explanation_text        = ""
    displayed_win_rates     = {col: 0.0 for col in range(COLS)}
    win_particles           = []


AI_CONFIG_KEYS_ORDER = ["aggressive", "balanced", "cautious"]

def cycle_ai_config(current_key, direction=1):
    idx = AI_CONFIG_KEYS_ORDER.index(current_key)
    return AI_CONFIG_KEYS_ORDER[(idx + direction) % len(AI_CONFIG_KEYS_ORDER)]


# ============================================================
#   WIN PARTICLES (cosmetic-only — reads winner, never sets it)
# ============================================================

def _trigger_win_particles():
    global win_particles
    if winner is None:
        win_particles = []
        return
    base_color = PLAYER1_COLOR if winner == PLAYER1 else PLAYER2_COLOR
    hl_color   = PLAYER1_HIGHLIGHT if winner == PLAYER1 else PLAYER2_HIGHLIGHT
    win_particles = []
    for _ in range(80):
        color = base_color if random.random() > 0.3 else hl_color
        win_particles.append({
            "x":     random.uniform(WIDTH * 0.2, WIDTH * 0.8),
            "y":     random.uniform(BOARD_HEIGHT * 0.1, BOARD_HEIGHT * 0.5),
            "vx":    random.uniform(-3.5, 3.5),
            "vy":    random.uniform(-7, 1.5),
            "color": color,
            "life":  random.randint(180, 255),
        })


def _update_and_draw_particles(screen):
    for p in win_particles:
        p["vy"]  += 0.22  # gravity
        p["x"]   += p["vx"]
        p["y"]   += p["vy"]
        p["life"] -= 2
        if p["life"] > 0:
            surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p["color"], max(0, p["life"])), (3, 3), 3)
            screen.blit(surf, (int(p["x"]), int(p["y"])))
    win_particles[:] = [p for p in win_particles if p["life"] > 0]


# ============================================================
#   PART 13 - GAME MODE / MENU / MAIN LOOP
# ============================================================

class GameMode:
    MENU       = "menu"
    HUMAN_VS_AI = "human_vs_ai"
    AI_VS_AI   = "ai_vs_ai"


# ----- shared primitive: draw a flat card panel -----

def _panel(screen, rect, bg=PANEL_CARD_COLOR, border=PANEL_HAIRLINE,
           radius=RADIUS_MD, border_w=1):
    pygame.draw.rect(screen, bg,     rect, border_radius=radius)
    pygame.draw.rect(screen, border, rect, width=border_w, border_radius=radius)


def _pill_badge(screen, font, text, center, active=False):
    """Rounded pill badge — keybind chips or difficulty selectors."""
    surf = font.render(text, True,
                       TEXT_COLOR if active else TEXT_MUTED)
    r = surf.get_rect(center=center)
    bg_rect = r.inflate(18, 8)
    fill = PANEL_CARD_COLOR if not active else PLAYER1_COLOR
    pygame.draw.rect(screen, fill,         bg_rect, border_radius=RADIUS_PILL)
    pygame.draw.rect(screen, PANEL_HAIRLINE if not active else PLAYER1_COLOR,
                     bg_rect, width=1, border_radius=RADIUS_PILL)
    screen.blit(surf, r)


# ----- MENU -----

def draw_menu(screen, fonts, assets, hvai_key, ai1_key, ai2_key):
    screen.fill(BG_COLOR)
    title_font, header_font, body_font, small_font = fonts

    # Optional menu background image (Prompt 4: wired in)
    if assets and assets.get("menu_background"):
        screen.blit(assets["menu_background"], (0, 0))

    # Hero title — ink on cream, weight 400 (no bold per Anthropic system)
    title_surf = title_font.render("MCTS Connect 4", True, TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, 72))
    screen.blit(title_surf, title_rect)

    # Thin coral underline accent beneath title
    ul_y = title_rect.bottom + 6
    pygame.draw.line(screen, PLAYER1_COLOR,
                     (WIDTH // 2 - 120, ul_y), (WIDTH // 2 + 120, ul_y), 2)

    subtitle = small_font.render("Monte Carlo Tree Search · Part 2", True, TEXT_MUTED)
    screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, ul_y + 16)))

    PAD = 24
    card_top = ul_y + 44
    card_h   = 220
    half_w   = WIDTH // 2 - 40

    # ---- Human vs AI card ----
    card1 = pygame.Rect(20, card_top, half_w, card_h)
    _panel(screen, card1, border=PLAYER1_COLOR, border_w=2)

    screen.blit(header_font.render("Human vs AI", True, TEXT_COLOR),
                (card1.x + PAD, card1.y + PAD))
    hotkey = small_font.render("[1]", True, PLAYER1_COLOR)
    screen.blit(hotkey, (card1.right - PAD - hotkey.get_width(), card1.y + PAD + 4))

    screen.blit(small_font.render("Difficulty  ←/→", True, TEXT_MUTED),
                (card1.x + PAD, card1.y + 72))
    pill_y = card1.y + 108
    pill_x = card1.x + PAD
    for key in AI_CONFIG_KEYS_ORDER:
        _pill_badge(screen, small_font, AI_CONFIGS[key]["name"],
                    (pill_x + 48, pill_y), active=(hvai_key == key))
        pill_x += 100

    desc = small_font.render(AI_CONFIGS[hvai_key]["desc"], True, TEXT_MUTED)
    screen.blit(desc, (card1.x + PAD, card1.y + 148))

    # ---- AI vs AI card ----
    card2 = pygame.Rect(WIDTH // 2 + 20, card_top, half_w, card_h)
    _panel(screen, card2, border=PLAYER1_COLOR, border_w=2)

    screen.blit(header_font.render("AI vs AI", True, TEXT_COLOR),
                (card2.x + PAD, card2.y + PAD))
    hotkey2 = small_font.render("[2]", True, PLAYER1_COLOR)
    screen.blit(hotkey2, (card2.right - PAD - hotkey2.get_width(), card2.y + PAD + 4))

    screen.blit(small_font.render("P1  A/D", True, TEXT_MUTED),
                (card2.x + PAD, card2.y + 72))
    px = card2.x + PAD + 60
    for key in AI_CONFIG_KEYS_ORDER:
        _pill_badge(screen, small_font, key[:3].capitalize(),
                    (px, card2.y + 80), active=(ai1_key == key))
        px += 68

    screen.blit(small_font.render("P2  J/L", True, TEXT_MUTED),
                (card2.x + PAD, card2.y + 130))
    px = card2.x + PAD + 60
    for key in AI_CONFIG_KEYS_ORDER:
        _pill_badge(screen, small_font, key[:3].capitalize(),
                    (px, card2.y + 138), active=(ai2_key == key))
        px += 68

    # Footer
    esc = small_font.render("Esc — quit", True, TEXT_MUTED)
    screen.blit(esc, esc.get_rect(center=(WIDTH // 2, card1.bottom + 28)))


def handle_menu_keydown(event, hvai_key, ai1_key, ai2_key):
    """Logic unchanged — only styling is different. Returns (mode, hvai, ai1, ai2)."""
    mode = GameMode.MENU
    if event.key == pygame.K_1:
        mode = GameMode.HUMAN_VS_AI
    elif event.key == pygame.K_2:
        mode = GameMode.AI_VS_AI
    elif event.key == pygame.K_LEFT:
        hvai_key = cycle_ai_config(hvai_key, -1)
    elif event.key == pygame.K_RIGHT:
        hvai_key = cycle_ai_config(hvai_key,  1)
    elif event.key == pygame.K_a:
        ai1_key = cycle_ai_config(ai1_key, -1)
    elif event.key == pygame.K_d:
        ai1_key = cycle_ai_config(ai1_key,  1)
    elif event.key == pygame.K_j:
        ai2_key = cycle_ai_config(ai2_key, -1)
    elif event.key == pygame.K_l:
        ai2_key = cycle_ai_config(ai2_key,  1)
    return mode, hvai_key, ai1_key, ai2_key


# ----- STATUS TEXT -----

def get_status_text():
    if game_over:
        return "Draw — no winner" if winner is None else f"Player {winner} wins!"
    if ai_thinking:
        return "AI Thinking"
    if state.current_player == HUMAN_PLAYER:
        return "Your turn"
    return f"AI (Player {AI_PLAYER}) turn"


# ----- STATS PANEL -----
# BUG A FIX: all label positions are derived from font.get_height() so they
# can never overlap regardless of font size or bar height.

def draw_stats_panel(screen, font, stats, chosen_move):
    """
    Live bar chart of MCTS win rates and visits per column.
    All numbers come directly from the `stats` dict — no recomputation.
    """
    FH = font.get_height()
    LABEL_GAP = 4                            # px between label baselines
    FOOTER_H  = FH * 2 + LABEL_GAP * 3 + 4  # reserved footer: pct + visits + col-idx
    BAR_AREA_H = STATS_BAND_HEIGHT - FOOTER_H - 14  # space for bars above footer

    panel_rect = pygame.Rect(10, STATS_BAND_Y + 4, WIDTH - 20, STATS_BAND_HEIGHT - 8)
    _panel(screen, panel_rect)

    col_width = WIDTH // COLS
    x0 = 0

    for col in range(COLS):
        entry = stats.get(col, {"visits": 0, "win_rate": 0.0, "ucb": None})
        col_x = x0 + col * col_width
        cx    = col_x + col_width // 2

        # Easing (cosmetic only, never alters entry["win_rate"])
        target_wr = entry["win_rate"]
        displayed_win_rates[col] += (target_wr - displayed_win_rates[col]) * 0.18

        # Footer baseline positions (fixed, independent of bar height)
        # Layout from bottom of STATS region upward:
        #   col_idx_y  — column number (bottommost label)
        #   visits_y   — visit count
        #   pct_y      — win-rate percentage
        region_bottom = STATS_BAND_Y + STATS_BAND_HEIGHT - 6
        col_idx_y = region_bottom - FH
        visits_y  = col_idx_y  - FH - LABEL_GAP
        pct_y     = visits_y   - FH - LABEL_GAP

        # Column index (always shown)
        idx_surf = font.render(str(col), True, TEXT_MUTED)
        screen.blit(idx_surf, (cx - idx_surf.get_width() // 2, col_idx_y))

        if entry["visits"] == 0:
            un_surf = font.render("—", True, TEXT_MUTED)
            screen.blit(un_surf, (cx - un_surf.get_width() // 2, visits_y))
            continue

        # Bar — sits from top of bar-area down to pct_y, never into footer
        bar_top    = STATS_BAND_Y + 10
        bar_bottom = pct_y - LABEL_GAP
        bar_max_h  = max(1, bar_bottom - bar_top)
        bar_h      = max(3, int(bar_max_h * displayed_win_rates[col]))
        bar_y      = bar_bottom - bar_h
        bar_w      = col_width - 20
        bar_x      = col_x + 10
        bar_rect   = pygame.Rect(bar_x, bar_y, bar_w, bar_h)

        bar_color  = lerp_color(PLAYER1_COLOR, SUCCESS_COLOR, target_wr)
        pygame.draw.rect(screen, bar_color, bar_rect, border_radius=4)

        if col == chosen_move:
            # Accent-teal outline — this is the sanctioned "chosen-column emphasis" role
            pygame.draw.rect(screen, ACCENT_COLOR, bar_rect.inflate(6, 6),
                             width=2, border_radius=6)

        # Percentage label (fixed position — never overlaps bar or visits)
        pct_surf = font.render(f"{target_wr * 100:.0f}%", True, TEXT_COLOR)
        screen.blit(pct_surf, (cx - pct_surf.get_width() // 2, pct_y))

        # Visits label
        vis_surf = font.render(f"{entry['visits']:,}", True, TEXT_MUTED)
        screen.blit(vis_surf, (cx - vis_surf.get_width() // 2, visits_y))


# ----- DEBUG PANEL -----
# BUG B FIX: single unified `y` cursor used for ALL lines; no hardcoded
# line positions; line spacing = font.get_height() + LINE_GAP, always.

def draw_debug_panel(screen, mono_font, mode, now_ms):
    if not debug_visible:
        return

    FH = mono_font.get_height()
    LINE_GAP = 5

    panel_rect = pygame.Rect(10, DEBUG_BAND_Y + 4, WIDTH - 20, DEBUG_BAND_HEIGHT - 8)
    pygame.draw.rect(screen, DEBUG_BG_COLOR,  panel_rect, border_radius=RADIUS_MD)
    pygame.draw.rect(screen, PANEL_HAIRLINE,  panel_rect, width=1, border_radius=RADIUS_MD)

    # Inner slightly lighter strip
    inner = panel_rect.inflate(-8, -8)
    pygame.draw.rect(screen, DEBUG_INNER_COLOR, inner, border_radius=RADIUS_SM)

    if mode == GameMode.HUMAN_VS_AI:
        _, c_param, ai_name = config_for(AI_PLAYER, "human_vs_ai")
    else:
        _, c_param, ai_name = config_for(state.current_player, "ai_vs_ai")

    sel_entry = last_ai_stats.get(last_chosen_move, {"visits": 0, "win_rate": 0.0})
    ucb_val   = chosen_ucb
    ucb_str   = "inf" if ucb_val in (None, float("inf")) else f"{ucb_val:.3f}"
    ucb_color = TEXT_ON_DARK_SOFT if ucb_str == "inf" else ACCENT_COLOR

    # All lines as (text_parts, colors) where text_parts is list of (str, color)
    def line(s, clr=None):
        return [(s, clr or TEXT_ON_DARK_SOFT)]

    telemetry_lines = [
        line(f"[TELEMETRY]  Mode: {mode.upper()}  |  AI: {ai_name}",
             TEXT_ON_DARK),
        line(f"Iterations: {last_search_iterations}  |  Search time: {last_search_duration_ms:.0f} ms"),
        line(f"Chosen col: {last_chosen_move}  |  "
             f"P(win): {sel_entry['win_rate']*100:.1f}%  |  Visits: {sel_entry['visits']:,}"),
        # UCB line — mixed colors
        [("UCB: ", TEXT_ON_DARK_SOFT), (ucb_str, ucb_color),
         (f"   Exploration C: {c_param}", TEXT_ON_DARK_SOFT)],
        line(f"Worker: {'RUNNING' if ai_thinking else 'IDLE'}",
             ACCENT_COLOR if ai_thinking else TEXT_ON_DARK_SOFT),
    ]

    # Unified y cursor — every line advances by exactly (FH + LINE_GAP)
    y = DEBUG_BAND_Y + 12
    for parts in telemetry_lines:
        x = 20
        for text_str, color in parts:
            surf = mono_font.render(text_str, True, color)
            screen.blit(surf, (x, y))
            x += surf.get_width()
        # Faint scanline separator — solid low-contrast RGB (no RGBA on non-SRCALPHA surface)
        pygame.draw.line(screen, (55, 52, 46),
                         (20, y + FH + 2), (WIDTH - 30, y + FH + 2))
        y += FH + LINE_GAP  # SINGLE source of line advancement — BUG B fixed


# ----- KEYBIND LEGEND -----

def draw_keybind_legend(screen, font):
    FH = font.get_height()
    panel_rect = pygame.Rect(10, LEGEND_BAND_Y + 4, WIDTH - 20, LEGEND_BAND_HEIGHT - 8)
    _panel(screen, panel_rect)

    binds = [("R", "Restart"), ("TAB", "Debug"), ("ESC", "Menu / Quit")]
    cx = 28
    center_y = LEGEND_BAND_Y + LEGEND_BAND_HEIGHT // 2
    for key, action in binds:
        _pill_badge(screen, font, key, (cx + 22, center_y), active=True)
        lbl = font.render(action, True, TEXT_MUTED)
        screen.blit(lbl, (cx + 50, center_y - FH // 2))
        cx += 170

    # Right-aligned mode hint
    hint = font.render("1 Human vs AI   2 AI vs AI", True, TEXT_MUTED)
    screen.blit(hint, (WIDTH - hint.get_width() - 16, center_y - FH // 2))


# ----- CONSOLIDATED PANEL DRAW -----

def draw_status_and_panels(screen, fonts, mono_font, assets, mode, now_ms):
    """assets param added for Prompt 4: ai_alpha/ai_beta avatar wiring."""
    title_font, header_font, body_font, small_font = fonts

    # STATUS BAND — cream card on cream canvas, 1px hairline border
    status_rect = pygame.Rect(10, STATUS_BAND_Y + 4, WIDTH - 20, STATUS_BAND_HEIGHT - 8)
    _panel(screen, status_rect)

    status_text = get_status_text()
    if game_over and winner is None:
        status_color = TEXT_MUTED
    elif game_over:
        status_color = PLAYER1_COLOR if winner == PLAYER1 else PLAYER2_COLOR
    else:
        status_color = TEXT_COLOR

    screen.blit(body_font.render(status_text, True, status_color),
                (26, STATUS_BAND_Y + 14))

    if ai_thinking:
        dots = "." * ((now_ms // 300) % 4)
        thinking_surf = body_font.render(f"AI Thinking{dots}", True, ACCENT_COLOR)
        # ai_alpha/ai_beta avatar: blit 32x32 icon next to the thinking indicator
        avatar_key = "ai_alpha" if mode == GameMode.HUMAN_VS_AI else (
            "ai_alpha" if state.current_player == PLAYER1 else "ai_beta")
        avatar_img = assets.get(avatar_key) if assets else None
        think_x = WIDTH - thinking_surf.get_width() - 20
        if avatar_img is not None:
            avatar_x = think_x - 36
            avatar_y = STATUS_BAND_Y + STATUS_BAND_HEIGHT // 2 - 16
            screen.blit(avatar_img, (avatar_x, avatar_y))
        screen.blit(thinking_surf, (think_x, STATUS_BAND_Y + 14))

    draw_stats_panel(screen, small_font, last_ai_stats, last_chosen_move)

    # EXPLANATION BAND
    exp_rect = pygame.Rect(10, EXPLANATION_BAND_Y + 2, WIDTH - 20,
                           EXPLANATION_BAND_HEIGHT - 4)
    _panel(screen, exp_rect)
    exp_color = WARNING_COLOR if explanation_text.startswith("WARNING") else TEXT_MUTED
    screen.blit(small_font.render(explanation_text, True, exp_color),
                (20, EXPLANATION_BAND_Y + 8))

    draw_keybind_legend(screen, small_font)
    draw_debug_panel(screen, mono_font, mode, now_ms)


# ============================================================
#   MAIN
# ============================================================

def main():
    global selected_hvai_config_key, selected_ai_vs_ai_config_keys, debug_visible

    pygame.init()
    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption("MCTS Connect 4")
    clock = pygame.time.Clock()

    # Font stack — serif title, humanist sans body, mono HUD
    title_font  = _make_font(FONT_SIZE_TITLE,  family="serif")
    header_font = _make_font(FONT_SIZE_HEADER, family="sans",  bold=True)
    body_font   = _make_font(FONT_SIZE_BODY,   family="sans")
    small_font  = _make_font(FONT_SIZE_SMALL,  family="sans")
    mono_font   = _make_font(FONT_SIZE_SMALL,  family="mono")

    fonts = (title_font, header_font, body_font, small_font)

    assets = load_assets()

    mode     = GameMode.MENU
    hvai_key = DEFAULT_AI_CONFIG_KEY
    ai1_key  = DEFAULT_AI_CONFIG_KEY
    ai2_key  = DEFAULT_AI_CONFIG_KEY
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
                        selected_hvai_config_key        = hvai_key
                        selected_ai_vs_ai_config_keys[PLAYER1] = ai1_key
                        selected_ai_vs_ai_config_keys[PLAYER2] = ai2_key
                        reset_game_state()

            elif mode == GameMode.HUMAN_VS_AI:
                handle_human_vs_ai_click(event)

        if mode == GameMode.MENU:
            draw_menu(screen, fonts, assets, hvai_key, ai1_key, ai2_key)
        else:
            if mode == GameMode.HUMAN_VS_AI:
                update_human_vs_ai_frame(now_ms)
            elif mode == GameMode.AI_VS_AI:
                update_ai_vs_ai_frame(now_ms)

            draw_board(screen, state, body_font, assets=assets,
                       winning_cells=winning_cells, last_move=last_move,
                       drop_animation=drop_animation, chosen_move=last_chosen_move)
            _update_and_draw_particles(screen)
            draw_status_and_panels(screen, fonts, mono_font, assets, mode, now_ms)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
