# Baseline snapshot — line 171 of connect4_mcts.py
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
