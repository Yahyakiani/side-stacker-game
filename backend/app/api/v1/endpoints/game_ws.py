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
)  # For type hinting and constants

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
                    # To be implemented in Phase 4
                    await manager.send_personal_message(
                        {
                            "type": "ERROR",
                            "payload": {"message": "JOIN_GAME not yet implemented."},
                        },
                        websocket,
                    )
                    pass

                elif message_type == "MAKE_MOVE":
                    # To be implemented in Phase 4
                    await manager.send_personal_message(
                        {
                            "type": "ERROR",
                            "payload": {"message": "MAKE_MOVE not yet implemented."},
                        },
                        websocket,
                    )
                    pass

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
