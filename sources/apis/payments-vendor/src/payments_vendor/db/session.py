"""Database engine and session management."""

import os
from collections.abc import Iterator

from sqlmodel import Session, create_engine

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql://payments:payments@localhost:5432/payments_vendor",
)

engine = create_engine(DATABASE_URL, echo=False)


def get_session() -> Iterator[Session]:
    """Yield a SQLModel session and close it when done."""
    with Session(engine) as session:
        yield session
