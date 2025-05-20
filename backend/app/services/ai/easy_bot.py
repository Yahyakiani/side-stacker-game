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
        self.opponent_piece = PLAYER_O if self.player_piece == PLAYER_X else PLAYER_X

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
            return None  # No valid moves left (should mean draw or game ended before AI's turn)

        # 1. Check for an immediate winning move for self
        for move in valid_moves:
            row, side = move
            # Create a temporary copy of the board to simulate the move
            temp_board = [row_list[:] for row_list in board]  # Deep copy

            # Simulate applying the move (need coordinates for check_win)
            # We need a way to get coordinates without actually modifying the main board
            # For simplicity, let's simulate the placement to find coordinates
            # This is a bit clunky; a better approach might be for apply_move to not modify
            # if a 'simulate' flag is true, or have a separate simulate_move function.
            # For EasyAI, this direct simulation is probably fine.

            # Find where the piece would land
            temp_target_row = temp_board[row]
            placed_coords = None
            if side == "L":
                for c in range(COLS):
                    if temp_target_row[c] == EMPTY_CELL:
                        temp_target_row[c] = self.player_piece  # Temporarily place
                        placed_coords = (row, c)
                        break
            elif side == "R":
                for c in range(COLS - 1, -1, -1):
                    if temp_target_row[c] == EMPTY_CELL:
                        temp_target_row[c] = self.player_piece  # Temporarily place
                        placed_coords = (row, c)
                        break

            if placed_coords and check_win(
                temp_board, self.player_piece, placed_coords
            ):
                # print(f"EasyAI ({self.player_piece}): Found winning move at {move}")
                return move  # Take the winning move
            # No need to revert temp_board change as it's a copy for this move check only

        # 2. Check to block opponent's immediate winning move
        for move in valid_moves:  # Iterate through AI's possible moves
            row, side = move
            # Simulate AI making this move, then check if opponent can win on THEIR next turn
            # This is becoming more complex. For EasyAI, let's simplify:
            # Check if opponent has a winning move on *their* current turn if AI doesn't move.
            # No, the rule is: if AI can block an *opponent's next winning move*.

            # So, for each of AI's valid moves:
            #   - AI makes its move (temp_board_after_ai_move)
            #   - Then, iterate all of opponent's possible next moves on temp_board_after_ai_move
            #   - If any of AI's moves PREVENTS ALL opponent's winning replies, that's complex.

            # Simpler "block" for Easy AI:
            # Iterate through opponent's possible winning moves on the *current* board.
            # If AI makes a move `(r,s)` that lands on the same spot as an opponent's winning move,
            # that's a block.

            # Create a temporary copy of the board to simulate the AI's potential block
            temp_board_for_block_check = [row_list[:] for row_list in board]
            # Simulate AI making its move (row, side)
            sim_placed_coords_ai = None
            temp_target_row_ai = temp_board_for_block_check[row]
            if side == "L":
                for c in range(COLS):
                    if temp_target_row_ai[c] == EMPTY_CELL:
                        sim_placed_coords_ai = (row, c)
                        break
            elif side == "R":
                for c in range(COLS - 1, -1, -1):
                    if temp_target_row_ai[c] == EMPTY_CELL:
                        sim_placed_coords_ai = (row, c)
                        break

            # Now, check if opponent has a winning move on the ORIGINAL board
            # that would land at sim_placed_coords_ai
            if sim_placed_coords_ai:
                # Temporarily place opponent's piece at that spot on a *different* temp board
                # to see if it's a winning spot for them.
                temp_board_opponent_win_check = [row_list[:] for row_list in board]
                temp_board_opponent_win_check[sim_placed_coords_ai[0]][
                    sim_placed_coords_ai[1]
                ] = self.opponent_piece
                if check_win(
                    temp_board_opponent_win_check,
                    self.opponent_piece,
                    sim_placed_coords_ai,
                ):
                    # print(f"EasyAI ({self.player_piece}): Found blocking move at {move} for opponent's win at {sim_placed_coords_ai}")
                    return move  # This move by AI blocks an opponent's win

        # 3. Make a random valid move
        # print(f"EasyAI ({self.player_piece}): Making random move.")
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
