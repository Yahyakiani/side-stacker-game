# backend/app/api/v1/endpoints/game_ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import json  # For parsing incoming messages and constructing outgoing ones
import uuid

from app.websockets.connection_manager import manager  # Our connection manager
from app.db.session import get_db
from app.crud import crud_game
from app.schemas.game import GameStateResponse  # Re-use for sending game state
from app.services.game_logic import (
    PLAYER_X,
    PLAYER_O,
    Board as GameLogicBoard,
    is_valid_move,
    apply_move,
    check_win,
    check_draw,
)  # For type hinting and constants
from app.services.game_logic import create_board as service_create_board

router = APIRouter()


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

                if message_type == "CREATE_GAME":
                    # Payload might contain: {"player_temp_id": "some_id", "mode": "PVP" | "PVE", "difficulty": "EASY" | "MEDIUM"}
                    # For now, player_temp_id from payload will be used as player1_token
                    player1_token = payload.get(
                        "player_temp_id", client_id
                    )  # Use client_id as fallback
                    game_mode = payload.get("mode", "PVP").upper()  # Default to PVP
                    # ai_difficulty = payload.get("difficulty", "EASY").upper() # For PVE later

                    # TODO: Handle PVE game creation with AI difficulty later
                    if game_mode not in ["PVP", "PVE_TEMP"]:  # PVE_TEMP as placeholder
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {"message": "Invalid game mode specified."},
                            },
                            websocket,
                        )
                        continue

                    # Create game in DB
                    db_game = crud_game.create_game_db(
                        db=db,
                        player1_token=player1_token,
                        initial_current_player_token=player1_token,  # P1 starts
                        game_mode=game_mode,
                    )
                    active_game_id = str(
                        db_game.id
                    )  # Store game_id for this connection

                    # Now add this websocket to the specific game room in the manager
                    await manager.connect(websocket, active_game_id)

                    response_payload = {
                        "game_id": active_game_id,
                        "player_token": player1_token,  # This client is Player 1
                        "player_piece": PLAYER_X,  # Player 1 is X by default
                        "message": (
                            f"Game created. You are Player 1 ({PLAYER_X}). Waiting for Player 2..."
                            if game_mode == "PVP"
                            else "Game created. You are Player 1."
                        ),
                    }
                    await manager.send_personal_message(
                        {"type": "GAME_CREATED", "payload": response_payload}, websocket
                    )

                    if game_mode == "PVP":
                        await manager.send_personal_message(
                            {
                                "type": "WAITING_FOR_PLAYER",
                                "payload": {"game_id": active_game_id},
                            },
                            websocket,
                        )
                    # If PVE, we might immediately start or send AI info later

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
                    if not active_game_id:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "No active game to make a move in. Create or join a game first."
                                },
                            },
                            websocket,
                        )
                        continue

                    # Payload example: {"player_token": "actual_player_token", "row": int, "side": "L" | "R"}
                    player_token_from_msg = payload.get("player_token")
                    row = payload.get("row")
                    side = payload.get("side")

                    if None in [player_token_from_msg, row, side] or side not in [
                        "L",
                        "R",
                    ]:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "Invalid MAKE_MOVE payload. Required: player_token, row, side."
                                },
                            },
                            websocket,
                        )
                        continue

                    # Fetch the game from DB
                    try:
                        game_uuid = uuid.UUID(active_game_id)
                    except (
                        ValueError
                    ):  # Should not happen if active_game_id is always a valid UUID string
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "Internal server error: Invalid game ID format."
                                },
                            },
                            websocket,
                        )
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
                        active_game_id = None  # Reset as this game ID is invalid
                        continue  # Or disconnect

                    if db_game.status != "active":
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": f"Game is not active. Current status: {db_game.status}"
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

                    # Determine player's piece (X or O)
                    player_piece = None
                    if db_game.player1_token == player_token_from_msg:
                        player_piece = PLAYER_X
                    elif db_game.player2_token == player_token_from_msg:
                        player_piece = PLAYER_O

                    if not player_piece:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "Player token not recognized for this game."
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
                                "payload": {"message": "Invalid move on the board."},
                            },
                            websocket,
                        )
                        continue

                    placed_coords = apply_move(
                        current_board_list, row, side, player_piece
                    )
                    if not placed_coords:  # Should be caught by is_valid_move above
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "Failed to apply move after validation."
                                },
                            },
                            websocket,
                        )
                        continue

                    new_board_state_json = {"board": current_board_list}
                    new_status = db_game.status
                    new_winner_token = db_game.winner_token
                    next_player_token = None

                    game_over = False
                    if check_win(current_board_list, player_piece, placed_coords):
                        new_status = f"player_{player_piece.lower()}_wins"
                        new_winner_token = player_token_from_msg
                        game_over = True
                    elif check_draw(current_board_list):
                        new_status = "draw"
                        new_winner_token = "draw"  # Special value for draw
                        game_over = True
                    else:
                        # Switch player token
                        if player_token_from_msg == db_game.player1_token:
                            next_player_token = db_game.player2_token
                        else:  # Assumes player_token_from_msg must be player2_token
                            next_player_token = db_game.player1_token
                        new_status = "active"

                    updated_db_game = crud_game.update_game_state(
                        db=db,
                        game_id=game_uuid,
                        board_state=new_board_state_json,
                        current_player_token=(
                            next_player_token if not game_over else None
                        ),
                        status=new_status,
                        winner_token=new_winner_token,
                    )

                    if not updated_db_game:
                        await manager.send_personal_message(
                            {
                                "type": "ERROR",
                                "payload": {
                                    "message": "Failed to update game state after move."
                                },
                            },
                            websocket,
                        )
                        continue

                    # Broadcast update or game over
                    final_board_to_broadcast: GameLogicBoard = (
                        updated_db_game.board_state.get("board", [])
                    )

                    if game_over:
                        game_over_payload = {
                            "game_id": active_game_id,
                            "board": final_board_to_broadcast,
                            "status": updated_db_game.status,  # e.g., "player_x_wins", "draw"
                            "winner_token": updated_db_game.winner_token,  # Token of winner or "draw"
                            "winning_player_piece": (
                                player_piece
                                if updated_db_game.winner_token != "draw"
                                else None
                            ),
                        }
                        await manager.broadcast_to_game(
                            {"type": "GAME_OVER", "payload": game_over_payload},
                            active_game_id,
                        )
                        # Optionally, disconnect players or clean up game room after a delay
                    else:
                        game_update_payload = {
                            "game_id": active_game_id,
                            "board": final_board_to_broadcast,
                            "current_player_token": updated_db_game.current_player_token,
                            "last_move": {  # Include details of the last move
                                "player_token": player_token_from_msg,
                                "player_piece": player_piece,
                                "row": placed_coords[0],  # row where piece was placed
                                "col": placed_coords[1],  # col where piece was placed
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
