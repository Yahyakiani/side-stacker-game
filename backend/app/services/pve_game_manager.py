# backend/app/services/pve_game_manager.py (NEW FILE for PvE AI logic)
import asyncio
from sqlalchemy.orm import Session
import uuid  # If game_id is uuid

from app.crud import crud_game
from app.websockets.connection_manager import manager  # For broadcasting
from app.services.game_logic import (
    PLAYER_X,
    PLAYER_O,
    EMPTY_CELL,
    Board as GameLogicBoard,
    apply_move,
    check_win,
    check_draw,
    create_board as service_create_board,
)
from app.services.ai.easy_bot import EasyAIBot
from app.services.ai.medium_bot import MediumAIBot
from app.services.ai.hard_bot import HardAIBot
from app.core import constants
from app.db.models import Game  # For type hinting db_game


def _get_pve_ai_bot_instance(game_mode: str, ai_player_piece: str):
    """Instantiates an AI bot for PVE based on game_mode and piece."""
    game_mode_upper = game_mode.upper()
    if constants.AI_DIFFICULTY_EASY in game_mode_upper:
        return EasyAIBot(player_piece=ai_player_piece)
    elif constants.AI_DIFFICULTY_MEDIUM in game_mode_upper:
        return MediumAIBot(player_piece=ai_player_piece, search_depth=2)
    elif constants.AI_DIFFICULTY_HARD in game_mode_upper:
        return HardAIBot(player_piece=ai_player_piece, search_depth=4)  # Example depth
    print(f"ERROR PVE: Could not determine AI type for game_mode {game_mode}")
    return None


async def _handle_pve_ai_turn(db: Session, db_game: Game, active_game_id: str):
    """Handles the AI's turn in a PVE game."""
    ai_player_token = db_game.current_player_token
    ai_player_piece = constants.PLAYER_O  # AI is always P2/O in PVE

    ai_bot_instance = _get_pve_ai_bot_instance(db_game.game_mode, ai_player_piece)

    if not ai_bot_instance:
        print(f"ERROR: PVE AI bot for mode {db_game.game_mode} not implemented.")
        error_message = f"{constants.AI_UNAVAILABLE_ERROR_PREFIX}{db_game.game_mode}{constants.AI_UNAVAILABLE_ERROR_SUFFIX}"
        await manager.broadcast_error_to_game(active_game_id, error_message)
        # Revert turn to human if AI is unavailable to prevent stall
        if db_game.current_player_token and db_game.current_player_token.startswith(
            constants.AI_PLAYER_TOKEN_PREFIX
        ):
            crud_game.update_game_state(
                db, game_id=db_game.id, current_player_token=db_game.player1_token
            )
            # Notify client about turn revert (optional, or let next human move trigger update)
        return

    print(f"PVE AI ({ai_player_piece}, {db_game.game_mode}) is thinking...")
    # Add a small delay to simulate thinking and improve UX
    await asyncio.sleep(
        0.5
        + (0.5 if constants.AI_DIFFICULTY_MEDIUM in db_game.game_mode else 0)
        + (1.0 if constants.AI_DIFFICULTY_HARD in db_game.game_mode else 0)
    )

    current_board: GameLogicBoard = db_game.board_state.get(
        "board", service_create_board()
    )
    # board_for_ai = [row[:] for row in current_board] # If AI mutates
    ai_move_tuple = ai_bot_instance.get_move(current_board)

    if not ai_move_tuple:
        print(f"PVE AI ({ai_player_piece}) found no valid moves. Board full or error.")
        # If AI can't move, it's likely a draw or an issue. For now, revert to human.
        # A more robust solution might end the game as a draw if the board is indeed full.
        crud_game.update_game_state(
            db, game_id=db_game.id, current_player_token=db_game.player1_token
        )
        await manager.broadcast_game_update(
            active_game_id,
            current_board,
            db_game.player1_token,
            None,  # No last AI move
        )
        return

    ai_row, ai_side = ai_move_tuple
    print(f"PVE AI ({ai_player_piece}) chose: r{ai_row}, s{ai_side}")

    board_after_ai_move = [row[:] for row in current_board]  # Work on a copy
    ai_placed_coords = apply_move(board_after_ai_move, ai_row, ai_side, ai_player_piece)

    if not ai_placed_coords:
        print(
            f"CRITICAL ERROR PVE: AI ({ai_player_piece}) made an invalid board move: {ai_move_tuple}"
        )
        await manager.broadcast_error_to_game(
            active_game_id, constants.AI_INVALID_MOVE_ERROR
        )
        # Revert turn to human.
        crud_game.update_game_state(
            db, game_id=db_game.id, current_player_token=db_game.player1_token
        )
        await manager.broadcast_game_update(
            active_game_id, current_board, db_game.player1_token, None
        )
        return

    new_board_state_json = {"board": board_after_ai_move}
    current_turn_status = constants.GAME_STATUS_ACTIVE
    winner_for_turn = None
    is_game_over_this_turn = False
    next_player_token_if_active = db_game.player1_token  # Back to Human

    if check_win(board_after_ai_move, ai_player_piece, ai_placed_coords):
        current_turn_status = constants.get_win_status(ai_player_piece)
        winner_for_turn = ai_player_token  # AI's token
        is_game_over_this_turn = True
    elif check_draw(board_after_ai_move):
        current_turn_status = constants.GAME_STATUS_DRAW
        winner_for_turn = constants.DRAW_WINNER_TOKEN_VALUE
        is_game_over_this_turn = True

    final_db_game_state = crud_game.update_game_state(
        db=db,
        game_id=db_game.id,
        board_state=new_board_state_json,
        current_player_token=(
            next_player_token_if_active if not is_game_over_this_turn else None
        ),
        status=current_turn_status,
        winner_token=winner_for_turn,
    )
    if not final_db_game_state:
        await manager.broadcast_error_to_game(
            active_game_id, constants.SAVE_MOVE_FAILED_ERROR
        )
        return  # Game state save failed

    final_board_to_broadcast = final_db_game_state.board_state.get("board", [])
    if is_game_over_this_turn:
        await manager.broadcast_game_over(
            active_game_id,
            final_board_to_broadcast,
            current_turn_status,
            winner_for_turn,
            (
                ai_player_piece
                if winner_for_turn != constants.DRAW_WINNER_TOKEN_VALUE
                else None
            ),
        )
    else:
        last_move_payload = {
            "player_token": ai_player_token,
            "player_piece": ai_player_piece,
            "row": ai_placed_coords[0],
            "col": ai_placed_coords[1],
            "side_played": ai_side,
        }
        await manager.broadcast_game_update(
            active_game_id,
            final_board_to_broadcast,
            next_player_token_if_active,
            last_move_payload,
        )
