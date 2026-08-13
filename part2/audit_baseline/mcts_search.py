# Baseline snapshot — line 571 of connect4_mcts.py
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
