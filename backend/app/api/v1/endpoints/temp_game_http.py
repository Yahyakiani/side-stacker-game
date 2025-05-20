from fastapi import APIRouter, HTTPException, Path, Body, Depends
from sqlalchemy.orm import Session
from typing import Any, Optional
import uuid

from app.services.game_logic import (
    apply_move,
    is_valid_move,
    check_win,
    check_draw,
    PLAYER_X,
    PLAYER_O,
    Board as GameLogicBoard,
    create_board as service_create_board,
)
from app.schemas.game import GameStateResponse, MoveRequest, BoardSchema
from app.db.session import get_db
from app.crud import crud_game

router = APIRouter()


@router.post("/create", response_model=GameStateResponse, status_code=201)
async def http_create_game(db: Session = Depends(get_db)):
    """
    Creates a new game instance in the database.
    Initial player is X. Player1_token will be a new UUID for now.
    """
    player1_temp_token = str(uuid.uuid4())

    db_game = crud_game.create_game_db(
        db=db,
        player1_token=player1_temp_token,
        initial_current_player_token=player1_temp_token,
        game_mode="PVP_HTTP_TEST",
    )

    board_to_respond_with: GameLogicBoard = db_game.board_state.get(
        "board", []
    )  # Default from model ensures "board" key

    return GameStateResponse(
        game_id=str(db_game.id),
        board=board_to_respond_with,
        current_player=db_game.current_player_token,
        status=db_game.status,
        winner=db_game.winner_token,
    )


@router.get("/{game_id_str}", response_model=GameStateResponse)
async def http_get_game_state(
    game_id_str: str = Path(
        ..., description="The ID of the game to retrieve (string UUID)"
    ),
    db: Session = Depends(get_db),
):
    """
    Gets the current state of a game from the database.
    """
    try:
        game_uuid = uuid.UUID(game_id_str)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid game ID format. Must be a UUID."
        )

    db_game = crud_game.get_game(db, game_id=game_uuid)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    board_to_respond_with: GameLogicBoard = db_game.board_state.get("board", [])

    return GameStateResponse(
        game_id=str(db_game.id),
        board=board_to_respond_with,
        current_player=db_game.current_player_token,
        status=db_game.status,
        winner=db_game.winner_token,
    )


@router.post("/{game_id_str}/move", response_model=GameStateResponse)
async def http_make_move(
    game_id_str: str = Path(..., description="The ID of the game (string UUID)"),
    move: MoveRequest = Body(...),
    db: Session = Depends(get_db),
):
    """
    Makes a move in the game stored in the database.
    """
    try:
        game_uuid = uuid.UUID(game_id_str)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid game ID format. Must be a UUID."
        )

    db_game = crud_game.get_game(db, game_id=game_uuid)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    if db_game.status not in [
        "active",
        "waiting_for_player2",
    ]:  # Allow first move if waiting
        raise HTTPException(
            status_code=400, detail=f"Game is not active. Status: {db_game.status}"
        )

    player_making_move_token: Optional[str] = None
    # This simple logic assumes the 'player' field in MoveRequest ('X' or 'O')
    # determines who the player_token is. This will be more robust with WebSockets.
    if (
        db_game.player1_token
        and db_game.current_player_token == db_game.player1_token
        and move.player == PLAYER_X
    ):
        player_making_move_token = db_game.player1_token
    elif (
        db_game.player2_token
        and db_game.current_player_token == db_game.player2_token
        and move.player == PLAYER_O
    ):
        player_making_move_token = db_game.player2_token
    # Handle case where it's P1's turn, P1 is X, and P2 hasn't joined yet.
    elif (
        db_game.player1_token
        and not db_game.player2_token
        and db_game.current_player_token == db_game.player1_token
        and move.player == PLAYER_X
    ):
        player_making_move_token = db_game.player1_token
    else:
        actual_current_player_piece = "Unknown"
        if db_game.current_player_token == db_game.player1_token:
            actual_current_player_piece = PLAYER_X
        elif db_game.current_player_token == db_game.player2_token:
            actual_current_player_piece = PLAYER_O

        detail_msg = f"It's not player {move.player}'s turn or player token mismatch. Current turn for token: {db_game.current_player_token} (expected piece: {actual_current_player_piece})."
        if not db_game.current_player_token:
            detail_msg = "Game is over or current player token is not set."
        raise HTTPException(status_code=400, detail=detail_msg)

    # Extract the list-based board from the JSONB structure
    # The default in the Game model ensures `board_state` has a `{"board": ...}` structure
    current_board_list: GameLogicBoard = db_game.board_state.get(
        "board", service_create_board()
    )

    if not is_valid_move(current_board_list, move.row, move.side):
        raise HTTPException(status_code=400, detail=f"Invalid move: row {move.row}, side {move.side} is not available or invalid.")

    placed_coords = apply_move(current_board_list, move.row, move.side, move.player)
    if placed_coords is None:
        raise HTTPException(
            status_code=400,
            detail="Move application failed unexpectedly after validation.",
        )

    new_board_state_json = {"board": current_board_list}

    next_player_token: Optional[str] = None
    new_status = db_game.status  # Start with current status
    new_winner_token = db_game.winner_token  # Start with current winner

    if check_win(current_board_list, move.player, placed_coords):
        new_status = f"player_{move.player.lower()}_wins"
        new_winner_token = player_making_move_token
    elif check_draw(current_board_list):
        new_status = "draw"
        new_winner_token = "draw"
    else:
        # Switch player token
        if player_making_move_token == db_game.player1_token:
            next_player_token = db_game.player2_token
            if (
                not next_player_token
            ):  # If P2 doesn't exist (PvE or P1 vs P1 test for HTTP)
                # For this HTTP test, let's assume P1 can keep playing if P2 isn't there.
                # This is a simplification.
                next_player_token = db_game.player1_token
        elif player_making_move_token == db_game.player2_token:
            next_player_token = db_game.player1_token
        else:
            # This case should ideally not be hit if the turn logic at the start is correct.
            # If it is, it means player_making_move_token didn't match current_player_token properly.
            # The exception at the start of the function should catch turn mismatches.
            # For safety, we can raise an error or default to current player if something unexpected happens.
            next_player_token = (
                db_game.current_player_token
            )  # Fallback, though ideally an error.
            # raise HTTPException(status_code=500, detail="Internal error determining next player after move.")

        new_status = "active"  # Game continues if not won or drawn

    updated_db_game = crud_game.update_game_state(
        db=db,
        game_id=game_uuid,
        board_state=new_board_state_json,
        current_player_token=next_player_token if new_status == "active" else None,
        status=new_status,
        winner_token=new_winner_token,
    )

    if not updated_db_game:
        raise HTTPException(status_code=500, detail="Failed to update game state.")

    final_board_to_respond_with: GameLogicBoard = updated_db_game.board_state.get(
        "board", []
    )

    return GameStateResponse(
        game_id=str(updated_db_game.id),
        board=final_board_to_respond_with,
        current_player=updated_db_game.current_player_token,
        status=updated_db_game.status,
        winner=updated_db_game.winner_token,
    )
