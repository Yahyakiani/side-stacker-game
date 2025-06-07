# backend/app/api/v1/endpoints/user_stats.py
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
import uuid # Not strictly needed here unless casting, but good practice

from app.db.session import get_db
from app.crud import crud_user, crud_user_stats
from app.schemas.user import UserGameStatsSchema # Response model
from app.db.models import User # For type hinting if needed

from app.core.logging_config import setup_logger
logger = setup_logger(__name__)

router = APIRouter()

@router.get(
    "/users/{username}/stats",
    response_model=UserGameStatsSchema,
    tags=["User Statistics"],
    summary="Get game statistics for a user"
)
async def get_user_game_stats(
    username: str = Path(..., description="The username of the player", min_length=1, max_length=50),
    db: Session = Depends(get_db)
):
    """
    Retrieves the aggregated game statistics (wins, losses, draws, etc.)
    for a given username.
    If the user exists but has no stats record yet, a default (all zeros)
    stats record will be returned.
    """
    logger.info(f"Attempting to fetch stats for username: {username}")
    db_user = crud_user.get_user_by_username(db, username=username)

    if not db_user:
        logger.warning(f"User not found: {username}")
        raise HTTPException(status_code=404, detail=f"User '{username}' not found.")

    # crud_user_stats.get_user_stats will create a default stats entry if one doesn't exist
    db_user_stats = crud_user_stats.get_user_stats(db, user_id=db_user.id)

    if not db_user_stats:
        # This case should ideally be handled by get_user_stats creating an entry.
        # If it still returns None, it means the user was found but creating stats failed,
        # or the user was deleted between get_user and get_user_stats (unlikely with one session).
        logger.error(f"Could not retrieve or create stats for user_id: {db_user.id} (username: {username})")
        raise HTTPException(status_code=500, detail="Failed to retrieve or initialize user statistics.")

    # Populate the UserGameStatsSchema, including the username
    return UserGameStatsSchema(
        user_id=db_user_stats.user_id,
        username=db_user.username, # Denormalize username into the response
        games_played=db_user_stats.games_played,
        wins=db_user_stats.wins,
        losses=db_user_stats.losses,
        draws=db_user_stats.draws,
        abandoned_by_user=db_user_stats.abandoned_by_user,
        updated_at=db_user_stats.updated_at
    )