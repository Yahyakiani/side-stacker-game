from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- BEGIN Standard Alembic Imports & Path Setup ---
import os
import sys

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add the project's root 'app' directory to the Python path
# This allows Alembic to find 'app.db.models', 'app.core.config', etc.
# The path needs to go up two levels from migrations/env.py to reach the backend/app directory effectively
# Assumes env.py is in app/db/migrations
sys.path.insert(
    0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
)
# --- END Standard Alembic Imports & Path Setup ---


# --- BEGIN Application Specific Imports for Alembic ---
# Import your Base model from your application's SQLAlchemy setup
from app.db.base_class import Base

# Import your application's models so Alembic can see them
from app.db import models  # This imports backend/app/db/models.py

# Import your application's settings to get the database URL
from app.core.config import settings

# --- END Application Specific Imports for Alembic ---


# --- BEGIN Alembic Configuration ---
# Set the target_metadata for Alembic's 'autogenerate' support
# This tells Alembic what your SQLAlchemy models define the schema to be
target_metadata = Base.metadata

# Set the sqlalchemy.url in the Alembic configuration context
# This ensures Alembic uses the same database URL as your application,
# overriding any URL that might be in alembic.ini.
if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
else:
    # Fallback or error if DATABASE_URL is not set, though it should be from .env
    # For offline mode, Alembic might still use a URL from alembic.ini if not set here.
    pass
# --- END Alembic Configuration ---


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # The URL should now be correctly set in the 'config' object
    # by the logic above (config.set_main_option)
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # For SQLite, render_as_batch=True is often needed. For PostgreSQL, it's optional.
        # render_as_batch=True,
        # compare_type=True # Can help detect type changes more accurately
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # The config.get_section method will use the sqlalchemy.url set dynamically above
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # render_as_batch=True, # Optional
            # compare_type=True    # Optional
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
