# Baseline snapshot — line 415 of connect4_mcts.py
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

