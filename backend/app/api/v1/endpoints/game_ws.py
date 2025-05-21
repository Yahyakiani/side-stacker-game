# backend/app/api/v1/endpoints/game_ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import json  # For parsing incoming messages and constructing outgoing ones
import uuid
import asyncio

from app.websockets.connection_manager import manager  # Our connection manager
from app.db.session import get_db
from app.crud import crud_game
from app.db.session import SessionLocal
from app.services.game_logic import (
    PLAYER_X,
    PLAYER_O,
    Board as GameLogicBoard,
    is_valid_move,
    apply_move,
    check_win,
    check_draw,
    EMPTY_CELL,
)  # For type hinting and constants
from app.services.ai.easy_bot import EasyAIBot
from app.services.ai.medium_bot import MediumAIBot
from app.services.ai.hard_bot import HardAIBot

from app.services.game_logic import create_board as service_create_board

router = APIRouter()


async def run_ai_vs_ai_game(game_id_uuid: uuid.UUID, initial_db_session: Session):
    """
    Manages an AI vs AI game, making moves for each AI until the game ends.
    Uses a new DB session for its operations to avoid issues with the WebSocket's session.
    """
    db: Session = SessionLocal()  # Create a fresh session for this long-running task
    try:
        active_game_id_str = str(game_id_uuid)
        print(f"AI vs AI Game Loop Started for: {active_game_id_str}")

        while True:
            await asyncio.sleep(
                1.0
            )  # Delay between AI moves for spectating, adjust as needed

            current_game_state = crud_game.get_game(db, game_id=game_id_uuid)
            if (
                not current_game_state
                or current_game_state.status != "active"
                or not current_game_state.current_player_token.startswith("AI_")
            ):
                print(
                    f"AvA Game {active_game_id_str}: Loop ending. Status: {current_game_state.status if current_game_state else 'Not Found'}"
                )
                break  # Game ended or invalid state

            ai_player_token = current_game_state.current_player_token
            ai_player_piece = (
                PLAYER_X
                if current_game_state.player1_token == ai_player_token
                else PLAYER_O
            )

            ai_bot_instance = None
            # Determine bot from current_player_token (e.g., "AI_EASY_PLAYER_1", "AI_MEDIUM_PLAYER_2")
            difficulty_and_player_num = (
                ai_player_token.replace("AI_", "")
                .replace("_PLAYER_1", "")
                .replace("_PLAYER_2", "")
            )

            if "EASY" in difficulty_and_player_num:
                ai_bot_instance = EasyAIBot(player_piece=ai_player_piece)
            elif "MEDIUM" in difficulty_and_player_num:
                ai_bot_instance = MediumAIBot(
                    player_piece=ai_player_piece, search_depth=2
                )
            elif "HARD" in difficulty_and_player_num:
                ai_bot_instance = HardAIBot(
                    player_piece=ai_player_piece, search_depth=3
                )

            if not ai_bot_instance:
                print(
                    f"ERROR AvA: Could not instantiate AI bot for token {ai_player_token} in game {active_game_id_str}"
                )
                break

            print(
                f"AvA Game {active_game_id_str}: AI Turn for {ai_player_token} ({ai_player_piece}) thinking..."
            )
            current_board_list: GameLogicBoard = current_game_state.board_state.get(
                "board", service_create_board()
            )

            ai_move_tuple = ai_bot_instance.get_move(current_board_list)

            if not ai_move_tuple:
                print(
                    f"AvA ERROR: AI {ai_player_token} could not find a move. Board full or error."
                )
                # Potentially declare draw or forfeit
                # For now, mark as draw if board is full, otherwise error
                is_full = not any(EMPTY_CELL in row for row in current_board_list)
                final_status = "draw" if is_full else "error_ai_stuck"  # Custom status
                crud_game.update_game_state(
                    db,
                    game_id_uuid,
                    status=final_status,
                    current_player_token=None,
                    winner_token="draw" if is_full else None,
                )
                game_over_payload = {
                    "game_id": active_game_id_str,
                    "board": current_board_list,
                    "status": final_status,
                    "winner_token": "draw" if is_full else None,
                    "winning_player_piece": None,
                }
                await manager.broadcast_to_game(
                    {"type": "GAME_OVER", "payload": game_over_payload},
                    active_game_id_str,
                )
                break

            ai_row, ai_side = ai_move_tuple
            print(
                f"AvA Game {active_game_id_str}: AI {ai_player_token} chose r{ai_row},s{ai_side}"
            )

            # Apply AI's move (current_board_list is a fresh copy from DB state)
            ai_placed_coords = apply_move(
                current_board_list, ai_row, ai_side, ai_player_piece
            )
            if not ai_placed_coords:  # Should not happen if AI is well-behaved
                print(
                    f"AvA ERROR: AI {ai_player_token} made an invalid board move: {ai_move_tuple}"
                )
                # Handle error, maybe end game as error for this AI
                break

            ai_move_board_json = {"board": current_board_list}
            ai_new_status = "active"
            ai_new_winner_token = None
            ai_next_player_token = (
                current_game_state.player1_token
                if ai_player_token == current_game_state.player2_token
                else current_game_state.player2_token
            )
            ai_game_over = False

            if check_win(current_board_list, ai_player_piece, ai_placed_coords):
                ai_new_status = f"player_{ai_player_piece.lower()}_wins"
                ai_new_winner_token = ai_player_token
                ai_game_over = True
            elif check_draw(current_board_list):
                ai_new_status = "draw"
                ai_new_winner_token = "draw"
                ai_game_over = True

            updated_game_after_ai_move = crud_game.update_game_state(
                db=db,
                game_id=game_id_uuid,
                board_state=ai_move_board_json,
                current_player_token=ai_next_player_token if not ai_game_over else None,
                status=ai_new_status,
                winner_token=ai_new_winner_token,
            )
            if not updated_game_after_ai_move:
                break  # Error saving state

            # Broadcast result
            final_board_to_broadcast: GameLogicBoard = (
                updated_game_after_ai_move.board_state.get("board", [])
            )
            if ai_game_over:
                game_over_payload = {
                    "game_id": active_game_id_str,
                    "board": final_board_to_broadcast,
                    "status": updated_game_after_ai_move.status,
                    "winner_token": updated_game_after_ai_move.winner_token,
                    "winning_player_piece": (
                        ai_player_piece
                        if updated_game_after_ai_move.winner_token != "draw"
                        else None
                    ),
                }
                await manager.broadcast_to_game(
                    {"type": "GAME_OVER", "payload": game_over_payload},
                    active_game_id_str,
                )
                break  # Game over
            else:
                game_update_payload = {
                    "game_id": active_game_id_str,
                    "board": final_board_to_broadcast,
                    "current_player_token": updated_game_after_ai_move.current_player_token,
                    "last_move": {
                        "player_token": ai_player_token,
                        "player_piece": ai_player_piece,
                        "row": ai_placed_coords[0],
                        "col": ai_placed_coords[1],
                        "side_played": ai_side,
                    },
                }
                await manager.broadcast_to_game(
                    {"type": "GAME_UPDATE", "payload": game_update_payload},
                    active_game_id_str,
                )

        print(f"AI vs AI Game Loop Ended for: {active_game_id_str}")
    except Exception as e:
        print(f"Exception in run_ai_vs_ai_game for {game_id_uuid}: {e}")
        # Optionally broadcast an error to spectators
        try:
            await manager.broadcast_to_game(
                {
                    "type": "ERROR",
                    "payload": {"message": "Critical error in AI vs AI game."},
                },
                str(game_id_uuid),
            )
        except:
            pass  # Ignore if broadcast fails
    finally:
        db.close()


@router.websocket(
    "/ws/{client_id}"
)  # Using client_id in path for now, could be part of message
async def websocket_endpoint(
    websocket: WebSocket, client_id: str, db: Session = Depends(get_db)
):
    """
    Main WebSocket endpoint for game interactions.
    A single client_id is used here for simplicity in identifying the connection.
    In a real app, you might generate this on the server or use a session cookie.
    """
    # For now, we don't associate the websocket with a game_id on initial connect.
    # The client will send a "CREATE_GAME" or "JOIN_GAME" message.
    # await manager.connect(websocket, client_id) # Temporarily connect with client_id as room

    # We will connect the websocket to a specific game_id *after* a CREATE_GAME or JOIN_GAME message
    # For now, accept the connection without adding to a specific game room in the manager yet.
    await websocket.accept()
    print(f"WebSocket connection accepted for client_id: {client_id}")

    active_game_id: str = (
        None  # To store which game this websocket is currently part of
    )

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                payload = message.get("payload", {})

                print(
                    f"Received message from {client_id}: type={message_type}, payload={payload}"
                )

                if (
                    message_type == "CREATE_GAME"
                ):  # Note: This block is getting long, refactor later
                    player_human_token = payload.get(
                        "player_temp_id", client_id
                    )  # Spectator's client_id
                    game_mode_from_payload = payload.get("mode", "PVP").upper()

                    ai1_difficulty_str = (
                        payload.get("ai1_difficulty", "EASY").upper()
                        if game_mode_from_payload == "AVA"
                        else None
                    )
                    ai2_difficulty_str = (
                        payload.get("ai2_difficulty", "EASY").upper()
                        if game_mode_from_payload == "AVA"
                        else None
                    )

                    # For PVE, get ai_difficulty if not AVA
                    pve_ai_difficulty_str = None
                    if (
                        game_mode_from_payload.startswith("PVE")
                        and game_mode_from_payload != "AVA"
                    ):
                        pve_ai_difficulty_str = payload.get(
                            "difficulty", "EASY"
                        ).upper()

                    db_game_mode = game_mode_from_payload
                    if (
                        game_mode_from_payload.startswith("PVE")
                        and pve_ai_difficulty_str
                    ):
                        if pve_ai_difficulty_str not in ["EASY", "MEDIUM", "HARD"]:
                            # ... (error handling for invalid PVE difficulty) ...
                            await manager.send_personal_message(
                                {
                                    "type": "ERROR",
                                    "payload": {
                                        "message": "Invalid AI difficulty for PVE."
                                    },
                                },
                                websocket,
                            )
                            continue
                        db_game_mode = f"PVE_{pve_ai_difficulty_str}"
                    elif game_mode_from_payload == "AVA":
                        if (
                            not ai1_difficulty_str
                            or ai1_difficulty_str not in ["EASY", "MEDIUM", "HARD"]
                            or not ai2_difficulty_str
                            or ai2_difficulty_str not in ["EASY", "MEDIUM", "HARD"]
                        ):
                            await manager.send_personal_message(
                                {
                                    "type": "ERROR",
                                    "payload": {
                                        "message": "Invalid AI difficulties for AVA."
                                    },
                                },
                                websocket,
                            )
                            continue
                        db_game_mode = f"AVA_{ai1_difficulty_str}_VS_{ai2_difficulty_str}"  # e.g., AVA_EASY_VS_MEDIUM

                    allowed_game_modes = ["PVP"]
                    for d1 in ["EASY", "MEDIUM", "HARD"]:
                        allowed_game_modes.append(f"PVE_{d1}")
                        for d2 in ["EASY", "MEDIUM", "HARD"]:
                            allowed_game_modes.append(f"AVA_{d1}_VS_{d2}")

                    if db_game_mode not in allowed_game_modes:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": f"Unsupported game mode: {db_game_mode}"
                                },
                            },
                            websocket,
                        )
                        continue

                    player1_token_for_game = (
                        player_human_token  # Human client is initially P1 for PvE/PvP
                    )
                    player2_token_for_game = None
                    initial_status = "waiting_for_player2"  # Default for PVP

                    if db_game_mode.startswith("PVE"):  # Player vs AI
                        difficulty_part = db_game_mode.split("_")[1]
                        player2_token_for_game = f"AI_{difficulty_part}_PLAYER"
                        initial_status = "active"
                    elif db_game_mode.startswith("AVA"):  # AI vs AI
                        player1_token_for_game = (
                            f"AI_{ai1_difficulty_str}_PLAYER_1"  # AI1 is P1 (X)
                        )
                        player2_token_for_game = (
                            f"AI_{ai2_difficulty_str}_PLAYER_2"  # AI2 is P2 (O)
                        )
                        initial_status = "active"
                        # The connected human client is a spectator for AVA games.

                    db_game = crud_game.create_game_db(
                        db=db,
                        player1_token=player1_token_for_game,
                        player2_token=player2_token_for_game,
                        initial_current_player_token=player1_token_for_game,  # AI1 or Human P1 starts
                        game_mode=db_game_mode,
                    )
                    if db_game.status != initial_status and (
                        db_game_mode.startswith("PVE") or db_game_mode.startswith("AVA")
                    ):
                        db_game = crud_game.update_game_state(
                            db, game_id=db_game.id, status=initial_status
                        )

                    active_game_id = str(db_game.id)
                    # Spectator joins the game room
                    await manager.connect(websocket, active_game_id)

                    game_created_message = f"Game mode: {db_game.game_mode}."
                    if db_game.game_mode == "PVP":
                        game_created_message += " Waiting for Player 2..."
                    elif db_game.game_mode.startswith("PVE"):
                        game_created_message += (
                            f" You are Player 1 ({PLAYER_X}) playing."
                        )
                    elif db_game.game_mode.startswith("AVA"):
                        game_created_message += " Spectating AI vs AI."

                    await manager.send_personal_message(
                        {
                            "type": "GAME_CREATED",  # Spectator gets this too
                            "payload": {
                                "game_id": active_game_id,
                                "player_token": (
                                    player_human_token
                                    if not db_game_mode.startswith("AVA")
                                    else "SPECTATOR"
                                ),
                                "player_piece": (
                                    PLAYER_X
                                    if not db_game_mode.startswith("AVA")
                                    else None
                                ),  # Spectator has no piece
                                "game_mode": db_game.game_mode,  # Send mode back
                                "message": game_created_message,
                            },
                        },
                        websocket,
                    )

                    if db_game.game_mode.startswith(
                        "PVE"
                    ) or db_game.game_mode.startswith("AVA"):
                        board_list_for_start: GameLogicBoard = db_game.board_state.get(
                            "board", service_create_board()
                        )
                        p1_actual_token = db_game.player1_token  # Could be human or AI1
                        p2_actual_token = (
                            db_game.player2_token
                        )  # Could be human P2 or AI2

                        if not p1_actual_token or not p2_actual_token:
                            continue  # Error check

                        game_start_payload = {
                            "game_id": active_game_id,
                            "board": board_list_for_start,
                            "current_player_token": db_game.current_player_token,  # AI1 or Human P1
                            "players": {
                                p1_actual_token: PLAYER_X,
                                p2_actual_token: PLAYER_O,
                            },
                            # For spectator in AVA, your_piece/your_token might be different
                            "your_piece": (
                                PLAYER_X
                                if db_game.player1_token == player_human_token
                                else (None if db_game_mode.startswith("AVA") else None)
                            ),
                            "your_token": (
                                player_human_token
                                if db_game.player1_token == player_human_token
                                else (None if db_game_mode.startswith("AVA") else None)
                            ),
                        }
                        # Send GAME_START to the spectator(s) in the room
                        await manager.broadcast_to_game(
                            {"type": "GAME_START", "payload": game_start_payload},
                            active_game_id,
                        )

                        # If AVA, automatically start AI turns
                        if db_game.game_mode.startswith(
                            "AVA"
                        ) and db_game.current_player_token.startswith("AI_"):
                            # Trigger the first AI's move (will be handled by MAKE_MOVE logic if we send a "dummy" trigger or refactor)
                            # For now, let's initiate the AI loop here directly or by calling a helper
                            print(
                                f"AVA Game {active_game_id}: Starting AI vs AI play. First turn: {db_game.current_player_token}"
                            )
                            # We need a task to run the AI vs AI game loop
                            # This is a good place for an asyncio task
                            asyncio.create_task(
                                run_ai_vs_ai_game(
                                    db_game.id, db
                                )  # Pass a new DB session if get_db isn't ideal for long task
                            )
                elif message_type == "JOIN_GAME":
                    game_to_join_id_str = payload.get("game_id")
                    player2_temp_id = payload.get(
                        "player_temp_id", client_id
                    )  # Use client_id as fallback

                    if not game_to_join_id_str:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "game_id not provided for JOIN_GAME."
                                },
                            },
                            websocket,
                        )
                        continue

                    try:
                        game_to_join_uuid = uuid.UUID(game_to_join_id_str)
                    except ValueError:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "Invalid game_id format for JOIN_GAME."
                                },
                            },
                            websocket,
                        )
                        continue

                    db_game = crud_game.get_game(db, game_id=game_to_join_uuid)

                    if not db_game:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {"message": "Game not found to join."},
                            },
                            websocket,
                        )
                        continue

                    if db_game.game_mode != "PVP":
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {"message": "This game is not a PvP game."},
                            },
                            websocket,
                        )
                        continue

                    if (
                        db_game.player2_token is not None
                        and db_game.player2_token != player2_temp_id
                    ):
                        # Game already has two distinct players (or P2 is trying to join again with different ID)
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "Game is already full or you cannot rejoin with a different ID."
                                },
                            },
                            websocket,
                        )
                        continue

                    if db_game.player1_token == player2_temp_id:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "You cannot join a game you created as Player 2."
                                },
                            },
                            websocket,
                        )
                        continue

                    # Successfully join the game as Player 2
                    active_game_id = (
                        game_to_join_id_str  # Associate this websocket with the game
                    )
                    await manager.connect(websocket, active_game_id)

                    new_player2_token = player2_temp_id
                    new_status_on_join = db_game.status  # Default to current status
                    if db_game.status == "waiting_for_player2":
                        new_status_on_join = "active"

                    db_game = crud_game.update_game_state(
                        db,
                        game_id=game_to_join_uuid,
                        player2_token=new_player2_token,  # Pass it directly
                        status=new_status_on_join,
                    )
                    if not db_game:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "Failed to update game state on join."
                                },
                            },
                            websocket,
                        )
                        continue

                    print(
                        f"DEBUG: For GAME_JOINED, db_game.player1_token is: {db_game.player1_token}"
                    )
                    # Notify this joining player (P2)
                    await manager.send_personal_message(
                        {
                            "type": "GAME_JOINED",
                            "payload": {
                                "game_id": active_game_id,
                                "player_token": player2_temp_id,  # Your (P2) token
                                "player_piece": PLAYER_O,  # P2 is O by default
                                "opponent_token": db_game.player1_token,
                                "message": f"Successfully joined game. You are Player 2 ({PLAYER_O}).",
                            },
                        },
                        websocket,
                    )

                    # Prepare GAME_START payload for both players
                    # The board from DB is {"board": [actual_list_of_lists]}
                    board_list_for_start: GameLogicBoard = db_game.board_state.get(
                        "board", service_create_board()
                    )

                    # Critical: Ensure tokens are correctly fetched from the updated db_game object
                    p1_token_for_payload = db_game.player1_token
                    p2_token_for_payload = db_game.player2_token

                    if not p1_token_for_payload or not p2_token_for_payload:
                        print(
                            f"ERROR: Missing player tokens for GAME_START. P1: {p1_token_for_payload}, P2: {p2_token_for_payload}"
                        )
                        # Handle error appropriately, maybe send an error to clients
                        continue  # Skip sending GAME_START if tokens are missing

                    game_start_payload = {
                        "game_id": active_game_id,
                        "board": board_list_for_start,
                        "current_player_token": db_game.current_player_token,  # Should be P1's token
                        "players": {
                            p1_token_for_payload: PLAYER_X,
                            p2_token_for_payload: PLAYER_O,
                        },
                        # 'your_piece' will be added per player by send_game_start_to_players
                    }

                    # Send GAME_START to both players
                    # Player 1 (Creator)
                    # await manager.broadcast_to_game(
                    #     {
                    #         "type": "GAME_START",
                    #         "payload": {
                    #             **game_start_payload,
                    #             "your_piece": PLAYER_X,
                    #             "your_token": db_game.player1_token,
                    #         },
                    #     },
                    #     active_game_id,  # This will send to both, we need to target or filter
                    # )
                    # This broadcast_to_game sends to everyone in the room.
                    # If we want to send specific 'your_piece' and 'your_token' to each, we'd need to iterate
                    # or have a more sophisticated broadcast/send_to_player method.
                    # For now, let's make two separate targeted sends for GAME_START

                    # Find player1's websocket (this is a bit manual without a direct map of token to websocket)
                    # This highlights a need for better player-websocket mapping if we need to target frequently.
                    # For now, we assume the first connection in the room for this game might be P1
                    # if the room was just formed. A better way is needed.

                    # --- REVISED GAME_START SENDING ---
                    # --- TEMPORARY SIMPLIFIED GAME_START SENDING for debugging double messages ---
                    # print(
                    #     f"DEBUG: About to broadcast GAME_START to game {active_game_id}"
                    # )
                    # await manager.broadcast_to_game(
                    #     {
                    #         "type": "GAME_START_BROADCAST_TEST",
                    #         "payload": game_start_payload,
                    #     },  # Note changed type
                    #     active_game_id,
                    # )
                    # --- END TEMPORARY ---
                    player_websockets = manager.active_connections.get(
                        active_game_id, []
                    )
                    print(
                        f"DEBUG: Game {active_game_id}, players in room for GAME_START: {len(player_websockets)}"
                    )
                    for ws_conn in player_websockets:
                        print(
                            f"DEBUG: Checking ws_conn: {ws_conn}, current joining P2 websocket: {websocket}"
                        )
                        if ws_conn == websocket:  # This is Player 2
                            await manager.send_personal_message(
                                {
                                    "type": "GAME_START",
                                    "payload": {
                                        **game_start_payload,
                                        "your_piece": PLAYER_O,
                                        "your_token": p2_token_for_payload,
                                    },
                                },
                                ws_conn,
                            )
                        else:  # Assume the other is Player 1
                            await manager.send_personal_message(
                                {
                                    "type": "GAME_START",
                                    "payload": {
                                        **game_start_payload,
                                        "your_piece": PLAYER_X,
                                        "your_token": p1_token_for_payload,
                                    },
                                },
                                ws_conn,
                            )

                elif message_type == "MAKE_MOVE":
                    if not active_game_id:  # Check if client is in a game
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "No active game. Create or join first."
                                },
                            },
                            websocket,
                        )
                        continue

                    player_token_from_msg = payload.get("player_token")
                    row = payload.get("row")
                    side = payload.get("side")

                    if (
                        None in [player_token_from_msg, row, side]
                        or side not in ["L", "R"]
                        or not isinstance(row, int)
                    ):
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {"message": "Invalid MAKE_MOVE payload."},
                            },
                            websocket,
                        )
                        continue

                    try:
                        game_uuid = uuid.UUID(active_game_id)
                    except ValueError:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "Internal server error: Corrupted game session."
                                },
                            },
                            websocket,
                        )
                        active_game_id = None  # Clear corrupted game_id
                        continue

                    db_game = crud_game.get_game(db, game_id=game_uuid)
                    if not db_game:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {"message": "Game not found."},
                            },
                            websocket,
                        )
                        active_game_id = None
                        continue

                    if db_game.status != "active":
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": f"Game is not active. Status: {db_game.status}"
                                },
                            },
                            websocket,
                        )
                        continue
                    if db_game.game_mode.startswith("AVA"):  # AI vs AI
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "Spectators cannot make moves in AI vs AI games."
                                },
                            },
                            websocket,
                        )
                        continue

                    if db_game.current_player_token != player_token_from_msg:
                        await manager.send_personal_message(
                            {"type": "ERROR", "payload": {"message": "Not your turn."}},
                            websocket,
                        )
                        continue

                    player_piece = (
                        PLAYER_X
                        if db_game.player1_token == player_token_from_msg
                        else PLAYER_O
                    )
                    if not (
                        (
                            db_game.player1_token == player_token_from_msg
                            and player_piece == PLAYER_X
                        )
                        or (
                            db_game.player2_token == player_token_from_msg
                            and player_piece == PLAYER_O
                        )
                    ):
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "Player token mismatch for game."
                                },
                            },
                            websocket,
                        )
                        continue

                    current_board_list: GameLogicBoard = db_game.board_state.get(
                        "board", service_create_board()
                    )
                    if not is_valid_move(current_board_list, row, side):
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {"message": "Invalid move on board."},
                            },
                            websocket,
                        )
                        continue

                    placed_coords = apply_move(
                        current_board_list, row, side, player_piece
                    )
                    if not placed_coords:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {"message": "Failed to apply move."},
                            },
                            websocket,
                        )
                        continue

                    # --- HUMAN PLAYER'S MOVE IS APPLIED, NOW UPDATE DB AND CHECK STATE ---
                    human_move_board_json = {"board": current_board_list}
                    human_move_status = "active"
                    human_move_winner = None
                    human_move_next_player_token = None
                    human_game_over = False

                    if check_win(current_board_list, player_piece, placed_coords):
                        human_move_status = f"player_{player_piece.lower()}_wins"
                        human_move_winner = player_token_from_msg
                        human_game_over = True
                    elif check_draw(current_board_list):
                        human_move_status = "draw"
                        human_move_winner = "draw"
                        human_game_over = True
                    else:
                        human_move_next_player_token = (
                            db_game.player2_token
                            if player_token_from_msg == db_game.player1_token
                            else db_game.player1_token
                        )

                    db_game = crud_game.update_game_state(
                        db=db,
                        game_id=game_uuid,
                        board_state=human_move_board_json,
                        current_player_token=(
                            human_move_next_player_token
                            if not human_game_over
                            else None
                        ),
                        status=human_move_status,
                        winner_token=human_move_winner,
                    )
                    if not db_game:  # Should not happen
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {"message": "Failed to save human move."},
                            },
                            websocket,
                        )
                        continue

                    # --- BROADCAST RESULT OF HUMAN MOVE OR PREPARE FOR AI ---
                    if human_game_over:
                        game_over_payload = {
                            "game_id": active_game_id,
                            "board": db_game.board_state.get("board", []),
                            "status": db_game.status,
                            "winner_token": db_game.winner_token,
                            "winning_player_piece": (
                                player_piece if db_game.winner_token != "draw" else None
                            ),
                        }
                        await manager.broadcast_to_game(
                            {"type": "GAME_OVER", "payload": game_over_payload},
                            active_game_id,
                        )
                        continue  # Game ended with human move
                    else:
                        game_update_payload_after_human = {
                            "game_id": active_game_id,
                            "board": db_game.board_state.get("board", []),
                            "current_player_token": db_game.current_player_token,
                            "last_move": {
                                "player_token": player_token_from_msg,
                                "player_piece": player_piece,
                                "row": placed_coords[0],
                                "col": placed_coords[1],
                                "side_played": side,
                            },
                        }
                        await manager.broadcast_to_game(
                            {
                                "type": "GAME_UPDATE",
                                "payload": game_update_payload_after_human,
                            },
                            active_game_id,
                        )

                    # If not game over, and it's PvE, and AI's turn:
                    is_ai_turn = (
                        db_game.game_mode.startswith("PVE")
                        and db_game.current_player_token
                        and db_game.current_player_token.startswith("AI_")
                    )

                    if is_ai_turn:
                        ai_player_token = (
                            db_game.current_player_token
                        )  # e.g. "AI_EASY_PLAYER"
                        ai_player_piece = (
                            PLAYER_O  # AI is always P2/O in this PVE setup
                        )

                        ai_bot_instance = None
                        game_mode_upper = db_game.game_mode.upper()
                        if "EASY" in game_mode_upper:
                            ai_bot_instance = EasyAIBot(player_piece=ai_player_piece)
                            await asyncio.sleep(1)
                        elif "MEDIUM" in game_mode_upper:
                            ai_bot_instance = MediumAIBot(
                                player_piece=ai_player_piece, search_depth=2
                            )
                            await asyncio.sleep(1)
                        elif "HARD" in game_mode_upper:
                            ai_bot_instance = HardAIBot(
                                player_piece=ai_player_piece, search_depth=4
                            )
                            await asyncio.sleep(0.5)

                        if ai_bot_instance:
                            print(
                                f"AI ({ai_player_piece}, {db_game.game_mode}) is thinking..."
                            )
                            ai_board_for_move: GameLogicBoard = db_game.board_state.get(
                                "board", service_create_board()
                            )
                            ai_move_tuple = ai_bot_instance.get_move(ai_board_for_move)

                            if ai_move_tuple:
                                ai_row, ai_side = ai_move_tuple
                                print(
                                    f"AI ({ai_player_piece}) chose: r{ai_row}, s{ai_side}"
                                )
                                ai_placed_coords = apply_move(
                                    ai_board_for_move, ai_row, ai_side, ai_player_piece
                                )

                                if not ai_placed_coords:
                                    print(
                                        f"ERROR: AI ({ai_player_piece}) made an invalid board move: {ai_move_tuple}"
                                    )
                                    # This is bad, AI should always make valid moves. Send error or default.
                                    # For now, just log and game might appear to stall or P1 plays again.
                                    # A robust system might have AI forfeit or try again.
                                    await manager.broadcast_to_game(
                                        {
                                            "type": "ERROR",
                                            "payload": {
                                                "message": "AI Error: Invalid move by AI."
                                            },
                                        },
                                        active_game_id,
                                    )
                                else:
                                    ai_move_board_json = {"board": ai_board_for_move}
                                    ai_move_status = "active"
                                    ai_move_winner = None
                                    ai_move_next_player = None  # Will be human (P1)
                                    ai_game_over = False

                                    if check_win(
                                        ai_board_for_move,
                                        ai_player_piece,
                                        ai_placed_coords,
                                    ):
                                        ai_move_status = (
                                            f"player_{ai_player_piece.lower()}_wins"
                                        )
                                        ai_move_winner = ai_player_token
                                        ai_game_over = True
                                    elif check_draw(ai_board_for_move):
                                        ai_move_status = "draw"
                                        ai_move_winner = "draw"
                                        ai_game_over = True
                                    else:
                                        ai_move_next_player = (
                                            db_game.player1_token
                                        )  # Back to human

                                    db_game = crud_game.update_game_state(
                                        db=db,
                                        game_id=game_uuid,
                                        board_state=ai_move_board_json,
                                        current_player_token=(
                                            ai_move_next_player
                                            if not ai_game_over
                                            else None
                                        ),
                                        status=ai_move_status,
                                        winner_token=ai_move_winner,
                                    )
                                    if not db_game:
                                        await manager.broadcast_to_game(
                                            {
                                                "type": "ERROR",
                                                "payload": {
                                                    "message": "Failed to save AI move."
                                                },
                                            },
                                            active_game_id,
                                        )
                                        continue

                                    # Now broadcast result of AI's move
                                    if ai_game_over:
                                        game_over_payload = {
                                            "game_id": active_game_id,
                                            "board": db_game.board_state.get(
                                                "board", []
                                            ),
                                            "status": db_game.status,
                                            "winner_token": db_game.winner_token,
                                            "winning_player_piece": (
                                                ai_player_piece
                                                if db_game.winner_token != "draw"
                                                else None
                                            ),
                                        }
                                        await manager.broadcast_to_game(
                                            {
                                                "type": "GAME_OVER",
                                                "payload": game_over_payload,
                                            },
                                            active_game_id,
                                        )
                                    else:
                                        game_update_payload = {
                                            "game_id": active_game_id,
                                            "board": db_game.board_state.get(
                                                "board", []
                                            ),
                                            "current_player_token": db_game.current_player_token,  # Should be P1's token
                                            "last_move": {
                                                "player_token": ai_player_token,
                                                "player_piece": ai_player_piece,
                                                "row": ai_placed_coords[0],
                                                "col": ai_placed_coords[1],
                                                "side_played": ai_side,
                                            },
                                        }
                                        await manager.broadcast_to_game(
                                            {
                                                "type": "GAME_UPDATE",
                                                "payload": game_update_payload,
                                            },
                                            active_game_id,
                                        )
                            else:  # AI found no move
                                print(
                                    f"AI ({ai_player_piece}) found no valid moves. Game state: {db_game.status}"
                                )
                                # This might be a draw if board is full but not detected as win by AI logic
                                # Or if AI logic is flawed. For now, control implicitly returns to human if no GAME_OVER.
                                # We should ensure the current_player_token is correctly set for human.
                                # If AI couldn't move and board isn't full (shouldn't happen with valid AI),
                                # it would be human's turn again if current_player_token wasn't P1.
                                # Let's ensure if AI fails to move, turn reverts to P1 (or an error state is set)
                                if (
                                    db_game.current_player_token
                                    and db_game.current_player_token.startswith("AI_")
                                ):  # If it was AI's turn
                                    db_game = crud_game.update_game_state(
                                        db,
                                        game_id=game_uuid,
                                        current_player_token=db_game.player1_token,
                                    )
                                    game_update_payload = {  # Send update that it's P1's turn again
                                        "game_id": active_game_id,
                                        "board": db_game.board_state.get("board", []),
                                        "current_player_token": db_game.current_player_token,
                                        "last_move": None,  # No AI move made
                                    }
                                    await manager.broadcast_to_game(
                                        {
                                            "type": "GAME_UPDATE",
                                            "payload": game_update_payload,
                                        },
                                        active_game_id,
                                    )

                        else:  # AI bot type not found
                            print(
                                f"ERROR: AI bot for mode {db_game.game_mode} not implemented."
                            )
                            await manager.broadcast_to_game(
                                {
                                    "type": "ERROR",
                                    "payload": {
                                        "message": f"AI for {db_game.game_mode} not available."
                                    },
                                },
                                active_game_id,
                            )
                            # Revert turn to human player to avoid game stall
                            if (
                                db_game.current_player_token
                                and db_game.current_player_token.startswith("AI_")
                            ):
                                db_game = crud_game.update_game_state(
                                    db,
                                    game_id=game_uuid,
                                    current_player_token=db_game.player1_token,
                                )
                                # Also send an update
                                game_update_payload = {
                                    "game_id": active_game_id,
                                    "board": db_game.board_state.get("board", []),
                                    "current_player_token": db_game.current_player_token,
                                    "last_move": None,
                                }
                                await manager.broadcast_to_game(
                                    {
                                        "type": "GAME_UPDATE",
                                        "payload": game_update_payload,
                                    },
                                    active_game_id,
                                )

                    else:  # Not AI's turn (PvP or AI just moved / game over by human)
                        # This is for PvP game update after human move
                        game_update_payload = {
                            "game_id": active_game_id,
                            "board": db_game.board_state.get("board", []),
                            "current_player_token": db_game.current_player_token,  # Next human player
                            "last_move": {
                                "player_token": player_token_from_msg,
                                "player_piece": player_piece,
                                "row": placed_coords[0],
                                "col": placed_coords[1],
                                "side_played": side,
                            },
                        }
                        await manager.broadcast_to_game(
                            {"type": "GAME_UPDATE", "payload": game_update_payload},
                            active_game_id,
                        )

                else:
                    await manager.send_personal_message(
                        {
                            "type": "ERROR",
                            "payload": {
                                "message": f"Unknown message type: {message_type}"
                            },
                        },
                        websocket,
                    )

            except json.JSONDecodeError:
                print(f"Error decoding JSON from {client_id}: {data}")
                await manager.send_personal_message(
                    {"type": "ERROR", "payload": {"message": "Invalid JSON format."}},
                    websocket,
                )
            except Exception as e:
                print(f"Error processing message from {client_id}: {e}")
                await manager.send_personal_message(
                    {
                        "type": "ERROR",
                        "payload": {"message": f"Server error: {str(e)}"},
                    },
                    websocket,
                )

    except WebSocketDisconnect:
        print(
            f"WebSocket disconnected for client_id: {client_id}, active_game_id: {active_game_id}"
        )
        if active_game_id:
            manager.disconnect(websocket, active_game_id)
            # Optionally, broadcast to other players in the game that this player disconnected
            # await manager.broadcast_to_game({"type": "PLAYER_DISCONNECTED", "payload": {"player_id": client_id}}, active_game_id)
    except Exception as e:
        # Catch any other exceptions during the WebSocket lifecycle
        print(
            f"Unhandled exception for WebSocket client {client_id} in game {active_game_id}: {e}"
        )
        if active_game_id and websocket:  # Ensure websocket is still valid
            try:
                await manager.send_personal_message(
                    {
                        "type": "ERROR",
                        "payload": {"message": f"Critical server error: {str(e)}"},
                    },
                    websocket,
                )
            except:  # Ignore if sending error also fails
                pass
        if active_game_id:  # Attempt to disconnect if game_id is known
            manager.disconnect(websocket, active_game_id)
