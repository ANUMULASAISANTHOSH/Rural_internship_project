"""
AQUILA - Database Configuration & Session Management
Reliable SQLite engine configuration with foreign key enforcement and timeout safeguards.
"""

import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Configurable database path via environment variable
_db_env_path = os.environ.get("AQUILA_DB_PATH", "aquila_mvp.db")
if not os.path.isabs(_db_env_path):
    DB_PATH = os.path.join(BASE_DIR, _db_env_path)
else:
    DB_PATH = _db_env_path

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")


def utc_now() -> datetime:
    """Returns timezone-naive UTC timestamp for standard SQLite persistence."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# SQLite Engine with multi-threaded support
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# Enforce SQLite foreign keys and set busy timeout on every connection
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Enables SQLite foreign key constraints (disabled by default in SQLite)
    and configures a 5000ms busy timeout to prevent concurrent lock errors.
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.close()
    except Exception:
        pass


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency injection generator yielding an isolated session with safe closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
