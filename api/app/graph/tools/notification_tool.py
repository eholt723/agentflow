# api/app/graph/tools/notification_tool.py
from __future__ import annotations

import logging

import httpx

from api.app.settings import settings

logger = logging.getLogger(__name__)


async def send_notification(payload: dict) -> bool:
    """
    POST payload to the configured n8n webhook URL.

    Returns True on success, False on any error. Never raises — a dead
    webhook must not crash the analysis pipeline.

    Disabled (no-op) when N8N_ENABLED=false or N8N_WEBHOOK_URL is unset.
    """
    if not settings.n8n_enabled or not settings.n8n_webhook_url:
        return False

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(settings.n8n_webhook_url, json=payload)
            resp.raise_for_status()
            logger.info("notification sent status=%d url=%s", resp.status_code, settings.n8n_webhook_url)
            return True
    except Exception as exc:
        logger.warning("notification failed exc=%s url=%s", exc, settings.n8n_webhook_url)
        return False
