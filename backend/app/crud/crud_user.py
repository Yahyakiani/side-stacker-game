# backend/app/crud/crud_user.py
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.db.models import User
# from app.schemas.user import UserCreate # We'll create schemas in the next step

from app.core.logging_config import setup_logger
logger = setup_logger(__name__)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Retrieves a user by their username.
    """
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """
    Retrieves a user by their ID.
    """
    return db.get(User, user_id) # Efficient for PK lookup

def create_user(db: Session, username: str) -> User:
    """
    Creates a new user.
    For now, username is the only input. Schemas will handle more complex creation later.
    """
    db_user = User(username=username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created: {username} (ID: {db_user.id})")
    return db_user

def get_or_create_user(db: Session, username: str) -> User:
    """
    Retrieves a user by username, or creates them if they don't exist.
    """
    db_user = get_user_by_username(db, username=username)
    if db_user:
        logger.debug(f"User found: {username}")
        return db_user
    logger.info(f"User not found, creating: {username}")
    return create_user(db, username=username)