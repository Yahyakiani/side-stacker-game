from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Type alias from game_logic for consistency, though Pydantic will validate structure
BoardSchema = List[List[Optional[Literal['X', 'O']]]]


class MoveRequest(BaseModel):
    player: Literal['X', 'O'] = Field(..., description="The player making the move ('X' or 'O')")
    row: int = Field(..., ge=0, lt=7, description="The row to play on (0-6)") # Assuming 7 rows
    side: Literal['L', 'R'] = Field(..., description="The side to play from ('L' for Left, 'R' for Right)")


class GameStateResponse(BaseModel):
    game_id: str
    board: BoardSchema # Use the imported Board type
    current_player: Optional[Literal['X', 'O']] = Field(description="Whose turn it is, null if game over")
    status: str = Field(description="Current status of the game (e.g., active, player_x_wins, draw)")
    winner: Optional[Literal['X', 'O', 'draw']] = Field(description="Winner of the game, if any, or 'draw'")

    class Config:
        from_attributes = True # For SQLAlchemy models later, not strictly needed here but good practice