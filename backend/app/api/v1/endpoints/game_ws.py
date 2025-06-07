# backend/app/api/v1/endpoints/game_ws.py
# (Keep existing imports for now, we'll adjust as we move logic)
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json
import uuid
import asyncio
from app.db.session import get_db, SessionLocal # 
from app.crud import crud_game, crud_user, crud_user_stats

from app.websockets.connection_manager import manager
from app.db.session import get_db
from app.crud import crud_game
from app.services.game_stats_service import update_player_stats_on_game_end
from app.services.game_logic import (
    Board as GameLogicBoard,
    apply_move,
    check_draw,
    check_win,
    create_board as service_create_board,
    is_valid_move,
)

# AI Bot imports (used in run_ai_vs_ai_game if it stays here)

from app.core import constants
from app.services.ava_game_manager import run_ai_vs_ai_game
from app.services.pve_game_manager import _handle_pve_ai_turn

from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


# --- Handler for CREATE_GAME ---
async def handle_create_game_message(
    websocket: WebSocket, client_id: str, payload: dict, db: Session
) -> str | None:  # Returns active_game_id if successful, else None
    """Handles the CREATE_GAME WebSocket message."""
    player_human_token = payload.get(constants.PLAYER_TEMP_ID_PAYLOAD_KEY, client_id)
    username = payload.get(constants.USERNAME_PAYLOAD_KEY)
    game_mode_from_payload = payload.get(
        constants.MODE_PAYLOAD_KEY, constants.GAME_MODE_PVP
    ).upper()

    player1_user_id_for_db: uuid.UUID | None = None
    if username and game_mode_from_payload != constants.GAME_MODE_AVA: # AI vs AI games don't have human users creating them
        user_obj = crud_user.get_or_create_user(db, username=username)
        player1_user_id_for_db = user_obj.id
        logger.info(f"User '{username}' (ID: {player1_user_id_for_db}) is Player 1.")

    # --- Determine db_game_mode (PVP, PVE_DIFFICULTY, AVA_DIFF_VS_DIFF) ---
    db_game_mode = game_mode_from_payload
    if (
        game_mode_from_payload.startswith(constants.GAME_MODE_PVE)
        and game_mode_from_payload != constants.GAME_MODE_AVA
    ):
        pve_ai_difficulty_str = payload.get(
            constants.DIFFICULTY_PAYLOAD_KEY, constants.DEFAULT_AI_DIFFICULTY
        ).upper()
        if pve_ai_difficulty_str not in [
            constants.AI_DIFFICULTY_EASY,
            constants.AI_DIFFICULTY_MEDIUM,
            constants.AI_DIFFICULTY_HARD,
        ]:
            await manager.send_error(websocket, "Invalid AI difficulty for PVE.")
            return None
        db_game_mode = f"{constants.DB_GAME_MODE_PVE_PREFIX}{pve_ai_difficulty_str}"
    elif game_mode_from_payload == constants.GAME_MODE_AVA:
        ai1_diff = payload.get(
            constants.AI1_DIFFICULTY_PAYLOAD_KEY, constants.DEFAULT_AI_DIFFICULTY
        ).upper()
        ai2_diff = payload.get(
            constants.AI2_DIFFICULTY_PAYLOAD_KEY, constants.DEFAULT_AI_DIFFICULTY
        ).upper()
        valid_diffs = [
            constants.AI_DIFFICULTY_EASY,
            constants.AI_DIFFICULTY_MEDIUM,
            constants.AI_DIFFICULTY_HARD,
        ]
        if ai1_diff not in valid_diffs or ai2_diff not in valid_diffs:
            await manager.send_error(websocket, "Invalid AI difficulties for AVA.")
            return None
        db_game_mode = f"{constants.DB_GAME_MODE_AVA_PREFIX}{ai1_diff}_VS_{ai2_diff}"

    # --- Validate Game Mode ---
    # This dynamic generation of allowed_game_modes can be simplified if your modes are fixed
    # Or pre-generate this list. For now, keeping it similar to original.
    allowed_game_modes = [constants.GAME_MODE_PVP]
    for d1 in [
        constants.AI_DIFFICULTY_EASY,
        constants.AI_DIFFICULTY_MEDIUM,
        constants.AI_DIFFICULTY_HARD,
    ]:
        allowed_game_modes.append(f"{constants.DB_GAME_MODE_PVE_PREFIX}{d1}")
        for d2 in [
            constants.AI_DIFFICULTY_EASY,
            constants.AI_DIFFICULTY_MEDIUM,
            constants.AI_DIFFICULTY_HARD,
        ]:
            allowed_game_modes.append(
                f"{constants.DB_GAME_MODE_AVA_PREFIX}{d1}_VS_{d2}"
            )
    if db_game_mode not in allowed_game_modes:
        await manager.send_error(websocket, f"Unsupported game mode: {db_game_mode}")
        return None

    # --- Determine Player Tokens and Initial Status ---
    player1_token = player_human_token  # Default for PVP/PVE
    player2_token = None
    initial_status = constants.GAME_STATUS_WAITING_FOR_PLAYER2  # Default for PVP

    if db_game_mode.startswith(constants.DB_GAME_MODE_PVE_PREFIX):
        difficulty_part = db_game_mode.split("_")[1]  # PVE_EASY -> EASY
        player2_token = f"{constants.AI_PLAYER_TOKEN_PREFIX}{difficulty_part}{constants.AI_PLAYER_TOKEN_GENERIC_SUFFIX}"
        initial_status = constants.GAME_STATUS_ACTIVE
    elif db_game_mode.startswith(constants.DB_GAME_MODE_AVA_PREFIX):
        # Example: AVA_EASY_VS_MEDIUM -> parts are ['AVA', 'EASY', 'VS', 'MEDIUM']
        parts = db_game_mode.split("_")  # Ensure this parsing is robust
        ai1_diff_for_token = (
            parts[1] if len(parts) > 1 else constants.DEFAULT_AI_DIFFICULTY
        )
        ai2_diff_for_token = (
            parts[3] if len(parts) > 3 else constants.DEFAULT_AI_DIFFICULTY
        )
        player1_token = f"{constants.AI_PLAYER_TOKEN_PREFIX}{ai1_diff_for_token}{constants.AI_PLAYER_TOKEN_PLAYER1_SUFFIX}"
        player2_token = f"{constants.AI_PLAYER_TOKEN_PREFIX}{ai2_diff_for_token}{constants.AI_PLAYER_TOKEN_PLAYER2_SUFFIX}"
        initial_status = constants.GAME_STATUS_ACTIVE
        player1_user_id_for_db = None

    # --- Create Game in DB ---
    db_game = crud_game.create_game_db(
        db=db,
        player1_token=player1_token,
        player2_token=player2_token,
        initial_current_player_token=player1_token,  # P1 or AI1 starts
        game_mode=db_game_mode,
         player1_user_id=player1_user_id_for_db,
        # initial_status is set by create_game_db based on P2 presence
    )
    # Ensure status is correctly set if create_game_db doesn't handle it for PVE/AVA
    if db_game.status != initial_status and (
        db_game_mode.startswith(constants.DB_GAME_MODE_PVE_PREFIX)
        or db_game_mode.startswith(constants.DB_GAME_MODE_AVA_PREFIX)
    ):
        db_game = crud_game.update_game_state(
            db, game_id=db_game.id, status=initial_status
        )

    active_game_id_str = str(db_game.id)
    await manager.connect(
        websocket, active_game_id_str, client_id
    )  # Connect this websocket to the game room

    # --- Send GAME_CREATED Message ---
    message_text = f"Game mode: {db_game.game_mode}."
    player_token_for_message = player_human_token
    player_piece_for_message = constants.PLAYER_X

    if db_game.game_mode == constants.GAME_MODE_PVP:
        message_text += " Waiting for Player 2..."
    elif db_game.game_mode.startswith(constants.DB_GAME_MODE_PVE_PREFIX):
        message_text += f" You are Player 1 ({constants.PLAYER_X})."
    elif db_game.game_mode.startswith(constants.DB_GAME_MODE_AVA_PREFIX):
        message_text += " Spectating AI vs AI."
        player_token_for_message = constants.SPECTATOR_TOKEN_VALUE
        player_piece_for_message = None  # Spectator has no piece

    await manager.send_personal_message(
        {
            "type": constants.WS_MSG_TYPE_GAME_CREATED,
            "payload": {
                "game_id": active_game_id_str,
                "player_token": player_token_for_message,
                "player_piece": player_piece_for_message,
                "game_mode": db_game.game_mode,
                "message": message_text,
                "username": username if player1_user_id_for_db else None
            },
        },
        websocket,
    )

    # --- Send WAITING_FOR_PLAYER for PVP ---
    if db_game.game_mode == constants.GAME_MODE_PVP:
        await manager.send_personal_message(
            {
                "type": constants.WS_MSG_TYPE_WAITING_FOR_PLAYER,
                "payload": {
                    "game_id": active_game_id_str,
                    "message": "Waiting for another player. Share the Game ID.",
                },
            },
            websocket,
        )

    # --- Send GAME_START for PVE/AVA and Start AvA Loop ---
    if db_game.game_mode.startswith(
        constants.DB_GAME_MODE_PVE_PREFIX
    ) or db_game.game_mode.startswith(constants.DB_GAME_MODE_AVA_PREFIX):

        board_to_start: GameLogicBoard = db_game.board_state.get(
            "board", service_create_board()
        )
        # Ensure tokens from DB are used for players map
        p1_token_db = db_game.player1_token
        p2_token_db = db_game.player2_token

        if not p1_token_db or not p2_token_db:  # Should not happen
            await manager.send_error(
                websocket,
                "Internal server error: Player tokens missing for game start.",
            )
            return None

        your_piece_for_start = None
        your_token_for_start = None
        if db_game.player1_token == player_human_token:  # Human is P1 (e.g. PVE)
            your_piece_for_start = constants.PLAYER_X
            your_token_for_start = player_human_token
        elif db_game.game_mode.startswith(
            constants.DB_GAME_MODE_AVA_PREFIX
        ):  # Human is spectator
            your_piece_for_start = None
            your_token_for_start = (
                constants.SPECTATOR_TOKEN_VALUE
            )  # Or client_id if preferred for spectator identity

        game_start_payload = {
            "game_id": active_game_id_str,
            "board": board_to_start,
            "current_player_token": db_game.current_player_token,
            "players": {
                p1_token_db: constants.PLAYER_X,
                p2_token_db: constants.PLAYER_O,
            },
            "your_piece": your_piece_for_start,
            "your_token": your_token_for_start,
            # Include game_mode in GAME_START as well, good for client state consistency
            "game_mode": db_game.game_mode,
        }
        await manager.broadcast_to_game(  # For PVE, only P1 is in room. For AVA, spectators.
            {"type": constants.WS_MSG_TYPE_GAME_START, "payload": game_start_payload},
            active_game_id_str,
        )

        if db_game.game_mode.startswith(
            constants.DB_GAME_MODE_AVA_PREFIX
        ) and db_game.current_player_token.startswith(constants.AI_PLAYER_TOKEN_PREFIX):
            logger.info(
                f"AvA Game {active_game_id_str}: Scheduling AI vs AI play. First turn: {db_game.current_player_token}"
            )
            asyncio.create_task(run_ai_vs_ai_game(db_game.id))

    return active_game_id_str


async def handle_make_move_message(
    websocket: WebSocket,
    client_id: str,  # client_id of the sender for validation
    current_active_game_id: str | None,  # Game client is currently in
    payload: dict,
    db: Session,
):
    """Handles the MAKE_MOVE WebSocket message."""
    if not current_active_game_id:
        await manager.send_error(websocket, constants.NO_ACTIVE_GAME_ERROR)
        return

    player_token_from_msg = payload.get(constants.PLAYER_TOKEN_PAYLOAD_KEY)
    row = payload.get(constants.ROW_PAYLOAD_KEY)  # Should be int
    side = payload.get(constants.SIDE_PAYLOAD_KEY)  # Should be 'L' or 'R'

    # Basic payload validation
    if (
        None in [player_token_from_msg, row, side]
        or not isinstance(row, int)
        or str(side).upper()
        not in [constants.CONTROL_SIDE_LEFT, constants.CONTROL_SIDE_RIGHT]
    ):
        await manager.send_error(websocket, constants.INVALID_MOVE_PAYLOAD_ERROR)
        return

    side = str(side).upper()  # Normalize

    try:
        game_uuid = uuid.UUID(current_active_game_id)
    except ValueError:
        await manager.send_error(websocket, constants.CORRUPTED_GAME_SESSION_ERROR)
        # Consider invalidating current_active_game_id in the main loop
        return {"invalidate_game_session": True}  # Signal to main loop

    db_game = crud_game.get_game(db, game_id=game_uuid)

    # Game and Player Validation
    if not db_game:
        await manager.send_error(websocket, constants.GAME_NOT_FOUND_ERROR)
        return {"invalidate_game_session": True}
    if db_game.status != constants.GAME_STATUS_ACTIVE:
        await manager.send_error(
            websocket, f"{constants.GAME_NOT_ACTIVE_ERROR_PREFIX}{db_game.status}"
        )
        return
    if db_game.game_mode.startswith(constants.DB_GAME_MODE_AVA_PREFIX):
        await manager.send_error(websocket, constants.SPECTATOR_CANNOT_MOVE_ERROR)
        return
    if db_game.current_player_token != player_token_from_msg:
        await manager.send_error(websocket, constants.NOT_YOUR_TURN_ERROR)
        return
    # Verify the client_id sending the message matches the player_token if you have such mapping
    # For now, we trust player_token_from_msg if it's the current_player_token

    # Determine player piece
    player_piece = None
    if db_game.player1_token == player_token_from_msg:
        player_piece = constants.PLAYER_X
    elif db_game.player2_token == player_token_from_msg:
        player_piece = constants.PLAYER_O

    if (
        not player_piece
    ):  # Should not happen if current_player_token matches a game player
        await manager.send_error(websocket, constants.PLAYER_TOKEN_MISMATCH_ERROR)
        return

    # Game Logic for Human Move
    current_board: GameLogicBoard = db_game.board_state.get(
        "board", service_create_board()
    )
    board_for_move = [r[:] for r in current_board]  # Work on a copy

    if not is_valid_move(
        board_for_move, row, side
    ):  # is_valid_move should take the board copy
        await manager.send_error(websocket, constants.INVALID_BOARD_MOVE_ERROR)
        return

    placed_coords = apply_move(board_for_move, row, side, player_piece)
    if not placed_coords:
        await manager.send_error(websocket, constants.APPLY_MOVE_FAILED_ERROR)
        return

    new_board_state_json = {"board": board_for_move}
    current_turn_status = constants.GAME_STATUS_ACTIVE
    winner_for_turn = None
    is_game_over_this_turn = False
    next_player_token_if_active = (
        db_game.player2_token
        if player_token_from_msg == db_game.player1_token
        else db_game.player1_token
    )

    if check_win(board_for_move, player_piece, placed_coords):
        current_turn_status = constants.get_win_status(player_piece)
        winner_for_turn = player_token_from_msg
        is_game_over_this_turn = True
    elif check_draw(board_for_move):
        current_turn_status = constants.GAME_STATUS_DRAW
        winner_for_turn = constants.DRAW_WINNER_TOKEN_VALUE
        is_game_over_this_turn = True

    updated_db_game_after_human_move = crud_game.update_game_state(
        db=db,
        game_id=game_uuid,
        board_state=new_board_state_json,
        current_player_token=(
            next_player_token_if_active if not is_game_over_this_turn else None
        ),
        status=current_turn_status,
        winner_token=winner_for_turn,
    )
    if not updated_db_game_after_human_move:
        await manager.send_error(websocket, constants.SAVE_MOVE_FAILED_ERROR)
        return

    final_board_to_broadcast = updated_db_game_after_human_move.board_state.get(
        "board", []
    )
    last_human_move_info = {
        "player_token": player_token_from_msg,
        "player_piece": player_piece,
        "row": placed_coords[0],
        "col": placed_coords[1],
        "side_played": side,
    }

    if is_game_over_this_turn:
        update_player_stats_on_game_end(
            db,
            updated_db_game_after_human_move.player1_user_id,
            updated_db_game_after_human_move.player2_user_id,
            updated_db_game_after_human_move.winner_token, # This is the game.winner_token field
            updated_db_game_after_human_move.player1_token,
            updated_db_game_after_human_move.player2_token,
            is_draw=(current_turn_status == constants.GAME_STATUS_DRAW)
        )
        await manager.broadcast_game_over(
            current_active_game_id,
            final_board_to_broadcast,
            current_turn_status,
            winner_for_turn,
            (
                player_piece
                if winner_for_turn != constants.DRAW_WINNER_TOKEN_VALUE
                else None
            ),
        )
    else:
        # Broadcast human move update FIRST
        await manager.broadcast_game_update(
            current_active_game_id,
            final_board_to_broadcast,
            next_player_token_if_active,  # This is now the AI's token if PVE
            last_human_move_info,
        )
        # THEN, if PVE and AI's turn, trigger AI move
        if (
            updated_db_game_after_human_move.game_mode.startswith(
                constants.DB_GAME_MODE_PVE_PREFIX
            )
            and updated_db_game_after_human_move.current_player_token
            and updated_db_game_after_human_move.current_player_token.startswith(
                constants.AI_PLAYER_TOKEN_PREFIX
            )
        ):
            # Pass the most up-to-date game state to the AI handler
            await _handle_pve_ai_turn(
                db, updated_db_game_after_human_move, current_active_game_id
            )

    return None  # No specific return needed to change main loop state unless error requires session invalidation


async def handle_join_game_message(
    websocket: WebSocket, client_id: str, payload: dict, db: Session
) -> str | None:  # Returns active_game_id if successful, else None
    """Handles the JOIN_GAME WebSocket message."""
    game_to_join_id_str = payload.get(constants.GAME_ID_PAYLOAD_KEY)
    player2_temp_id = payload.get(constants.PLAYER_TEMP_ID_PAYLOAD_KEY, client_id)
    username = payload.get(constants.USERNAME_PAYLOAD_KEY)

    if not game_to_join_id_str:
        await manager.send_error(websocket, constants.JOIN_GAME_ID_MISSING_ERROR)
        return None

    try:
        game_to_join_uuid = uuid.UUID(game_to_join_id_str)
    except ValueError:
        await manager.send_error(websocket, constants.JOIN_INVALID_GAME_ID_FORMAT_ERROR)
        return None

    db_game = crud_game.get_game(db, game_id=game_to_join_uuid)

    # Validation checks
    if not db_game:
        await manager.send_error(websocket, constants.JOIN_GAME_NOT_FOUND_ERROR)
        return None
    if db_game.game_mode != constants.GAME_MODE_PVP:
        await manager.send_error(websocket, constants.JOIN_NOT_PVP_ERROR)
        return None
    if db_game.player2_token is not None and db_game.player2_token != player2_temp_id:
        await manager.send_error(websocket, constants.JOIN_GAME_FULL_ERROR)
        return None
    if db_game.player1_token == player2_temp_id:
        await manager.send_error(websocket, constants.JOIN_AS_PLAYER2_IN_OWN_GAME_ERROR)
        return None
    
    player2_user_id_for_db: uuid.UUID | None = None
    if username: # Only if username is provided
        user_obj = crud_user.get_or_create_user(db, username=username)
        player2_user_id_for_db = user_obj.id
        logger.info(f"User '{username}' (ID: {player2_user_id_for_db}) is Player 2 joining game {game_to_join_id_str}.")

    # Successfully join the game as Player 2
    await manager.connect(
        websocket, game_to_join_id_str, player2_temp_id
    )  # Connect this websocket to the game room

    new_status_on_join = db_game.status
    if db_game.status == constants.GAME_STATUS_WAITING_FOR_PLAYER2:
        new_status_on_join = constants.GAME_STATUS_ACTIVE

    updated_db_game = crud_game.update_game_state(
        db,
        game_id=game_to_join_uuid,
        player2_token=player2_temp_id,
        player2_user_id=player2_user_id_for_db,
        status=new_status_on_join,
    )
    if not updated_db_game:
        await manager.send_error(websocket, constants.JOIN_UPDATE_FAILED_ERROR)
        # Disconnect from room if connect was called but update failed
        manager.disconnect(websocket, game_to_join_id_str)
        return None

    # Use the state from the updated_db_game object
    await manager.send_personal_message(
        {
            "type": constants.WS_MSG_TYPE_GAME_JOINED,
            "payload": {
                "game_id": game_to_join_id_str,
                "player_token": player2_temp_id,
                "player_piece": constants.PLAYER_O,
                "opponent_token": updated_db_game.player1_token,
                "game_mode": updated_db_game.game_mode,
                "message": f"Successfully joined game. You are Player 2 ({constants.PLAYER_O}).",
                "username": username if player2_user_id_for_db else None
            },
        },
        websocket,
    )

    # Prepare GAME_START payload for both players
    board_to_start: GameLogicBoard = updated_db_game.board_state.get(
        "board", service_create_board()
    )
    p1_token_from_db = updated_db_game.player1_token
    p2_token_from_db = updated_db_game.player2_token  # This should be player2_temp_id

    if not p1_token_from_db or not p2_token_from_db:
        logger.critical(
            f"CRITICAL ERROR JOIN_GAME: Missing player tokens for GAME_START. P1: {p1_token_from_db}, P2: {p2_token_from_db}"
        )
        await manager.send_error(websocket, "Internal error preparing game start.")
        return game_to_join_id_str

    base_game_start_payload = {
        "game_id": game_to_join_id_str,
        "board": board_to_start,
        "current_player_token": updated_db_game.current_player_token,  # Should be P1's token at game start
        "players": {
            p1_token_from_db: constants.PLAYER_X,
            p2_token_from_db: constants.PLAYER_O,
        },
        "game_mode": updated_db_game.game_mode,
    }

    # --- CORRECTED SECTION FOR SENDING GAME_START ---
    # Get Player 1's WebSocket using the new manager method
    ws_player1 = manager.get_websocket_for_client(game_to_join_id_str, p1_token_from_db)

    # Player 2's WebSocket is the current `websocket` argument of this function
    ws_player2 = websocket

    # Send GAME_START to Player 1
    if ws_player1:
        await manager.send_personal_message(
            {
                "type": constants.WS_MSG_TYPE_GAME_START,
                "payload": {
                    **base_game_start_payload,
                    "your_piece": constants.PLAYER_X,
                    "your_token": p1_token_from_db,  # Player 1's token
                },
            },
            ws_player1,
        )
        logger.info(
            f"Sent GAME_START to Player 1 ({p1_token_from_db}) in game {game_to_join_id_str}"
        )
    else:
        # This is a critical issue if P1 is supposed to be connected
        logger.warning(
            f"Warning/Error: Could not find WebSocket for Player 1 ({p1_token_from_db}) in game {game_to_join_id_str} to send GAME_START."
        )
        # Depending on your game logic, you might want to handle this more formally.
        # For instance, if P1 disconnected right before P2 joined, the game might be invalid.

    # Send GAME_START to Player 2 (the one who just joined)
    # ws_player2 should always be valid here as it's the current connection.
    await manager.send_personal_message(
        {
            "type": constants.WS_MSG_TYPE_GAME_START,
            "payload": {
                **base_game_start_payload,
                "your_piece": constants.PLAYER_O,
                "your_token": p2_token_from_db,  # Player 2's token
            },
        },
        ws_player2,
    )
    logger.info(
        f"Sent GAME_START to Player 2 ({p2_token_from_db}) in game {game_to_join_id_str}"
    )
    # --- END OF CORRECTED SECTION ---

    return game_to_join_id_str


# kept in game_message_handlers.py / game_ws.py
async def handle_player_departure_in_active_game(
    game_id_str: str,
    disconnected_player_token: str, # This is the client_id that was associated with the game
    db: Session
):
    logger.info(f"Handling player departure: Player {disconnected_player_token} from game {game_id_str}")
    try:
        game_uuid = uuid.UUID(game_id_str)
        db_game = crud_game.get_game(db, game_id=game_uuid)

        if not db_game:
            logger.warning(f"Game {game_id_str} not found during disconnect handling for player {disconnected_player_token}.")
            return

        if db_game.status != constants.GAME_STATUS_ACTIVE:
            logger.info(f"Game {game_id_str} is not active (status: {db_game.status}). No forfeit action needed for player {disconnected_player_token}.")
            return

        # Determine who the remaining player is and their piece
        remaining_player_token_for_win: str | None = None
        winning_piece_by_forfeit: str | None = None
        disconnected_user_id: uuid.UUID | None = None
        winner_user_id_by_forfeit: uuid.UUID | None = None

        if db_game.player1_token == disconnected_player_token:
            remaining_player_token_for_win = db_game.player2_token
            winning_piece_by_forfeit = constants.PLAYER_O # P2 (O) wins if P1 (X) disconnects
            disconnected_user_id = db_game.player1_user_id
            winner_user_id_by_forfeit = db_game.player2_user_id
        elif db_game.player2_token == disconnected_player_token:
            remaining_player_token_for_win = db_game.player1_token
            winning_piece_by_forfeit = constants.PLAYER_X # P1 (X) wins if P2 (O) disconnects
            disconnected_user_id = db_game.player2_user_id
            winner_user_id_by_forfeit = db_game.player1_user_id
        else:
            # Disconnected client was not P1 or P2 (e.g., a spectator, or an already ended game)
            logger.info(f"Player {disconnected_player_token} was not an active player in game {game_id_str}. No forfeit.")
            return

        if not remaining_player_token_for_win and not db_game.game_mode.startswith(constants.DB_GAME_MODE_PVE_PREFIX):
            logger.warning(f"No remaining player token in PvP game {game_id_str} after {disconnected_player_token} disconnected. Marking abandoned.")
            updated_game = crud_game.update_game_state(db, game_id=game_uuid, status="error_abandoned_pvp_no_opponent", current_player_token=None, winner_token=None)
            await manager.broadcast_error_to_game(game_id_str, "A player disconnected, game cannot continue.")

            if disconnected_user_id and updated_game:
                 update_player_stats_on_game_end(
                    db,
                    updated_game.player1_user_id,
                    updated_game.player2_user_id,
                    None, # No winner token
                    updated_game.player1_token,
                    updated_game.player2_token,
                    is_draw=False, # Not a draw
                    abandoned_by_user_id=disconnected_user_id
                )
            # ### NEW LINE/BLOCK END ###
            return

        logger.info(f"Player {disconnected_player_token} disconnected from active game {game_id_str}. Player {remaining_player_token_for_win} wins by forfeit.")
        
        new_status = constants.get_win_status(winning_piece_by_forfeit)
        updated_game_after_disconnect = crud_game.update_game_state(
            db, game_id=game_uuid, status=new_status,
            winner_token=remaining_player_token_for_win, current_player_token=None
        )

        if updated_game_after_disconnect: # Ensure game was updated
            update_player_stats_on_game_end(
                db,
                updated_game_after_disconnect.player1_user_id,
                updated_game_after_disconnect.player2_user_id,
                updated_game_after_disconnect.winner_token, # This is the remaining player's token
                updated_game_after_disconnect.player1_token,
                updated_game_after_disconnect.player2_token,
                is_draw=False,
                abandoned_by_user_id=disconnected_user_id # ID of the user who abandoned
            )

        # Fetch the final board state to broadcast
        final_board_state = db_game.board_state.get("board", service_create_board()) # Use current board, as no new move was made

        await manager.broadcast_game_over(
            game_id_str,
            final_board_state,
            new_status,
            remaining_player_token_for_win,
            winning_piece_by_forfeit,
            reason="opponent_disconnected"
        )
        logger.info(f"Broadcasted GAME_OVER for game {game_id_str} due to player {disconnected_player_token} disconnect.")

    except Exception as e:
        logger.exception(f"Error in handle_player_departure_in_active_game for game {game_id_str}, player {disconnected_player_token}: {e}")

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, client_id: str, # ### MODIFICATION START ### Remove Depends(get_db) ### MODIFICATION END ###
):
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for client_id: {client_id}")
    current_active_game_id: str | None = None

    try:
        while True:
            data = await websocket.receive_text()
            message_type = None
            try:
                message = json.loads(data)
                message_type = message.get("type")
                payload = message.get("payload", {})
                logger.info(f"Msg from {client_id} in game {current_active_game_id or 'N/A'}: type={message_type}")

                # ### NEW LINE/BLOCK START ### DB Session per message ### NEW LINE/BLOCK END ###
                db_for_message: Session = SessionLocal()
                result_from_handler = None # To catch invalidate_game_session signal
                try:
                # ### NEW LINE/BLOCK END ###
                    if message_type == constants.WS_MSG_TYPE_CLIENT_CREATE_GAME:
                        if current_active_game_id:
                            # Disconnect from manager's perspective for the old game
                            manager.disconnect(websocket, current_active_game_id, client_id)
                            current_active_game_id = None
                        # ### MODIFICATION START ### Pass db_for_message ### MODIFICATION END ###
                        new_game_id = await handle_create_game_message(websocket, client_id, payload, db_for_message)
                        # ### MODIFICATION END ###
                        current_active_game_id = new_game_id
                    elif message_type == constants.WS_MSG_TYPE_CLIENT_JOIN_GAME:
                        if current_active_game_id:
                            manager.disconnect(websocket, current_active_game_id, client_id)
                            current_active_game_id = None # Reset before joining/creating new
                        # ### MODIFICATION START ### Pass db_for_message ### MODIFICATION END ###
                        joined_game_id = await handle_join_game_message(websocket, client_id, payload, db_for_message)
                        # ### MODIFICATION END ###
                        current_active_game_id = joined_game_id
                    elif message_type == constants.WS_MSG_TYPE_CLIENT_MAKE_MOVE:
                        # ### MODIFICATION START ### Pass db_for_message ### MODIFICATION END ###
                        result_from_handler = await handle_make_move_message(
                            websocket, client_id, current_active_game_id, payload, db_for_message
                        )
                        # ### MODIFICATION END ###
                    else:
                        logger.warning(f"Unknown message type received from {client_id}: {message_type}")
                        await manager.send_error(websocket, f"Unknown message type: {message_type}")
                    
                    # ### NEW LINE/BLOCK START ### Check for invalidate_game_session from handler ### NEW LINE/BLOCK END ###
                    if result_from_handler and result_from_handler.get("invalidate_game_session"):
                        current_active_game_id = None # Clear if handler signaled session became invalid
                    # ### NEW LINE/BLOCK END ###
                # ### NEW LINE/BLOCK START ### Ensure DB session for message is closed ### NEW LINE/BLOCK END ###
                finally:
                    db_for_message.close()
                # ### NEW LINE/BLOCK END ###

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from {client_id}: {data}")
                await manager.send_error(websocket, "Invalid JSON format.")
            except Exception as e:
                logger.error(f"Error processing message from {client_id} (type: {message_type}): {e}", exc_info=True)
                await manager.send_error(websocket, "Error processing your request.")

    except WebSocketDisconnect:
        disconnect_context = manager.websocket_to_ids.get(websocket)
        game_id_of_disconnected_ws = None
        client_id_of_disconnected_ws = None

        if disconnect_context:
            game_id_of_disconnected_ws = disconnect_context.get("game_id")
            client_id_of_disconnected_ws = disconnect_context.get("client_id")
            logger.info(f"Client {client_id_of_disconnected_ws or client_id} (WebSocket: {websocket}) disconnected from game {game_id_of_disconnected_ws or 'N/A'}.")
        else:
            logger.info(f"Client {client_id} (WebSocket: {websocket}) disconnected. No game context found in manager for this websocket.")

        manager.disconnect(websocket)

        if game_id_of_disconnected_ws and client_id_of_disconnected_ws:
            # ### NEW LINE/BLOCK START ### DB Session for disconnect handling ### NEW LINE/BLOCK END ###
            db_for_disconnect: Session = SessionLocal()
            try:
                await handle_player_departure_in_active_game(
                    game_id_of_disconnected_ws,
                    client_id_of_disconnected_ws, # Use client_id from game room context
                    db_for_disconnect
                )
            finally:
                db_for_disconnect.close()
            # ### NEW LINE/BLOCK END ###
        current_active_game_id = None
    except Exception as e:
        logger.error(f"Unhandled exception in WebSocket endpoint for {client_id}: {e}", exc_info=True)
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass
    finally:
        logger.info(f"WebSocket for client {client_id} (instance: {websocket}) entering finally block. Current game: {current_active_game_id or 'N/A'}")
        if manager.websocket_to_ids.get(websocket):
             logger.info(f"Performing cleanup disconnect for websocket {websocket} via finally block (game_ws).")
             manager.disconnect(websocket)
        else:
             logger.info(f"Websocket {websocket} not found in manager's active mappings in game_ws finally; no explicit disconnect needed.")