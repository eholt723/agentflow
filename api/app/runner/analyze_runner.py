# runner/analyze_runner.py
from __future__ import annotations

import logging
import time
from typing import Any, Dict

from api.app.parsers.document_parser import parse_document
from api.app.clients.inference_client import run_vision_inference
from api.app.graph.analyze_graph import run_analyze_graph
from api.app.schemas.agent import ToolAction

logger = logging.getLogger(__name__)

_TRANSCRIBE_PROMPT = (
    "Transcribe all text visible in this image exactly as written. "
    "Preserve the original structure, formatting, and line breaks. "
    "If the handwriting is unclear, write [unclear] in place of the word. "
    "Do not summarize or interpret — transcribe only."
)


async def run_analyze(
    filename: str,
    content: bytes,
    request_id: str,
    context: str = "",
) -> Dict[str, Any]:
    """
    Parse an uploaded file and run it through the analyze graph.
    For image uploads (JPG, PNG, WEBP), uses Groq vision to transcribe
    before passing to the graph. Returns a dict mapping onto AnalyzeResponse.
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

    # Image path: transcribe via vision LLM before passing to the graph
    vision_action: list = []
    if parsed.image_bytes:
        t0 = time.perf_counter()
        try:
            transcribed = await run_vision_inference(
                prompt=_TRANSCRIBE_PROMPT,
                image_bytes=parsed.image_bytes,
                media_type=parsed.image_media_type or "image/jpeg",
            )
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            parsed.text = transcribed
            logger.info(
                "vision_transcribe filename=%s chars=%d ms=%d ok=true",
                filename, len(transcribed), elapsed_ms,
            )
            vision_action = [
                ToolAction(kind="llm", name="vision_transcribe", ok=True, ms=elapsed_ms,
                           details={"chars": len(transcribed), "media_type": parsed.image_media_type})
            ]
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            logger.error("vision_transcribe failed=%s ms=%d", exc, elapsed_ms)
            return {
                "request_id": request_id,
                "filename": filename,
                "doc_type": "unknown",
                "doc_type_confidence": 0.0,
                "key_fields": {},
                "analysis": {},
                "summary": "",
                "actions_taken": [
                    ToolAction(kind="llm", name="vision_transcribe", ok=False, ms=elapsed_ms,
                               details={"error": str(exc)})
                ],
                "warnings": [f"Image transcription failed: {exc}"],
            }

    result = await run_analyze_graph(
        filename=parsed.filename,
        extension=parsed.extension,
        text=parsed.truncated_text,
        rows=parsed.rows,
        row_count=parsed.row_count,
        request_id=request_id,
        context=context,
    )

    # Prepend the vision transcription action so the caller can see it happened
    if vision_action:
        result["actions_taken"] = vision_action + result.get("actions_taken", [])

    return result
