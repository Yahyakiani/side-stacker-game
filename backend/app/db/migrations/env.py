# backend/app/db/migrations/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sends Soutput to the logger.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.db.models import User, Game, UserGameStats # Explicitly import all models


import os
import sys

# Get the directory of the current file (env.py)
# then go up two levels (migrations -> db -> app) to reach the 'app' directory.
# This ensures that 'app' is in sys.path when alembic runs, allowing imports like 'from app.db.models import ...'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.db.base_class import Base  # Import your SQLAlchemy Base
                                                   # to ensure they are registered with Base.metadata

# This is the crucial line. Alembic uses this to know what your models *should* look like.
target_metadata = Base.metadata
# <<< --- END MODEL IMPORTS --- >>>

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here too.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata, # Ensure target_metadata is passed here
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True, # Recommended for more accurate type comparison
        render_as_batch=True # Often needed for SQLite, good practice
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )
    
    # --- Use your actual database URL from settings for online mode ---
    from app.core.config import settings # Import your app's settings
    
    # Construct the connectable engine manually
    # This ensures it uses the same URL your application does
    from sqlalchemy import create_engine
    connectable = create_engine(str(settings.DATABASE_URL)) # Ensure it's a string

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata, # Ensure target_metadata is passed here
            compare_type=True, # Recommended
            render_as_batch=True # Often needed for SQLite, good practice
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()