# backend/app/websockets/connection_manager.py
from fastapi import WebSocket
from typing import List, Dict, Optional
import json  # For sending structured messages


class ConnectionManager:
    def __init__(self):
        # Stores active connections per game_id
        # Example: {"game_uuid_1": [WebSocket1, WebSocket2], "game_uuid_2": [WebSocket3]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str):
        # await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)
        print(
            f"WebSocket connected for game {game_id}. Total in room: {len(self.active_connections[game_id])}"
        )

    def disconnect(self, websocket: WebSocket, game_id: str):
        if game_id in self.active_connections:
            if websocket in self.active_connections[game_id]:
                self.active_connections[game_id].remove(websocket)
                print(
                    f"WebSocket disconnected for game {game_id}. Remaining in room: {len(self.active_connections[game_id])}"
                )
                if not self.active_connections[game_id]:  # If room is empty, remove it
                    del self.active_connections[game_id]
                    print(f"Game room {game_id} removed as it's empty.")
        else:
            print(f"Warning: WebSocket for game {game_id} not found during disconnect.")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Sends a JSON message to a specific websocket connection."""
        await websocket.send_text(json.dumps(message))

    async def broadcast_to_game(
        self, message: dict, game_id: str, exclude_websocket: Optional[WebSocket] = None
    ):
        """Broadcasts a JSON message to all clients in a specific game room, optionally excluding one."""
        if game_id in self.active_connections:
            # print(f"Broadcasting to game {game_id}: {message}")
            disconnected_clients = []
            for connection in self.active_connections[game_id]:
                if connection != exclude_websocket:
                    try:
                        await connection.send_text(json.dumps(message))
                    except (
                        Exception
                    ) as e:  # Catch potential errors if client disconnected abruptly
                        print(
                            f"Error sending message to a websocket in game {game_id}: {e}"
                        )
                        disconnected_clients.append(connection)

            # Clean up any clients that errored out during broadcast
            for client in disconnected_clients:
                self.disconnect(client, game_id)
        else:
            print(
                f"Warning: No active connections found for game_id {game_id} to broadcast message: {message}"
            )


# Singleton instance of the manager
manager = ConnectionManager()
