from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings  # Your application settings

# Create a SQLAlchemy engine instance.
# The engine is the starting point for any SQLAlchemy application.
# It's a “home base” for the actual database and its DBAPI.
# connect_args is used for SQLite, for PostgreSQL it's usually not needed for this.
# We might add pool_pre_ping=True for production later.
engine = create_engine(
    str(settings.DATABASE_URL),  # Ensure DATABASE_URL from settings is a string
    # pool_pre_ping=True # Good for production to check connections before use
)

# Create a SessionLocal class.
# Each instance of SessionLocal will be a database session.
# The class itself is not a database session yet.
# autocommit=False and autoflush=False are common defaults.
#   autocommit=False: Transactions are not committed automatically. You must call session.commit().
#   autoflush=False: Changes are not automatically flushed to the DB before queries,
#                    you might need session.flush() in specific cases or rely on commit.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get a DB session
# This is a generator function that will be used as a FastAPI dependency.
# It yields a database session and ensures it's closed after the request is handled.
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db  # Provide the session to the path operation function
    finally:
        db.close()  # Ensure the session is closed after use


# You could also define an async version if using async SQLAlchemy features,
# but for standard sync SQLAlchemy, this is typical.
# Example for async (requires asyncpg driver and async engine):
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# async_engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=True)
# AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
# async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
#     async with AsyncSessionLocal() as session:
#         yield session
