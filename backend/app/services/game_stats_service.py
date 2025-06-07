# backend/app/services/game_stats_service.py
from sqlalchemy.orm import Session
import uuid
from typing import Optional # Added Optional

from app.crud import crud_user_stats # We'll call CRUD functions from here
from app.core import constants
# We don't need db.models here directly if crud_user_stats handles the DB interaction

from app.core.logging_config import setup_logger
logger = setup_logger(__name__)

def update_player_stats_on_game_end( # Renamed by removing leading underscore
    db: Session,
    player1_user_id: uuid.UUID | None,
    player2_user_id: uuid.UUID | None,
    winner_token: str | None, # Game.winner_token (can be player's token or 'draw')
    player1_token: str | None, # Game.player1_token
    player2_token: str | None, # Game.player2_token
    is_draw: bool,
    abandoned_by_user_id: uuid.UUID | None = None
):
    """Updates stats for players involved in a completed or abandoned game."""
    logger.info(f"Updating stats: P1_User({player1_user_id}), P2_User({player2_user_id}), WinnerToken({winner_token}), IsDraw({is_draw}), AbandonedBy({abandoned_by_user_id})")
    if is_draw:
        if player1_user_id:
            crud_user_stats.increment_user_stat(db, player1_user_id, constants.STAT_DRAWS)
        if player2_user_id:
            crud_user_stats.increment_user_stat(db, player2_user_id, constants.STAT_DRAWS)
        logger.info(f"Stats updated for draw: P1_User: {player1_user_id}, P2_User: {player2_user_id}")
        return

    winner_user_id_for_stats: uuid.UUID | None = None
    loser_user_id_for_stats: uuid.UUID | None = None

    if winner_token == player1_token: # P1 won
        winner_user_id_for_stats = player1_user_id
        loser_user_id_for_stats = player2_user_id
    elif winner_token == player2_token: # P2 won
        winner_user_id_for_stats = player2_user_id
        loser_user_id_for_stats = player1_user_id
    
    if abandoned_by_user_id:
        crud_user_stats.increment_user_stat(db, abandoned_by_user_id, constants.STAT_ABANDONED, increment_games_played=True)
        crud_user_stats.increment_user_stat(db, abandoned_by_user_id, constants.STAT_LOSSES, increment_games_played=False)
        
        if winner_user_id_for_stats and winner_user_id_for_stats != abandoned_by_user_id:
            crud_user_stats.increment_user_stat(db, winner_user_id_for_stats, constants.STAT_WINS, increment_games_played=True)
        logger.info(f"Stats updated for abandonment: Abandoned by User: {abandoned_by_user_id}, Winner User: {winner_user_id_for_stats}")
    elif winner_user_id_for_stats: # Normal win/loss
        crud_user_stats.increment_user_stat(db, winner_user_id_for_stats, constants.STAT_WINS)
        if loser_user_id_for_stats:
            crud_user_stats.increment_user_stat(db, loser_user_id_for_stats, constants.STAT_LOSSES)
        logger.info(f"Stats updated for win/loss: Winner User: {winner_user_id_for_stats}, Loser User: {loser_user_id_for_stats}")