# backend/app/services/ai/medium_bot.py
import random
import math
from typing import Tuple, List, Optional, Dict

from .base_bot import BaseBot, GameLogicBoard
from app.services.game_logic import (
    is_valid_move,
    check_win
)
from app.core.constants import (
    COLS,
    PLAYER_X,
    PLAYER_O,
    EMPTY_CELL,
    ROWS,
    CONNECT_N
)

from app.core.logging_config import setup_logger

logger = setup_logger(__name__)


# Helper to simulate applying a move and getting resulting coordinates
def _simulate_apply_move_and_get_coords(
    board: GameLogicBoard, row: int, side: str, player: str
) -> Optional[Tuple[int, int]]:
    # IMPORTANT: This function MODIFIES the board passed to it. Always pass a copy.
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

    def _evaluate_line(
        self, line: List[Optional[str]], piece_to_evaluate_for: str
    ) -> int:
        # piece_to_evaluate_for is self.player_piece (the AI)
        score = 0
        ai_piece = piece_to_evaluate_for
        opponent_piece = (
            self.opponent_piece if ai_piece == self.player_piece else self.player_piece
        )

        ai_count = line.count(ai_piece)
        opponent_count = line.count(opponent_piece)
        empty_count = line.count(EMPTY_CELL)

        if ai_count == CONNECT_N:
            return 100000  # AI wins
        if opponent_count == CONNECT_N:
            return -100000  # Opponent wins (very bad for AI)

        if ai_count == CONNECT_N - 1 and empty_count == 1:
            score += 1000  # AI 3-in-a-row, 1 empty
        elif ai_count == CONNECT_N - 2 and empty_count == 2:
            score += 100  # AI 2-in-a-row, 2 empty

        if opponent_count == CONNECT_N - 1 and empty_count == 1:
            score -= 5000  # Opponent 3-in-a-row (CRITICAL BLOCK)
        elif opponent_count == CONNECT_N - 2 and empty_count == 2:
            score -= 50  # Opponent 2-in-a-row

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
                _simulate_apply_move_and_get_coords(
                    temp_board, row, side, self.player_piece
                )

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
                _simulate_apply_move_and_get_coords(
                    temp_board, row, side, self.opponent_piece
                )

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
        if len(valid_moves) == 1:
            return valid_moves[0]

        # 1. Check for AI's immediate winning move
        for move_action in valid_moves:
            r, s = move_action
            temp_board_ai_win = [row[:] for row in board]
            coords = _simulate_apply_move_and_get_coords(
                temp_board_ai_win, r, s, self.player_piece
            )
            if coords and check_win(temp_board_ai_win, self.player_piece, coords):
                # print(f"MediumAI ({self.player_piece}): Taking winning move {move_action}")
                return move_action

        # 2. Check to block opponent's immediate winning move
        # For each spot the opponent could play to win, can AI play there first?
        opponent_winning_moves_to_block = []
        for opp_r in range(ROWS):  # Check all possible opponent moves
            for opp_s in ["L", "R"]:
                if is_valid_move(board, opp_r, opp_s):  # Can opponent play here?
                    temp_board_opp_check = [row[:] for row in board]
                    opp_coords = _simulate_apply_move_and_get_coords(
                        temp_board_opp_check, opp_r, opp_s, self.opponent_piece
                    )
                    if opp_coords and check_win(
                        temp_board_opp_check, self.opponent_piece, opp_coords
                    ):
                        # Opponent can win by playing at (opp_r, opp_s) which results in opp_coords
                        # Can AI play at (opp_r, opp_s) and land on opp_coords?
                        # This means AI needs to make the move (opp_r, opp_s)
                        if (opp_r, opp_s) in valid_moves:
                            # print(f"MediumAI ({self.player_piece}): Opponent can win with ({opp_r},{opp_s}). AI must block.")
                            opponent_winning_moves_to_block.append((opp_r, opp_s))

        if opponent_winning_moves_to_block:
            # If multiple blocking moves, pick one (e.g., first found, or one evaluated best by heuristic)
            # For Medium, just pick the first one found that's a valid AI move.
            # print(f"MediumAI ({self.player_piece}): Blocking opponent's win with {opponent_winning_moves_to_block[0]}")
            return opponent_winning_moves_to_block[0]

        # 3. If no immediate win/loss, use Minimax
        best_score = -math.inf
        best_move = None
        alpha = -math.inf
        beta = math.inf

        for move_action in valid_moves:
            r, s = move_action
            temp_board = [row[:] for row in board]
            _simulate_apply_move_and_get_coords(
                temp_board, r, s, self.player_piece
            )  # AI makes this move

            score = self.minimax(
                temp_board, self.search_depth - 1, alpha, beta, False
            )  # Opponent plays next

            if score > best_score:
                best_score = score
                best_move = move_action
            alpha = max(alpha, score)  # For root node, this is just tracking best score

        # print(f"MediumAI ({self.player_piece}): Chose {best_move} (score: {best_score}) via Minimax.")
        return best_move if best_move else random.choice(valid_moves)


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

    logger.info("Board before MediumAI (X)'s turn:")
    print_board(test_board)

    medium_bot_x = MediumAIBot(PLAYER_X, search_depth=2)  # X is AI
    # X needs one more X at (3,0) to win. (0,0) (1,0) (2,0) are X.
    # Or it needs to block O.

    logger.info(f"\nMediumAI ({PLAYER_X}) thinking...")
    chosen_move = medium_bot_x.get_move(test_board)
    logger.info(f"MediumAI ({PLAYER_X}) suggests move: {chosen_move}")

    if chosen_move:
        actual_apply_move(test_board, chosen_move[0], chosen_move[1], PLAYER_X)
        print_board(test_board)
        if check_win(test_board, PLAYER_X):
            logger.info("MediumAI X wins!")

    test_board_o_threat = create_board()
    actual_apply_move(test_board_o_threat, 0, "L", PLAYER_O)  # O
    actual_apply_move(test_board_o_threat, 0, "L", PLAYER_O)  # O
    actual_apply_move(test_board_o_threat, 0, "L", PLAYER_O)  # O
    actual_apply_move(test_board_o_threat, 1, "L", PLAYER_X)  # X
    actual_apply_move(test_board_o_threat, 2, "L", PLAYER_X)  # X
    logger.info("\nBoard where O threatens win, X (AI) to move:")
    print_board(test_board_o_threat)
    medium_bot_x_block = MediumAIBot(PLAYER_X, search_depth=2)
    chosen_move_block = medium_bot_x_block.get_move(test_board_o_threat)
    logger.info(
        f"MediumAI ({PLAYER_X}) suggests move to block: {chosen_move_block}"
    )  # Should be (0,L) to block (0,3)
