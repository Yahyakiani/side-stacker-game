# File: test_game_logic.py
# backend/tests/test_game_logic.py
# Test cases for game logic functions

import pytest
from app.services.game_logic import (
    create_board,
    is_valid_move,
    apply_move,
    check_win,
    check_draw
)
from app.core.constants import (
    PLAYER_X,
    PLAYER_O,
    EMPTY_CELL,
    ROWS,
    COLS,
    CONNECT_N,
)

def test_create_board():
    board = create_board()
    assert len(board) == ROWS
    assert all(len(row) == COLS for row in board)
    assert all(cell == EMPTY_CELL for row in board for cell in row)

def test_is_valid_move_initial_board():
    board = create_board()
    assert is_valid_move(board, 0, "L") == True
    assert is_valid_move(board, ROWS - 1, "R") == True
    assert is_valid_move(board, ROWS, "L") == False  # Invalid row
    assert is_valid_move(board, -1, "R") == False # Invalid row
    assert is_valid_move(board, 0, "X") == False  # Invalid side

def test_apply_move_and_is_valid_after_moves():
    board = create_board()
    
    # Valid first move
    assert apply_move(board, 1, "L", PLAYER_X) == (1, 0)
    assert board[1][0] == PLAYER_X
    assert is_valid_move(board, 1, "L") == True # Next spot is valid

    # Valid second move on same row, different side
    assert apply_move(board, 1, "R", PLAYER_O) == (1, COLS - 1)
    assert board[1][COLS - 1] == PLAYER_O

    # Valid third move, stacking
    assert apply_move(board, 1, "L", PLAYER_X) == (1, 1)
    assert board[1][1] == PLAYER_X
    
    # Fill a row completely from left
    test_row = 3
    for i in range(COLS):
        assert apply_move(board, test_row, "L", PLAYER_X if i % 2 == 0 else PLAYER_O) == (test_row, i)
    
    assert is_valid_move(board, test_row, "L") == False # Row now full from left
    assert is_valid_move(board, test_row, "R") == False # Row now full from right (as it's entirely full)
    assert apply_move(board, test_row, "L", PLAYER_X) == None # Cannot apply move to full row

def test_check_win_horizontal():
    board = create_board()
    for i in range(CONNECT_N):
        board[0][i] = PLAYER_X # Manual placement for clear test
    assert check_win(board, PLAYER_X) == True
    assert check_win(board, PLAYER_O) == False

    board = create_board() # Test other side
    for i in range(CONNECT_N):
        board[1][COLS - 1 - i] = PLAYER_O
    assert check_win(board, PLAYER_O) == True

def test_check_win_vertical():
    board = create_board()
    for i in range(CONNECT_N):
        board[i][0] = PLAYER_X
    assert check_win(board, PLAYER_X) == True
    assert check_win(board, PLAYER_O) == False

    board = create_board() # Test other column
    for i in range(CONNECT_N):
        board[ROWS - 1 - i][COLS - 1] = PLAYER_O
    assert check_win(board, PLAYER_O) == True

def test_check_win_positive_diagonal(): # \
    board = create_board()
    for i in range(CONNECT_N):
        board[i][i] = PLAYER_X
    assert check_win(board, PLAYER_X) == True

    board = create_board()
    for i in range(CONNECT_N):
        board[1+i][2+i] = PLAYER_O # Offset diagonal
    assert check_win(board, PLAYER_O) == True

def test_check_win_negative_diagonal(): # /
    board = create_board()
    for i in range(CONNECT_N):
        board[CONNECT_N - 1 - i][i] = PLAYER_X
    assert check_win(board, PLAYER_X) == True
    
    board = create_board()
    for i in range(CONNECT_N):
        board[ROWS - 1 - i][COLS - CONNECT_N + i] = PLAYER_O # Offset diagonal from bottom right part
    assert check_win(board, PLAYER_O) == True
    
def test_no_win():
    board = create_board()
    apply_move(board, 0, "L", PLAYER_X)
    apply_move(board, 0, "L", PLAYER_O)
    apply_move(board, 1, "L", PLAYER_X)
    assert check_win(board, PLAYER_X) == False
    assert check_win(board, PLAYER_O) == False

def test_check_draw():
    board = create_board()
    assert check_draw(board) == False # Not full initially

    # Fill the board completely
    for r in range(ROWS):
        for c in range(COLS):
            board[r][c] = PLAYER_X if (r + c) % 2 == 0 else PLAYER_O 
            # This pattern might lead to a win, but check_draw only cares if full
    
    assert check_draw(board) == True # Board is now full

    # Test a scenario where board is full but there's a winner
    # check_draw should still be true, game logic layer decides outcome
    win_board_full = create_board()
    for r in range(ROWS): # Fill all cells
         for c in range(COLS):
            win_board_full[r][c] = PLAYER_O
    for i in range(CONNECT_N): # Ensure X has a winning line
        win_board_full[0][i] = PLAYER_X
    
    assert check_draw(win_board_full) == True # Still full
    assert check_win(win_board_full, PLAYER_X) == True # X has won

def test_edge_case_stacking_full_row():
    board = create_board()
    row_to_fill = 2
    # Fill from left
    for i in range(COLS // 2):
        apply_move(board, row_to_fill, "L", PLAYER_X)
    # Fill from right
    for i in range(COLS - (COLS // 2)): # remaining cells
        apply_move(board, row_to_fill, "R", PLAYER_O)
    
    # Now the row should be full
    assert is_valid_move(board, row_to_fill, "L") == False
    assert is_valid_move(board, row_to_fill, "R") == False