from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Define naming conventions for database constraints (optional but good practice for Alembic)
# This helps Alembic auto-generate migration scripts with consistent naming.
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    metadata = metadata_obj
    # You can define a default __tablename__ generation here if you like,
    # or define it explicitly in each model.
    # For example:
    # @declared_attr
    # def __tablename__(cls) -> str:
    #     return cls.__name__.lower() + "s" # e.g. Game -> games
