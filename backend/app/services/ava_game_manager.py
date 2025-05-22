# backend/app/services/ava_game_manager.py (NEW FILE)
# Or keep it in game_ws.py if it's not reused elsewhere, but for SRP, a new file is better.
# For now, I'll assume we are refactoring it within game_ws.py context first,
# and then we can decide to move it.

import asyncio
import uuid
from fastapi import WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db.session import SessionLocal  # For creating a new session
from app.crud import crud_game
from app.websockets.connection_manager import manager
from app.services.game_logic import (
    Board as GameLogicBoard,
    apply_move,
    check_win,
    check_draw,
    create_board as service_create_board,
)
from app.services.ai.easy_bot import EasyAIBot
from app.services.ai.medium_bot import MediumAIBot
from app.services.ai.hard_bot import HardAIBot
from app.core import constants  # Import our new constants

from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

# Helper function to instantiate AI bot
def _get_ai_bot_instance(ai_player_token: str, ai_player_piece: str):
    """Instantiates an AI bot based on its token and piece."""
    # Token example: "AI_EASY_PLAYER_1", "AI_MEDIUM_PLAYER_2"
    # Remove prefixes/suffixes to get difficulty string
    difficulty_str_part = (
        ai_player_token.replace(constants.AI_PLAYER_TOKEN_PREFIX, "")
        .replace(constants.AI_PLAYER_TOKEN_PLAYER1_SUFFIX, "")
        .replace(constants.AI_PLAYER_TOKEN_PLAYER2_SUFFIX, "")
    )

    if constants.AI_DIFFICULTY_EASY in difficulty_str_part:
        return EasyAIBot(player_piece=ai_player_piece)
    elif constants.AI_DIFFICULTY_MEDIUM in difficulty_str_part:
        return MediumAIBot(
            player_piece=ai_player_piece, search_depth=2
        )  # Search depth could be a constant or config
    elif constants.AI_DIFFICULTY_HARD in difficulty_str_part:
        return HardAIBot(
            player_piece=ai_player_piece, search_depth=3
        )  # Search depth could be a constant or config

    logger.error(f"ERROR AvA: Could not determine AI type for token {ai_player_token}")
    return None


# Helper function to handle game over scenario in AvA loop
async def _handle_ava_game_over(
    db: Session,
    game_id_uuid: uuid.UUID,
    game_id_str: str,
    board: GameLogicBoard,
    status: str,
    winner_token: str | None,
    winning_piece: str | None,
):
    """Updates DB and broadcasts GAME_OVER for AvA."""
    crud_game.update_game_state(
        db,
        game_id_uuid,
        status=status,
        current_player_token=None,  # No next player
        winner_token=winner_token,
    )
    game_over_payload = {
        "game_id": game_id_str,
        "board": board,
        "status": status,
        "winner_token": winner_token,
        "winning_player_piece": winning_piece,
    }
    await manager.broadcast_to_game(
        {"type": constants.WS_MSG_TYPE_GAME_OVER, "payload": game_over_payload},
        game_id_str,
    )


async def run_ai_vs_ai_game(game_id_uuid: uuid.UUID):  # Removed initial_db_session
    """
    Manages an AI vs AI game, making moves for each AI until the game ends.
    Uses a new DB session for its operations.
    """
    db: Session = SessionLocal()
    active_game_id_str = str(game_id_uuid)
    logger.info(f"AI vs AI Game Loop Started for: {active_game_id_str}")

    try:
        while True:
            await asyncio.sleep(1.0)  # Delay for spectating

            current_game_state = crud_game.get_game(db, game_id=game_id_uuid)
            if (
                not current_game_state
                or current_game_state.status != constants.GAME_STATUS_ACTIVE
                or not current_game_state.current_player_token.startswith(
                    constants.AI_PLAYER_TOKEN_PREFIX
                )
            ):
                status_info = (
                    current_game_state.status if current_game_state else "Not Found"
                )
                logger.info(
                    f"AvA Game {active_game_id_str}: Loop ending. Status: {status_info}"
                )
                break

            ai_player_token = current_game_state.current_player_token
            ai_player_piece = (
                constants.PLAYER_X
                if current_game_state.player1_token == ai_player_token
                else constants.PLAYER_O
            )

            ai_bot_instance = _get_ai_bot_instance(ai_player_token, ai_player_piece)
            if not ai_bot_instance:
                # Error already logged in _get_ai_bot_instance
                # Consider a more graceful game end, e.g., technical forfeit
                await _handle_ava_game_over(
                    db,
                    game_id_uuid,
                    active_game_id_str,
                    current_game_state.board_state.get(
                        "board", service_create_board()
                    ),  # Pass current board
                    constants.GAME_STATUS_ERROR_AI_STUCK,  # Or a more specific error status
                    None,
                    None,
                )
                break

            logger.info(
                f"AvA Game {active_game_id_str}: AI Turn for {ai_player_token} ({ai_player_piece}) thinking..."
            )
            current_board: GameLogicBoard = current_game_state.board_state.get(
                "board", service_create_board()
            )

            # Create a copy for the AI to modify if its `get_move` modifies the board
            # board_for_ai = [row[:] for row in current_board] # If AI mutates board
            # ai_move_tuple = ai_bot_instance.get_move(board_for_ai)
            ai_move_tuple = ai_bot_instance.get_move(
                current_board
            )  # Assuming get_move is pure or operates on a copy

            if not ai_move_tuple:
                logger.error(f"AvA ERROR: AI {ai_player_token} could not find a move.")
                is_board_full = not any(
                    constants.EMPTY_CELL in row for row in current_board
                )
                final_status = (
                    constants.GAME_STATUS_DRAW
                    if is_board_full
                    else constants.GAME_STATUS_ERROR_AI_STUCK
                )
                winner_token = (
                    constants.DRAW_WINNER_TOKEN_VALUE if is_board_full else None
                )
                await _handle_ava_game_over(
                    db,
                    game_id_uuid,
                    active_game_id_str,
                    current_board,
                    final_status,
                    winner_token,
                    None,
                )
                break

            ai_row, ai_side = ai_move_tuple
            logger.info(
                f"AvA Game {active_game_id_str}: AI {ai_player_token} chose r{ai_row},s{ai_side}"
            )

            # It's crucial that apply_move operates on a fresh copy or the DB state's board,
            # not a mutated one from the AI if the AI mutates its input.
            # Assuming current_board is the canonical state before this AI's move.
            board_after_ai_move = [
                row[:] for row in current_board
            ]  # Work on a copy for this turn
            ai_placed_coords = apply_move(
                board_after_ai_move, ai_row, ai_side, ai_player_piece
            )

            if not ai_placed_coords:
                logger.critical(
                    f"AvA CRITICAL ERROR: AI {ai_player_token} made an invalid board move: {ai_move_tuple}. This should not happen."
                )
                await _handle_ava_game_over(
                    db,
                    game_id_uuid,
                    active_game_id_str,
                    current_board,
                    "error_ai_invalid_move",
                    None,
                    None,
                )
                break

            new_board_state_json = {"board": board_after_ai_move}
            current_turn_status = constants.GAME_STATUS_ACTIVE
            winner_for_turn = None
            is_game_over_this_turn = False

            next_player_token_if_active = (
                current_game_state.player1_token
                if ai_player_token == current_game_state.player2_token
                else current_game_state.player2_token
            )

            if check_win(board_after_ai_move, ai_player_piece, ai_placed_coords):
                current_turn_status = constants.get_win_status(ai_player_piece)
                winner_for_turn = ai_player_token
                is_game_over_this_turn = True
            elif check_draw(board_after_ai_move):
                current_turn_status = constants.GAME_STATUS_DRAW
                winner_for_turn = constants.DRAW_WINNER_TOKEN_VALUE
                is_game_over_this_turn = True

            crud_game.update_game_state(
                db=db,
                game_id=game_id_uuid,
                board_state=new_board_state_json,
                current_player_token=(
                    next_player_token_if_active if not is_game_over_this_turn else None
                ),
                status=current_turn_status,
                winner_token=winner_for_turn,
            )
            # No need to re-fetch 'updated_game_after_ai_move' if we use the values set above.

            if is_game_over_this_turn:
                await _handle_ava_game_over(
                    db,
                    game_id_uuid,
                    active_game_id_str,
                    board_after_ai_move,
                    current_turn_status,
                    winner_for_turn,
                    (
                        ai_player_piece
                        if winner_for_turn != constants.DRAW_WINNER_TOKEN_VALUE
                        else None
                    ),
                )
                break
            else:
                game_update_payload = {
                    "game_id": active_game_id_str,
                    "board": board_after_ai_move,
                    "current_player_token": next_player_token_if_active,
                    "last_move": {  # Construct last_move accurately
                        "player_token": ai_player_token,
                        "player_piece": ai_player_piece,
                        "row": ai_placed_coords[0],  # Actual row where piece landed
                        "col": ai_placed_coords[1],  # Actual col where piece landed
                        "side_played": ai_side,  # Side from which move was made
                    },
                }
                await manager.broadcast_to_game(
                    {
                        "type": constants.WS_MSG_TYPE_GAME_UPDATE,
                        "payload": game_update_payload,
                    },
                    active_game_id_str,
                )

        logger.info(f"AI vs AI Game Loop Gracefully Ended for: {active_game_id_str}")

    except WebSocketDisconnect:  # Should not happen in a detached task usually
        logger.error(
            f"AvA Game {active_game_id_str}: WebSocketDisconnect encountered unexpectedly."
        )
    except asyncio.CancelledError:
        logger.info(f"AvA Game {active_game_id_str}: Task was cancelled.")
        # Perform any cleanup if necessary
    except Exception as e:
        logger.critical(
            f"CRITICAL EXCEPTION in run_ai_vs_ai_game for {active_game_id_str}: {e}"
        )
        # Attempt to notify spectators of a critical failure
        try:
            critical_error_board = (
                crud_game.get_game(db, game_id=game_id_uuid).board_state.get(
                    "board", []
                )
                if crud_game.get_game(db, game_id=game_id_uuid)
                else service_create_board()
            )
            await _handle_ava_game_over(
                db,
                game_id_uuid,
                active_game_id_str,
                critical_error_board,
                "error_critical_ava_failure",
                None,
                None,
            )
        except Exception as broadcast_err:
            logger.error(
                f"AvA Game {active_game_id_str}: Failed to broadcast critical error: {broadcast_err}"
            )
    finally:
        logger.info(
            f"AvA Game {active_game_id_str}: Closing DB session in run_ai_vs_ai_game."
        )
        db.close()
