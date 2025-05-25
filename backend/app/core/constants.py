# backend/app/core/constants.py
from typing import Optional


PLAYER_X: str = "X"
PLAYER_O: str = "O"
EMPTY_CELL: Optional[str] = None  # From game_logic.py

# Game Statuses
GAME_STATUS_WAITING_FOR_PLAYER2: str = "waiting_for_player2"
GAME_STATUS_ACTIVE: str = "active"
GAME_STATUS_DRAW: str = "draw"

# Board Dimensions
ROWS: int = 7
COLS: int = 7
CONNECT_N: int = 4


# Function to generate win status, e.g., player_x_wins
def get_win_status(player_piece: str) -> str:
    return f"player_{player_piece.lower()}_wins"


GAME_STATUS_ERROR_AI_STUCK: str = "error_ai_stuck"  # Custom status from run_ai_vs_ai_game

# Game Modes - Raw from client (PVP, PVE, AVA)
GAME_MODE_PVP: str = "PVP"
GAME_MODE_PVE: str = "PVE"
GAME_MODE_AVA: str = "AVA"

# AI Difficulty Levels
AI_DIFFICULTY_EASY: str = "EASY"
AI_DIFFICULTY_MEDIUM: str = "MEDIUM"
AI_DIFFICULTY_HARD: str = "HARD"

# DB Game Modes (Constructed, e.g., PVE_EASY, AVA_EASY_VS_MEDIUM)
DB_GAME_MODE_PVE_PREFIX: str = "PVE_"
DB_GAME_MODE_AVA_PREFIX: str = "AVA_"

# WebSocket Message Types - Server to Client
WS_MSG_TYPE_GAME_CREATED: str = "GAME_CREATED"
WS_MSG_TYPE_GAME_JOINED: str = "GAME_JOINED"
WS_MSG_TYPE_GAME_START: str = "GAME_START"
WS_MSG_TYPE_GAME_UPDATE: str = "GAME_UPDATE"
WS_MSG_TYPE_GAME_OVER: str = "GAME_OVER"
WS_MSG_TYPE_WAITING_FOR_PLAYER: str = "WAITING_FOR_PLAYER"
WS_MSG_TYPE_ERROR: str = "ERROR"

# WebSocket Message Types - Client to Server
WS_MSG_TYPE_CLIENT_CREATE_GAME: str = "CREATE_GAME"
WS_MSG_TYPE_CLIENT_JOIN_GAME: str = "JOIN_GAME"
WS_MSG_TYPE_CLIENT_MAKE_MOVE: str = "MAKE_MOVE"

# AI Player Token Prefixes/Suffixes
AI_PLAYER_TOKEN_PREFIX: str = "AI_"
AI_PLAYER_TOKEN_PLAYER1_SUFFIX: str = "_PLAYER_1"
AI_PLAYER_TOKEN_PLAYER2_SUFFIX: str = "_PLAYER_2"
AI_PLAYER_TOKEN_GENERIC_SUFFIX: str = "_PLAYER"

# Default Values
DEFAULT_AI_DIFFICULTY: str = AI_DIFFICULTY_EASY

# Magic Strings for Tokens/Values
SPECTATOR_TOKEN_VALUE: str = "SPECTATOR"
DRAW_WINNER_TOKEN_VALUE: str = "draw"

# Payload Keys
CLIENT_ID_PARAM_NAME: str = "client_id"
PLAYER_TEMP_ID_PAYLOAD_KEY: str = "player_temp_id"
MODE_PAYLOAD_KEY: str = "mode"
DIFFICULTY_PAYLOAD_KEY: str = "difficulty"
AI1_DIFFICULTY_PAYLOAD_KEY: str = "ai1_difficulty"
AI2_DIFFICULTY_PAYLOAD_KEY: str = "ai2_difficulty"
GAME_ID_PAYLOAD_KEY: str = "game_id"
PLAYER_TOKEN_PAYLOAD_KEY: str = "player_token"
ROW_PAYLOAD_KEY: str = "row"
SIDE_PAYLOAD_KEY: str = "side"

# Control Sides
CONTROL_SIDE_LEFT: str = "L"
CONTROL_SIDE_RIGHT: str = "R"

# Error Message Strings (Centralized for consistency)
SPECTATOR_CANNOT_MOVE_ERROR: str = "Spectators cannot make moves in AI vs AI games."
NOT_YOUR_TURN_ERROR: str = "Not your turn."
GAME_NOT_ACTIVE_ERROR_PREFIX: str = "Game is not active. Status: "
INVALID_MOVE_PAYLOAD_ERROR: str = "Invalid MAKE_MOVE payload."
GAME_NOT_FOUND_ERROR: str = "Game not found."
PLAYER_TOKEN_MISMATCH_ERROR: str = "Player token mismatch for game."
INVALID_BOARD_MOVE_ERROR: str = "Invalid move on board."
APPLY_MOVE_FAILED_ERROR: str = "Failed to apply move."
SAVE_MOVE_FAILED_ERROR: str = "Failed to save move."
AI_INVALID_MOVE_ERROR: str = "AI Error: Invalid move by AI."
AI_UNAVAILABLE_ERROR_PREFIX: str = "AI for "
AI_UNAVAILABLE_ERROR_SUFFIX: str = " not available."
JOIN_GAME_ID_MISSING_ERROR: str = "game_id not provided for JOIN_GAME."
JOIN_INVALID_GAME_ID_FORMAT_ERROR: str = "Invalid game_id format for JOIN_GAME."
JOIN_GAME_NOT_FOUND_ERROR: str = "Game not found to join."
JOIN_NOT_PVP_ERROR: str = "This game is not a PvP game."
JOIN_GAME_FULL_ERROR: str = "Game is already full or you cannot rejoin with a different ID."
JOIN_AS_PLAYER2_IN_OWN_GAME_ERROR: str = "You cannot join a game you created as Player 2."
JOIN_UPDATE_FAILED_ERROR: str = "Failed to update game state on join."
NO_ACTIVE_GAME_ERROR: str = "No active game. Create or join first."
CORRUPTED_GAME_SESSION_ERROR: str = "Internal server error: Corrupted game session."
