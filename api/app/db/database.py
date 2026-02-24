# api/app/db/database.py
from __future__ import annotations

import logging

import aiosqlite

from api.app.settings import settings

logger = logging.getLogger(__name__)

_CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id           TEXT,
    request_id           TEXT NOT NULL UNIQUE,
    created_at           TEXT NOT NULL,
    endpoint             TEXT NOT NULL,
    -- /agent fields
    message              TEXT,
    intent               TEXT,
    anomaly_detected     INTEGER,
    -- /agent/analyze fields
    filename             TEXT,
    doc_type             TEXT,
    doc_type_confidence  REAL,
    recommendation       TEXT,
    -- shared
    summary              TEXT,
    warnings             TEXT
);
"""

_CREATE_IDX_SESSION = """
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
"""

_CREATE_IDX_CREATED = """
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
"""


async def init_db() -> None:
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(_CREATE_SESSIONS)
        await db.execute(_CREATE_IDX_SESSION)
        await db.execute(_CREATE_IDX_CREATED)
        await db.commit()
    logger.info("db_init path=%s ok=true", settings.db_path)
