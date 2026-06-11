"""
Database schema initialisation.
Creates all tables and seeds essential reference data.
"""

import logging
from sqlalchemy.exc import OperationalError

from src.database.db import engine, Base

logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Create all tables defined in the ORM models.
    Safe to call on every startup — uses CREATE TABLE IF NOT EXISTS semantics.
    """
    try:
        # Import all models so SQLAlchemy registers them with Base.metadata
        from src.database import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialised successfully.")
    except OperationalError as exc:
        logger.error(
            f"Failed to initialise database tables: {exc}. "
            "Check your DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, and DB_NAME settings."
        )
        raise


def drop_all_tables() -> None:
    """
    Drop ALL tables — use only in tests / dev resets.
    NEVER call in production.
    """
    from src.database import models  # noqa: F401
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped.")
