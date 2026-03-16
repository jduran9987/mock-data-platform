"""Database initialization — creates all tables from registered SQLModel models."""

from sqlmodel import SQLModel

from payments_vendor.db.session import engine


def init_db() -> None:
    """Create all tables defined by SQLModel metadata."""
    import payments_vendor.models.customer  # noqa: F401 — register models before create_all

    SQLModel.metadata.create_all(engine)
