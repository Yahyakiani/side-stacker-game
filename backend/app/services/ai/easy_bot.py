# backend/app/services/ai/easy_bot.py
import random
from typing import Tuple, List, Optional

from .base_bot import BaseBot, GameLogicBoard
from app.services.game_logic import (  # Import necessary functions from game_logic
    is_valid_move,
    apply_move as service_apply_move,  # To avoid confusion if we had a local apply_move
    check_win,
    ROWS,
    COLS,
    PLAYER_X,
    PLAYER_O,
    EMPTY_CELL,
)


class EasyAIBot(BaseBot):
    def __init__(self, player_piece: str):
        super().__init__(player_piece)
        # self.opponent_piece = PLAYER_O if self.player_piece == PLAYER_X else PLAYER_X

    def _get_all_valid_moves(self, board: GameLogicBoard) -> List[Tuple[int, str]]:
        valid_moves = []
        for r in range(ROWS):
            if is_valid_move(board, r, "L"):
                valid_moves.append((r, "L"))
            if is_valid_move(board, r, "R"):  # Check right side independently
                valid_moves.append((r, "R"))
        return valid_moves

    def get_move(self, board: GameLogicBoard) -> Optional[Tuple[int, str]]:
        valid_moves = self._get_all_valid_moves(board)
        if not valid_moves:
            return None

        # 1. Immediate winning move
        for move in valid_moves:
            row, side = move
            temp_board = [row_list[:] for row_list in board]
            placed_coords = None
            temp_target_row = temp_board[row]
            if side == "L":
                for c in range(COLS):
                    if temp_target_row[c] == EMPTY_CELL:
                        temp_target_row[c] = self.player_piece
                        placed_coords = (row, c)
                        break
            else:  # "R"
                for c in range(COLS - 1, -1, -1):
                    if temp_target_row[c] == EMPTY_CELL:
                        temp_target_row[c] = self.player_piece
                        placed_coords = (row, c)
                        break
            if placed_coords and check_win(
                temp_board, self.player_piece, placed_coords
            ):
                return move  # Take winning move

        # 2. No block logic—just random
        return random.choice(valid_moves)

if __name__ == "__main__":
    from app.services.game_logic import print_board, create_board

    # Test EasyBot
    board1 = create_board()
    # Setup a scenario where 'O' can win
    board1[0][0] = PLAYER_O
    board1[0][1] = PLAYER_O
    board1[0][2] = PLAYER_O
    # board1[0][3] is empty - O can win here
    print("Scenario 1: O can win at (0,3) via (0,L)")
    print_board(board1)

    easy_bot_x = EasyAIBot(PLAYER_X)  # X needs to block
    move_x = easy_bot_x.get_move(board1)
    print(f"EasyBot X suggests move: {move_x}")  # Should be (0, "L") to place at (0,3)

    # Test winning move for self
    board2 = create_board()
    board2[1][0] = PLAYER_X
    board2[1][1] = PLAYER_X
    board2[1][2] = PLAYER_X
    # board2[1][3] is empty - X can win here
    print("\nScenario 2: X can win at (1,3) via (1,L)")
    print_board(board2)
    move_x2 = easy_bot_x.get_move(board2)
    print(f"EasyBot X suggests move: {move_x2}")  # Should be (1, "L")

    # Test random move
    board3 = create_board()
    print("\nScenario 3: Random move")
    print_board(board3)
    move_x3 = easy_bot_x.get_move(board3)
    print(f"EasyBot X suggests random move: {move_x3}")  # Should be a valid move
