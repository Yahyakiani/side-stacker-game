# File: models.py
# backend/app/db/models.py
from datetime import datetime
import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    func,
    JSON,
    ForeignKey, # Added ForeignKey
    Integer # Added Integer
)  # For JSONB, use dialect-specific import later if needed
from sqlalchemy.dialects.postgresql import UUID, JSONB  # PostgreSQL specific JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, Dict, Any

from .base_class import Base  # Import Base from our base_class.py


# NEW User Model
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship to UserGameStats (one-to-one)
    stats: Mapped["UserGameStats"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Relationships to Game model (one-to-many for each player role)
    games_as_player1: Mapped[List["Game"]] = relationship(foreign_keys="[Game.player1_user_id]", back_populates="player1_user_obj")
    games_as_player2: Mapped[List["Game"]] = relationship(foreign_keys="[Game.player2_user_id]", back_populates="player2_user_obj")


    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

# NEW UserGameStats Model
class UserGameStats(Base):
    __tablename__ = "user_game_stats"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    games_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    draws: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    abandoned_by_user: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # Games this user quit
    # abandoned_games_won: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # Games won because opponent quit
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship to User (many-to-one, but effectively one-to-one from User's perspective)
    user: Mapped["User"] = relationship(back_populates="stats")

    def __repr__(self):
        return f"<UserGameStats(user_id={self.user_id}, wins={self.wins}, losses={self.losses})>"


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

    # MODIFIED: Add ForeignKey columns for user IDs
    player1_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    player2_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # MODIFIED: Add relationships to User model
    player1_user_obj: Mapped[Optional["User"]] = relationship(foreign_keys=[player1_user_id], back_populates="games_as_player1")
    player2_user_obj: Mapped[Optional["User"]] = relationship(foreign_keys=[player2_user_id], back_populates="games_as_player2")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Game(id={self.id}, status='{self.status}', mode='{self.game_mode}')>"
