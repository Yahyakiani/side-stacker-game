# backend/app/schemas/game.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union  # Added Union

# Corrected BoardSchema
BoardSchema = List[List[Optional[Literal['X', 'O']]]]


class MoveRequest(BaseModel):
    player: Literal['X', 'O'] = Field(..., description="The player making the move ('X' or 'O')")
    row: int = Field(..., ge=0, lt=7, description="The row to play on (0-6)")
    side: Literal['L', 'R'] = Field(..., description="The side to play from ('L' for Left, 'R' for Right)")


class GameStateResponse(BaseModel):
    game_id: str
    board: BoardSchema
    current_player: Optional[Union[Literal["X", "O"], str]] = Field(
        description="Whose turn it is (player token or X/O piece), null if game over"
    )
    status: str = Field(description="Current status of the game (e.g., active, player_x_wins, draw)")
    winner: Optional[Union[Literal["X", "O", "draw"], str]] = Field(
        description="Winner of the game (player token or X/O piece, or 'draw'), if any"
    )

    class Config:
        from_attributes = True
