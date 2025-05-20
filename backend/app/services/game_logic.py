from typing import List, Optional, Tuple


ROWS: int = 7
COLS: int = 7
CONNECT_N: int = 4

PLAYER_X: str = "X"
PLAYER_O: str = "O"
EMPTY_CELL: Optional[str] = None

Board = List[List[Optional[str]]]

def create_board() -> Board:
    """Creates a new empty game board."""
    return [[EMPTY_CELL for _ in range(COLS)] for _ in range(ROWS)]

def print_board(board: Board):
    """Helper function to print the board to the console (for debugging)."""
    print("\n  " + " ".join(str(i) for i in range(COLS))) 
    for r_idx, row in enumerate(board):
        display_row = [cell if cell is not None else "_" for cell in row]
        print(f"{r_idx} [" + " ".join(display_row) + "]")
    print("-" * (COLS * 2 + 5))

def is_valid_move(board: Board, row_idx: int, side: str) -> bool:
    """
    Checks if a piece can be placed in the given row from the given side ('L' or 'R').
    """
    if not (0 <= row_idx < ROWS):
        return False
    if side not in ["L", "R"]:
        return False
    target_row = board[row_idx]
    if side == "L":
        for col_idx in range(COLS):
            if target_row[col_idx] == EMPTY_CELL:
                return True
        return False
    elif side == "R":
        for col_idx in range(COLS - 1, -1, -1):
            if target_row[col_idx] == EMPTY_CELL:
                return True
        return False
    return False

def apply_move(board: Board, row_idx: int, side: str, player: str) -> Optional[Tuple[int, int]]:
    """
    Places the player's piece on the board from the specified side.
    Returns the (row, col) of the placed piece if successful, otherwise None.
    """
    if not is_valid_move(board, row_idx, side):
        return None
    target_row = board[row_idx]
    placed_coords: Optional[Tuple[int, int]] = None
    if side == "L":
        for col_idx in range(COLS):
            if target_row[col_idx] == EMPTY_CELL:
                target_row[col_idx] = player
                placed_coords = (row_idx, col_idx)
                break
    elif side == "R":
        for col_idx in range(COLS - 1, -1, -1):
            if target_row[col_idx] == EMPTY_CELL:
                target_row[col_idx] = player
                placed_coords = (row_idx, col_idx)
                break
    return placed_coords

def check_win(board: Board, player: str, last_move_coords: Optional[Tuple[int, int]] = None) -> bool:
    """
    Checks if the given player has won.
    If last_move_coords is provided, it ideally would optimize by checking only lines involving that piece.
    For simplicity in this initial version, we will check the whole board.
    A more optimized version could be implemented later if performance becomes an issue.
    """
    # Check horizontal wins
    for r in range(ROWS):
        for c in range(COLS - CONNECT_N + 1):
            if all(board[r][c + i] == player for i in range(CONNECT_N)):
                return True

    # Check vertical wins
    for c in range(COLS):
        for r in range(ROWS - CONNECT_N + 1):
            if all(board[r + i][c] == player for i in range(CONNECT_N)):
                return True

    # Check positive diagonal wins (\)
    for r in range(ROWS - CONNECT_N + 1):
        for c in range(COLS - CONNECT_N + 1):
            if all(board[r + i][c + i] == player for i in range(CONNECT_N)):
                return True

    # Check negative diagonal wins (/)
    for r in range(CONNECT_N - 1, ROWS):
        for c in range(COLS - CONNECT_N + 1):
            if all(board[r - i][c + i] == player for i in range(CONNECT_N)):
                return True
                
    return False

def check_draw(board: Board) -> bool:
    """
    Checks if the game is a draw (board is full and no winner).
    This function assumes check_win would be called first for both players.
    A draw occurs if all cells are filled and no one has won.
    """
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == EMPTY_CELL:
                return False # Found an empty cell, so not a draw
    return True # All cells are filled


if __name__ == '__main__':
    # --- Existing Test Cases from Step 1.1 ---
    game_board = create_board()
    print("Initial Board:")
    print_board(game_board)

    print(f"\nIs move (0, 'L') valid? {is_valid_move(game_board, 0, 'L')}") 
    print(f"Is move (7, 'L') valid? {is_valid_move(game_board, 7, 'L')}") 
    print(f"Is move (0, 'X') valid? {is_valid_move(game_board, 0, 'X')}") 

    print("\nApplying move (1, 'L', PLAYER_X)")
    coords = apply_move(game_board, 1, "L", PLAYER_X)
    print(f"Piece placed at: {coords}")
    print_board(game_board)

    print("\nApplying move (1, 'R', PLAYER_O)")
    coords = apply_move(game_board, 1, "R", PLAYER_O)
    print(f"Piece placed at: {coords}")
    print_board(game_board)

    print("\nApplying move (1, 'L', PLAYER_X)") 
    coords = apply_move(game_board, 1, "L", PLAYER_X)
    print(f"Piece placed at: {coords}")
    print_board(game_board)
    
    print("\nApplying move (1, 'L', PLAYER_O)") 
    coords = apply_move(game_board, 1, "L", PLAYER_O)
    print(f"Piece placed at: {coords}")
    print_board(game_board)

    temp_board_fill = create_board()
    for i in range(COLS):
        apply_move(temp_board_fill, 3, "L", PLAYER_X if i % 2 == 0 else PLAYER_O)
    print("\nBoard after filling row 3 (on temp_board_fill):")
    print_board(temp_board_fill)
    print(f"Is move (3, 'L') valid now? {is_valid_move(temp_board_fill, 3, 'L')}") 
    print(f"Is move (3, 'R') valid now? {is_valid_move(temp_board_fill, 3, 'R')}")

    print("\nTrying to apply move to full row (3, 'L', PLAYER_X) on temp_board_fill")
    coords = apply_move(temp_board_fill, 3, "L", PLAYER_X)
    print(f"Piece placed at: {coords}") 
    print_board(temp_board_fill)

    print("\nApplying move (6, 'R', PLAYER_O) to original game_board")
    coords = apply_move(game_board, 6, "R", PLAYER_O)
    print(f"Piece placed at: {coords}")
    print_board(game_board) # Print the original board being modified

    # --- New Test Cases for check_win and check_draw ---
    print("\n--- Testing Win Conditions ---")

    # Horizontal Win
    h_win_board = create_board()
    for i in range(CONNECT_N):
        apply_move(h_win_board, 0, "L", PLAYER_X)
    print_board(h_win_board)
    print(f"Player X wins horizontally? {check_win(h_win_board, PLAYER_X)}") # True
    print(f"Player O wins horizontally? {check_win(h_win_board, PLAYER_O)}") # False

    # Vertical Win
    v_win_board = create_board()
    for i in range(CONNECT_N):
        apply_move(v_win_board, i, "L", PLAYER_O)
    print_board(v_win_board)
    print(f"Player O wins vertically? {check_win(v_win_board, PLAYER_O)}") # True
    print(f"Player X wins vertically? {check_win(v_win_board, PLAYER_X)}") # False

    # Positive Diagonal Win (\)
    pd_win_board = create_board()
    for i in range(CONNECT_N):
        apply_move(pd_win_board, i, "L", PLAYER_X) # X at (0,0), (1,0), (2,0), (3,0) - need to adjust for diagonal
    
    pd_win_board_actual = create_board() # Create a fresh board for this specific test
    for i in range(CONNECT_N):
        pd_win_board_actual[i][i] = PLAYER_X # (0,0), (1,1), (2,2), (3,3)
    print_board(pd_win_board_actual)
    print(f"Player X wins pos-diag? {check_win(pd_win_board_actual, PLAYER_X)}") # True

    # Negative Diagonal Win (/)
    nd_win_board = create_board()
    for i in range(CONNECT_N):
        nd_win_board[CONNECT_N - 1 - i][i] = PLAYER_O # (3,0), (2,1), (1,2), (0,3) for CONNECT_N=4
    print_board(nd_win_board)
    print(f"Player O wins neg-diag? {check_win(nd_win_board, PLAYER_O)}") # True
    
    # No Win
    no_win_board = create_board()
    apply_move(no_win_board, 0, "L", PLAYER_X)
    apply_move(no_win_board, 1, "L", PLAYER_O)
    apply_move(no_win_board, 0, "L", PLAYER_X)
    print_board(no_win_board)
    print(f"Player X wins (no win board)? {check_win(no_win_board, PLAYER_X)}") # False
    print(f"Player O wins (no win board)? {check_win(no_win_board, PLAYER_O)}") # False

    print("\n--- Testing Draw Condition ---")
    draw_board = create_board()
    # Fill the board without a winner (checkerboard pattern)
    for r in range(ROWS):
        for c in range(COLS):
            if (r + c) % 2 == 0:
                draw_board[r][c] = PLAYER_X
            else:
                draw_board[r][c] = PLAYER_O
    
    # Ensure no one actually won with this pattern (unlikely for connect 4 but good test for full board)
    # This pattern might accidentally create a win, so a better draw test is just a full board.
    # Let's make a specific non-winning full board for testing draw.
    # For simplicity, assume no win, just check if full.
    
    full_board_no_win = create_board() # Create a fresh board
    for r_idx in range(ROWS):
        for c_idx in range(COLS):
            # A simple alternating pattern that's unlikely to win immediately but fills the board
            full_board_no_win[r_idx][c_idx] = PLAYER_X if (r_idx + c_idx) % 2 == 0 else PLAYER_O

    print_board(full_board_no_win)
    is_x_winner_on_full = check_win(full_board_no_win, PLAYER_X)
    is_o_winner_on_full = check_win(full_board_no_win, PLAYER_O)
    print(f"Is X winner on full board? {is_x_winner_on_full}")
    print(f"Is O winner on full board? {is_o_winner_on_full}")
    
    # Only a draw if no one has won AND the board is full
    is_it_a_draw = check_draw(full_board_no_win) and not is_x_winner_on_full and not is_o_winner_on_full
    print(f"Is it a draw (full board, assumed no win)? {check_draw(full_board_no_win)}") # True (if board is full)
    print(f"Actual Draw condition (full and no winner): {is_it_a_draw}")
    
    not_draw_board = create_board()
    apply_move(not_draw_board, 0, "L", PLAYER_X)
    print_board(not_draw_board)
    print(f"Is it a draw (not full board)? {check_draw(not_draw_board)}") # False
