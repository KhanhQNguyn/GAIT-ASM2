# Baseline snapshot — line 510 of connect4_mcts.py
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


