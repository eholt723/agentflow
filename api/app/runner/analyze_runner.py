# runner/analyze_runner.py
from __future__ import annotations

import logging
from typing import Any, Dict

from api.app.parsers.document_parser import parse_document
from api.app.graph.analyze_graph import run_analyze_graph

logger = logging.getLogger(__name__)


async def run_analyze(
    filename: str,
    content: bytes,
    request_id: str,
    context: str = "",
) -> Dict[str, Any]:
    """
    Parse an uploaded file and run it through the analyze graph.
    Returns a dict that maps directly onto AnalyzeResponse.
    """
    parsed = parse_document(filename, content)

    if parsed.parse_error:
        logger.error("analyze_runner parse_failed filename=%s error=%s", filename, parsed.parse_error)
        return {
            "request_id": request_id,
            "filename": filename,
            "doc_type": "unknown",
            "doc_type_confidence": 0.0,
            "key_fields": {},
            "analysis": {},
            "summary": "",
            "actions_taken": [],
            "warnings": [f"File could not be parsed: {parsed.parse_error}"],
        }

    return await run_analyze_graph(
        filename=parsed.filename,
        extension=parsed.extension,
        text=parsed.truncated_text,
        rows=parsed.rows,
        row_count=parsed.row_count,
        request_id=request_id,
        context=context,
    )
