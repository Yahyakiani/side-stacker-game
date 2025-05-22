# backend/app/services/ai/hard_bot.py
import random
import math
from typing import Tuple, List, Optional

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
)

from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

# Use the same helper as MediumBot or define it here
def _simulate_apply_move_and_get_coords(
    board: GameLogicBoard, row: int, side: str, player: str
) -> Optional[Tuple[int, int]]:
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


class HardAIBot(BaseBot):

    def __init__(
        self, player_piece: str, search_depth: int = 3
    ):  # Default depth 3 for Hard
        super().__init__(player_piece)
        self.opponent_piece = PLAYER_O if self.player_piece == PLAYER_X else PLAYER_X
        self.search_depth = search_depth

    def _get_all_valid_moves(self, board: GameLogicBoard) -> List[Tuple[int, str]]:
        # ... (same as MediumBot, with random.shuffle)
        valid_moves = []
        for r in range(ROWS):
            if is_valid_move(board, r, "L"):
                valid_moves.append((r, "L"))
            if is_valid_move(board, r, "R"):
                valid_moves.append((r, "R"))
        random.shuffle(valid_moves)
        return valid_moves

    def _evaluate_line(
        self, line: List[Optional[str]], piece_to_evaluate_for: str
    ) -> int:
        # Using a more aggressive heuristic from our previous HardBot iteration
        score = 0
        ai_piece = piece_to_evaluate_for
        opponent_piece = (
            self.opponent_piece if ai_piece == self.player_piece else self.player_piece
        )

        ai_count = line.count(ai_piece)
        opponent_count = line.count(opponent_piece)
        empty_count = line.count(EMPTY_CELL)

        if ai_count == CONNECT_N:
            return 10000000  # AI wins
        if opponent_count == CONNECT_N:
            return -10000000  # Opponent wins

        if ai_count == CONNECT_N - 1 and empty_count == 1:
            score += 50000  # AI imminent win
        elif ai_count == CONNECT_N - 2 and empty_count == 2:
            score += 5000  # AI strong setup (2 open)
        elif ai_count == CONNECT_N - 2 and empty_count == 1:
            score += 200  # AI 2, 1 empty, 1 opp (less ideal)
        elif ai_count == CONNECT_N - 3 and empty_count == 3:
            score += 500  # AI developing line (3 open)

        if opponent_count == CONNECT_N - 1 and empty_count == 1:
            score -= 250000  # Opponent imminent win (CRITICAL BLOCK)
        elif opponent_count == CONNECT_N - 2 and empty_count == 2:
            score -= 25000  # Opponent strong setup
        elif opponent_count == CONNECT_N - 2 and empty_count == 1:
            score -= 1000
        elif opponent_count == CONNECT_N - 3 and empty_count == 3:
            score -= 250

        return score

    def _evaluate_board(
        self, board: GameLogicBoard
    ) -> int:  # Always from AI's perspective
        score = 0
        # Center control bonus: Rows 2, 3, 4 for a 7-row board
        center_rows = [
            ROWS // 2 - 1,
            ROWS // 2,
            ROWS // 2 + 1,
        ]  # e.g., rows 2, 3, 4 for 7 rows
        for r_idx, row_val in enumerate(board):
            for cell_val in row_val:
                if r_idx in center_rows:
                    if cell_val == self.player_piece:
                        score += 5  # Small bonus for AI in center rows
                    elif cell_val == self.opponent_piece:
                        score -= 5  # Small penalty for Opponent in center

        # Line evaluation (same structure as MediumBot, but uses HardBot's _evaluate_line)
        for r in range(ROWS):  # Horizontal
            for c in range(COLS - CONNECT_N + 1):
                score += self._evaluate_line(
                    [board[r][c + i] for i in range(CONNECT_N)], self.player_piece
                )
        for c in range(COLS):  # Vertical
            for r in range(ROWS - CONNECT_N + 1):
                score += self._evaluate_line(
                    [board[r + i][c] for i in range(CONNECT_N)], self.player_piece
                )
        for r in range(ROWS - CONNECT_N + 1):  # Positive Diagonal
            for c in range(COLS - CONNECT_N + 1):
                score += self._evaluate_line(
                    [board[r + i][c + i] for i in range(CONNECT_N)], self.player_piece
                )
        for r in range(CONNECT_N - 1, ROWS):  # Negative Diagonal
            for c in range(COLS - CONNECT_N + 1):
                score += self._evaluate_line(
                    [board[r - i][c + i] for i in range(CONNECT_N)], self.player_piece
                )
        return score

    def minimax(
        self,
        board: GameLogicBoard,
        depth: int,
        alpha: float,
        beta: float,
        maximizing_player: bool,
    ) -> int:
        # ... (Minimax logic is identical to MediumBot's, it just uses HardBot's _evaluate_board and deeper depth)
        if check_win(board, self.player_piece):
            return 10000000 + depth
        if check_win(board, self.opponent_piece):
            return -10000000 - depth
        is_board_full = not any(EMPTY_CELL in row for row in board)
        if is_board_full or depth == 0:
            return self._evaluate_board(board)
        valid_moves = self._get_all_valid_moves(board)
        if not valid_moves:
            return self._evaluate_board(board)

        if maximizing_player:
            max_eval = -math.inf
            for r, s in valid_moves:
                temp_board = [row[:] for row in board]
                _simulate_apply_move_and_get_coords(temp_board, r, s, self.player_piece)
                evaluation = self.minimax(temp_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, evaluation)
                alpha = max(alpha, evaluation)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for r, s in valid_moves:
                temp_board = [row[:] for row in board]
                _simulate_apply_move_and_get_coords(
                    temp_board, r, s, self.opponent_piece
                )
                evaluation = self.minimax(temp_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, evaluation)
                beta = min(beta, evaluation)
                if beta <= alpha:
                    break
            return min_eval

    def get_move(self, board: GameLogicBoard) -> Optional[Tuple[int, str]]:
        # ... (get_move logic with win/block checks is identical to MediumBot's refined version)
        # It will simply use HardBot's minimax if those checks don't yield a move.
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
                return move_action

        # 2. Check to block opponent's immediate winning move
        opponent_winning_moves_to_block = []
        for opp_r in range(ROWS):
            for opp_s in ["L", "R"]:
                if is_valid_move(board, opp_r, opp_s):
                    temp_board_opp_check = [row[:] for row in board]
                    opp_coords = _simulate_apply_move_and_get_coords(
                        temp_board_opp_check, opp_r, opp_s, self.opponent_piece
                    )
                    if opp_coords and check_win(
                        temp_board_opp_check, self.opponent_piece, opp_coords
                    ):
                        if (opp_r, opp_s) in valid_moves:
                            opponent_winning_moves_to_block.append((opp_r, opp_s))

        if opponent_winning_moves_to_block:
            return opponent_winning_moves_to_block[0]

        # 3. Minimax
        best_score = -math.inf
        best_move = None  # random.choice(valid_moves) # Ensure a fallback if all scores are -inf
        alpha = -math.inf
        beta = math.inf

        for move_action in valid_moves:
            r, s = move_action
            temp_board = [row[:] for row in board]
            _simulate_apply_move_and_get_coords(temp_board, r, s, self.player_piece)
            score = self.minimax(temp_board, self.search_depth - 1, alpha, beta, False)
            if score > best_score:
                best_score = score
                best_move = move_action
            alpha = max(alpha, score)

        # print(f"HardAI ({self.player_piece}): Chose {best_move} (score: {best_score}, depth: {self.search_depth}) via Minimax.")
        return best_move if best_move else (valid_moves[0] if valid_moves else None)

if __name__ == "__main__":
    from app.services.game_logic import (
        print_board,
        create_board,
        apply_move as actual_apply_move,
    )

    test_board = create_board()
    actual_apply_move(test_board, 0, "L", PLAYER_X)  # X (0,0)
    actual_apply_move(test_board, 1, "L", PLAYER_O)  # O (1,0)
    actual_apply_move(test_board, 0, "L", PLAYER_X)  # X (0,1)
    actual_apply_move(test_board, 1, "R", PLAYER_O)  # O (1,6)
    actual_apply_move(test_board, 0, "L", PLAYER_X)  # X (0,2)
    # X is at (0,0), (0,1), (0,2). Needs (0,3) for win.

    logger.info("Board before HardAI (O)'s turn to block X:")
    print_board(test_board)

    hard_bot_o = HardAIBot(PLAYER_O, search_depth=3)  # O is AI, depth 3
    logger.info(f"\nHardAI ({PLAYER_O}) thinking...")
    chosen_move_o = hard_bot_o.get_move(test_board)
    logger.info(
        f"HardAI ({PLAYER_O}) suggests move: {chosen_move_o}"
    )  # Should be (0,"L") to block X at (0,3)

    if chosen_move_o:
        actual_apply_move(test_board, chosen_move_o[0], chosen_move_o[1], PLAYER_O)
        print_board(test_board)

    test_board_x_win = create_board()
    actual_apply_move(test_board_x_win, 0, "L", PLAYER_X)
    actual_apply_move(test_board_x_win, 0, "L", PLAYER_X)
    actual_apply_move(test_board_x_win, 0, "L", PLAYER_X)
    # X can win at (0,3) with (0,L)
    logger.info("\nBoard before HardAI (X)'s turn to win:")
    print_board(test_board_x_win)
    hard_bot_x = HardAIBot(PLAYER_X, search_depth=3)
    logger.info(f"\nHardAI ({PLAYER_X}) thinking...")
    chosen_move_x = hard_bot_x.get_move(test_board_x_win)
    logger.info(
        f"HardAI ({PLAYER_X}) suggests move: {chosen_move_x}"
    )  # Should be (0,"L")
