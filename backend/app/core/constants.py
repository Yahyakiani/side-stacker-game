# backend/app/core/constants.py

# Player Pieces (already in game_logic.py, but good to centralize if used widely)
PLAYER_X = "X"
PLAYER_O = "O"
EMPTY_CELL = None  # From game_logic.py

# Game Statuses
GAME_STATUS_WAITING_FOR_PLAYER2 = "waiting_for_player2"
GAME_STATUS_ACTIVE = "active"
GAME_STATUS_DRAW = "draw"


# Function to generate win status, e.g., player_x_wins
def get_win_status(player_piece: str) -> str:
    return f"player_{player_piece.lower()}_wins"


GAME_STATUS_ERROR_AI_STUCK = "error_ai_stuck"  # Custom status from run_ai_vs_ai_game

# Game Modes - Raw from client (PVP, PVE, AVA)
GAME_MODE_PVP = "PVP"
GAME_MODE_PVE = "PVE"
GAME_MODE_AVA = "AVA"

# AI Difficulty Levels
AI_DIFFICULTY_EASY = "EASY"
AI_DIFFICULTY_MEDIUM = "MEDIUM"
AI_DIFFICULTY_HARD = "HARD"

# DB Game Modes (Constructed, e.g., PVE_EASY, AVA_EASY_VS_MEDIUM)
DB_GAME_MODE_PVE_PREFIX = "PVE_"
DB_GAME_MODE_AVA_PREFIX = "AVA_"

# WebSocket Message Types - Server to Client
WS_MSG_TYPE_GAME_CREATED = "GAME_CREATED"
WS_MSG_TYPE_GAME_JOINED = "GAME_JOINED"
WS_MSG_TYPE_GAME_START = "GAME_START"
WS_MSG_TYPE_GAME_UPDATE = "GAME_UPDATE"
WS_MSG_TYPE_GAME_OVER = "GAME_OVER"
WS_MSG_TYPE_WAITING_FOR_PLAYER = "WAITING_FOR_PLAYER"
WS_MSG_TYPE_ERROR = "ERROR"

# WebSocket Message Types - Client to Server
WS_MSG_TYPE_CLIENT_CREATE_GAME = "CREATE_GAME"
WS_MSG_TYPE_CLIENT_JOIN_GAME = "JOIN_GAME"
WS_MSG_TYPE_CLIENT_MAKE_MOVE = "MAKE_MOVE"

# AI Player Token Prefixes/Suffixes
AI_PLAYER_TOKEN_PREFIX = "AI_"
AI_PLAYER_TOKEN_PLAYER1_SUFFIX = "_PLAYER_1"
AI_PLAYER_TOKEN_PLAYER2_SUFFIX = "_PLAYER_2"
AI_PLAYER_TOKEN_GENERIC_SUFFIX = "_PLAYER"

# Default Values
DEFAULT_AI_DIFFICULTY = AI_DIFFICULTY_EASY

# Magic Strings for Tokens/Values
SPECTATOR_TOKEN_VALUE = "SPECTATOR"
DRAW_WINNER_TOKEN_VALUE = "draw"

# Payload Keys
CLIENT_ID_PARAM_NAME = "client_id"
PLAYER_TEMP_ID_PAYLOAD_KEY = "player_temp_id"
MODE_PAYLOAD_KEY = "mode"
DIFFICULTY_PAYLOAD_KEY = "difficulty"
AI1_DIFFICULTY_PAYLOAD_KEY = "ai1_difficulty"
AI2_DIFFICULTY_PAYLOAD_KEY = "ai2_difficulty"
GAME_ID_PAYLOAD_KEY = "game_id"
PLAYER_TOKEN_PAYLOAD_KEY = "player_token"
ROW_PAYLOAD_KEY = "row"
SIDE_PAYLOAD_KEY = "side"

# Control Sides
CONTROL_SIDE_LEFT = "L"
CONTROL_SIDE_RIGHT = "R"

# Error Message Strings (Centralized for consistency)
SPECTATOR_CANNOT_MOVE_ERROR = "Spectators cannot make moves in AI vs AI games."
NOT_YOUR_TURN_ERROR = "Not your turn."
GAME_NOT_ACTIVE_ERROR_PREFIX = "Game is not active. Status: "
INVALID_MOVE_PAYLOAD_ERROR = "Invalid MAKE_MOVE payload."
GAME_NOT_FOUND_ERROR = "Game not found."
PLAYER_TOKEN_MISMATCH_ERROR = "Player token mismatch for game."
INVALID_BOARD_MOVE_ERROR = "Invalid move on board."
APPLY_MOVE_FAILED_ERROR = "Failed to apply move."
SAVE_MOVE_FAILED_ERROR = "Failed to save move."
AI_INVALID_MOVE_ERROR = "AI Error: Invalid move by AI."
AI_UNAVAILABLE_ERROR_PREFIX = "AI for "
AI_UNAVAILABLE_ERROR_SUFFIX = " not available."
JOIN_GAME_ID_MISSING_ERROR = "game_id not provided for JOIN_GAME."
JOIN_INVALID_GAME_ID_FORMAT_ERROR = "Invalid game_id format for JOIN_GAME."
JOIN_GAME_NOT_FOUND_ERROR = "Game not found to join."
JOIN_NOT_PVP_ERROR = "This game is not a PvP game."
JOIN_GAME_FULL_ERROR = "Game is already full or you cannot rejoin with a different ID."
JOIN_AS_PLAYER2_IN_OWN_GAME_ERROR = "You cannot join a game you created as Player 2."
JOIN_UPDATE_FAILED_ERROR = "Failed to update game state on join."
NO_ACTIVE_GAME_ERROR = "No active game. Create or join first."
CORRUPTED_GAME_SESSION_ERROR = "Internal server error: Corrupted game session."
