# backend/app/schemas/user.py
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$",
                          description="Unique username for the player (3-50 chars, alphanumeric, _, -)")

class UserCreate(UserBase):
    # For now, creating a user only requires a username.
    pass

class UserSchema(UserBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True # Replaces orm_mode = True


# --- UserGameStats Schemas ---
class UserGameStatsBase(BaseModel):
    games_played: int = Field(default=0, ge=0)
    wins: int = Field(default=0, ge=0)
    losses: int = Field(default=0, ge=0)
    draws: int = Field(default=0, ge=0)
    abandoned_by_user: int = Field(default=0, ge=0)

class UserGameStatsSchema(UserGameStatsBase):
    user_id: uuid.UUID
    username: str # Denormalized from User model for convenience in response
    updated_at: datetime

    class Config:
        from_attributes = True


# Optional: Schema for updating stats (might not be directly used by API but good for internal consistency)
class UserGameStatsUpdate(BaseModel):
    games_played: Optional[int] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    draws: Optional[int] = None
    abandoned_by_user: Optional[int] = None