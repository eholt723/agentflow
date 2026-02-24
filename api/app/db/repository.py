# api/app/db/repository.py
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiosqlite

from api.app.settings import settings

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def save_analyze_session(
    *,
    session_id: Optional[str],
    request_id: str,
    filename: str,
    doc_type: str,
    doc_type_confidence: float,
    recommendation: Optional[str],
    summary: str,
    warnings: List[str],
) -> None:
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO sessions
                (session_id, request_id, created_at, endpoint,
                 filename, doc_type, doc_type_confidence, recommendation,
                 summary, warnings)
            VALUES (?, ?, ?, 'analyze', ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id, request_id, _now_iso(),
                filename, doc_type, doc_type_confidence, recommendation,
                summary, json.dumps(warnings),
            ),
        )
        await db.commit()
    logger.info("session_saved endpoint=analyze request_id=%s", request_id)


async def save_agent_session(
    *,
    session_id: Optional[str],
    request_id: str,
    message: str,
    intent: Optional[str],
    anomaly_detected: bool,
    summary: str,
    warnings: List[str],
) -> None:
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO sessions
                (session_id, request_id, created_at, endpoint,
                 message, intent, anomaly_detected,
                 summary, warnings)
            VALUES (?, ?, ?, 'agent', ?, ?, ?, ?, ?)
            """,
            (
                session_id, request_id, _now_iso(),
                message, intent, int(anomaly_detected),
                summary, json.dumps(warnings),
            ),
        )
        await db.commit()
    logger.info("session_saved endpoint=agent request_id=%s", request_id)


def _row_to_dict(row: aiosqlite.Row, description: Any) -> Dict[str, Any]:
    return {description[i][0]: row[i] for i in range(len(description))}


async def list_sessions(limit: int = 20) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["warnings"] = json.loads(d["warnings"] or "[]")
        result.append(d)
    return result


async def get_sessions_by_id(session_id: str) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM sessions WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ) as cursor:
            rows = await cursor.fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["warnings"] = json.loads(d["warnings"] or "[]")
        result.append(d)
    return result
