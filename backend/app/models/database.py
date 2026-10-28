"""Backward-compatible database exports.

The canonical database setup lives in app.core.database.
"""

from app.core.database import Base, SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
