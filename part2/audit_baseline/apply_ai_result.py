# Baseline snapshot — line 891 of connect4_mcts.py
from connect4_mcts import game_over
from connect4_mcts import drop_animation
from connect4_mcts import winning_cells
from connect4_mcts import last_ai_stats
from connect4_mcts import last_move
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

