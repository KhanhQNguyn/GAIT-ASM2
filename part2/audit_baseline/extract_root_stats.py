# Baseline snapshot — line 551 of connect4_mcts.py
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

