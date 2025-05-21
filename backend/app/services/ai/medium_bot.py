# backend/app/services/ai/medium_bot.py
import random
import math
from typing import Tuple, List, Optional, Dict

from .base_bot import BaseBot, GameLogicBoard
from app.services.game_logic import (
    is_valid_move,
    check_win,
    ROWS,
    COLS,
    PLAYER_X,
    PLAYER_O,
    EMPTY_CELL,
    CONNECT_N,
    # We need a way to simulate apply_move without modifying the board passed,
    # or by always working on copies.
)


# Helper to simulate applying a move and getting resulting coordinates
def _simulate_apply_move(
    board: GameLogicBoard, row: int, side: str, player: str
) -> Optional[Tuple[int, int]]:
    # Assumes board is a copy if it's not to be modified by this simulation
    target_row = board[row]
    if side == "L":
        for c in range(COLS):
            if target_row[c] == EMPTY_CELL:
                target_row[c] = player
                return (row, c)
    elif side == "R":
        for c in range(COLS - 1, -1, -1):
            if target_row[c] == EMPTY_CELL:
                target_row[c] = player
                return (row, c)
    return None


class MediumAIBot(BaseBot):
    def __init__(
        self, player_piece: str, search_depth: int = 2
    ):  # Depth 2 means AI move, Opponent reply
        super().__init__(player_piece)
        self.opponent_piece = PLAYER_O if self.player_piece == PLAYER_X else PLAYER_X
        self.search_depth = search_depth

    def _get_all_valid_moves(self, board: GameLogicBoard) -> List[Tuple[int, str]]:
        valid_moves = []
        for r in range(ROWS):
            if is_valid_move(board, r, "L"):  # is_valid_move doesn't modify board
                valid_moves.append((r, "L"))
            if is_valid_move(board, r, "R"):
                valid_moves.append((r, "R"))
        # Shuffle to add some variability if scores are equal
        random.shuffle(valid_moves)
        return valid_moves

    def _evaluate_line(self, line: List[Optional[str]], piece: str) -> int:
        score = 0
        opponent_piece = PLAYER_O if piece == PLAYER_X else PLAYER_X

        # Count occurrences of piece and opponent_piece in the window
        piece_count = line.count(piece)
        opponent_count = line.count(opponent_piece)
        empty_count = line.count(EMPTY_CELL)

        if piece_count == CONNECT_N:
            return 100000  # AI wins
        if opponent_count == CONNECT_N:
            return -100000  # Opponent wins (AI should avoid this state for opponent)

        if piece_count == CONNECT_N - 1 and empty_count == 1:
            score += 100  # AI has three in a line with one empty
        elif piece_count == CONNECT_N - 2 and empty_count == 2:
            score += 10  # AI has two in a line with two empty

        if opponent_count == CONNECT_N - 1 and empty_count == 1:
            score -= 1000  # Opponent has three in a line (high threat)
        elif opponent_count == CONNECT_N - 2 and empty_count == 2:
            score -= 50  # Opponent has two in a line

        return score

    def _evaluate_board(self, board: GameLogicBoard, for_player: str) -> int:
        score = 0

        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - CONNECT_N + 1):
                window = [board[r][c + i] for i in range(CONNECT_N)]
                score += self._evaluate_line(window, for_player)

        # Vertical
        for c in range(COLS):
            for r in range(ROWS - CONNECT_N + 1):
                window = [board[r + i][c] for i in range(CONNECT_N)]
                score += self._evaluate_line(window, for_player)

        # Positive Diagonal (\)
        for r in range(ROWS - CONNECT_N + 1):
            for c in range(COLS - CONNECT_N + 1):
                window = [board[r + i][c + i] for i in range(CONNECT_N)]
                score += self._evaluate_line(window, for_player)

        # Negative Diagonal (/)
        for r in range(CONNECT_N - 1, ROWS):
            for c in range(COLS - CONNECT_N + 1):
                window = [board[r - i][c + i] for i in range(CONNECT_N)]
                score += self._evaluate_line(window, for_player)

        return score

    def minimax(
        self,
        board: GameLogicBoard,
        depth: int,
        alpha: float,
        beta: float,
        maximizing_player: bool,
    ) -> int:
        # Check terminal states
        if check_win(board, self.player_piece):  # AI (self) wins
            return 100000 + depth  # Prioritize faster wins
        if check_win(board, self.opponent_piece):  # Opponent wins
            return -100000 - depth  # Prioritize blocking faster opponent wins

        is_board_full = not any(EMPTY_CELL in row for row in board)
        if is_board_full or depth == 0:  # Draw or depth limit
            return self._evaluate_board(board, self.player_piece)  # Evaluate for AI

        valid_moves = self._get_all_valid_moves(board)
        if not valid_moves:  # No moves left (should be caught by is_board_full)
            return self._evaluate_board(board, self.player_piece)

        if maximizing_player:  # AI's turn (maximizer)
            max_eval = -math.inf
            for move in valid_moves:
                row, side = move
                temp_board = [r[:] for r in board]  # Create a copy
                # Simulate AI's move
                _simulate_apply_move(temp_board, row, side, self.player_piece)

                eval_score = self.minimax(
                    temp_board, depth - 1, alpha, beta, False
                )  # Opponent's turn next
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cut-off
            return max_eval
        else:  # Opponent's turn (minimizer)
            min_eval = math.inf
            for move in valid_moves:
                row, side = move
                temp_board = [r[:] for r in board]  # Create a copy
                # Simulate opponent's move
                _simulate_apply_move(temp_board, row, side, self.opponent_piece)

                eval_score = self.minimax(
                    temp_board, depth - 1, alpha, beta, True
                )  # AI's turn next
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cut-off
            return min_eval

    def get_move(self, board: GameLogicBoard) -> Optional[Tuple[int, str]]:
        valid_moves = self._get_all_valid_moves(board)
        if not valid_moves:
            return None

        best_score = -math.inf
        best_move = None  # random.choice(valid_moves) # Default to a random move

        # Check for immediate win first (can be faster than full minimax for depth 0 win)
        for move in valid_moves:
            r, s = move
            temp_b = [row[:] for row in board]
            coords = _simulate_apply_move(temp_b, r, s, self.player_piece)
            if coords and check_win(temp_b, self.player_piece, coords):
                # print(f"MediumAI ({self.player_piece}): Found immediate winning move at {move}")
                return move

        # Check to block immediate opponent win
        for move in valid_moves:  # AI's potential moves
            r, s = move
            # What spot would AI land on if it made this move?
            ai_landing_spot_board = [row[:] for row in board]
            sim_coords_ai_landing = _simulate_apply_move(
                ai_landing_spot_board, r, s, "TEMP"
            )  # Use temp piece

            if sim_coords_ai_landing:
                # Can opponent win by placing THEIR piece at sim_coords_ai_landing on ORIGINAL board?
                opponent_win_check_board = [row[:] for row in board]
                opponent_win_check_board[sim_coords_ai_landing[0]][
                    sim_coords_ai_landing[1]
                ] = self.opponent_piece
                if check_win(
                    opponent_win_check_board, self.opponent_piece, sim_coords_ai_landing
                ):
                    # print(f"MediumAI ({self.player_piece}): Blocking opponent win with move {move} at {sim_coords_ai_landing}")
                    return move  # This AI move blocks opponent's win

        # If no immediate win/loss, use Minimax for strategic move
        alpha = -math.inf
        beta = math.inf

        # If only one valid move, take it (e.g. nearly full board)
        if len(valid_moves) == 1:
            return valid_moves[0]

        for move in valid_moves:
            row, side = move
            temp_board = [r[:] for r in board]
            _simulate_apply_move(
                temp_board, row, side, self.player_piece
            )  # AI makes this move

            # Opponent will play next, so it's minimizing player's turn from AI's perspective
            eval_score = self.minimax(
                temp_board, self.search_depth - 1, alpha, beta, False
            )

            if eval_score > best_score:
                best_score = eval_score
                best_move = move
            # Basic alpha update for the root node's children
            alpha = max(alpha, eval_score)

        # print(f"MediumAI ({self.player_piece}): Chose move {best_move} with score {best_score} from {len(valid_moves)} options.")
        return (
            best_move if best_move else random.choice(valid_moves)
        )  # Fallback if all moves have terrible scores (shouldn't happen)


if __name__ == "__main__":
    from app.services.game_logic import (
        print_board,
        create_board,
        apply_move as actual_apply_move,
    )

    test_board = create_board()
    # P1: (0,L) -> (0,0)X
    # P2: (0,L) -> (0,1)O
    # P1: (1,L) -> (1,0)X
    # P2: (1,L) -> (1,1)O
    # P1: (2,L) -> (2,0)X
    # P2: (2,R) -> (2,6)O
    # P1: (3,L) -> (3,0)X <- P1 wants to win here with (3,L)

    actual_apply_move(test_board, 0, "L", PLAYER_X)
    actual_apply_move(test_board, 0, "L", PLAYER_O)
    actual_apply_move(test_board, 1, "L", PLAYER_X)
    actual_apply_move(test_board, 1, "L", PLAYER_O)
    actual_apply_move(test_board, 2, "L", PLAYER_X)
    actual_apply_move(test_board, 2, "R", PLAYER_O)  # O plays on right

    print("Board before MediumAI (X)'s turn:")
    print_board(test_board)

    medium_bot_x = MediumAIBot(PLAYER_X, search_depth=2)  # X is AI
    # X needs one more X at (3,0) to win. (0,0) (1,0) (2,0) are X.
    # Or it needs to block O.

    print(f"\nMediumAI ({PLAYER_X}) thinking...")
    chosen_move = medium_bot_x.get_move(test_board)
    print(f"MediumAI ({PLAYER_X}) suggests move: {chosen_move}")

    if chosen_move:
        actual_apply_move(test_board, chosen_move[0], chosen_move[1], PLAYER_X)
        print_board(test_board)
        if check_win(test_board, PLAYER_X):
            print("MediumAI X wins!")

    test_board_o_threat = create_board()
    actual_apply_move(test_board_o_threat, 0, "L", PLAYER_O)  # O
    actual_apply_move(test_board_o_threat, 0, "L", PLAYER_O)  # O
    actual_apply_move(test_board_o_threat, 0, "L", PLAYER_O)  # O
    actual_apply_move(test_board_o_threat, 1, "L", PLAYER_X)  # X
    actual_apply_move(test_board_o_threat, 2, "L", PLAYER_X)  # X
    print("\nBoard where O threatens win, X (AI) to move:")
    print_board(test_board_o_threat)
    medium_bot_x_block = MediumAIBot(PLAYER_X, search_depth=2)
    chosen_move_block = medium_bot_x_block.get_move(test_board_o_threat)
    print(
        f"MediumAI ({PLAYER_X}) suggests move to block: {chosen_move_block}"
    )  # Should be (0,L) to block (0,3)
