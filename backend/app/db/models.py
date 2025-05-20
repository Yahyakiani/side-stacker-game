from datetime import datetime
import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    func,
    JSON,
)  # For JSONB, use dialect-specific import later if needed
from sqlalchemy.dialects.postgresql import UUID, JSONB  # PostgreSQL specific JSONB
from sqlalchemy.orm import Mapped, mapped_column
from typing import List, Optional, Dict, Any

from .base_class import Base  # Import Base from our base_class.py


class Game(Base):
    __tablename__ = "games"  # Explicitly define table name

    # Mapped column syntax (SQLAlchemy 2.0 style)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # For anonymous players, these tokens identify them for a game session
    # Could be session IDs or simple UUIDs generated on connection/game creation
    player1_token: Mapped[Optional[str]] = mapped_column(
        String, index=True, nullable=True
    )  # Nullable if AI is P1
    player2_token: Mapped[Optional[str]] = mapped_column(
        String, index=True, nullable=True
    )  # Nullable if AI is P2 or waiting

    current_player_token: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Whose turn it is

    # Store board state as JSON. PostgreSQL JSONB is efficient.
    # The structure will be List[List[Optional[str]]]
    board_state: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, default=lambda: {"board": [([None] * 7) for _ in range(7)]}
    )

    # Game status: 'waiting_for_player2', 'active', 'player_x_wins', 'player_o_wins', 'draw', 'ava_active'
    # 'player_x_wins' assumes X is identified by player1_token or player2_token.
    # A more robust way might be to store winner_token and derive status.
    status: Mapped[str] = mapped_column(String, default="active", index=True)

    # Game mode: 'PVP', 'PVE_EASY', 'PVE_MEDIUM', 'PVE_HARD', 'AVA_...'
    game_mode: Mapped[str] = mapped_column(String, default="PVP")

    winner_token: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Stores the token of the winning player

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Game(id={self.id}, status='{self.status}', mode='{self.game_mode}')>"
