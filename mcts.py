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
