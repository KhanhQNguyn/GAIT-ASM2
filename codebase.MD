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
part1/
  entities/
    fly.py
    frog.py
    snake.py
  codebase.MD
  debug_state.py
  main.py
  pathfinding.py
  settings.py
  steering.py
  utils.py
  world.py
part2/
  connect4_mcts.py
  startercodeassignment2.MD
README.md
</directory_structure>

<files>
This section contains the contents of the repository's files.

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

<file path="part1/entities/fly.py">
# ============================================================================
# fly.py
# Purpose
#   Autonomous flocking agent with a small FSM.
#   States: Flock, Fleeing, Idle.
#   Flock uses boids separation, cohesion, alignment.
#   Fleeing uses flee or the new evade behavior.
#   Idle uses a gentle wander to drift when far from danger.
# Update order
#   Compute state transitions from triggers, then apply the behavior for state.
# ============================================================================

import random
from enum import Enum, auto
import pygame
from pygame.math import Vector2 as V2
import settings
from settings import (
    WIDTH, HEIGHT, WHITE, YELLOW, PURPLE,
    FLY_RADIUS, FLY_SPEED, NEIGHBOR_RADIUS,
    ANCHOR_WEIGHT, FROG_SPEED
)
from utils import limit, draw_debug_overlay
import debug_state
from steering import (
    boids_separation, boids_cohesion, boids_alignment,
    flee, evade, wander_force, seek
)

class FlyState(Enum):
    Flock   = auto()
    Fleeing = auto()
    Idle    = auto()

class Fly:
    def __init__(self, pos):
        self.pos = V2(pos)
        self.vel = V2(random.uniform(-1, 1), random.uniform(-1, 1))
        if self.vel.length_squared() == 0:
            self.vel = V2(1, 0)
        self.vel.scale_to_length(FLY_SPEED * 0.5)

        self.radius = FLY_RADIUS
        self.state = FlyState.Flock

        # Timers and cached values
        self.scare_timer = 0.0   # counts down while nervous before calming
        self.idle_timer  = 0.0   # time spent far from frog
        self._catching_up = False  # True while hurrying to merge into a bigger flock
        self._rng_seed   = random.randint(0, 999999)
        self._debug_neighbors = []   # cached neighbor list for debug neighbor-link drawing

    def sense_bubbles_close(self, bubbles, r):
        """Return True if any bubble is within range r of the fly."""
        for b in bubbles:
            if (b.pos - self.pos).length_squared() <= r * r:
                return True
        return False

    def _set_state(self, new_state):
        """Switch FSM state and log the transition when it actually changes."""
        if new_state != self.state:
            debug_state.log_transition("Fly", id(self) % 1000, self.state.name, new_state.name)
        self.state = new_state

    def update(self, dt, flies, frog, bounds_rect, bubbles, neighbor_counts=None, neighbors=None, neighbor_ids=None):
        """
        Update FSM and behavior. Flies use perception to switch states.
        Parameters
          flies: list of all flies for neighborhood queries
          frog:  player agent used as a threat source
          bounds_rect: world rectangle for anchor force and containment
          bubbles: list of active bubbles to trigger panic
        """

        # Perception radii and timers for the FSM
        BubbleFleeRange  = settings.FLY_BUBBLE_FLEE_RANGE
        StopFleeingRange = settings.FLY_CALM_RANGE
        IdleDistance     = settings.FLY_IDLE_DISTANCE
        IdleDelay        = settings.FLY_IDLE_DELAY

        # Triggers based on the frog and bubbles
        dist_to_frog = (frog.pos - self.pos).length()
        scared_by_frog   = dist_to_frog < settings.FLY_SCARED_RANGE
        scared_by_bubble = self.sense_bubbles_close(bubbles, BubbleFleeRange)

        # Cheap neighbor-presence check: true if any other fly is within NEIGHBOR_RADIUS
        has_nearby_flockmate = bool(neighbors)

        # ---------------- FSM transitions ----------------
        if self.state == FlyState.Flock:
            if scared_by_frog or scared_by_bubble:
                self._set_state(FlyState.Fleeing)
                self.scare_timer = settings.FLY_SCARE_TIMER
                # One-time velocity kick directly away from threat
                burst_dir = self.pos - frog.pos
                if burst_dir.length_squared() > 0:
                    burst_dir = burst_dir.normalize()
                else:
                    burst_dir = V2(0, -1)
                self.vel += burst_dir * settings.FLEE_BURST_STRENGTH
            else:
                if dist_to_frog > IdleDistance:
                    self.idle_timer += dt
                    if self.idle_timer >= IdleDelay:
                        self._set_state(FlyState.Idle)
                else:
                    self.idle_timer = 0.0

        elif self.state == FlyState.Fleeing:
            calm = dist_to_frog > StopFleeingRange and not self.sense_bubbles_close(bubbles, StopFleeingRange)
            if calm:
                self.scare_timer -= dt
                if self.scare_timer <= 0:
                    self._set_state(FlyState.Flock)
                    self.idle_timer = 0.0
            else:
                self.scare_timer = settings.FLY_SCARE_TIMER

        elif self.state == FlyState.Idle:
            if scared_by_frog or scared_by_bubble:
                self._set_state(FlyState.Fleeing)
                self.scare_timer = settings.FLY_SCARE_TIMER
                burst_dir = self.pos - frog.pos
                if burst_dir.length_squared() > 0:
                    burst_dir = burst_dir.normalize()
                else:
                    burst_dir = V2(0, -1)
                self.vel += burst_dir * settings.FLEE_BURST_STRENGTH
            elif dist_to_frog <= IdleDistance:
                self._set_state(FlyState.Flock)
                self.idle_timer = 0.0

        # ---------------- State behaviours ----------------
        if self.state == FlyState.Flock:
            # Neighbor list and neighbor-id set are precomputed once per frame in main.py
            # (single O(N^2) pass shared by every fly) and passed in here — no need to
            # rebuild them per-fly anymore.
            neighbors = neighbors if neighbors is not None else []
            neighbor_ids = neighbor_ids if neighbor_ids is not None else set()
            self._debug_neighbors = neighbors   # cache for debug drawing

            self._catching_up = False  # will be set True only if we decide to catch up below

            my_group_size = len(neighbors)
            best_bigger = None
            best_bigger_size = my_group_size

            # Only genuinely small/isolated groups should ever consider catching up —
            # density variation inside an already-joined flock should not re-trigger this
            # Only a genuinely small-but-real flock (not a lone straggler or a pair) should
            # actively hurry toward a meaningfully bigger one nearby. A lone fly or pair just
            # flocks normally and merges naturally whenever it happens to encounter a group —
            # no active cross-map hunting for those.
            if (neighbor_counts is not None
                    and settings.CATCHUP_MIN_OWN_GROUP <= my_group_size <= settings.CATCHUP_MAX_OWN_GROUP):
                for f in flies:
                    if f is self:
                        continue
                    # Skip flies already in my own neighbor set — cohesion handles them
                    if id(f) in neighbor_ids:
                        continue
                    d = (f.pos - self.pos).length()
                    if d <= settings.CATCHUP_SEARCH_RADIUS:
                        f_count = neighbor_counts.get(id(f), 0)
                        if f_count > best_bigger_size + settings.CATCHUP_GROUP_DELTA:
                            best_bigger_size = f_count
                            best_bigger = f

            if best_bigger is not None:
                # A meaningfully bigger flock is nearby — hurry to join it
                self._catching_up = True
                force = seek(
                    self.pos, self.vel, best_bigger.pos, FLY_SPEED * settings.CATCHUP_SPEED_MULT
                ) * settings.CATCHUP_WEIGHT
            elif len(neighbors) == 0:
                nearest = None
                min_dist = settings.REGROUP_RADIUS
                for f in flies:
                    if f is self:
                        continue
                    d = (f.pos - self.pos).length()
                    if d < min_dist:
                        min_dist = d
                        nearest = f

                if nearest is not None:
                    force = seek(self.pos, self.vel, nearest.pos, FLY_SPEED) * settings.REGROUP_WEIGHT
                else:
                    force = V2()
            else:
                sep = boids_separation(self.pos, self.vel, neighbors, settings.SEP_RADIUS, FLY_SPEED)
                coh = boids_cohesion(self.pos, self.vel, neighbors, FLY_SPEED)
                ali = boids_alignment(self.vel, neighbors, FLY_SPEED)
                force = sep * settings.SEP_WEIGHT + coh * settings.COH_WEIGHT + ali * settings.ALI_WEIGHT

            # Gentle anchor toward arena center to avoid drifting out of bounds
            center = V2(bounds_rect.centerx, bounds_rect.centery)
            force += (center - self.pos) * ANCHOR_WEIGHT * 0.002

            # Integrate velocity
            self.vel += limit(force, 240.0) * dt

        elif self.state == FlyState.Fleeing:
            force = evade(self.pos, self.vel, frog.pos, frog.vel, FLY_SPEED, predict_speed=FROG_SPEED)

            # Scale evade force by proximity — the closer the frog, the sharper the panic
            closeness = 1.0 - min(dist_to_frog, settings.FLEE_PANIC_RANGE) / settings.FLEE_PANIC_RANGE
            panic_mult = 1.0 + (settings.FLEE_PANIC_MAX_MULT - 1.0) * (closeness ** settings.FLEE_PANIC_EXPONENT)
            force *= panic_mult

            # Mild separation so panicking flies scatter apart instead of overlapping each
            # other — reuse the neighbor list precomputed once per frame in main.py instead
            # of rebuilding it here.
            neighbors = neighbors if neighbors is not None else []
            self._debug_neighbors = neighbors
            if neighbors:
                sep = boids_separation(self.pos, self.vel, neighbors, settings.SEP_RADIUS, FLY_SPEED)
                force += sep * settings.SEP_WEIGHT * 0.6

            # Anchor blend so the group does not disappear off screen
            center = V2(bounds_rect.centerx, bounds_rect.centery)
            force += (center - self.pos) * ANCHOR_WEIGHT * 0.002

            self.vel += limit(force, 420.0) * dt

        elif self.state == FlyState.Idle:
            force = wander_force(self.vel, FLY_SPEED, rng_seed=self._rng_seed)
            self.vel += limit(force, 120.0) * dt
            self.vel *= 0.98  # mild damping so idle feels soft

        # Speed clamp and position integrate — allow a temporary higher cap while catching up
        if self.state == FlyState.Fleeing:
            effective_max_speed = FLY_SPEED * settings.FLEE_PANIC_MAX_MULT
        elif self._catching_up:
            effective_max_speed = FLY_SPEED * settings.CATCHUP_SPEED_MULT
        else:
            effective_max_speed = FLY_SPEED

        if self.vel.length() > effective_max_speed:
            self.vel.scale_to_length(effective_max_speed)
        self.pos += self.vel * dt

        # Soft containment inside arena
        if self.pos.x < self.radius:
            self.pos.x = self.radius; self.vel.x *= -0.4
        if self.pos.x > WIDTH - self.radius:
            self.pos.x = WIDTH - self.radius; self.vel.x *= -0.4
        if self.pos.y < self.radius:
            self.pos.y = self.radius; self.vel.y *= -0.4
        if self.pos.y > HEIGHT - self.radius:
            self.pos.y = HEIGHT - self.radius; self.vel.y *= -0.4

    def draw(self, surf):
        color = YELLOW if self.state in (FlyState.Flock, FlyState.Idle) else PURPLE
        pygame.draw.circle(surf, color, self.pos, self.radius)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            # Draw faint lines to each boid neighbor
            for n_pos, n_vel in self._debug_neighbors:
                pygame.draw.line(surf, (60, 90, 110), self.pos, n_pos, 1)
            # Draw velocity vector, NEIGHBOR_RADIUS perception, and state name
            perception_radii = [(NEIGHBOR_RADIUS, (100, 200, 255))]
            draw_debug_overlay(surf, self.pos, self.vel, perception_radii, self.state.name, vel_color=(230, 220, 100))
</file>

<file path="part1/entities/frog.py">
# ============================================================================
# frog.py
# Purpose
#   Player controlled agent. Moves with Arrive. Shoots bubbles.
#   Holds a short Hurt state for temporary invulnerability after damage.
# Update order
#   Compute steering, integrate velocity with dt, clamp to bounds, update bubbles.
# Drawing
#   Draw the frog body and a simple eye that points in the facing direction.
# ============================================================================

import time
import pygame
from pygame.math import Vector2 as V2
from settings import (
    WIDTH, HEIGHT, WHITE, GREEN, BLUE,
    FROG_RADIUS, FROG_SPEED,
    BUBBLE_RADIUS, BUBBLE_SPEED, BUBBLE_LIFETIME,
    HURT_INVULN, FROG_FACING_MIN_SPEED_SQ,
    ARRIVE_STOP_RADIUS, ARRIVE_STOP_DAMPING, ARRIVE_STOP_SNAP,
    PATH_WAYPOINT_RADIUS
)
from utils import clamp, draw_debug_overlay, circle_rect_intersect, nearest_point_on_rect
import debug_state
from steering import arrive, seek, integrate_velocity, apply_arrive_stop

class Bubble:
    """
    Simple projectile that moves in a straight line and pops after a short time.
    You can destroy it early when it hits a snake or an obstacle.
    """
    def __init__(self, pos, dir_vec):
        self.pos = V2(pos)
        self.vel = (dir_vec.normalize() if dir_vec.length_squared() > 0 else V2(1, 0)) * BUBBLE_SPEED
        self.birth = time.time()
        self.alive = True

    def update(self, dt):
        self.pos += self.vel * dt
        if time.time() - self.birth > BUBBLE_LIFETIME:
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, BLUE, self.pos, BUBBLE_RADIUS)
        pygame.draw.circle(surf, WHITE, self.pos, BUBBLE_RADIUS, 2)

class Frog:
    def __init__(self, pos, rects=None):
        self.pos = V2(pos)
        self.vel = V2()
        self.target = V2(pos)

        # A* path-following state (Assignment 2, Part 1). When self.path is
        # non-empty, update() steers through these waypoints instead of
        # jumping straight at self.target.
        self.path = []          # list[V2] of smoothed A* waypoints
        self.path_index = 0
        self.path_cost = 0.0

        self.radius = FROG_RADIUS
        self.speed = FROG_SPEED
        self.facing = V2(1, 0)   # used to aim bubbles when frog is not moving
        self.bubbles = []
        self.rects = rects if rects is not None else []
        self.hurt_timer = 0.0

    def set_target(self, p):
        """Set a new target the frog will move toward using Arrive."""
        self.target = V2(p)

    def set_path(self, path_points, cost=0.0):
        """Replace the current A* path with a new list of world-space waypoints."""
        self.path = [V2(p) for p in path_points]
        self.path_index = 0
        self.path_cost = cost
        if self.path:
            self.target = self.path[-1]

    def shoot(self):
        """Spawn a bubble just in front of the frog, moving along the facing direction."""
        dir_vec = self.vel if self.vel.length_squared() > FROG_FACING_MIN_SPEED_SQ else self.facing
        origin = self.pos + dir_vec.normalize() * (self.radius + 6)
        self.bubbles.append(Bubble(origin, dir_vec))

    def start_hurt(self):
        """Begin the invulnerability window after damage."""
        if self.hurt_timer <= 0:
            self.hurt_timer = HURT_INVULN

    def can_be_hurt(self):
        """Return True if the frog can take damage right now."""
        return self.hurt_timer <= 0

    def update(self, dt):
        # --- A* path following (Assignment 2, Part 1) -----------------------
        # Intermediate waypoints use seek() to keep full speed through turns
        # (Arrive's slow-down would make the frog visibly brake at every
        # corner). Only the FINAL waypoint uses arrive(), for a smooth stop
        # at the true destination. If no path is set, fall back to the
        # original Assignment 1 direct-Arrive behaviour (legacy left-click).
        if self.path and self.path_index < len(self.path):
            wp = self.path[self.path_index]
            is_last = (self.path_index == len(self.path) - 1)

            if not is_last and (wp - self.pos).length_squared() < PATH_WAYPOINT_RADIUS ** 2:
                self.path_index += 1
                wp = self.path[self.path_index]
                is_last = (self.path_index == len(self.path) - 1)

            if is_last:
                self.target = wp
                steer = arrive(self.pos, self.vel, wp, self.speed)
            else:
                steer = seek(self.pos, self.vel, wp, self.speed)

            final_dest = self.path[-1]
        else:
            steer = arrive(self.pos, self.vel, self.target, self.speed)
            final_dest = self.target

        self.vel = integrate_velocity(
            self.vel,
            steer,
            dt,
            self.speed,
        )

        # Only apply the hard-stop damping toward the TRUE final destination
        # (last path waypoint, or the legacy direct target) - applying it on
        # intermediate waypoints would brake the frog at every corner.
        self.vel = apply_arrive_stop(
            self.pos,
            self.vel,
            final_dest,
            dt,
        )

        # Path is finished once we've arrived and stopped at the last waypoint
        if self.path and self.path_index == len(self.path) - 1:
            if (final_dest - self.pos).length() < ARRIVE_STOP_RADIUS and self.vel.length() < 1.0:
                self.path = []


        # Move the frog
        self.pos += self.vel * dt

        # Face in the direction of motion when moving
        if self.vel.length_squared() > FROG_FACING_MIN_SPEED_SQ:
            self.facing = self.vel.normalize()

        # Keep inside bounds
        self.pos.x = clamp(self.pos.x, self.radius, WIDTH - self.radius)
        self.pos.y = clamp(self.pos.y, self.radius, HEIGHT - self.radius)

        # Push frog out of any obstacle rectangle it overlaps
        # for rect in self.rects:
        #     if circle_rect_intersect(self.pos, self.radius, rect):
        #         nearest = nearest_point_on_rect(self.pos, rect)
        #         diff = self.pos - nearest
        #         if diff.length_squared() > 0:
        #             push_dir = diff.normalize()
        #         else:
        #             push_dir = V2(0, -1)
        #         self.pos = nearest + push_dir * self.radius
        #         # Kill velocity component pushing further into the obstacle
        #         into_wall = self.vel.dot(push_dir)
        #         if into_wall < 0:
        #             self.vel -= push_dir * into_wall

        # Update bubbles and remove popped ones
        for b in list(self.bubbles):
            b.update(dt)
            if not b.alive:
                self.bubbles.remove(b)

        # Count down invulnerability
        if self.hurt_timer > 0:
            self.hurt_timer -= dt

    def draw(self, surf):
        # Flash while hurt. This provides player feedback and helps debugging.
        color = GREEN
        if self.hurt_timer > 0:
            t = int(pygame.time.get_ticks() * 0.01) % 2
            color = (220, 220, 220) if t == 0 else (160, 160, 160)

        # Body
        pygame.draw.circle(surf, color, self.pos, self.radius)

        # Eye looks in facing direction
        eye = self.pos + self.facing * (self.radius - 4)
        pygame.draw.circle(surf, WHITE, eye, 5)
        pygame.draw.circle(surf, (30, 30, 30), eye, 2)

        # Bubbles
        for b in self.bubbles:
            b.draw(surf)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            draw_debug_overlay(surf, self.pos, self.vel, [], "khanh", vel_color=(120, 255, 160))
            
            # Draw crosshair at target
            pygame.draw.circle(surf, (200, 200, 200), self.target, 3)
            pygame.draw.line(surf, (200, 200, 200), self.target - V2(8, 0), self.target + V2(8, 0), 1)
            pygame.draw.line(surf, (200, 200, 200), self.target - V2(0, 8), self.target + V2(0, 8), 1)
            
            # Draw ARRIVE_SLOW_RADIUS and ARRIVE_STOP_RADIUS around the target
            from settings import ARRIVE_SLOW_RADIUS, ARRIVE_STOP_RADIUS
            pygame.draw.circle(surf, (255, 200, 100), self.target, ARRIVE_SLOW_RADIUS, 1)
            pygame.draw.circle(surf, (255, 100, 100), self.target, ARRIVE_STOP_RADIUS, 1)
</file>

<file path="part1/entities/snake.py">
# ============================================================================
# snake.py
# Purpose
#   Predator agent with a five-state FSM.
#   States: PatrolAway, PatrolHome, Aggro, Harmless, Confused.
#   Aggro chases the frog. Harmless returns home after pacification.
#   Confused wanders briefly after reaching home, then resumes patrol.
# Update order
#   Evaluate transitions first, then run the behavior for the active state.
# Drawing
#   Simple circle with a tiny eye that turns toward the current velocity.
# ============================================================================

from enum import Enum, auto
import math, random
import pygame
from pygame.math import Vector2 as V2
import settings
from settings import (
    WIDTH, HEIGHT, WHITE,
    SNAKE_RADIUS, SNAKE_SPEED, DEAGGRO_RANGE
)
from utils import draw_debug_overlay, nearest_point_on_rect, circle_rect_intersect
import debug_state
from steering import arrive, seek, seek_with_avoid, arrive_with_avoid, integrate_velocity, pursue, wander_force, predict_future_position
class SnakeState(Enum):
    PatrolAway = auto()
    PatrolHome = auto()
    Aggro      = auto()
    Harmless   = auto()
    Confused   = auto()

class Snake:
    def __init__(self, pos, patrol_point, rects):
        # Motion and shape
        self.pos = V2(pos)
        self.vel = V2(1, 0)
        self.radius = SNAKE_RADIUS
        self.speed = SNAKE_SPEED

        # Home base and patrol destination
        self.home = V2(pos)
        self.patrol_point = V2(patrol_point)

        # Initial state
        self.state = SnakeState.PatrolAway

        # Obstacles for avoidance
        self.rects = rects

        # Drawing hint for head direction
        self.heading_deg = 0.0

        # Color varies by state for quick visual debug
        self.color = (190, 130, 110)

        # Confused state timer
        self.confused_timer = 0.0

        # RNG for wander if needed
        self._rng_seed = random.randint(0, 999999)
        self._avoid_angle = 0.0

        # Debug overlay info
        self._debug_target = None
        self._debug_steer = V2()
        self._debug_avoid = V2()

    def set_state(self, st):
        """Switch to a new FSM state and log the transition for debug overlay."""
        if st != self.state:
            debug_state.log_transition("Snake", id(self) % 1000, self.state.name, st.name)
        self.state = st
        
        # Start the confused timer immediately when entering the state
        if self.state == SnakeState.Confused:
            self.confused_timer = settings.SNAKE_CONFUSED_DURATION

    def update(self, dt, frog):
        """
        Update state transitions based on distance to frog and timers.
        Then compute a steering force for the active state and integrate motion.
        """

        # Distance to frog for transitions
        dist = (frog.pos - self.pos).length()

        # ---------------- FSM transitions ----------------
        if self.state == SnakeState.Aggro:
            if dist > DEAGGRO_RANGE:
                self.set_state(SnakeState.PatrolHome)

        elif self.state in (SnakeState.PatrolHome, SnakeState.PatrolAway):
            if dist < settings.AGGRO_RANGE:
                self.set_state(SnakeState.Aggro)

        elif self.state == SnakeState.Confused:
            self.confused_timer -= dt
            if self.confused_timer <= 0:
                self.set_state(SnakeState.PatrolAway)

        elif self.state == SnakeState.Harmless:
            # Walk home, then resume patrol
            if (self.home - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.Confused)

        # ---------------- State behaviours ----------------
        if self.state == SnakeState.Aggro:
            self.color = (255, 150, 150)
            # Predict where the frog will be, then let the corridor search pick the actual
            # direction toward that point — avoidance has full authority when something is
            # in the way, instead of being a weak add-on to a separately-computed chase force
            predicted = predict_future_position(self.pos, frog.pos, frog.vel, self.speed)
            steer, self._avoid_angle = seek_with_avoid(
                self.pos, self.vel, predicted, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)

        elif self.state == SnakeState.PatrolAway:
            self.color = (180, 200, 255)
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.patrol_point, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)
            if (self.patrol_point - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.PatrolHome)

        elif self.state == SnakeState.PatrolHome:
            self.color = (180, 220, 180)
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.home, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)
            if (self.home - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.PatrolAway)

        elif self.state == SnakeState.Harmless:
            self.color = (190, 180, 255)
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.home, self.speed * settings.SNAKE_HARMLESS_SPEED_MULT,
                self.radius, self.rects, preferred_angle=self._avoid_angle)

        else:  # Confused
            self.color = (245, 210, 160)
            steer = wander_force(self.vel, rng_seed=self._rng_seed)

        # Integrate velocity and update position
        self.vel = integrate_velocity(self.vel, steer, dt, self.speed)
        self.pos += self.vel * dt

        # Hard fallback: guarantee the snake never ends up overlapping an obstacle, even on
        # frames where the soft avoidance steering wasn't enough (tight corners, high speed)
        for rect in self.rects:
            if circle_rect_intersect(self.pos, self.radius, rect):
                nearest = nearest_point_on_rect(self.pos, rect)
                diff = self.pos - nearest
                if diff.length_squared() > 0:
                    push_dir = diff.normalize()
                else:
                    push_dir = V2(0, -1)
                self.pos = nearest + push_dir * self.radius
                into_wall = self.vel.dot(push_dir)
                if into_wall < 0:
                    self.vel -= push_dir * into_wall

        # Smooth eye heading based on velocity
        spd = self.vel.length()
        if spd > 4:
            def lerp(a, b, t): return a + (b - a) * t
            self.heading_deg = lerp(self.heading_deg, math.degrees(math.atan2(self.vel.y, self.vel.x)), 0.15)

        # Keep inside arena
        if self.pos.x < self.radius: self.pos.x = self.radius
        if self.pos.x > WIDTH - self.radius: self.pos.x = WIDTH - self.radius
        if self.pos.y < self.radius: self.pos.y = self.radius
        if self.pos.y > HEIGHT - self.radius: self.pos.y = HEIGHT - self.radius

    def draw(self, surf):
        # Body
        pygame.draw.circle(surf, self.color, self.pos, self.radius)
        # Simple eye in heading direction
        head = self.pos + V2(1, 0).rotate(self.heading_deg) * (self.radius - 2)
        pygame.draw.circle(surf, (30, 30, 30), head, 3)
        pygame.draw.circle(surf, WHITE, head, 5, 1)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            perception_radii = [
                (settings.AGGRO_RANGE, (255, 100, 100)),
                (DEAGGRO_RANGE, (100, 100, 255))
            ]
            draw_debug_overlay(surf, self.pos, self.vel, perception_radii, self.state.name, vel_color=(255, 130, 100))
            
            # Draw individual forces
            scale = 0.3
            if self._debug_steer.length_squared() > 0.01:
                pygame.draw.line(surf, (100, 255, 100), self.pos, self.pos + self._debug_steer * scale, 2) # Green for base steer
            if self._debug_avoid.length_squared() > 0.01:
                pygame.draw.line(surf, (255, 200, 100), self.pos, self.pos + self._debug_avoid * scale, 2) # Orange for avoid force
                
            # Draw marker at active target
            if self._debug_target:
                pygame.draw.line(surf, (255, 50, 50), self._debug_target - V2(6, 6), self._debug_target + V2(6, 6), 2)
                pygame.draw.line(surf, (255, 50, 50), self._debug_target - V2(6, -6), self._debug_target + V2(6, -6), 2)
</file>

<file path="part1/codebase.MD">
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
entities/
  fly.py
  frog.py
  snake.py
debug_state.py
main.py
pathfinding.py
settings.py
steering.py
utils.py
world.py
</directory_structure>

<files>
This section contains the contents of the repository's files.

<file path="pathfinding.py">
# ============================================================================
# pathfinding.py
# Purpose
#   A* search over a uniform grid baked from the World's obstacle rects,
#   plus path smoothing (string-pulling) so the returned route looks
#   natural instead of grid-staircased.
# Mathematics
#   f(n) = g(n) + h(n). Cardinal step cost = 1.0, diagonal step cost = sqrt(2).
#   h(n) = octile distance (admissible for this cost model -> A* is optimal).
#   Diagonal moves are only legal if both adjacent cardinal cells are open
#   ("corner-cut guard") so the path never grazes an obstacle corner.
# ============================================================================

import heapq
import math
from pygame.math import Vector2 as V2
from utils import circlecast_hits_any_rect

SQRT2 = math.sqrt(2)


class Grid:
    """
    Uniform grid over the arena, rasterized once from a list of pygame.Rect
    obstacles. Each obstacle is inflated by `padding` (agent radius + a
    small margin) before rasterizing, so a path computed on this grid keeps
    the WHOLE agent body clear of walls, not just its center point.
    """

    def __init__(self, width, height, cell_size, obstacles, padding=0):
        self.cell_size = cell_size
        self.cols = math.ceil(width / cell_size)
        self.rows = math.ceil(height / cell_size)
        self.blocked = [[False] * self.cols for _ in range(self.rows)]
        self._rasterize(obstacles, padding)

    def _rasterize(self, obstacles, padding):
        for rect in obstacles:
            inflated = rect.inflate(padding * 2, padding * 2)
            c0 = max(0, inflated.left // self.cell_size)
            c1 = min(self.cols - 1, inflated.right // self.cell_size)
            r0 = max(0, inflated.top // self.cell_size)
            r1 = min(self.rows - 1, inflated.bottom // self.cell_size)
            for r in range(int(r0), int(r1) + 1):
                for c in range(int(c0), int(c1) + 1):
                    self.blocked[r][c] = True

    def in_bounds(self, cell):
        c, r = cell
        return 0 <= c < self.cols and 0 <= r < self.rows

    def walkable(self, cell):
        c, r = cell
        return self.in_bounds(cell) and not self.blocked[r][c]

    def world_to_cell(self, pos):
        return (int(pos.x // self.cell_size), int(pos.y // self.cell_size))

    def cell_to_world(self, cell):
        c, r = cell
        return V2(c * self.cell_size + self.cell_size / 2,
                  r * self.cell_size + self.cell_size / 2)

    def nearest_walkable(self, cell, max_radius=8):
        """Ring-search outward from `cell` for the closest open cell. Used
        when a click lands inside/behind an obstacle."""
        if self.walkable(cell):
            return cell
        c0, r0 = cell
        for radius in range(1, max_radius + 1):
            for dc in range(-radius, radius + 1):
                for dr in range(-radius, radius + 1):
                    if max(abs(dc), abs(dr)) != radius:
                        continue  # only test the ring's edge, not its interior again
                    cand = (c0 + dc, r0 + dr)
                    if self.walkable(cand):
                        return cand
        return None

    def neighbors(self, cell, allow_diagonal=True):
        """
        Yields (neighbor_cell, step_cost).
        Cardinal cost = 1.0. Diagonal cost = sqrt(2), and a diagonal is only
        yielded if BOTH flanking cardinal cells are walkable (corner-cut guard).
        """
        c, r = cell
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c + dc, r + dr)
            if self.walkable(n):
                yield n, 1.0

        if allow_diagonal:
            for dc, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = (c + dc, r + dr)
                side_a = (c + dc, r)
                side_b = (c, r + dr)
                if self.walkable(n) and self.walkable(side_a) and self.walkable(side_b):
                    yield n, SQRT2


def octile_heuristic(a, b):
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return (dx + dy) + (SQRT2 - 2) * min(dx, dy)


def astar(grid, start_cell, goal_cell, allow_diagonal=True):
    """
    Returns:
        {
          "path_cells": [cell, ...] or None if unreachable,
          "explored_order": [cell, ...],  # order cells were POPPED (settled)
          "g_cost": {cell: g_value, ...},  # cost of every explored cell
          "total_cost": float or None,
        }
    """
    if not grid.walkable(start_cell) or not grid.walkable(goal_cell):
        return {"path_cells": None, "explored_order": [], "g_cost": {}, "total_cost": None}

    open_heap = []
    counter = 0  # tie-breaker so heapq never has to compare cell tuples
    heapq.heappush(open_heap, (0.0, counter, start_cell))

    g_cost = {start_cell: 0.0}
    parent = {start_cell: None}
    closed = set()
    explored_order = []

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)
        explored_order.append(current)

        if current == goal_cell:
            return {
                "path_cells": _reconstruct(parent, current),
                "explored_order": explored_order,
                "g_cost": g_cost,
                "total_cost": g_cost[current],
            }

        for neighbor, step_cost in grid.neighbors(current, allow_diagonal):
            if neighbor in closed:
                continue
            tentative_g = g_cost[current] + step_cost
            if neighbor not in g_cost or tentative_g < g_cost[neighbor]:
                g_cost[neighbor] = tentative_g
                parent[neighbor] = current
                f = tentative_g + octile_heuristic(neighbor, goal_cell)
                counter += 1
                heapq.heappush(open_heap, (f, counter, neighbor))

    return {"path_cells": None, "explored_order": explored_order, "g_cost": g_cost, "total_cost": None}


def _reconstruct(parent, node):
    path = [node]
    while parent[node] is not None:
        node = parent[node]
        path.append(node)
    path.reverse()
    return path


def line_of_sight(p0, p1, obstacles, radius):
    """True if a circle of `radius` can travel straight from p0 to p1
    without touching any obstacle rect."""
    return not circlecast_hits_any_rect(p0, p1, radius, obstacles)


def smooth_path(world_points, obstacles, radius):
    """
    String-pulling: from each kept waypoint, jump directly to the FURTHEST
    waypoint still in a straight line-of-sight, skipping every grid-forced
    zig-zag point in between. This is what turns a jagged, grid-aligned
    A* path into a natural-looking route, and reduces how many corners the
    steering code has to actually turn through.
    """
    if len(world_points) <= 2:
        return list(world_points)

    smoothed = [world_points[0]]
    i = 0
    n = len(world_points)
    while i < n - 1:
        furthest = i + 1
        for j in range(n - 1, i, -1):
            if line_of_sight(world_points[i], world_points[j], obstacles, radius):
                furthest = j
                break
        smoothed.append(world_points[furthest])
        i = furthest
    return smoothed


def find_path(grid, start_world, goal_world, obstacles, agent_radius, allow_diagonal=True):
    """
    High-level entry point used by main.py.
    1. snap start/goal to the nearest walkable grid cell
    2. run A*
    3. convert the cell path to world-space points
    4. smooth it

    Returns a dict ready for both frog.set_path() and the HUD/visualization:
        raw_world_path        - list[V2] or None
        smoothed_world_path   - list[V2] or None
        explored_world        - list[V2] (for drawing, in visit order)
        explored_cells        - list[cell] (for indexing g_cost, in visit order)
        g_cost_by_cell         - {cell: g}
        total_cost              - float or None
    """
    start_cell = grid.world_to_cell(start_world)
    goal_cell = grid.world_to_cell(goal_world)

    snapped_start = grid.nearest_walkable(start_cell)
    snapped_goal = grid.nearest_walkable(goal_cell)
    start_cell = snapped_start if snapped_start else start_cell
    goal_cell = snapped_goal if snapped_goal else goal_cell

    result = astar(grid, start_cell, goal_cell, allow_diagonal)

    world_path = None
    smoothed_world_path = None
    if result["path_cells"]:
        world_path = [grid.cell_to_world(c) for c in result["path_cells"]]
        smoothed_world_path = smooth_path(world_path, obstacles, agent_radius)

    return {
        "raw_world_path": world_path,
        "smoothed_world_path": smoothed_world_path,
        "explored_world": [grid.cell_to_world(c) for c in result["explored_order"]],
        "explored_cells": result["explored_order"],
        "g_cost_by_cell": result["g_cost"],
        "total_cost": result["total_cost"],
    }
</file>

<file path="world.py">
# ============================================================================
# world.py
# Purpose
#   Build the arena and a list of rectangular obstacles.
#   Obstacles are static and are used by the snake for avoidance checks.
# Why rectangles
#   Rectangles are easy to draw and fast to test against with our helpers.
# ============================================================================

import random
import pygame
from pathfinding import Grid
from settings import CELL_SIZE, PATH_OBSTACLE_PADDING

class World:
    def __init__(self, width, height):
        # Whole world bounds as a pygame.Rect for convenience
        self.rect = pygame.Rect(0, 0, width, height)

        # Container that holds all blocking rectangles
        self.obstacles = []

        # Build a reproducible obstacle set
        self._build_obstacles(width, height)

        # Bake a walkability grid once, used by A* (pathfinding.py). Obstacles
        # are inflated by the frog's radius so a path never hugs a wall.
        self.grid = Grid(width, height, CELL_SIZE, self.obstacles, padding=PATH_OBSTACLE_PADDING)


    def _build_obstacles(self, w, h):
        """Create a few rectangles with a fixed random seed for reproducibility."""
        rng = random.Random(9)
        for _ in range(9):
            ww = rng.randint(80, 180)
            hh = rng.randint(60, 140)
            x = rng.randint(40, w - ww - 40)
            y = rng.randint(40, h - hh - 40)
            rect = pygame.Rect(x, y, ww, hh)
            self.obstacles.append(rect)

    def draw(self, surf):
        """Render each obstacle with a fill and a subtle outline."""
        for r in self.obstacles:
            pygame.draw.rect(surf, (70, 85, 95), r, border_radius=10)
            pygame.draw.rect(surf, (110, 130, 145), r, 2, border_radius=10)
</file>

<file path="debug_state.py">
# ============================================================================
# debug_state.py
# Purpose
#   Global debug flag that can be toggled by F1 key.
#   Entities import this to check if debug mode is enabled.
#   Also holds a live FSM transition log for the debug overlay.
# ============================================================================

# Global debug toggle flag
DEBUG = False

# Live FSM transition log — list of (time_str, kind, index, old_state, new_state)
TRANSITION_LOG = []
MAX_LOG_ENTRIES = 10

def log_transition(kind, index, old_state, new_state):
    """Record a state transition to the live debug log."""
    import time as _time
    TRANSITION_LOG.append((_time.strftime("%H:%M:%S"), kind, index, old_state, new_state))
    if len(TRANSITION_LOG) > MAX_LOG_ENTRIES:
        TRANSITION_LOG.pop(0)
</file>

<file path="utils.py">
# ============================================================================
# utils.py
# Purpose
#   Small helper functions that do not belong to a specific agent.
#   Drawing helpers and collision checks live here.
# Notes
#   None of these helpers should change game rules or AI decisions.
# ============================================================================

import pygame
from pygame.math import Vector2 as V2
from settings import WIDTH, HEIGHT
import pygame.gfxdraw

# A soft grid color for the background
GRID = (36, 42, 48)

def draw_grid(surf):
    """
    Draw a light grid to help the eye judge motion and distance.
    The grid has no effect on gameplay. It is only visual.
    """
    gap = 36  # distance between grid lines
    # Draw vertical lines
    for x in range(0, WIDTH, gap):
        pygame.draw.line(surf, GRID, (x, 0), (x, HEIGHT))
    # Draw horizontal lines
    for y in range(0, HEIGHT, gap):
        pygame.draw.line(surf, GRID, (0, y), (WIDTH, y))

def clamp(x, a, b):
    """Limit a scalar value x so it stays between a and b inclusive."""
    return max(a, min(b, x))

def limit(v, max_len):
    """
    Limit a vector length.
    If v is longer than max_len, scale it down to exactly max_len.
    """
    if v.length_squared() > max_len * max_len:
        v.scale_to_length(max_len)
    return v

def nearest_point_on_rect(point, rect):
    """Return the closest point on an axis aligned rectangle to a given point."""
    x = clamp(point.x, rect.left, rect.right)
    y = clamp(point.y, rect.top, rect.bottom)
    return V2(x, y)

def circle_rect_intersect(center, radius, rect):
    """Return True if a circle touches or overlaps a rectangle."""
    np = nearest_point_on_rect(center, rect)
    return (center - np).length_squared() <= radius * radius

def segment_circlecast_hits_rect(p0, p1, radius, rect, step=6.0):
    """
    Approximate a circle cast along a line from p0 to p1.
    We sample points along the segment and test a circle intersect at each step.
    """
    d = p1 - p0
    length = d.length()
    if length == 0:
        return circle_rect_intersect(p0, radius, rect)
    n = max(1, int(length / step))
    for i in range(n + 1):
        t = i / n
        pos = p0 + d * t
        if circle_rect_intersect(pos, radius, rect):
            return True
    return False

def circlecast_hits_any_rect(p0, p1, radius, rects, step=6.0):
    """Return True if the swept circle between p0 and p1 hits any rect in the list."""
    for r in rects:
        if segment_circlecast_hits_rect(p0, p1, radius, r, step):
            return True
    return False

def draw_debug_overlay(surf, pos, vel, perception_radii, state_name=None, vel_color=(255, 100, 100)):
    """
    Draw debug overlay for an entity: velocity vector, perception radii, and state name.

    Parameters:
      surf: pygame surface to draw on
      pos: entity position (V2)
      vel: entity velocity (V2)
      perception_radii: list of (radius_value, color) tuples to draw as circles
      state_name: string name of state to render, or None to skip state text
      vel_color: color of the velocity arrow, so different entity types read distinctly
    """
    # Draw velocity vector — bigger scale, thicker line, solid filled arrowhead
    if vel.length_squared() > 0.01:
        vel_end = pos + vel * 0.45
        pygame.draw.line(surf, vel_color, pos, vel_end, 3)
        arrow_dir = vel.normalize()
        tip = vel_end + arrow_dir * 10
        left = vel_end + arrow_dir.rotate(140) * 9
        right = vel_end + arrow_dir.rotate(-140) * 9
        pygame.draw.polygon(surf, vel_color, [tip, left, right])

    # Draw perception radius circles
    for radius, color in perception_radii:
        pygame.draw.circle(surf, color, pos, radius, 1)

    # Draw state name as small text above entity, with a background for legibility
    if state_name is not None:
        from pygame.font import Font
        tiny_font = Font(None, 22)
        txt = tiny_font.render(state_name, True, (235, 235, 235))
        text_rect = txt.get_rect(midbottom=(int(pos.x), int(pos.y) - 20))
        bg_rect = text_rect.inflate(6, 4)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 140))
        surf.blit(bg_surf, bg_rect.topleft)
        surf.blit(txt, text_rect)

def draw_heart(screen, x, y, color):
    pts = [
        (x + 6, y + 18),
        (x + 17, y + 12),
        (x + 20, y + 5),
        (x + 16, y - 1),
        (x + 10, y - 2),
        (x + 6, y + 2),
        (x + 2, y - 2),
        (x - 4, y - 1),
        (x - 8, y + 5),
        (x - 5, y + 12),
    ]

    pygame.gfxdraw.aapolygon(screen, pts, (30, 30, 30))
    pygame.gfxdraw.filled_polygon(screen, pts, color)


from settings import EXPLORED_COLOR_LOW, EXPLORED_COLOR_HIGH

def draw_explored_heatmap(surf, grid, explored_cells, g_cost_by_cell, font):
    """
    Draws every explored A* cell as a translucent square colored by its
    g-cost (blue = cheap, red = expensive), with the numeric cost printed
    inside the cell. This satisfies "display the cost of each explored
    cell" and "show all explored areas before the frog follows the path".
    """
    if not explored_cells:
        return
    max_g = max(g_cost_by_cell[c] for c in explored_cells) or 1.0

    for cell in explored_cells:
        g = g_cost_by_cell[cell]
        t = clamp(g / max_g, 0.0, 1.0)
        color = (
            int(EXPLORED_COLOR_LOW[0] + (EXPLORED_COLOR_HIGH[0] - EXPLORED_COLOR_LOW[0]) * t),
            int(EXPLORED_COLOR_LOW[1] + (EXPLORED_COLOR_HIGH[1] - EXPLORED_COLOR_LOW[1]) * t),
            int(EXPLORED_COLOR_LOW[2] + (EXPLORED_COLOR_HIGH[2] - EXPLORED_COLOR_LOW[2]) * t),
        )
        world_pos = grid.cell_to_world(cell)
        rect = pygame.Rect(0, 0, grid.cell_size - 2, grid.cell_size - 2)
        rect.center = (world_pos.x, world_pos.y)

        cell_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cell_surf.fill((*color, 110))
        surf.blit(cell_surf, rect.topleft)

        label = font.render(f"{g:.0f}", True, (255, 255, 255))
        surf.blit(label, label.get_rect(center=(world_pos.x, world_pos.y)))


def draw_astar_path(surf, world_points):
    """Draws the smoothed A* path in green with waypoint markers."""
    if len(world_points) < 2:
        return
    pts = [(p.x, p.y) for p in world_points]
    pygame.draw.lines(surf, (90, 220, 120), False, pts, 4)
    for p in world_points:
        pygame.draw.circle(surf, (90, 220, 120), p, 5)
        pygame.draw.circle(surf, (255, 255, 255), p, 5, 1)
</file>

<file path="entities/frog.py">
# ============================================================================
# frog.py
# Purpose
#   Player controlled agent. Moves with Arrive. Shoots bubbles.
#   Holds a short Hurt state for temporary invulnerability after damage.
# Update order
#   Compute steering, integrate velocity with dt, clamp to bounds, update bubbles.
# Drawing
#   Draw the frog body and a simple eye that points in the facing direction.
# ============================================================================

import time
import pygame
from pygame.math import Vector2 as V2
from settings import (
    WIDTH, HEIGHT, WHITE, GREEN, BLUE,
    FROG_RADIUS, FROG_SPEED,
    BUBBLE_RADIUS, BUBBLE_SPEED, BUBBLE_LIFETIME,
    HURT_INVULN, FROG_FACING_MIN_SPEED_SQ,
    ARRIVE_STOP_RADIUS, ARRIVE_STOP_DAMPING, ARRIVE_STOP_SNAP,
    PATH_WAYPOINT_RADIUS
)
from utils import clamp, draw_debug_overlay, circle_rect_intersect, nearest_point_on_rect
import debug_state
from steering import arrive, seek, integrate_velocity, apply_arrive_stop

class Bubble:
    """
    Simple projectile that moves in a straight line and pops after a short time.
    You can destroy it early when it hits a snake or an obstacle.
    """
    def __init__(self, pos, dir_vec):
        self.pos = V2(pos)
        self.vel = (dir_vec.normalize() if dir_vec.length_squared() > 0 else V2(1, 0)) * BUBBLE_SPEED
        self.birth = time.time()
        self.alive = True

    def update(self, dt):
        self.pos += self.vel * dt
        if time.time() - self.birth > BUBBLE_LIFETIME:
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, BLUE, self.pos, BUBBLE_RADIUS)
        pygame.draw.circle(surf, WHITE, self.pos, BUBBLE_RADIUS, 2)

class Frog:
    def __init__(self, pos, rects=None):
        self.pos = V2(pos)
        self.vel = V2()
        self.target = V2(pos)

        # A* path-following state (Assignment 2, Part 1). When self.path is
        # non-empty, update() steers through these waypoints instead of
        # jumping straight at self.target.
        self.path = []          # list[V2] of smoothed A* waypoints
        self.path_index = 0
        self.path_cost = 0.0

        self.radius = FROG_RADIUS
        self.speed = FROG_SPEED
        self.facing = V2(1, 0)   # used to aim bubbles when frog is not moving
        self.bubbles = []
        self.rects = rects if rects is not None else []
        self.hurt_timer = 0.0

    def set_target(self, p):
        """Set a new target the frog will move toward using Arrive."""
        self.target = V2(p)

    def set_path(self, path_points, cost=0.0):
        """Replace the current A* path with a new list of world-space waypoints."""
        self.path = [V2(p) for p in path_points]
        self.path_index = 0
        self.path_cost = cost
        if self.path:
            self.target = self.path[-1]

    def shoot(self):
        """Spawn a bubble just in front of the frog, moving along the facing direction."""
        dir_vec = self.vel if self.vel.length_squared() > FROG_FACING_MIN_SPEED_SQ else self.facing
        origin = self.pos + dir_vec.normalize() * (self.radius + 6)
        self.bubbles.append(Bubble(origin, dir_vec))

    def start_hurt(self):
        """Begin the invulnerability window after damage."""
        if self.hurt_timer <= 0:
            self.hurt_timer = HURT_INVULN

    def can_be_hurt(self):
        """Return True if the frog can take damage right now."""
        return self.hurt_timer <= 0

    def update(self, dt):
        # --- A* path following (Assignment 2, Part 1) -----------------------
        # Intermediate waypoints use seek() to keep full speed through turns
        # (Arrive's slow-down would make the frog visibly brake at every
        # corner). Only the FINAL waypoint uses arrive(), for a smooth stop
        # at the true destination. If no path is set, fall back to the
        # original Assignment 1 direct-Arrive behaviour (legacy left-click).
        if self.path and self.path_index < len(self.path):
            wp = self.path[self.path_index]
            is_last = (self.path_index == len(self.path) - 1)

            if not is_last and (wp - self.pos).length_squared() < PATH_WAYPOINT_RADIUS ** 2:
                self.path_index += 1
                wp = self.path[self.path_index]
                is_last = (self.path_index == len(self.path) - 1)

            if is_last:
                self.target = wp
                steer = arrive(self.pos, self.vel, wp, self.speed)
            else:
                steer = seek(self.pos, self.vel, wp, self.speed)

            final_dest = self.path[-1]
        else:
            steer = arrive(self.pos, self.vel, self.target, self.speed)
            final_dest = self.target

        self.vel = integrate_velocity(
            self.vel,
            steer,
            dt,
            self.speed,
        )

        # Only apply the hard-stop damping toward the TRUE final destination
        # (last path waypoint, or the legacy direct target) - applying it on
        # intermediate waypoints would brake the frog at every corner.
        self.vel = apply_arrive_stop(
            self.pos,
            self.vel,
            final_dest,
            dt,
        )

        # Path is finished once we've arrived and stopped at the last waypoint
        if self.path and self.path_index == len(self.path) - 1:
            if (final_dest - self.pos).length() < ARRIVE_STOP_RADIUS and self.vel.length() < 1.0:
                self.path = []


        # Move the frog
        self.pos += self.vel * dt

        # Face in the direction of motion when moving
        if self.vel.length_squared() > FROG_FACING_MIN_SPEED_SQ:
            self.facing = self.vel.normalize()

        # Keep inside bounds
        self.pos.x = clamp(self.pos.x, self.radius, WIDTH - self.radius)
        self.pos.y = clamp(self.pos.y, self.radius, HEIGHT - self.radius)

        # Push frog out of any obstacle rectangle it overlaps
        # for rect in self.rects:
        #     if circle_rect_intersect(self.pos, self.radius, rect):
        #         nearest = nearest_point_on_rect(self.pos, rect)
        #         diff = self.pos - nearest
        #         if diff.length_squared() > 0:
        #             push_dir = diff.normalize()
        #         else:
        #             push_dir = V2(0, -1)
        #         self.pos = nearest + push_dir * self.radius
        #         # Kill velocity component pushing further into the obstacle
        #         into_wall = self.vel.dot(push_dir)
        #         if into_wall < 0:
        #             self.vel -= push_dir * into_wall

        # Update bubbles and remove popped ones
        for b in list(self.bubbles):
            b.update(dt)
            if not b.alive:
                self.bubbles.remove(b)

        # Count down invulnerability
        if self.hurt_timer > 0:
            self.hurt_timer -= dt

    def draw(self, surf):
        # Flash while hurt. This provides player feedback and helps debugging.
        color = GREEN
        if self.hurt_timer > 0:
            t = int(pygame.time.get_ticks() * 0.01) % 2
            color = (220, 220, 220) if t == 0 else (160, 160, 160)

        # Body
        pygame.draw.circle(surf, color, self.pos, self.radius)

        # Eye looks in facing direction
        eye = self.pos + self.facing * (self.radius - 4)
        pygame.draw.circle(surf, WHITE, eye, 5)
        pygame.draw.circle(surf, (30, 30, 30), eye, 2)

        # Bubbles
        for b in self.bubbles:
            b.draw(surf)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            draw_debug_overlay(surf, self.pos, self.vel, [], "khanh", vel_color=(120, 255, 160))
            
            # Draw crosshair at target
            pygame.draw.circle(surf, (200, 200, 200), self.target, 3)
            pygame.draw.line(surf, (200, 200, 200), self.target - V2(8, 0), self.target + V2(8, 0), 1)
            pygame.draw.line(surf, (200, 200, 200), self.target - V2(0, 8), self.target + V2(0, 8), 1)
            
            # Draw ARRIVE_SLOW_RADIUS and ARRIVE_STOP_RADIUS around the target
            from settings import ARRIVE_SLOW_RADIUS, ARRIVE_STOP_RADIUS
            pygame.draw.circle(surf, (255, 200, 100), self.target, ARRIVE_SLOW_RADIUS, 1)
            pygame.draw.circle(surf, (255, 100, 100), self.target, ARRIVE_STOP_RADIUS, 1)
</file>

<file path="entities/snake.py">
# ============================================================================
# snake.py
# Purpose
#   Predator agent with a five-state FSM.
#   States: PatrolAway, PatrolHome, Aggro, Harmless, Confused.
#   Aggro chases the frog. Harmless returns home after pacification.
#   Confused wanders briefly after reaching home, then resumes patrol.
# Update order
#   Evaluate transitions first, then run the behavior for the active state.
# Drawing
#   Simple circle with a tiny eye that turns toward the current velocity.
# ============================================================================

from enum import Enum, auto
import math, random
import pygame
from pygame.math import Vector2 as V2
import settings
from settings import (
    WIDTH, HEIGHT, WHITE,
    SNAKE_RADIUS, SNAKE_SPEED, DEAGGRO_RANGE
)
from utils import draw_debug_overlay, nearest_point_on_rect, circle_rect_intersect
import debug_state
from steering import arrive, seek, seek_with_avoid, arrive_with_avoid, integrate_velocity, pursue, wander_force, predict_future_position
class SnakeState(Enum):
    PatrolAway = auto()
    PatrolHome = auto()
    Aggro      = auto()
    Harmless   = auto()
    Confused   = auto()

class Snake:
    def __init__(self, pos, patrol_point, rects):
        # Motion and shape
        self.pos = V2(pos)
        self.vel = V2(1, 0)
        self.radius = SNAKE_RADIUS
        self.speed = SNAKE_SPEED

        # Home base and patrol destination
        self.home = V2(pos)
        self.patrol_point = V2(patrol_point)

        # Initial state
        self.state = SnakeState.PatrolAway

        # Obstacles for avoidance
        self.rects = rects

        # Drawing hint for head direction
        self.heading_deg = 0.0

        # Color varies by state for quick visual debug
        self.color = (190, 130, 110)

        # Confused state timer
        self.confused_timer = 0.0

        # RNG for wander if needed
        self._rng_seed = random.randint(0, 999999)
        self._avoid_angle = 0.0

        # Debug overlay info
        self._debug_target = None
        self._debug_steer = V2()
        self._debug_avoid = V2()

    def set_state(self, st):
        """Switch to a new FSM state and log the transition for debug overlay."""
        if st != self.state:
            debug_state.log_transition("Snake", id(self) % 1000, self.state.name, st.name)
        self.state = st
        
        # Start the confused timer immediately when entering the state
        if self.state == SnakeState.Confused:
            self.confused_timer = settings.SNAKE_CONFUSED_DURATION

    def update(self, dt, frog):
        """
        Update state transitions based on distance to frog and timers.
        Then compute a steering force for the active state and integrate motion.
        """

        # Distance to frog for transitions
        dist = (frog.pos - self.pos).length()

        # ---------------- FSM transitions ----------------
        if self.state == SnakeState.Aggro:
            if dist > DEAGGRO_RANGE:
                self.set_state(SnakeState.PatrolHome)

        elif self.state in (SnakeState.PatrolHome, SnakeState.PatrolAway):
            if dist < settings.AGGRO_RANGE:
                self.set_state(SnakeState.Aggro)

        elif self.state == SnakeState.Confused:
            self.confused_timer -= dt
            if self.confused_timer <= 0:
                self.set_state(SnakeState.PatrolAway)

        elif self.state == SnakeState.Harmless:
            # Walk home, then resume patrol
            if (self.home - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.Confused)

        # ---------------- State behaviours ----------------
        if self.state == SnakeState.Aggro:
            self.color = (255, 150, 150)
            # Predict where the frog will be, then let the corridor search pick the actual
            # direction toward that point — avoidance has full authority when something is
            # in the way, instead of being a weak add-on to a separately-computed chase force
            predicted = predict_future_position(self.pos, frog.pos, frog.vel, self.speed)
            steer, self._avoid_angle = seek_with_avoid(
                self.pos, self.vel, predicted, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)

        elif self.state == SnakeState.PatrolAway:
            self.color = (180, 200, 255)
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.patrol_point, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)
            if (self.patrol_point - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.PatrolHome)

        elif self.state == SnakeState.PatrolHome:
            self.color = (180, 220, 180)
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.home, self.speed, self.radius, self.rects,
                preferred_angle=self._avoid_angle)
            if (self.home - self.pos).length() < settings.SNAKE_ARRIVE_THRESHOLD:
                self.set_state(SnakeState.PatrolAway)

        elif self.state == SnakeState.Harmless:
            self.color = (190, 180, 255)
            steer, self._avoid_angle = arrive_with_avoid(
                self.pos, self.vel, self.home, self.speed * settings.SNAKE_HARMLESS_SPEED_MULT,
                self.radius, self.rects, preferred_angle=self._avoid_angle)

        else:  # Confused
            self.color = (245, 210, 160)
            steer = wander_force(self.vel, rng_seed=self._rng_seed)

        # Integrate velocity and update position
        self.vel = integrate_velocity(self.vel, steer, dt, self.speed)
        self.pos += self.vel * dt

        # Hard fallback: guarantee the snake never ends up overlapping an obstacle, even on
        # frames where the soft avoidance steering wasn't enough (tight corners, high speed)
        for rect in self.rects:
            if circle_rect_intersect(self.pos, self.radius, rect):
                nearest = nearest_point_on_rect(self.pos, rect)
                diff = self.pos - nearest
                if diff.length_squared() > 0:
                    push_dir = diff.normalize()
                else:
                    push_dir = V2(0, -1)
                self.pos = nearest + push_dir * self.radius
                into_wall = self.vel.dot(push_dir)
                if into_wall < 0:
                    self.vel -= push_dir * into_wall

        # Smooth eye heading based on velocity
        spd = self.vel.length()
        if spd > 4:
            def lerp(a, b, t): return a + (b - a) * t
            self.heading_deg = lerp(self.heading_deg, math.degrees(math.atan2(self.vel.y, self.vel.x)), 0.15)

        # Keep inside arena
        if self.pos.x < self.radius: self.pos.x = self.radius
        if self.pos.x > WIDTH - self.radius: self.pos.x = WIDTH - self.radius
        if self.pos.y < self.radius: self.pos.y = self.radius
        if self.pos.y > HEIGHT - self.radius: self.pos.y = HEIGHT - self.radius

    def draw(self, surf):
        # Body
        pygame.draw.circle(surf, self.color, self.pos, self.radius)
        # Simple eye in heading direction
        head = self.pos + V2(1, 0).rotate(self.heading_deg) * (self.radius - 2)
        pygame.draw.circle(surf, (30, 30, 30), head, 3)
        pygame.draw.circle(surf, WHITE, head, 5, 1)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            perception_radii = [
                (settings.AGGRO_RANGE, (255, 100, 100)),
                (DEAGGRO_RANGE, (100, 100, 255))
            ]
            draw_debug_overlay(surf, self.pos, self.vel, perception_radii, self.state.name, vel_color=(255, 130, 100))
            
            # Draw individual forces
            scale = 0.3
            if self._debug_steer.length_squared() > 0.01:
                pygame.draw.line(surf, (100, 255, 100), self.pos, self.pos + self._debug_steer * scale, 2) # Green for base steer
            if self._debug_avoid.length_squared() > 0.01:
                pygame.draw.line(surf, (255, 200, 100), self.pos, self.pos + self._debug_avoid * scale, 2) # Orange for avoid force
                
            # Draw marker at active target
            if self._debug_target:
                pygame.draw.line(surf, (255, 50, 50), self._debug_target - V2(6, 6), self._debug_target + V2(6, 6), 2)
                pygame.draw.line(surf, (255, 50, 50), self._debug_target - V2(6, -6), self._debug_target + V2(6, -6), 2)
</file>

<file path="entities/fly.py">
# ============================================================================
# fly.py
# Purpose
#   Autonomous flocking agent with a small FSM.
#   States: Flock, Fleeing, Idle.
#   Flock uses boids separation, cohesion, alignment.
#   Fleeing uses flee or the new evade behavior.
#   Idle uses a gentle wander to drift when far from danger.
# Update order
#   Compute state transitions from triggers, then apply the behavior for state.
# ============================================================================

import random
from enum import Enum, auto
import pygame
from pygame.math import Vector2 as V2
import settings
from settings import (
    WIDTH, HEIGHT, WHITE, YELLOW, PURPLE,
    FLY_RADIUS, FLY_SPEED, NEIGHBOR_RADIUS,
    ANCHOR_WEIGHT, FROG_SPEED
)
from utils import limit, draw_debug_overlay
import debug_state
from steering import (
    boids_separation, boids_cohesion, boids_alignment,
    flee, evade, wander_force, seek
)

class FlyState(Enum):
    Flock   = auto()
    Fleeing = auto()
    Idle    = auto()

class Fly:
    def __init__(self, pos):
        self.pos = V2(pos)
        self.vel = V2(random.uniform(-1, 1), random.uniform(-1, 1))
        if self.vel.length_squared() == 0:
            self.vel = V2(1, 0)
        self.vel.scale_to_length(FLY_SPEED * 0.5)

        self.radius = FLY_RADIUS
        self.state = FlyState.Flock

        # Timers and cached values
        self.scare_timer = 0.0   # counts down while nervous before calming
        self.idle_timer  = 0.0   # time spent far from frog
        self._catching_up = False  # True while hurrying to merge into a bigger flock
        self._rng_seed   = random.randint(0, 999999)
        self._debug_neighbors = []   # cached neighbor list for debug neighbor-link drawing

    def sense_bubbles_close(self, bubbles, r):
        """Return True if any bubble is within range r of the fly."""
        for b in bubbles:
            if (b.pos - self.pos).length_squared() <= r * r:
                return True
        return False

    def _set_state(self, new_state):
        """Switch FSM state and log the transition when it actually changes."""
        if new_state != self.state:
            debug_state.log_transition("Fly", id(self) % 1000, self.state.name, new_state.name)
        self.state = new_state

    def update(self, dt, flies, frog, bounds_rect, bubbles, neighbor_counts=None, neighbors=None, neighbor_ids=None):
        """
        Update FSM and behavior. Flies use perception to switch states.
        Parameters
          flies: list of all flies for neighborhood queries
          frog:  player agent used as a threat source
          bounds_rect: world rectangle for anchor force and containment
          bubbles: list of active bubbles to trigger panic
        """

        # Perception radii and timers for the FSM
        BubbleFleeRange  = settings.FLY_BUBBLE_FLEE_RANGE
        StopFleeingRange = settings.FLY_CALM_RANGE
        IdleDistance     = settings.FLY_IDLE_DISTANCE
        IdleDelay        = settings.FLY_IDLE_DELAY

        # Triggers based on the frog and bubbles
        dist_to_frog = (frog.pos - self.pos).length()
        scared_by_frog   = dist_to_frog < settings.FLY_SCARED_RANGE
        scared_by_bubble = self.sense_bubbles_close(bubbles, BubbleFleeRange)

        # Cheap neighbor-presence check: true if any other fly is within NEIGHBOR_RADIUS
        has_nearby_flockmate = bool(neighbors)

        # ---------------- FSM transitions ----------------
        if self.state == FlyState.Flock:
            if scared_by_frog or scared_by_bubble:
                self._set_state(FlyState.Fleeing)
                self.scare_timer = settings.FLY_SCARE_TIMER
                # One-time velocity kick directly away from threat
                burst_dir = self.pos - frog.pos
                if burst_dir.length_squared() > 0:
                    burst_dir = burst_dir.normalize()
                else:
                    burst_dir = V2(0, -1)
                self.vel += burst_dir * settings.FLEE_BURST_STRENGTH
            else:
                if dist_to_frog > IdleDistance:
                    self.idle_timer += dt
                    if self.idle_timer >= IdleDelay:
                        self._set_state(FlyState.Idle)
                else:
                    self.idle_timer = 0.0

        elif self.state == FlyState.Fleeing:
            calm = dist_to_frog > StopFleeingRange and not self.sense_bubbles_close(bubbles, StopFleeingRange)
            if calm:
                self.scare_timer -= dt
                if self.scare_timer <= 0:
                    self._set_state(FlyState.Flock)
                    self.idle_timer = 0.0
            else:
                self.scare_timer = settings.FLY_SCARE_TIMER

        elif self.state == FlyState.Idle:
            if scared_by_frog or scared_by_bubble:
                self._set_state(FlyState.Fleeing)
                self.scare_timer = settings.FLY_SCARE_TIMER
                burst_dir = self.pos - frog.pos
                if burst_dir.length_squared() > 0:
                    burst_dir = burst_dir.normalize()
                else:
                    burst_dir = V2(0, -1)
                self.vel += burst_dir * settings.FLEE_BURST_STRENGTH
            elif dist_to_frog <= IdleDistance:
                self._set_state(FlyState.Flock)
                self.idle_timer = 0.0

        # ---------------- State behaviours ----------------
        if self.state == FlyState.Flock:
            # Neighbor list and neighbor-id set are precomputed once per frame in main.py
            # (single O(N^2) pass shared by every fly) and passed in here — no need to
            # rebuild them per-fly anymore.
            neighbors = neighbors if neighbors is not None else []
            neighbor_ids = neighbor_ids if neighbor_ids is not None else set()
            self._debug_neighbors = neighbors   # cache for debug drawing

            self._catching_up = False  # will be set True only if we decide to catch up below

            my_group_size = len(neighbors)
            best_bigger = None
            best_bigger_size = my_group_size

            # Only genuinely small/isolated groups should ever consider catching up —
            # density variation inside an already-joined flock should not re-trigger this
            # Only a genuinely small-but-real flock (not a lone straggler or a pair) should
            # actively hurry toward a meaningfully bigger one nearby. A lone fly or pair just
            # flocks normally and merges naturally whenever it happens to encounter a group —
            # no active cross-map hunting for those.
            if (neighbor_counts is not None
                    and settings.CATCHUP_MIN_OWN_GROUP <= my_group_size <= settings.CATCHUP_MAX_OWN_GROUP):
                for f in flies:
                    if f is self:
                        continue
                    # Skip flies already in my own neighbor set — cohesion handles them
                    if id(f) in neighbor_ids:
                        continue
                    d = (f.pos - self.pos).length()
                    if d <= settings.CATCHUP_SEARCH_RADIUS:
                        f_count = neighbor_counts.get(id(f), 0)
                        if f_count > best_bigger_size + settings.CATCHUP_GROUP_DELTA:
                            best_bigger_size = f_count
                            best_bigger = f

            if best_bigger is not None:
                # A meaningfully bigger flock is nearby — hurry to join it
                self._catching_up = True
                force = seek(
                    self.pos, self.vel, best_bigger.pos, FLY_SPEED * settings.CATCHUP_SPEED_MULT
                ) * settings.CATCHUP_WEIGHT
            elif len(neighbors) == 0:
                nearest = None
                min_dist = settings.REGROUP_RADIUS
                for f in flies:
                    if f is self:
                        continue
                    d = (f.pos - self.pos).length()
                    if d < min_dist:
                        min_dist = d
                        nearest = f

                if nearest is not None:
                    force = seek(self.pos, self.vel, nearest.pos, FLY_SPEED) * settings.REGROUP_WEIGHT
                else:
                    force = V2()
            else:
                sep = boids_separation(self.pos, self.vel, neighbors, settings.SEP_RADIUS, FLY_SPEED)
                coh = boids_cohesion(self.pos, self.vel, neighbors, FLY_SPEED)
                ali = boids_alignment(self.vel, neighbors, FLY_SPEED)
                force = sep * settings.SEP_WEIGHT + coh * settings.COH_WEIGHT + ali * settings.ALI_WEIGHT

            # Gentle anchor toward arena center to avoid drifting out of bounds
            center = V2(bounds_rect.centerx, bounds_rect.centery)
            force += (center - self.pos) * ANCHOR_WEIGHT * 0.002

            # Integrate velocity
            self.vel += limit(force, 240.0) * dt

        elif self.state == FlyState.Fleeing:
            force = evade(self.pos, self.vel, frog.pos, frog.vel, FLY_SPEED, predict_speed=FROG_SPEED)

            # Scale evade force by proximity — the closer the frog, the sharper the panic
            closeness = 1.0 - min(dist_to_frog, settings.FLEE_PANIC_RANGE) / settings.FLEE_PANIC_RANGE
            panic_mult = 1.0 + (settings.FLEE_PANIC_MAX_MULT - 1.0) * (closeness ** settings.FLEE_PANIC_EXPONENT)
            force *= panic_mult

            # Mild separation so panicking flies scatter apart instead of overlapping each
            # other — reuse the neighbor list precomputed once per frame in main.py instead
            # of rebuilding it here.
            neighbors = neighbors if neighbors is not None else []
            self._debug_neighbors = neighbors
            if neighbors:
                sep = boids_separation(self.pos, self.vel, neighbors, settings.SEP_RADIUS, FLY_SPEED)
                force += sep * settings.SEP_WEIGHT * 0.6

            # Anchor blend so the group does not disappear off screen
            center = V2(bounds_rect.centerx, bounds_rect.centery)
            force += (center - self.pos) * ANCHOR_WEIGHT * 0.002

            self.vel += limit(force, 420.0) * dt

        elif self.state == FlyState.Idle:
            force = wander_force(self.vel, FLY_SPEED, rng_seed=self._rng_seed)
            self.vel += limit(force, 120.0) * dt
            self.vel *= 0.98  # mild damping so idle feels soft

        # Speed clamp and position integrate — allow a temporary higher cap while catching up
        if self.state == FlyState.Fleeing:
            effective_max_speed = FLY_SPEED * settings.FLEE_PANIC_MAX_MULT
        elif self._catching_up:
            effective_max_speed = FLY_SPEED * settings.CATCHUP_SPEED_MULT
        else:
            effective_max_speed = FLY_SPEED

        if self.vel.length() > effective_max_speed:
            self.vel.scale_to_length(effective_max_speed)
        self.pos += self.vel * dt

        # Soft containment inside arena
        if self.pos.x < self.radius:
            self.pos.x = self.radius; self.vel.x *= -0.4
        if self.pos.x > WIDTH - self.radius:
            self.pos.x = WIDTH - self.radius; self.vel.x *= -0.4
        if self.pos.y < self.radius:
            self.pos.y = self.radius; self.vel.y *= -0.4
        if self.pos.y > HEIGHT - self.radius:
            self.pos.y = HEIGHT - self.radius; self.vel.y *= -0.4

    def draw(self, surf):
        color = YELLOW if self.state in (FlyState.Flock, FlyState.Idle) else PURPLE
        pygame.draw.circle(surf, color, self.pos, self.radius)
        
        # Debug overlay when enabled
        if debug_state.DEBUG:
            # Draw faint lines to each boid neighbor
            for n_pos, n_vel in self._debug_neighbors:
                pygame.draw.line(surf, (60, 90, 110), self.pos, n_pos, 1)
            # Draw velocity vector, NEIGHBOR_RADIUS perception, and state name
            perception_radii = [(NEIGHBOR_RADIUS, (100, 200, 255))]
            draw_debug_overlay(surf, self.pos, self.vel, perception_radii, self.state.name, vel_color=(230, 220, 100))
</file>

<file path="main.py">
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
</file>

<file path="settings.py">
# ============================================================================
# settings.py
# Purpose
#   Central place for all constants and tuning values.
#   You can tweak speeds, radii, and counts here without touching logic.
# Reading guide
#   Each variable has a short note so you know what it controls.
# ============================================================================

# Window size in pixels
WIDTH, HEIGHT = 1280, 720

# Target frames per second for the game loop
FPS = 60

# Colors as RGB tuples. Used by drawing code for the UI and agents.
BG    = (28, 33, 38)     # background color
WHITE = (240, 240, 240)  # text and highlights
GREEN = (90, 220, 120)   # frog color
BLUE  = (120, 180, 250)  # bubble color
YELLOW= (250, 225, 120)  # fly color when flocking or idle
PURPLE= (185, 120, 250)  # fly color when fleeing
RED   = (232, 88, 88)    # health hearts
MUTED = (180, 188, 196)  # hint text

# Frog setup
FROG_RADIUS = 16          # draw size and collision size for the frog
FROG_SPEED  = 300.0       # top speed for the frog in pixels per second
HURT_INVULN = 3.0         # seconds of temporary invulnerability after damage
FROG_FACING_MIN_SPEED_SQ = 16.0 # speed for facing shotting
# Bubble setup
BUBBLE_RADIUS   = 8       # visual radius and collision radius
BUBBLE_SPEED    = 380.0   # how fast the bubble travels
BUBBLE_LIFETIME = 2.0     # seconds before the bubble pops automatically

# Fly setup
FLY_CLUSTER_COUNT = 4        # number of initial flock clusters
FLY_CLUSTER_SPAWN_RADIUS = 90.0  # max offset from a cluster center when spawning
NUM_FLIES = 10           # how many flies spawn
FLY_RADIUS = 8            # fly draw and collision radius
FLY_SPEED  = 120.0        # fly max speed

# Fly panic/fleeing tuning
FLEE_PANIC_RANGE    = 220.0   # distance at which panic scaling starts kicking in
FLEE_PANIC_EXPONENT = 2.4     # >1 = sharper, more dramatic ramp-up as distance shrinks
FLEE_PANIC_MAX_MULT = 3.0     # maximum multiplier applied to evade force at point-blank range
FLEE_BURST_STRENGTH = 360.0   # one-time velocity kick applied the instant a fly starts fleeing

# Fly FSM perception radii and timers
FLY_SCARED_RANGE      = 160.0   # frog proximity that triggers Fleeing
FLY_BUBBLE_FLEE_RANGE = 140.0   # bubble proximity that triggers Fleeing
FLY_CALM_RANGE        = 220.0   # frog and bubbles must both clear this to start calming
FLY_IDLE_DISTANCE     = 380.0   # frog distance beyond which an isolated fly may idle
FLY_IDLE_DELAY        = 10     # seconds of isolation+distance before entering Idle
FLY_SCARE_TIMER       = 0.6     # seconds a fly stays nervous after the last scare

# Boids neighborhood and weights
# These determine how flies react to neighbors
NEIGHBOR_RADIUS = 150.0   # how far a fly considers other flies as neighbors
REGROUP_RADIUS  = 500.0   # search radius for the nearest fly when totally alone
REGROUP_WEIGHT  = 0.6     # how gently an isolated fly steers back toward the group
SEP_RADIUS      = 40.0    # separation threshold distance
SEP_WEIGHT      = 2.0     # weight for separation force
COH_WEIGHT      = 0.8     # weight for cohesion force
ALI_WEIGHT      = 1.1     # weight for alignment force
ALI_STRENGTH    = 1.5     # base scale for the alignment force before ALI_WEIGHT is applied
ANCHOR_WEIGHT   = 0.6     # small pull to arena center to keep flock on screen
CATCHUP_GROUP_DELTA  = 1     # how many more neighbors the other group needs to trigger catch-up
CATCHUP_SPEED_MULT   = 1.6   # speed multiplier while hurrying to join a bigger group
CATCHUP_WEIGHT       = 1.4   # steering weight while catching up
CATCHUP_MIN_OWN_GROUP = 2     # only consider catch-up if my own group is this small or smaller 
CATCHUP_MAX_OWN_GROUP = 4    # only consider catch-up if my own group is this small or smaller
CATCHUP_SEARCH_RADIUS = 350.0 
COH_DEAD_ZONE_RADIUS  = 6.0  # boids cohesion: no pull if within this distance of flock center
COH_SLOW_ZONE_RADIUS  = 30.0 # boids cohesion: full-strength pull begins beyond this distance

# Arrive behavior
# Slow inside slow radius and stop inside stop radius
ARRIVE_SLOW_RADIUS  = 120.0
ARRIVE_STOP_RADIUS  = 8.0
ARRIVE_STOP_DAMPING = 14.0   # 1/seconds — higher = faster hard stop once inside stop radius
ARRIVE_STOP_SNAP    = 2.0    # px/s — below this speed, snap directly to zero
STEER_MAX_FORCE = 1500.0

# Snake setup
NUM_SNAKES  = 0
SNAKE_RADIUS = 18
SNAKE_SPEED  = 160.0

# Snake perception ranges for FSM transitions
AGGRO_RANGE   = 260.0     # start chasing when frog gets this close
DEAGGRO_RANGE = 360.0     # stop chasing when frog moves this far

# Snake FSM thresholds and obstacle-avoidance weight curve
SNAKE_ARRIVE_THRESHOLD    = 10.0  # distance considered "reached" for patrol/home targets
SNAKE_CONFUSED_DURATION   = 5   # seconds a snake wanders confused after reaching home
SNAKE_HARMLESS_SPEED_MULT = 0.9   # Harmless state moves slightly slower than normal
SNAKE_AVOID_WEIGHT_MIN    = 0.25  # avoid_weight floor, far from any obstacle
SNAKE_AVOID_WEIGHT_MAX    = 0.65  # avoid_weight ceiling, right next to an obstacle
SNAKE_AVOID_NEAR_DIST     = 80.0  # obstacle distance at which avoid_weight reaches max

# Obstacle avoidance tuning
AVOID_LOOKAHEAD       = 260.0   # how far the snake looks ahead when checking a corridor
AVOID_ANGLE_INCREMENT = 12      # degrees to rotate per step when searching for a free path
AVOID_MAX_ANGLE       = 160     # maximum deviation to try on either side
AVOID_MAX_ANGLE       = 160     # maximum deviation to try on either side
SNAKE_AVOID_RETREAT_RADIUS_MULT = 3.0  # if nearest obstacle is closer than radius * this, retreat instead of creeping forward

# Game rules
START_HEALTH = 3                 # how many hits the frog can take
FLIES_TO_WIN = 10                # win condition counter

# Visual/effect timing
PARTICLE_LIFETIME   = 2   # seconds a burst particle stays visible
HURT_FLASH_DURATION = 0.15  # seconds the red damage flash stays on screen

# --- A* Pathfinding (Assignment 2, Part 1) ---
CELL_SIZE = 24                             # grid cell size in pixels
PATH_OBSTACLE_PADDING = FROG_RADIUS + 6    # inflate obstacles so the path keeps the frog's body clear
PATH_WAYPOINT_RADIUS = FROG_RADIUS * 1.5   # distance at which the frog advances to the next waypoint
PATH_REVEAL_CELLS_PER_FRAME = 40           # how fast the explored-area heatmap animates in
EXPLORED_COLOR_LOW  = (60, 90, 200)        # heatmap color at g-cost = 0 (blue = cheap)
EXPLORED_COLOR_HIGH = (220, 70, 70)        # heatmap color at max explored g-cost (red = expensive)
</file>

<file path="steering.py">
# ============================================================================
# steering.py
# Purpose
#   Implement all steering behaviours here. Each function computes a steering
#   force vector. Entities apply that force to their velocity each frame.
# Key idea
#   desired_velocity minus current_velocity gives the steering force.
#   Use dt in update loops when integrating velocity to keep motion consistent.
# ============================================================================

import math
from pygame.math import Vector2 as V2
from utils import limit, clamp, circlecast_hits_any_rect, nearest_point_on_rect
from settings import (
    ARRIVE_SLOW_RADIUS, ARRIVE_STOP_DAMPING, ARRIVE_STOP_RADIUS, ARRIVE_STOP_SNAP,
    AVOID_LOOKAHEAD, AVOID_ANGLE_INCREMENT, AVOID_MAX_ANGLE,
    ALI_STRENGTH, COH_DEAD_ZONE_RADIUS, COH_SLOW_ZONE_RADIUS,
    SNAKE_AVOID_RETREAT_RADIUS_MULT, STEER_MAX_FORCE
)

# ---------------- Base behaviours ----------------

def seek(pos, vel, target, max_speed):
    """
    Move toward a target. Returns a steering force.
    desired = direction_to_target * max_speed
    steering = desired - current_velocity
    """
    d = target - pos
    if d.length_squared() == 0:
        return V2()
    desired = d.normalize() * max_speed
    return desired - vel

def flee(pos, vel, target, max_speed):
    """
    Move away from a target. This is the opposite of seek.
    You need to implement the mirror of seek using direction from threat to self.
    """
    d = pos - target
    if d.length_squared() == 0:
        return V2()
    desired = d.normalize() * max_speed
    return desired - vel


def _braking_speed(dist, slow_radius, max_speed):
    """
    Kinematically-exact deceleration curve.

    We want a speed profile v(d) such that, under a constant maximum
    deceleration a_max, the agent reaches v = 0 at EXACTLY d = 0 with no
    residual creep and no overshoot. The physics for constant-deceleration
    braking gives:

        v(d) = sqrt(2 * a_max * d)

    We choose a_max so the curve is C0-continuous with the "cruise" branch
    (desired_vel = direction * max_speed) at d = slow_radius, i.e.
    v(slow_radius) = max_speed:

        max_speed = sqrt(2 * a_max * slow_radius)
        => a_max = max_speed^2 / (2 * slow_radius)

    Substituting back:

        v(d) = max_speed * sqrt(d / slow_radius)

    This is a strictly increasing, continuous function of d that starts at 0
    at the target and reaches max_speed exactly at the slow_radius boundary,
    with no seam/discontinuity and no tunable magic constant beyond the two
    radii that already define the behaviour.
    """
    t = clamp(dist / slow_radius, 0.0, 1.0)
    return max_speed * math.sqrt(t)


def _cancel_tangential(vel, direction, strength):
    """
    Orthogonal velocity cancellation via vector projection/rejection.

    Decompose vel into:
      radial_speed = vel . direction                (component along target dir)
      tangential   = vel - direction * radial_speed  (orthogonal rejection)

    Subtracting `tangential * strength` actively counters sideways drift
    instead of just letting the reduced-speed cruise vector "out-argue" it
    over distance/time. strength in [0, 1]; 1.0 fully removes the sideways
    component in a single step (subject to the max-force clamp applied later
    during integration), preventing the wide orbiting arcs around a target.
    """
    radial_speed = vel.dot(direction)
    tangential = vel - direction * radial_speed
    return -tangential * strength


def arrive(pos, vel, target, max_speed, slow_radius=ARRIVE_SLOW_RADIUS, stop_radius=ARRIVE_STOP_RADIUS):
    """
    Like seek when far, but slow down near the target using a kinematically
    exact braking curve (see _braking_speed), and actively cancels sideways
    (tangential) velocity while inside the slow zone so a fast approach from
    an angle settles in a straight line instead of arcing/orbiting.
    """
    d = target - pos
    dist = d.length()

    if dist < stop_radius:
        return -vel  # Cancel velocity to stop

    direction = d.normalize()

    if dist < slow_radius:
        desired_speed = _braking_speed(dist, slow_radius, max_speed)
        desired_vel = direction * desired_speed

        # Damp harder (cancel more of the sideways component) the closer we get,
        # so cornering tightens up right at the end instead of orbiting.
        t = dist / slow_radius
        cancel_strength = clamp(1.0 - t * 0.4, 0.6, 1.0)
        desired_vel += _cancel_tangential(vel, direction, cancel_strength)
    else:
        desired_vel = direction * max_speed

    return desired_vel - vel

def apply_arrive_stop(
    pos,
    vel,
    target,
    dt,
    stop_radius=ARRIVE_STOP_RADIUS,
    damping=ARRIVE_STOP_DAMPING,
    snap=ARRIVE_STOP_SNAP,
):
    """
    Apply the final convergence after velocity integration.

    Uses exact exponential decay exp(-damping * dt) rather than the linear
    approximation (1 - damping * dt). The linear form can overshoot into
    negative scale (and thus flip velocity direction) if dt * damping > 1 on
    a slow frame; the exponential form is bounded in (0, 1] for any dt >= 0,
    so it stays frame-rate independent even under frame-time spikes.
    """

    if (target - pos).length() < stop_radius:
        vel *= math.exp(-damping * dt)

        if vel.length() < snap:
            vel = V2()

    return vel

def integrate_velocity(vel, force, dt, max_speed):
    """
    Apply a steering force to velocity using Euler integration.
    Then clamp to max speed and return the new velocity.
    Use this inside agent update methods after computing steering forces.
    """
    vel += limit(force, STEER_MAX_FORCE) * dt
    if vel.length() > max_speed:
        vel.scale_to_length(max_speed)
    return vel

# ---------------- Boids components ----------------

def boids_separation(me_pos, me_vel, neighbors, sep_radius, max_speed):
    """
    Push away from neighbors that are too close.
    """
    steering = V2()
    count = 0
    for n_pos, n_vel in neighbors:
        d = me_pos - n_pos
        dist = d.length()
        if 0 < dist < sep_radius:
            # Scale the repulsion so closer neighbors push harder
            steering += d.normalize() * (sep_radius / dist)
            count += 1
            
    if count > 0:
        steering /= count
        # Calculate standard steering force
        steering = steering.normalize() * max_speed
        return steering - me_vel
        
    return V2()

def boids_cohesion(me_pos, me_vel, neighbors, max_speed, dead_zone_radius=COH_DEAD_ZONE_RADIUS, slow_zone_radius=COH_SLOW_ZONE_RADIUS):
    """
    Pull toward the center of mass of neighbors.
    """
    if not neighbors:
        return V2()
        
    avg_pos = V2()
    for n_pos, n_vel in neighbors:
        avg_pos += n_pos
    avg_pos /= len(neighbors)

    target_vec = avg_pos - me_pos
    dist = target_vec.length()

    # Cancel out velocity if perfectly centered
    if dist < dead_zone_radius:
        return -me_vel * 0.5 
        
    # Scale desired speed similar to Arrive behavior
    if dist < slow_zone_radius:
        desired_speed = max_speed * (dist / slow_zone_radius)
    else:
        desired_speed = max_speed
        
    desired_vel = target_vec.normalize() * desired_speed
    return desired_vel - me_vel

def boids_alignment(me_vel, neighbors, max_speed):
    """
    Match the average velocity of neighbors.
    """
    if not neighbors:
        return V2()
        
    avg_vel = V2()
    for n_pos, n_vel in neighbors:
        avg_vel += n_vel
    avg_vel /= len(neighbors)

    if avg_vel.length_squared() == 0:
        return V2()

    # The average velocity direction is our desired direction
    desired_vel = avg_vel.normalize() * max_speed
    return desired_vel - me_vel

# ---------------- Obstacle avoidance blend ----------------

def seek_with_avoid(pos, vel, target, max_speed, radius, rects, preferred_angle=0.0):
    """
    Move towards a target, but sweep a path ahead using circle casts.
    If the direct path is blocked, try looking left and right at increasing angles
    until a clear path is found.

    Contract: this function ALWAYS commands full max_speed along whatever
    direction it returns (never a slowed-down speed). Deceleration is the
    exclusive responsibility of the Arrive layer above it, and only once
    this function reports a clear line of sight (angle == 0.0).
    """
    d = target - pos
    if d.length_squared() == 0:
        return (V2(0, 0), 0.0)
        
    base_dir = d.normalize()
    look_ahead = AVOID_LOOKAHEAD  # how far ahead the snake scans
    
    # Angles to test: straight ahead (0) first, then sweep outward on both sides
    angles_to_check = [0]
    angle = AVOID_ANGLE_INCREMENT
    while angle <= AVOID_MAX_ANGLE:
        angles_to_check.extend([-angle, angle])
        angle += AVOID_ANGLE_INCREMENT
        
    if preferred_angle != 0.0 and preferred_angle in angles_to_check:
        angles_to_check.remove(preferred_angle)
        angles_to_check.insert(1, preferred_angle)  # right after 0, not before it
    
    for angle in angles_to_check:
        # Rotate the base direction to get the candidate heading
        check_dir = base_dir.rotate(angle)
        
        # Sweep endpoint for the circle cast
        p1 = pos + check_dir * look_ahead
        
        # Circle-cast (swept-circle test) against every obstacle rect
        hit_wall = circlecast_hits_any_rect(pos, p1, radius, rects)
        
        if not hit_wall:
            # Clear corridor found - always commit at full speed
            desired = check_dir * max_speed
            return (desired - vel, angle)
            
    # Every tested angle is still blocked: don't ram forward, back away from the
    # nearest obstacle so the snake repositions and gets a fresh angle next frame.
    nearest_obstacle_point = None
    nearest_dist = float('inf')
    for r in rects:
        np = nearest_point_on_rect(pos, r)
        d = (pos - np).length()
        if d < nearest_dist:
            nearest_dist = d
            nearest_obstacle_point = np

    if nearest_obstacle_point is not None and nearest_dist < radius * SNAKE_AVOID_RETREAT_RADIUS_MULT:
        away = pos - nearest_obstacle_point
        retreat_dir = away.normalize() if away.length_squared() > 0 else -base_dir
        desired = retreat_dir * max_speed * 0.6
    else:
        # Not actually touching anything nearby — safe to creep forward slowly and re-try
        desired = base_dir * max_speed * 0.4

    return (desired - vel, 0.0)

def arrive_with_avoid(pos, vel, target, max_speed, radius, rects, preferred_angle=0.0,
                       slow_radius=ARRIVE_SLOW_RADIUS, stop_radius=ARRIVE_STOP_RADIUS):
    """
    Unified Arrive + obstacle avoidance, for Patrol-style states.

    The old Patrol code called arrive(target) and seek_with_avoid(target)
    separately and ADDED the two resulting forces together — two complete,
    independently-computed steering forces that can point in different
    directions near an obstacle, which is what caused the rattling near
    trees. This function instead picks ONE direction — whatever
    seek_with_avoid decides on (straight at the target if clear, or a
    corridor-adjusted direction if something is in the way) — and applies
    Arrive's slow/stop-radius speed profile to that single direction, the
    same way Aggro lets seek_with_avoid have full authority over direction
    rather than fighting it with a separately-aimed force.

    Returns (force, angle) — same shape as seek_with_avoid, so callers can
    keep passing the returned angle back in as preferred_angle next frame.
    """
    d = target - pos
    dist = d.length()

    if dist < stop_radius:
        return -vel, preferred_angle  # same "cancel velocity" rule as arrive()

    avoid_force, angle = seek_with_avoid(pos, vel, target, max_speed, radius, rects,
                                          preferred_angle=preferred_angle)
    # seek_with_avoid returned avoid_force = desired_velocity - vel, so add
    # vel back to recover the DIRECTION it picked internally — we want to
    # reuse that direction, just re-scale its SPEED using Arrive's taper.
    desired_dir_vel = avoid_force + vel
    direction = desired_dir_vel.normalize() if desired_dir_vel.length_squared() > 0 else d.normalize()

    if dist < slow_radius:
        desired_speed = max_speed * (dist / slow_radius)
    else:
        desired_speed = max_speed

    desired_vel = direction * desired_speed
    return desired_vel - vel, angle

# ---------------- New behaviours to be implemented ----------------

def predict_future_position(pos, target_pos, target_vel, max_speed):
    """
    Shared prediction helper used by pursue(), evade(), and Aggro's unified
    seek_with_avoid call.
    Uses the combined closing speed (pursuer + target) to estimate a more
    accurate interception time_horizon than using either speed alone.
    """
    distance = (target_pos - pos).length()
    target_speed = target_vel.length()
    
    # Target is effectively stationary - no need to predict ahead
    if target_speed < 5.0:
        return target_pos
        
    # Combined closing speed gives a more realistic time-to-intercept
    closing_speed = max_speed + target_speed
    
    # Cap the horizon so long-range chases don't extrapolate too far ahead
    time_horizon = min(distance / closing_speed, 1.5)
    
    return target_pos + target_vel * time_horizon

def pursue(pos, vel, target_pos, target_vel, max_speed):
    """
    Predict the future position of the target then seek that point.
    Suggested
      distance = |target_pos - pos|
      time_horizon = distance / (max_speed + small_eps)
      predicted    = target_pos + target_vel * time_horizon
      return seek toward predicted
    Replace simple seek in Snake Aggro with pursue for better interception.
    """
    predicted = predict_future_position(pos, target_pos, target_vel, max_speed)
    return seek(pos, vel, predicted, max_speed)

def evade(pos, vel, threat_pos, threat_vel, max_speed, predict_speed=None):
    """
    Predict the future position of a threat then flee from that point.
    This is the inverse of pursue. Use the same prediction idea.

    predict_speed: speed used to scale the prediction time horizon
    (time_horizon = distance / predict_speed). Defaults to max_speed (the
    evader's own speed) for backward compatibility — but when the evader is
    much SLOWER than the threat (a fly evading the faster frog), that
    default inflates the time horizon and can push the predicted point past
    the evader's own position, flipping the flee direction so the evader
    briefly steers TOWARD the threat instead of away from it. Pass the
    threat's own speed here (e.g. FROG_SPEED) to fix that.
    """
    if predict_speed is None:
        predict_speed = max_speed
    predicted = predict_future_position(pos, threat_pos, threat_vel, predict_speed)
    return flee(pos, vel, predicted, max_speed)

import random
def wander_force(me_vel, jitter_deg=8.0, circle_distance=24.0, circle_radius=18.0,
                  rng_seed=None, smoothing=0.85):
    """
    Return a small random steering vector for gentle drift.
    Classic wander: project a small circle ahead along current heading,
    then jitter the target point on that circle by a tiny random angle
    each update.

    smoothing (0-1): exponential low-pass filter applied to the OUTPUT
    force, not the underlying angle random-walk. 0 = no smoothing (raw
    circle-wander output, can look twitchy at 60 FPS). Closer to 1 = each
    frame's force is mostly last frame's force with a small nudge, which
    is what actually removes the "steering noise" look without needing to
    swap in Perlin/OU noise — the circle-wander angle is already a random
    walk (smooth), the twitchiness was coming from applying its full
    output un-damped every frame.
    """
    if not hasattr(wander_force, "_state"):
        wander_force._state = {}

    if rng_seed not in wander_force._state:
        rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
        wander_force._state[rng_seed] = {
            'angle': rng.uniform(0, 360),
            'rng': rng,
            'smoothed_force': V2(0, 0),
        }

    state = wander_force._state[rng_seed]
    rng = state['rng']

    # Jitter the angle (unchanged — this part was already correct)
    state['angle'] += rng.uniform(-jitter_deg, jitter_deg)

    if me_vel.length_squared() == 0:
        heading = V2(1, 0)
    else:
        heading = me_vel.normalize()

    circle_center = heading * circle_distance
    displacement = V2(circle_radius, 0).rotate(state['angle'])

    desired = circle_center + displacement
    raw_force = desired - me_vel

    # Low-pass filter: blend toward the new raw force instead of jumping to it
    state['smoothed_force'] = (
        state['smoothed_force'] * smoothing + raw_force * (1.0 - smoothing)
    )
    return state['smoothed_force']
</file>

</files>
</file>

<file path="part1/debug_state.py">
# ============================================================================
# debug_state.py
# Purpose
#   Global debug flag that can be toggled by F1 key.
#   Entities import this to check if debug mode is enabled.
#   Also holds a live FSM transition log for the debug overlay.
# ============================================================================

# Global debug toggle flag
DEBUG = False

# Live FSM transition log — list of (time_str, kind, index, old_state, new_state)
TRANSITION_LOG = []
MAX_LOG_ENTRIES = 10

def log_transition(kind, index, old_state, new_state):
    """Record a state transition to the live debug log."""
    import time as _time
    TRANSITION_LOG.append((_time.strftime("%H:%M:%S"), kind, index, old_state, new_state))
    if len(TRANSITION_LOG) > MAX_LOG_ENTRIES:
        TRANSITION_LOG.pop(0)
</file>

<file path="part1/main.py">
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
</file>

<file path="part1/pathfinding.py">
# ============================================================================
# pathfinding.py
# Purpose
#   A* search over a uniform grid baked from the World's obstacle rects,
#   plus path smoothing (string-pulling) so the returned route looks
#   natural instead of grid-staircased.
# Mathematics
#   f(n) = g(n) + h(n). Cardinal step cost = 1.0, diagonal step cost = sqrt(2).
#   h(n) = octile distance (admissible for this cost model -> A* is optimal).
#   Diagonal moves are only legal if both adjacent cardinal cells are open
#   ("corner-cut guard") so the path never grazes an obstacle corner.
# ============================================================================

import heapq
import math
from pygame.math import Vector2 as V2
from utils import circlecast_hits_any_rect

SQRT2 = math.sqrt(2)


class Grid:
    """
    Uniform grid over the arena, rasterized once from a list of pygame.Rect
    obstacles. Each obstacle is inflated by `padding` (agent radius + a
    small margin) before rasterizing, so a path computed on this grid keeps
    the WHOLE agent body clear of walls, not just its center point.
    """

    def __init__(self, width, height, cell_size, obstacles, padding=0):
        self.cell_size = cell_size
        self.cols = math.ceil(width / cell_size)
        self.rows = math.ceil(height / cell_size)
        self.blocked = [[False] * self.cols for _ in range(self.rows)]
        self._rasterize(obstacles, padding)

    def _rasterize(self, obstacles, padding):
        for rect in obstacles:
            inflated = rect.inflate(padding * 2, padding * 2)
            c0 = max(0, inflated.left // self.cell_size)
            c1 = min(self.cols - 1, inflated.right // self.cell_size)
            r0 = max(0, inflated.top // self.cell_size)
            r1 = min(self.rows - 1, inflated.bottom // self.cell_size)
            for r in range(int(r0), int(r1) + 1):
                for c in range(int(c0), int(c1) + 1):
                    self.blocked[r][c] = True

    def in_bounds(self, cell):
        c, r = cell
        return 0 <= c < self.cols and 0 <= r < self.rows

    def walkable(self, cell):
        c, r = cell
        return self.in_bounds(cell) and not self.blocked[r][c]

    def world_to_cell(self, pos):
        return (int(pos.x // self.cell_size), int(pos.y // self.cell_size))

    def cell_to_world(self, cell):
        c, r = cell
        return V2(c * self.cell_size + self.cell_size / 2,
                  r * self.cell_size + self.cell_size / 2)

    def nearest_walkable(self, cell, max_radius=8):
        """Ring-search outward from `cell` for the closest open cell. Used
        when a click lands inside/behind an obstacle."""
        if self.walkable(cell):
            return cell
        c0, r0 = cell
        for radius in range(1, max_radius + 1):
            for dc in range(-radius, radius + 1):
                for dr in range(-radius, radius + 1):
                    if max(abs(dc), abs(dr)) != radius:
                        continue  # only test the ring's edge, not its interior again
                    cand = (c0 + dc, r0 + dr)
                    if self.walkable(cand):
                        return cand
        return None

    def neighbors(self, cell, allow_diagonal=True):
        """
        Yields (neighbor_cell, step_cost).
        Cardinal cost = 1.0. Diagonal cost = sqrt(2), and a diagonal is only
        yielded if BOTH flanking cardinal cells are walkable (corner-cut guard).
        """
        c, r = cell
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c + dc, r + dr)
            if self.walkable(n):
                yield n, 1.0

        if allow_diagonal:
            for dc, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = (c + dc, r + dr)
                side_a = (c + dc, r)
                side_b = (c, r + dr)
                if self.walkable(n) and self.walkable(side_a) and self.walkable(side_b):
                    yield n, SQRT2


def octile_heuristic(a, b):
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return (dx + dy) + (SQRT2 - 2) * min(dx, dy)


def astar(grid, start_cell, goal_cell, allow_diagonal=True):
    """
    Returns:
        {
          "path_cells": [cell, ...] or None if unreachable,
          "explored_order": [cell, ...],  # order cells were POPPED (settled)
          "g_cost": {cell: g_value, ...},  # cost of every explored cell
          "total_cost": float or None,
        }
    """
    if not grid.walkable(start_cell) or not grid.walkable(goal_cell):
        return {"path_cells": None, "explored_order": [], "g_cost": {}, "total_cost": None}

    open_heap = []
    counter = 0  # tie-breaker so heapq never has to compare cell tuples
    heapq.heappush(open_heap, (0.0, counter, start_cell))

    g_cost = {start_cell: 0.0}
    parent = {start_cell: None}
    closed = set()
    explored_order = []

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)
        explored_order.append(current)

        if current == goal_cell:
            return {
                "path_cells": _reconstruct(parent, current),
                "explored_order": explored_order,
                "g_cost": g_cost,
                "total_cost": g_cost[current],
            }

        for neighbor, step_cost in grid.neighbors(current, allow_diagonal):
            if neighbor in closed:
                continue
            tentative_g = g_cost[current] + step_cost
            if neighbor not in g_cost or tentative_g < g_cost[neighbor]:
                g_cost[neighbor] = tentative_g
                parent[neighbor] = current
                f = tentative_g + octile_heuristic(neighbor, goal_cell)
                counter += 1
                heapq.heappush(open_heap, (f, counter, neighbor))

    return {"path_cells": None, "explored_order": explored_order, "g_cost": g_cost, "total_cost": None}


def _reconstruct(parent, node):
    path = [node]
    while parent[node] is not None:
        node = parent[node]
        path.append(node)
    path.reverse()
    return path


def line_of_sight(p0, p1, obstacles, radius):
    """True if a circle of `radius` can travel straight from p0 to p1
    without touching any obstacle rect."""
    return not circlecast_hits_any_rect(p0, p1, radius, obstacles)


def smooth_path(world_points, obstacles, radius):
    """
    String-pulling: from each kept waypoint, jump directly to the FURTHEST
    waypoint still in a straight line-of-sight, skipping every grid-forced
    zig-zag point in between. This is what turns a jagged, grid-aligned
    A* path into a natural-looking route, and reduces how many corners the
    steering code has to actually turn through.
    """
    if len(world_points) <= 2:
        return list(world_points)

    smoothed = [world_points[0]]
    i = 0
    n = len(world_points)
    while i < n - 1:
        furthest = i + 1
        for j in range(n - 1, i, -1):
            if line_of_sight(world_points[i], world_points[j], obstacles, radius):
                furthest = j
                break
        smoothed.append(world_points[furthest])
        i = furthest
    return smoothed


def find_path(grid, start_world, goal_world, obstacles, agent_radius, allow_diagonal=True):
    """
    High-level entry point used by main.py.
    1. snap start/goal to the nearest walkable grid cell
    2. run A*
    3. convert the cell path to world-space points
    4. smooth it

    Returns a dict ready for both frog.set_path() and the HUD/visualization:
        raw_world_path        - list[V2] or None
        smoothed_world_path   - list[V2] or None
        explored_world        - list[V2] (for drawing, in visit order)
        explored_cells        - list[cell] (for indexing g_cost, in visit order)
        g_cost_by_cell         - {cell: g}
        total_cost              - float or None
    """
    start_cell = grid.world_to_cell(start_world)
    goal_cell = grid.world_to_cell(goal_world)

    snapped_start = grid.nearest_walkable(start_cell)
    snapped_goal = grid.nearest_walkable(goal_cell)
    start_cell = snapped_start if snapped_start else start_cell
    goal_cell = snapped_goal if snapped_goal else goal_cell

    result = astar(grid, start_cell, goal_cell, allow_diagonal)

    world_path = None
    smoothed_world_path = None
    if result["path_cells"]:
        world_path = [grid.cell_to_world(c) for c in result["path_cells"]]
        smoothed_world_path = smooth_path(world_path, obstacles, agent_radius)

    return {
        "raw_world_path": world_path,
        "smoothed_world_path": smoothed_world_path,
        "explored_world": [grid.cell_to_world(c) for c in result["explored_order"]],
        "explored_cells": result["explored_order"],
        "g_cost_by_cell": result["g_cost"],
        "total_cost": result["total_cost"],
    }
</file>

<file path="part1/settings.py">
# ============================================================================
# settings.py
# Purpose
#   Central place for all constants and tuning values.
#   You can tweak speeds, radii, and counts here without touching logic.
# Reading guide
#   Each variable has a short note so you know what it controls.
# ============================================================================

# Window size in pixels
WIDTH, HEIGHT = 1280, 720

# Target frames per second for the game loop
FPS = 60

# Colors as RGB tuples. Used by drawing code for the UI and agents.
BG    = (28, 33, 38)     # background color
WHITE = (240, 240, 240)  # text and highlights
GREEN = (90, 220, 120)   # frog color
BLUE  = (120, 180, 250)  # bubble color
YELLOW= (250, 225, 120)  # fly color when flocking or idle
PURPLE= (185, 120, 250)  # fly color when fleeing
RED   = (232, 88, 88)    # health hearts
MUTED = (180, 188, 196)  # hint text

# Frog setup
FROG_RADIUS = 16          # draw size and collision size for the frog
FROG_SPEED  = 300.0       # top speed for the frog in pixels per second
HURT_INVULN = 3.0         # seconds of temporary invulnerability after damage
FROG_FACING_MIN_SPEED_SQ = 16.0 # speed for facing shotting
# Bubble setup
BUBBLE_RADIUS   = 8       # visual radius and collision radius
BUBBLE_SPEED    = 380.0   # how fast the bubble travels
BUBBLE_LIFETIME = 2.0     # seconds before the bubble pops automatically

# Fly setup
FLY_CLUSTER_COUNT = 4        # number of initial flock clusters
FLY_CLUSTER_SPAWN_RADIUS = 90.0  # max offset from a cluster center when spawning
NUM_FLIES = 10           # how many flies spawn
FLY_RADIUS = 8            # fly draw and collision radius
FLY_SPEED  = 120.0        # fly max speed

# Fly panic/fleeing tuning
FLEE_PANIC_RANGE    = 220.0   # distance at which panic scaling starts kicking in
FLEE_PANIC_EXPONENT = 2.4     # >1 = sharper, more dramatic ramp-up as distance shrinks
FLEE_PANIC_MAX_MULT = 3.0     # maximum multiplier applied to evade force at point-blank range
FLEE_BURST_STRENGTH = 360.0   # one-time velocity kick applied the instant a fly starts fleeing

# Fly FSM perception radii and timers
FLY_SCARED_RANGE      = 160.0   # frog proximity that triggers Fleeing
FLY_BUBBLE_FLEE_RANGE = 140.0   # bubble proximity that triggers Fleeing
FLY_CALM_RANGE        = 220.0   # frog and bubbles must both clear this to start calming
FLY_IDLE_DISTANCE     = 380.0   # frog distance beyond which an isolated fly may idle
FLY_IDLE_DELAY        = 10     # seconds of isolation+distance before entering Idle
FLY_SCARE_TIMER       = 0.6     # seconds a fly stays nervous after the last scare

# Boids neighborhood and weights
# These determine how flies react to neighbors
NEIGHBOR_RADIUS = 150.0   # how far a fly considers other flies as neighbors
REGROUP_RADIUS  = 500.0   # search radius for the nearest fly when totally alone
REGROUP_WEIGHT  = 0.6     # how gently an isolated fly steers back toward the group
SEP_RADIUS      = 40.0    # separation threshold distance
SEP_WEIGHT      = 2.0     # weight for separation force
COH_WEIGHT      = 0.8     # weight for cohesion force
ALI_WEIGHT      = 1.1     # weight for alignment force
ALI_STRENGTH    = 1.5     # base scale for the alignment force before ALI_WEIGHT is applied
ANCHOR_WEIGHT   = 0.6     # small pull to arena center to keep flock on screen
CATCHUP_GROUP_DELTA  = 1     # how many more neighbors the other group needs to trigger catch-up
CATCHUP_SPEED_MULT   = 1.6   # speed multiplier while hurrying to join a bigger group
CATCHUP_WEIGHT       = 1.4   # steering weight while catching up
CATCHUP_MIN_OWN_GROUP = 2     # only consider catch-up if my own group is this small or smaller 
CATCHUP_MAX_OWN_GROUP = 4    # only consider catch-up if my own group is this small or smaller
CATCHUP_SEARCH_RADIUS = 350.0 
COH_DEAD_ZONE_RADIUS  = 6.0  # boids cohesion: no pull if within this distance of flock center
COH_SLOW_ZONE_RADIUS  = 30.0 # boids cohesion: full-strength pull begins beyond this distance

# Arrive behavior
# Slow inside slow radius and stop inside stop radius
ARRIVE_SLOW_RADIUS  = 120.0
ARRIVE_STOP_RADIUS  = 8.0
ARRIVE_STOP_DAMPING = 14.0   # 1/seconds — higher = faster hard stop once inside stop radius
ARRIVE_STOP_SNAP    = 2.0    # px/s — below this speed, snap directly to zero
STEER_MAX_FORCE = 1500.0

# Snake setup
NUM_SNAKES  = 0
SNAKE_RADIUS = 18
SNAKE_SPEED  = 160.0

# Snake perception ranges for FSM transitions
AGGRO_RANGE   = 260.0     # start chasing when frog gets this close
DEAGGRO_RANGE = 360.0     # stop chasing when frog moves this far

# Snake FSM thresholds and obstacle-avoidance weight curve
SNAKE_ARRIVE_THRESHOLD    = 10.0  # distance considered "reached" for patrol/home targets
SNAKE_CONFUSED_DURATION   = 5   # seconds a snake wanders confused after reaching home
SNAKE_HARMLESS_SPEED_MULT = 0.9   # Harmless state moves slightly slower than normal
SNAKE_AVOID_WEIGHT_MIN    = 0.25  # avoid_weight floor, far from any obstacle
SNAKE_AVOID_WEIGHT_MAX    = 0.65  # avoid_weight ceiling, right next to an obstacle
SNAKE_AVOID_NEAR_DIST     = 80.0  # obstacle distance at which avoid_weight reaches max

# Obstacle avoidance tuning
AVOID_LOOKAHEAD       = 260.0   # how far the snake looks ahead when checking a corridor
AVOID_ANGLE_INCREMENT = 12      # degrees to rotate per step when searching for a free path
AVOID_MAX_ANGLE       = 160     # maximum deviation to try on either side
AVOID_MAX_ANGLE       = 160     # maximum deviation to try on either side
SNAKE_AVOID_RETREAT_RADIUS_MULT = 3.0  # if nearest obstacle is closer than radius * this, retreat instead of creeping forward

# Game rules
START_HEALTH = 3                 # how many hits the frog can take
FLIES_TO_WIN = 10                # win condition counter

# Visual/effect timing
PARTICLE_LIFETIME   = 2   # seconds a burst particle stays visible
HURT_FLASH_DURATION = 0.15  # seconds the red damage flash stays on screen

# --- A* Pathfinding (Assignment 2, Part 1) ---
CELL_SIZE = 24                             # grid cell size in pixels
PATH_OBSTACLE_PADDING = FROG_RADIUS + 6    # inflate obstacles so the path keeps the frog's body clear
PATH_WAYPOINT_RADIUS = FROG_RADIUS * 1.5   # distance at which the frog advances to the next waypoint
PATH_REVEAL_CELLS_PER_FRAME = 40           # how fast the explored-area heatmap animates in
EXPLORED_COLOR_LOW  = (60, 90, 200)        # heatmap color at g-cost = 0 (blue = cheap)
EXPLORED_COLOR_HIGH = (220, 70, 70)        # heatmap color at max explored g-cost (red = expensive)
</file>

<file path="part1/steering.py">
# ============================================================================
# steering.py
# Purpose
#   Implement all steering behaviours here. Each function computes a steering
#   force vector. Entities apply that force to their velocity each frame.
# Key idea
#   desired_velocity minus current_velocity gives the steering force.
#   Use dt in update loops when integrating velocity to keep motion consistent.
# ============================================================================

import math
from pygame.math import Vector2 as V2
from utils import limit, clamp, circlecast_hits_any_rect, nearest_point_on_rect
from settings import (
    ARRIVE_SLOW_RADIUS, ARRIVE_STOP_DAMPING, ARRIVE_STOP_RADIUS, ARRIVE_STOP_SNAP,
    AVOID_LOOKAHEAD, AVOID_ANGLE_INCREMENT, AVOID_MAX_ANGLE,
    ALI_STRENGTH, COH_DEAD_ZONE_RADIUS, COH_SLOW_ZONE_RADIUS,
    SNAKE_AVOID_RETREAT_RADIUS_MULT, STEER_MAX_FORCE
)

# ---------------- Base behaviours ----------------

def seek(pos, vel, target, max_speed):
    """
    Move toward a target. Returns a steering force.
    desired = direction_to_target * max_speed
    steering = desired - current_velocity
    """
    d = target - pos
    if d.length_squared() == 0:
        return V2()
    desired = d.normalize() * max_speed
    return desired - vel

def flee(pos, vel, target, max_speed):
    """
    Move away from a target. This is the opposite of seek.
    You need to implement the mirror of seek using direction from threat to self.
    """
    d = pos - target
    if d.length_squared() == 0:
        return V2()
    desired = d.normalize() * max_speed
    return desired - vel


def _braking_speed(dist, slow_radius, max_speed):
    """
    Kinematically-exact deceleration curve.

    We want a speed profile v(d) such that, under a constant maximum
    deceleration a_max, the agent reaches v = 0 at EXACTLY d = 0 with no
    residual creep and no overshoot. The physics for constant-deceleration
    braking gives:

        v(d) = sqrt(2 * a_max * d)

    We choose a_max so the curve is C0-continuous with the "cruise" branch
    (desired_vel = direction * max_speed) at d = slow_radius, i.e.
    v(slow_radius) = max_speed:

        max_speed = sqrt(2 * a_max * slow_radius)
        => a_max = max_speed^2 / (2 * slow_radius)

    Substituting back:

        v(d) = max_speed * sqrt(d / slow_radius)

    This is a strictly increasing, continuous function of d that starts at 0
    at the target and reaches max_speed exactly at the slow_radius boundary,
    with no seam/discontinuity and no tunable magic constant beyond the two
    radii that already define the behaviour.
    """
    t = clamp(dist / slow_radius, 0.0, 1.0)
    return max_speed * math.sqrt(t)


def _cancel_tangential(vel, direction, strength):
    """
    Orthogonal velocity cancellation via vector projection/rejection.

    Decompose vel into:
      radial_speed = vel . direction                (component along target dir)
      tangential   = vel - direction * radial_speed  (orthogonal rejection)

    Subtracting `tangential * strength` actively counters sideways drift
    instead of just letting the reduced-speed cruise vector "out-argue" it
    over distance/time. strength in [0, 1]; 1.0 fully removes the sideways
    component in a single step (subject to the max-force clamp applied later
    during integration), preventing the wide orbiting arcs around a target.
    """
    radial_speed = vel.dot(direction)
    tangential = vel - direction * radial_speed
    return -tangential * strength


def arrive(pos, vel, target, max_speed, slow_radius=ARRIVE_SLOW_RADIUS, stop_radius=ARRIVE_STOP_RADIUS):
    """
    Like seek when far, but slow down near the target using a kinematically
    exact braking curve (see _braking_speed), and actively cancels sideways
    (tangential) velocity while inside the slow zone so a fast approach from
    an angle settles in a straight line instead of arcing/orbiting.
    """
    d = target - pos
    dist = d.length()

    if dist < stop_radius:
        return -vel  # Cancel velocity to stop

    direction = d.normalize()

    if dist < slow_radius:
        desired_speed = _braking_speed(dist, slow_radius, max_speed)
        desired_vel = direction * desired_speed

        # Damp harder (cancel more of the sideways component) the closer we get,
        # so cornering tightens up right at the end instead of orbiting.
        t = dist / slow_radius
        cancel_strength = clamp(1.0 - t * 0.4, 0.6, 1.0)
        desired_vel += _cancel_tangential(vel, direction, cancel_strength)
    else:
        desired_vel = direction * max_speed

    return desired_vel - vel

def apply_arrive_stop(
    pos,
    vel,
    target,
    dt,
    stop_radius=ARRIVE_STOP_RADIUS,
    damping=ARRIVE_STOP_DAMPING,
    snap=ARRIVE_STOP_SNAP,
):
    """
    Apply the final convergence after velocity integration.

    Uses exact exponential decay exp(-damping * dt) rather than the linear
    approximation (1 - damping * dt). The linear form can overshoot into
    negative scale (and thus flip velocity direction) if dt * damping > 1 on
    a slow frame; the exponential form is bounded in (0, 1] for any dt >= 0,
    so it stays frame-rate independent even under frame-time spikes.
    """

    if (target - pos).length() < stop_radius:
        vel *= math.exp(-damping * dt)

        if vel.length() < snap:
            vel = V2()

    return vel

def integrate_velocity(vel, force, dt, max_speed):
    """
    Apply a steering force to velocity using Euler integration.
    Then clamp to max speed and return the new velocity.
    Use this inside agent update methods after computing steering forces.
    """
    vel += limit(force, STEER_MAX_FORCE) * dt
    if vel.length() > max_speed:
        vel.scale_to_length(max_speed)
    return vel

# ---------------- Boids components ----------------

def boids_separation(me_pos, me_vel, neighbors, sep_radius, max_speed):
    """
    Push away from neighbors that are too close.
    """
    steering = V2()
    count = 0
    for n_pos, n_vel in neighbors:
        d = me_pos - n_pos
        dist = d.length()
        if 0 < dist < sep_radius:
            # Scale the repulsion so closer neighbors push harder
            steering += d.normalize() * (sep_radius / dist)
            count += 1
            
    if count > 0:
        steering /= count
        # Calculate standard steering force
        steering = steering.normalize() * max_speed
        return steering - me_vel
        
    return V2()

def boids_cohesion(me_pos, me_vel, neighbors, max_speed, dead_zone_radius=COH_DEAD_ZONE_RADIUS, slow_zone_radius=COH_SLOW_ZONE_RADIUS):
    """
    Pull toward the center of mass of neighbors.
    """
    if not neighbors:
        return V2()
        
    avg_pos = V2()
    for n_pos, n_vel in neighbors:
        avg_pos += n_pos
    avg_pos /= len(neighbors)

    target_vec = avg_pos - me_pos
    dist = target_vec.length()

    # Cancel out velocity if perfectly centered
    if dist < dead_zone_radius:
        return -me_vel * 0.5 
        
    # Scale desired speed similar to Arrive behavior
    if dist < slow_zone_radius:
        desired_speed = max_speed * (dist / slow_zone_radius)
    else:
        desired_speed = max_speed
        
    desired_vel = target_vec.normalize() * desired_speed
    return desired_vel - me_vel

def boids_alignment(me_vel, neighbors, max_speed):
    """
    Match the average velocity of neighbors.
    """
    if not neighbors:
        return V2()
        
    avg_vel = V2()
    for n_pos, n_vel in neighbors:
        avg_vel += n_vel
    avg_vel /= len(neighbors)

    if avg_vel.length_squared() == 0:
        return V2()

    # The average velocity direction is our desired direction
    desired_vel = avg_vel.normalize() * max_speed
    return desired_vel - me_vel

# ---------------- Obstacle avoidance blend ----------------

def seek_with_avoid(pos, vel, target, max_speed, radius, rects, preferred_angle=0.0):
    """
    Move towards a target, but sweep a path ahead using circle casts.
    If the direct path is blocked, try looking left and right at increasing angles
    until a clear path is found.

    Contract: this function ALWAYS commands full max_speed along whatever
    direction it returns (never a slowed-down speed). Deceleration is the
    exclusive responsibility of the Arrive layer above it, and only once
    this function reports a clear line of sight (angle == 0.0).
    """
    d = target - pos
    if d.length_squared() == 0:
        return (V2(0, 0), 0.0)
        
    base_dir = d.normalize()
    look_ahead = AVOID_LOOKAHEAD  # how far ahead the snake scans
    
    # Angles to test: straight ahead (0) first, then sweep outward on both sides
    angles_to_check = [0]
    angle = AVOID_ANGLE_INCREMENT
    while angle <= AVOID_MAX_ANGLE:
        angles_to_check.extend([-angle, angle])
        angle += AVOID_ANGLE_INCREMENT
        
    if preferred_angle != 0.0 and preferred_angle in angles_to_check:
        angles_to_check.remove(preferred_angle)
        angles_to_check.insert(1, preferred_angle)  # right after 0, not before it
    
    for angle in angles_to_check:
        # Rotate the base direction to get the candidate heading
        check_dir = base_dir.rotate(angle)
        
        # Sweep endpoint for the circle cast
        p1 = pos + check_dir * look_ahead
        
        # Circle-cast (swept-circle test) against every obstacle rect
        hit_wall = circlecast_hits_any_rect(pos, p1, radius, rects)
        
        if not hit_wall:
            # Clear corridor found - always commit at full speed
            desired = check_dir * max_speed
            return (desired - vel, angle)
            
    # Every tested angle is still blocked: don't ram forward, back away from the
    # nearest obstacle so the snake repositions and gets a fresh angle next frame.
    nearest_obstacle_point = None
    nearest_dist = float('inf')
    for r in rects:
        np = nearest_point_on_rect(pos, r)
        d = (pos - np).length()
        if d < nearest_dist:
            nearest_dist = d
            nearest_obstacle_point = np

    if nearest_obstacle_point is not None and nearest_dist < radius * SNAKE_AVOID_RETREAT_RADIUS_MULT:
        away = pos - nearest_obstacle_point
        retreat_dir = away.normalize() if away.length_squared() > 0 else -base_dir
        desired = retreat_dir * max_speed * 0.6
    else:
        # Not actually touching anything nearby — safe to creep forward slowly and re-try
        desired = base_dir * max_speed * 0.4

    return (desired - vel, 0.0)

def arrive_with_avoid(pos, vel, target, max_speed, radius, rects, preferred_angle=0.0,
                       slow_radius=ARRIVE_SLOW_RADIUS, stop_radius=ARRIVE_STOP_RADIUS):
    """
    Unified Arrive + obstacle avoidance, for Patrol-style states.

    The old Patrol code called arrive(target) and seek_with_avoid(target)
    separately and ADDED the two resulting forces together — two complete,
    independently-computed steering forces that can point in different
    directions near an obstacle, which is what caused the rattling near
    trees. This function instead picks ONE direction — whatever
    seek_with_avoid decides on (straight at the target if clear, or a
    corridor-adjusted direction if something is in the way) — and applies
    Arrive's slow/stop-radius speed profile to that single direction, the
    same way Aggro lets seek_with_avoid have full authority over direction
    rather than fighting it with a separately-aimed force.

    Returns (force, angle) — same shape as seek_with_avoid, so callers can
    keep passing the returned angle back in as preferred_angle next frame.
    """
    d = target - pos
    dist = d.length()

    if dist < stop_radius:
        return -vel, preferred_angle  # same "cancel velocity" rule as arrive()

    avoid_force, angle = seek_with_avoid(pos, vel, target, max_speed, radius, rects,
                                          preferred_angle=preferred_angle)
    # seek_with_avoid returned avoid_force = desired_velocity - vel, so add
    # vel back to recover the DIRECTION it picked internally — we want to
    # reuse that direction, just re-scale its SPEED using Arrive's taper.
    desired_dir_vel = avoid_force + vel
    direction = desired_dir_vel.normalize() if desired_dir_vel.length_squared() > 0 else d.normalize()

    if dist < slow_radius:
        desired_speed = max_speed * (dist / slow_radius)
    else:
        desired_speed = max_speed

    desired_vel = direction * desired_speed
    return desired_vel - vel, angle

# ---------------- New behaviours to be implemented ----------------

def predict_future_position(pos, target_pos, target_vel, max_speed):
    """
    Shared prediction helper used by pursue(), evade(), and Aggro's unified
    seek_with_avoid call.
    Uses the combined closing speed (pursuer + target) to estimate a more
    accurate interception time_horizon than using either speed alone.
    """
    distance = (target_pos - pos).length()
    target_speed = target_vel.length()
    
    # Target is effectively stationary - no need to predict ahead
    if target_speed < 5.0:
        return target_pos
        
    # Combined closing speed gives a more realistic time-to-intercept
    closing_speed = max_speed + target_speed
    
    # Cap the horizon so long-range chases don't extrapolate too far ahead
    time_horizon = min(distance / closing_speed, 1.5)
    
    return target_pos + target_vel * time_horizon

def pursue(pos, vel, target_pos, target_vel, max_speed):
    """
    Predict the future position of the target then seek that point.
    Suggested
      distance = |target_pos - pos|
      time_horizon = distance / (max_speed + small_eps)
      predicted    = target_pos + target_vel * time_horizon
      return seek toward predicted
    Replace simple seek in Snake Aggro with pursue for better interception.
    """
    predicted = predict_future_position(pos, target_pos, target_vel, max_speed)
    return seek(pos, vel, predicted, max_speed)

def evade(pos, vel, threat_pos, threat_vel, max_speed, predict_speed=None):
    """
    Predict the future position of a threat then flee from that point.
    This is the inverse of pursue. Use the same prediction idea.

    predict_speed: speed used to scale the prediction time horizon
    (time_horizon = distance / predict_speed). Defaults to max_speed (the
    evader's own speed) for backward compatibility — but when the evader is
    much SLOWER than the threat (a fly evading the faster frog), that
    default inflates the time horizon and can push the predicted point past
    the evader's own position, flipping the flee direction so the evader
    briefly steers TOWARD the threat instead of away from it. Pass the
    threat's own speed here (e.g. FROG_SPEED) to fix that.
    """
    if predict_speed is None:
        predict_speed = max_speed
    predicted = predict_future_position(pos, threat_pos, threat_vel, predict_speed)
    return flee(pos, vel, predicted, max_speed)

import random
def wander_force(me_vel, jitter_deg=8.0, circle_distance=24.0, circle_radius=18.0,
                  rng_seed=None, smoothing=0.85):
    """
    Return a small random steering vector for gentle drift.
    Classic wander: project a small circle ahead along current heading,
    then jitter the target point on that circle by a tiny random angle
    each update.

    smoothing (0-1): exponential low-pass filter applied to the OUTPUT
    force, not the underlying angle random-walk. 0 = no smoothing (raw
    circle-wander output, can look twitchy at 60 FPS). Closer to 1 = each
    frame's force is mostly last frame's force with a small nudge, which
    is what actually removes the "steering noise" look without needing to
    swap in Perlin/OU noise — the circle-wander angle is already a random
    walk (smooth), the twitchiness was coming from applying its full
    output un-damped every frame.
    """
    if not hasattr(wander_force, "_state"):
        wander_force._state = {}

    if rng_seed not in wander_force._state:
        rng = random.Random(rng_seed) if rng_seed is not None else random.Random()
        wander_force._state[rng_seed] = {
            'angle': rng.uniform(0, 360),
            'rng': rng,
            'smoothed_force': V2(0, 0),
        }

    state = wander_force._state[rng_seed]
    rng = state['rng']

    # Jitter the angle (unchanged — this part was already correct)
    state['angle'] += rng.uniform(-jitter_deg, jitter_deg)

    if me_vel.length_squared() == 0:
        heading = V2(1, 0)
    else:
        heading = me_vel.normalize()

    circle_center = heading * circle_distance
    displacement = V2(circle_radius, 0).rotate(state['angle'])

    desired = circle_center + displacement
    raw_force = desired - me_vel

    # Low-pass filter: blend toward the new raw force instead of jumping to it
    state['smoothed_force'] = (
        state['smoothed_force'] * smoothing + raw_force * (1.0 - smoothing)
    )
    return state['smoothed_force']
</file>

<file path="part1/utils.py">
# ============================================================================
# utils.py
# Purpose
#   Small helper functions that do not belong to a specific agent.
#   Drawing helpers and collision checks live here.
# Notes
#   None of these helpers should change game rules or AI decisions.
# ============================================================================

import pygame
from pygame.math import Vector2 as V2
from settings import WIDTH, HEIGHT
import pygame.gfxdraw

# A soft grid color for the background
GRID = (36, 42, 48)

def draw_grid(surf):
    """
    Draw a light grid to help the eye judge motion and distance.
    The grid has no effect on gameplay. It is only visual.
    """
    gap = 36  # distance between grid lines
    # Draw vertical lines
    for x in range(0, WIDTH, gap):
        pygame.draw.line(surf, GRID, (x, 0), (x, HEIGHT))
    # Draw horizontal lines
    for y in range(0, HEIGHT, gap):
        pygame.draw.line(surf, GRID, (0, y), (WIDTH, y))

def clamp(x, a, b):
    """Limit a scalar value x so it stays between a and b inclusive."""
    return max(a, min(b, x))

def limit(v, max_len):
    """
    Limit a vector length.
    If v is longer than max_len, scale it down to exactly max_len.
    """
    if v.length_squared() > max_len * max_len:
        v.scale_to_length(max_len)
    return v

def nearest_point_on_rect(point, rect):
    """Return the closest point on an axis aligned rectangle to a given point."""
    x = clamp(point.x, rect.left, rect.right)
    y = clamp(point.y, rect.top, rect.bottom)
    return V2(x, y)

def circle_rect_intersect(center, radius, rect):
    """Return True if a circle touches or overlaps a rectangle."""
    np = nearest_point_on_rect(center, rect)
    return (center - np).length_squared() <= radius * radius

def segment_circlecast_hits_rect(p0, p1, radius, rect, step=6.0):
    """
    Approximate a circle cast along a line from p0 to p1.
    We sample points along the segment and test a circle intersect at each step.
    """
    d = p1 - p0
    length = d.length()
    if length == 0:
        return circle_rect_intersect(p0, radius, rect)
    n = max(1, int(length / step))
    for i in range(n + 1):
        t = i / n
        pos = p0 + d * t
        if circle_rect_intersect(pos, radius, rect):
            return True
    return False

def circlecast_hits_any_rect(p0, p1, radius, rects, step=6.0):
    """Return True if the swept circle between p0 and p1 hits any rect in the list."""
    for r in rects:
        if segment_circlecast_hits_rect(p0, p1, radius, r, step):
            return True
    return False

def draw_debug_overlay(surf, pos, vel, perception_radii, state_name=None, vel_color=(255, 100, 100)):
    """
    Draw debug overlay for an entity: velocity vector, perception radii, and state name.

    Parameters:
      surf: pygame surface to draw on
      pos: entity position (V2)
      vel: entity velocity (V2)
      perception_radii: list of (radius_value, color) tuples to draw as circles
      state_name: string name of state to render, or None to skip state text
      vel_color: color of the velocity arrow, so different entity types read distinctly
    """
    # Draw velocity vector — bigger scale, thicker line, solid filled arrowhead
    if vel.length_squared() > 0.01:
        vel_end = pos + vel * 0.45
        pygame.draw.line(surf, vel_color, pos, vel_end, 3)
        arrow_dir = vel.normalize()
        tip = vel_end + arrow_dir * 10
        left = vel_end + arrow_dir.rotate(140) * 9
        right = vel_end + arrow_dir.rotate(-140) * 9
        pygame.draw.polygon(surf, vel_color, [tip, left, right])

    # Draw perception radius circles
    for radius, color in perception_radii:
        pygame.draw.circle(surf, color, pos, radius, 1)

    # Draw state name as small text above entity, with a background for legibility
    if state_name is not None:
        from pygame.font import Font
        tiny_font = Font(None, 22)
        txt = tiny_font.render(state_name, True, (235, 235, 235))
        text_rect = txt.get_rect(midbottom=(int(pos.x), int(pos.y) - 20))
        bg_rect = text_rect.inflate(6, 4)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 140))
        surf.blit(bg_surf, bg_rect.topleft)
        surf.blit(txt, text_rect)

def draw_heart(screen, x, y, color):
    pts = [
        (x + 6, y + 18),
        (x + 17, y + 12),
        (x + 20, y + 5),
        (x + 16, y - 1),
        (x + 10, y - 2),
        (x + 6, y + 2),
        (x + 2, y - 2),
        (x - 4, y - 1),
        (x - 8, y + 5),
        (x - 5, y + 12),
    ]

    pygame.gfxdraw.aapolygon(screen, pts, (30, 30, 30))
    pygame.gfxdraw.filled_polygon(screen, pts, color)


from settings import EXPLORED_COLOR_LOW, EXPLORED_COLOR_HIGH

def draw_explored_heatmap(surf, grid, explored_cells, g_cost_by_cell, font):
    """
    Draws every explored A* cell as a translucent square colored by its
    g-cost (blue = cheap, red = expensive), with the numeric cost printed
    inside the cell. This satisfies "display the cost of each explored
    cell" and "show all explored areas before the frog follows the path".
    """
    if not explored_cells:
        return
    max_g = max(g_cost_by_cell[c] for c in explored_cells) or 1.0

    for cell in explored_cells:
        g = g_cost_by_cell[cell]
        t = clamp(g / max_g, 0.0, 1.0)
        color = (
            int(EXPLORED_COLOR_LOW[0] + (EXPLORED_COLOR_HIGH[0] - EXPLORED_COLOR_LOW[0]) * t),
            int(EXPLORED_COLOR_LOW[1] + (EXPLORED_COLOR_HIGH[1] - EXPLORED_COLOR_LOW[1]) * t),
            int(EXPLORED_COLOR_LOW[2] + (EXPLORED_COLOR_HIGH[2] - EXPLORED_COLOR_LOW[2]) * t),
        )
        world_pos = grid.cell_to_world(cell)
        rect = pygame.Rect(0, 0, grid.cell_size - 2, grid.cell_size - 2)
        rect.center = (world_pos.x, world_pos.y)

        cell_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cell_surf.fill((*color, 110))
        surf.blit(cell_surf, rect.topleft)

        label = font.render(f"{g:.0f}", True, (255, 255, 255))
        surf.blit(label, label.get_rect(center=(world_pos.x, world_pos.y)))


def draw_astar_path(surf, world_points):
    """Draws the smoothed A* path in green with waypoint markers."""
    if len(world_points) < 2:
        return
    pts = [(p.x, p.y) for p in world_points]
    pygame.draw.lines(surf, (90, 220, 120), False, pts, 4)
    for p in world_points:
        pygame.draw.circle(surf, (90, 220, 120), p, 5)
        pygame.draw.circle(surf, (255, 255, 255), p, 5, 1)
</file>

<file path="part1/world.py">
# ============================================================================
# world.py
# Purpose
#   Build the arena and a list of rectangular obstacles.
#   Obstacles are static and are used by the snake for avoidance checks.
# Why rectangles
#   Rectangles are easy to draw and fast to test against with our helpers.
# ============================================================================

import random
import pygame
from pathfinding import Grid
from settings import CELL_SIZE, PATH_OBSTACLE_PADDING

class World:
    def __init__(self, width, height):
        # Whole world bounds as a pygame.Rect for convenience
        self.rect = pygame.Rect(0, 0, width, height)

        # Container that holds all blocking rectangles
        self.obstacles = []

        # Build a reproducible obstacle set
        self._build_obstacles(width, height)

        # Bake a walkability grid once, used by A* (pathfinding.py). Obstacles
        # are inflated by the frog's radius so a path never hugs a wall.
        self.grid = Grid(width, height, CELL_SIZE, self.obstacles, padding=PATH_OBSTACLE_PADDING)


    def _build_obstacles(self, w, h):
        """Create a few rectangles with a fixed random seed for reproducibility."""
        rng = random.Random(9)
        for _ in range(9):
            ww = rng.randint(80, 180)
            hh = rng.randint(60, 140)
            x = rng.randint(40, w - ww - 40)
            y = rng.randint(40, h - hh - 40)
            rect = pygame.Rect(x, y, ww, hh)
            self.obstacles.append(rect)

    def draw(self, surf):
        """Render each obstacle with a fill and a subtle outline."""
        for r in self.obstacles:
            pygame.draw.rect(surf, (70, 85, 95), r, border_radius=10)
            pygame.draw.rect(surf, (110, 130, 145), r, 2, border_radius=10)
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

<file path="README.md">
# GAIT-ASM2
</file>

</files>
