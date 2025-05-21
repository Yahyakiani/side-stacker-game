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


# Helper from medium_bot, can be shared or copied
def _simulate_apply_move(
    board: GameLogicBoard, row: int, side: str, player: str
) -> Optional[Tuple[int, int]]:
    target_row = board[row]  # Assumes board is a mutable copy
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
    ):  # Increased default depth
        super().__init__(player_piece)
        self.opponent_piece = PLAYER_O if self.player_piece == PLAYER_X else PLAYER_X
        self.search_depth = search_depth
        # For very deep searches, transposition tables could be added, but that's advanced.

    def _get_all_valid_moves(self, board: GameLogicBoard) -> List[Tuple[int, str]]:
        valid_moves = []
        for r in range(ROWS):
            if is_valid_move(board, r, "L"):
                valid_moves.append((r, "L"))
            if is_valid_move(board, r, "R"):
                valid_moves.append((r, "R"))
        random.shuffle(valid_moves)  # Shuffle for variety if scores are equal
        return valid_moves

    def _evaluate_line(self, line: List[Optional[str]], piece: str) -> int:
        score = 0
        opponent_piece = self.opponent_piece  # Use instance opponent_piece

        piece_count = line.count(piece)
        opponent_count = line.count(opponent_piece)
        empty_count = line.count(EMPTY_CELL)

        if piece_count == CONNECT_N:
            return 1000000  # AI wins (higher score than Medium)
        if opponent_count == CONNECT_N:
            return -1000000  # Opponent wins

        # More aggressive scoring for potential wins and blocking threats
        if (
            piece_count == CONNECT_N - 1 and empty_count == 1
        ):  # Three in a row with one empty
            score += 5000
        elif (
            piece_count == CONNECT_N - 2 and empty_count == 2
        ):  # Two in a row with two empty (open ended)
            score += 500
        elif (
            piece_count == CONNECT_N - 3 and empty_count == 3
        ):  # One piece with three empty (less valuable but still something)
            score += 50

        if (
            opponent_count == CONNECT_N - 1 and empty_count == 1
        ):  # Opponent has three (urgent block)
            score -= 20000  # Increased penalty
        elif (
            opponent_count == CONNECT_N - 2 and empty_count == 2
        ):  # Opponent has two open
            score -= 200
        elif (
            opponent_count == CONNECT_N - 3 and empty_count == 3
        ):  # Opponent has one open
            score -= 20

        return score

    def _evaluate_board(self, board: GameLogicBoard, for_player: str) -> int:
        score = 0

        # Centrality bonus (simple version: pieces in middle rows/cols are slightly better)
        # This is very game-specific for Side-Stacker.
        # For side stacker, maybe rows near center, or just having more pieces.
        # For now, let's focus on lines. A more complex heuristic could add this.
        # Example:
        # for r_idx, row_val in enumerate(board):
        #     for c_idx, cell_val in enumerate(row_val):
        #         if cell_val == for_player:
        #             if 2 <= r_idx <= ROWS - 3: # Middle rows
        #                 score += 1 # Small bonus for central rows
        #         elif cell_val == self.opponent_piece:
        #             if 2 <= r_idx <= ROWS - 3:
        #                 score -= 1

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
        last_move_coords: Optional[Tuple[int, int]] = None,
    ) -> int:
        # Pass self.player_piece and self.opponent_piece to check_win
        if last_move_coords and check_win(
            board,
            self.player_piece if maximizing_player else self.opponent_piece,
            last_move_coords,
        ):
            # If check_win can use last_move_coords, this will be faster.
            # The piece that just moved belongs to 'not maximizing_player' if we are evaluating for 'maximizing_player'
            if (
                maximizing_player
            ):  # This state resulted from opponent's move, so opponent might have won
                return -1000000 - depth
            else:  # This state resulted from AI's move, so AI might have won
                return 1000000 + depth

        # Fallback full board check if no last_move_coords or check_win doesn't use it optimally yet
        # For simplicity, our current check_win doesn't use last_move_coords optimally for minimax decision logic
        if check_win(board, self.player_piece):
            return 1000000 + depth
        if check_win(board, self.opponent_piece):
            return -1000000 - depth

        is_board_full = not any(EMPTY_CELL in row for row in board)
        if is_board_full or depth == 0:
            return self._evaluate_board(board, self.player_piece)

        valid_moves = self._get_all_valid_moves(board)
        if not valid_moves:
            return self._evaluate_board(board, self.player_piece)

        if maximizing_player:  # AI's turn
            max_eval = -math.inf
            for move in valid_moves:
                row, side = move
                temp_board = [r[:] for r in board]
                coords = _simulate_apply_move(temp_board, row, side, self.player_piece)
                if not coords:
                    continue  # Should not happen if valid_moves is correct

                eval_score = self.minimax(
                    temp_board, depth - 1, alpha, beta, False, coords
                )
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:  # Opponent's turn
            min_eval = math.inf
            for move in valid_moves:
                row, side = move
                temp_board = [r[:] for r in board]
                coords = _simulate_apply_move(
                    temp_board, row, side, self.opponent_piece
                )
                if not coords:
                    continue

                eval_score = self.minimax(
                    temp_board, depth - 1, alpha, beta, True, coords
                )
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def get_move(self, board: GameLogicBoard) -> Optional[Tuple[int, str]]:
        valid_moves = self._get_all_valid_moves(board)
        if not valid_moves:
            return None
        if len(valid_moves) == 1:
            return valid_moves[0]  # Only one choice

        best_score = -math.inf
        best_move = None
        alpha = -math.inf
        beta = math.inf

        # Prioritize immediate win/loss checks from MediumBot can be kept
        # Or rely purely on minimax if depth is sufficient. For "Hard", minimax should find these.
        # For speed, keeping quick checks might be good.

        for move_action in valid_moves:  # Check for immediate win
            r, s = move_action
            temp_b = [row[:] for row in board]
            coords = _simulate_apply_move(temp_b, r, s, self.player_piece)
            if coords and check_win(temp_b, self.player_piece, coords):
                # print(f"HardAI ({self.player_piece}): Immediate win with {move_action}")
                return move_action

        # Check to block immediate opponent win
        for move_action in valid_moves:  # AI's potential moves
            r, s = move_action
            ai_landing_spot_board = [row[:] for row in board]
            sim_coords_ai_landing = _simulate_apply_move(
                ai_landing_spot_board, r, s, "TEMP"
            )

            if sim_coords_ai_landing:
                opponent_win_check_board = [row[:] for row in board]
                # What if opponent played at the spot AI is considering landing on?
                opponent_win_check_board[sim_coords_ai_landing[0]][
                    sim_coords_ai_landing[1]
                ] = self.opponent_piece
                if check_win(
                    opponent_win_check_board, self.opponent_piece, sim_coords_ai_landing
                ):
                    # print(f"HardAI ({self.player_piece}): Blocking opponent win with {move_action}")
                    return move_action

        # Minimax for strategic move
        for move in valid_moves:
            row, side = move
            temp_board = [r[:] for r in board]
            coords = _simulate_apply_move(temp_board, row, side, self.player_piece)
            if not coords:
                continue  # Should not happen with valid_moves

            eval_score = self.minimax(
                temp_board, self.search_depth - 1, alpha, beta, False, coords
            )  # Opponent's turn next

            if eval_score > best_score:
                best_score = eval_score
                best_move = move

            alpha = max(alpha, eval_score)  # Update alpha for root search
            # No beta pruning at the root's direct children in this loop structure,
            # pruning happens deeper in the recursive calls.

        # print(f"HardAI ({self.player_piece}): Chose move {best_move} with score {best_score} (depth {self.search_depth})")
        return best_move if best_move else random.choice(valid_moves)  # Fallback


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

    print("Board before HardAI (O)'s turn to block X:")
    print_board(test_board)

    hard_bot_o = HardAIBot(PLAYER_O, search_depth=3)  # O is AI, depth 3
    print(f"\nHardAI ({PLAYER_O}) thinking...")
    chosen_move_o = hard_bot_o.get_move(test_board)
    print(
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
    print("\nBoard before HardAI (X)'s turn to win:")
    print_board(test_board_x_win)
    hard_bot_x = HardAIBot(PLAYER_X, search_depth=3)
    print(f"\nHardAI ({PLAYER_X}) thinking...")
    chosen_move_x = hard_bot_x.get_move(test_board_x_win)
    print(f"HardAI ({PLAYER_X}) suggests move: {chosen_move_x}")  # Should be (0,"L")
