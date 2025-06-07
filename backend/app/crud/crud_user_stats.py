# backend/app/crud/crud_user_stats.py
from sqlalchemy.orm import Session
from typing import Optional, Literal
import uuid

from app.db.models import UserGameStats, User
from app.crud.crud_user import get_user_by_id # To link stats back to user for some responses

from app.core.logging_config import setup_logger
logger = setup_logger(__name__)

# Define valid stat field names for type safety if desired, or just use string
StatFieldName = Literal["wins", "losses", "draws", "abandoned_by_user"]


def get_user_stats(db: Session, user_id: uuid.UUID) -> Optional[UserGameStats]:
    """
    Retrieves game statistics for a given user_id.
    """
    stats = db.get(UserGameStats, user_id)
    if not stats: # If stats record doesn't exist, create one for the user
        user = get_user_by_id(db, user_id=user_id)
        if user: # Only create stats if the user actually exists
            logger.info(f"No stats found for user {user_id}, creating new entry.")
            return create_user_stats_entry(db, user_id=user_id)
        else:
            logger.warning(f"Attempted to get/create stats for non-existent user_id: {user_id}")
            return None
    return stats

def create_user_stats_entry(db: Session, user_id: uuid.UUID) -> UserGameStats:
    """
    Creates a new, empty statistics entry for a user.
    Assumes user_id is valid and user exists.
    """
    db_stats = UserGameStats(user_id=user_id) # Defaults from model will apply (0 for all counts)
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)
    logger.info(f"Initial stats entry created for user_id: {user_id}")
    return db_stats

def increment_user_stat(
    db: Session,
    user_id: uuid.UUID,
    stat_to_increment: StatFieldName,
    increment_value: int = 1,
    increment_games_played: bool = True # Usually, a stat change means a game was played
) -> Optional[UserGameStats]:
    """
    Increments a specific statistic for a user, and optionally games_played.
    If stats record doesn't exist, it's created.
    """
    db_stats = get_user_stats(db, user_id=user_id) # This will create if not exists

    if not db_stats:
        logger.error(f"Failed to get or create stats for user_id {user_id}. Cannot increment stat.")
        return None

    if hasattr(db_stats, stat_to_increment):
        current_value = getattr(db_stats, stat_to_increment)
        setattr(db_stats, stat_to_increment, current_value + increment_value)
    else:
        logger.error(f"Invalid stat field '{stat_to_increment}' for UserGameStats.")
        return db_stats # Return current stats without change

    if increment_games_played:
        db_stats.games_played += 1 # Always increment games_played by 1 if specified

    db.commit()
    db.refresh(db_stats)
    logger.info(f"Stats updated for user {user_id}: {stat_to_increment} incremented, games_played: {db_stats.games_played}")
    return db_stats