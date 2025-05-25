# backend/app/websockets/connection_manager.py
from fastapi import WebSocket
from typing import List, Dict, Optional, Any
import json

from app.core import constants

from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

class ConnectionManager:
    def __init__(self):
        # Stores active connections: game_id -> {client_id: WebSocket}
        self.game_rooms: Dict[str, Dict[str, WebSocket]] = {}
        # Optional: A reverse mapping to quickly find game_id and client_id from a WebSocket object
        # This is useful for disconnect logic if client_id/game_id isn't passed.
        self.websocket_to_ids: Dict[WebSocket, Dict[str, str]] = (
            {}
        )  # {websocket: {"game_id": ..., "client_id": ...}}

    async def connect(self, websocket: WebSocket, game_id: str, client_id: str):
        """
        Connects a WebSocket to a game room, associating it with a client_id.
        If the client_id already exists in the room with a different WebSocket,
        the old WebSocket is implicitly orphaned (should be disconnected first if possible).
        """
        if not game_id or not client_id:
            logger.error(
                f"Error: game_id and client_id are required to connect. Game: '{game_id}', Client: '{client_id}'"
            )
            # Optionally, raise an error or send one back via websocket if it's already accepted
            return

        if game_id not in self.game_rooms:
            self.game_rooms[game_id] = {}

        # If this client was already connected with a *different* websocket instance,
        # this new connection will overwrite the old one for this client_id in this room.
        # The old websocket, if still active, would need to be disconnected separately.
        if (
            client_id in self.game_rooms[game_id]
            and self.game_rooms[game_id][client_id] != websocket
        ):
            old_ws = self.game_rooms[game_id][client_id]
            logger.warning(
                f"Warning: Client {client_id} in game {game_id} reconnected with a new WebSocket instance. Old instance {old_ws} is now orphaned in this mapping."
            )
            # Clean up old websocket from websocket_to_ids if it exists
            if old_ws in self.websocket_to_ids:
                del self.websocket_to_ids[old_ws]

        self.game_rooms[game_id][client_id] = websocket
        self.websocket_to_ids[websocket] = {"game_id": game_id, "client_id": client_id}

        logger.info(
            f"WebSocket for client {client_id} connected to game {game_id}. Total clients in room: {len(self.game_rooms[game_id])}"
        )

    def disconnect(
        self,
        websocket: WebSocket,
        game_id: Optional[str] = None,
        client_id: Optional[str] = None,
    ):
        """
        Disconnects a WebSocket. If game_id and client_id are not provided,
        it attempts to find them using the websocket_to_ids mapping.
        """
        ids = self.websocket_to_ids.get(websocket)

        # Use provided ids or try to find them from the mapping
        effective_game_id = game_id or (ids.get("game_id") if ids else None)
        effective_client_id = client_id or (ids.get("client_id") if ids else None)

        if not effective_game_id or not effective_client_id:
            logger.warning(
                f"Warning: Could not determine game_id or client_id for websocket {websocket} during disconnect. Game: {effective_game_id}, Client: {effective_client_id}"
            )
            return

        room = self.game_rooms.get(effective_game_id)
        if room and effective_client_id in room:
            # Ensure we are removing the exact websocket instance that was registered for this client_id
            if room[effective_client_id] == websocket:
                del room[effective_client_id]
                logger.info(
                    f"WebSocket for client {effective_client_id} disconnected from game {effective_game_id}. Remaining: {len(room)}"
                )
                if not room:  # If room is empty, remove it
                    del self.game_rooms[effective_game_id]
                    logger.info(f"Game room {effective_game_id} removed as it's empty.")
            else:
                logger.warning(
                    f"Warning: WebSocket instance mismatch for client {effective_client_id} in game {effective_game_id} during disconnect."
                )
        else:
            logger.warning(
                f"Warning: Client {effective_client_id} or game room {effective_game_id} not found during disconnect."
            )

        if websocket in self.websocket_to_ids:
            del self.websocket_to_ids[websocket]

    async def send_personal_message(self, message_payload: dict, websocket: WebSocket):
        """Sends a JSON message to a specific websocket connection."""
        try:
            await websocket.send_text(json.dumps(message_payload))
        except Exception as e:
            logger.error(
                f"Error sending personal message to {websocket}: {e}. Client might have disconnected."
            )
            # Attempt to clean up if the websocket is known
            self.disconnect(websocket)  # Will use websocket_to_ids to find context

    async def send_error(self, websocket: WebSocket, error_message: str):
        """Sends a structured ERROR message to a specific websocket."""
        await self.send_personal_message(
            {
                "type": constants.WS_MSG_TYPE_ERROR,
                "payload": {"message": error_message},
            },
            websocket,
        )

    async def broadcast_to_game(
        self,
        message_payload: dict,
        game_id: str,
        exclude_client_id: Optional[str] = None,  # Changed from exclude_websocket
    ):
        """Broadcasts a JSON message to all clients in a specific game room, optionally excluding one by client_id."""
        room = self.game_rooms.get(game_id)
        if room:
            disconnected_clients_to_remove = []  # Store client_ids to remove
            for cid, ws_conn in room.items():  # Iterate over client_id, websocket pairs
                if cid != exclude_client_id:
                    try:
                        await ws_conn.send_text(json.dumps(message_payload))
                    except Exception as e:
                        logger.error(
                            f"Error sending broadcast message to client {cid} in game {game_id}: {e}"
                        )
                        disconnected_clients_to_remove.append(cid)  # Store client_id

            for cid_to_remove in disconnected_clients_to_remove:
                # Retrieve websocket again for disconnect, or ensure disconnect can take client_id
                ws_to_disconnect = room.get(cid_to_remove)  # Get the ws instance
                if ws_to_disconnect:
                    self.disconnect(ws_to_disconnect, game_id, cid_to_remove)
        else:
            logger.warning(
                f"Warning: No active room for game_id {game_id} to broadcast: {message_payload.get('type', 'Unknown type')}"
            )

    async def broadcast_error_to_game(
        self,
        game_id: str,
        error_message: str,
        exclude_client_id: Optional[str] = None,
    ):
        await self.broadcast_to_game(
            {
                "type": constants.WS_MSG_TYPE_ERROR,
                "payload": {"message": error_message},
            },
            game_id,
            exclude_client_id=exclude_client_id,
        )

    async def broadcast_game_update(
        self,
        game_id: str,
        board: List[List[Optional[str]]],
        current_player_token: str,
        last_move: Optional[Dict[str, Any]],
        exclude_client_id: Optional[str] = None,
    ):
        payload = {
            "game_id": game_id,
            "board": board,
            "current_player_token": current_player_token,
            "last_move": last_move,
        }
        await self.broadcast_to_game(
            {"type": constants.WS_MSG_TYPE_GAME_UPDATE, "payload": payload},
            game_id,
            exclude_client_id=exclude_client_id,
        )

    async def broadcast_game_over(
        self,
        game_id: str,
        board: List[List[Optional[str]]],
        status: str,
        winner_token: Optional[str],
        winning_player_piece: Optional[str],
        reason: Optional[str] = None,
        exclude_client_id: Optional[str] = None,
    ):
        payload = {
            "game_id": game_id,
            "board": board,
            "status": status,
            "winner_token": winner_token,
            "winning_player_piece": winning_player_piece,
            "reason": reason,
        }
        await self.broadcast_to_game(
            {"type": constants.WS_MSG_TYPE_GAME_OVER, "payload": payload},
            game_id,
            exclude_client_id=exclude_client_id,
        )

    def get_websocket_for_client(
        self, game_id: str, client_id: str
    ) -> Optional[WebSocket]:
        """Retrieves the WebSocket for a specific client_id in a game_id."""
        room = self.game_rooms.get(game_id)
        if room:
            return room.get(client_id)
        return None

    def get_all_websockets_in_game(self, game_id: str) -> List[WebSocket]:
        """Returns a list of all WebSockets in a given game room."""
        room = self.game_rooms.get(game_id)
        if room:
            return list(room.values())
        return []

    def get_client_ids_in_game(self, game_id: str) -> List[str]:
        """Returns a list of all client_ids in a given game room."""
        room = self.game_rooms.get(game_id)
        if room:
            return list(room.keys())
        return []


# Singleton instance of the manager
manager = ConnectionManager()
