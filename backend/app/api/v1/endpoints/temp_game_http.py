from fastapi import APIRouter, HTTPException, Path, Body
from typing import Dict, Any
import uuid

from app.services.game_logic import (
    create_board,
    apply_move,
    is_valid_move,
    check_win,
    check_draw,
    PLAYER_X,
    PLAYER_O,
    Board  # Import the Board type alias
)
from app.schemas.game import GameStateResponse, MoveRequest # We'll create these schemas next

router = APIRouter()

# In-memory store for game states for these temporary HTTP endpoints
# NOT SUITABLE FOR PRODUCTION - just for quick testing of game logic via HTTP
# { "game_id": {"board": Board, "current_player": str, "status": str, "winner": Optional[str]} }
http_games_db: Dict[str, Dict[str, Any]] = {}


@router.post("/create", response_model=GameStateResponse, status_code=201)
async def http_create_game():
    """
    Creates a new game instance (in-memory for HTTP testing).
    Initial player is X.
    """
    game_id = str(uuid.uuid4())
    board = create_board()
    http_games_db[game_id] = {
        "board": board,
        "current_player": PLAYER_X,
        "status": "active", # e.g., "active", "player_x_wins", "player_o_wins", "draw"
        "winner": None
    }
    return GameStateResponse(
        game_id=game_id,
        board=board,
        current_player=PLAYER_X,
        status="active",
        winner=None
    )

@router.get("/{game_id}", response_model=GameStateResponse)
async def http_get_game_state(game_id: str = Path(..., description="The ID of the game to retrieve")):
    """
    Gets the current state of a game (in-memory for HTTP testing).
    """
    game = http_games_db.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return GameStateResponse(
        game_id=game_id,
        board=game["board"],
        current_player=game["current_player"],
        status=game["status"],
        winner=game["winner"]
    )

@router.post("/{game_id}/move", response_model=GameStateResponse)
async def http_make_move(
    game_id: str = Path(..., description="The ID of the game"),
    move: MoveRequest = Body(...) # Pydantic model for request body
):
    """
    Makes a move in the game (in-memory for HTTP testing).
    `move` body should contain: `{"player": "X" or "O", "row": int, "side": "L" or "R"}`
    """
    game = http_games_db.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game["status"] != "active":
        raise HTTPException(status_code=400, detail=f"Game is not active. Status: {game['status']}")

    if game["current_player"] != move.player:
        raise HTTPException(status_code=400, detail=f"Not player {move.player}'s turn. It's {game['current_player']}'s turn.")

    board = game["board"]
    
    # Validate move using game_logic
    if not is_valid_move(board, move.row, move.side):
        raise HTTPException(status_code=400, detail=f"Invalid move: row {move.row}, side {move.side} is not available or invalid.")

    # Apply move using game_logic
    placed_coords = apply_move(board, move.row, move.side, move.player)
    if placed_coords is None: # Should be caught by is_valid_move, but as a safeguard
         raise HTTPException(status_code=400, detail="Move application failed unexpectedly after validation.")

    game["board"] = board # Update board in our mock DB

    # Check for win condition
    if check_win(board, move.player, placed_coords):
        game["status"] = f"player_{move.player.lower()}_wins"
        game["winner"] = move.player
        game["current_player"] = None # Game over
    # Check for draw condition (if no win)
    elif check_draw(board):
        game["status"] = "draw"
        game["winner"] = "draw" # Or None, depending on how you want to represent draw winner
        game["current_player"] = None # Game over
    else:
        # Switch player
        game["current_player"] = PLAYER_O if move.player == PLAYER_X else PLAYER_X
        
    return GameStateResponse(
        game_id=game_id,
        board=game["board"],
        current_player=game["current_player"],
        status=game["status"],
        winner=game["winner"]
    )