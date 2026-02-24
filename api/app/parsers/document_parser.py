# api/app/parsers/document_parser.py
from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {"pdf", "docx", "txt", "csv", "xlsx", "xls"}
MAX_TEXT_CHARS = 12_000  # truncation ceiling before LLM calls


@dataclass
class ParsedDocument:
    filename: str
    extension: str
    text: Optional[str] = None
    rows: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    parse_error: Optional[str] = None

    @property
    def truncated_text(self) -> str:
        """Text trimmed to MAX_TEXT_CHARS for LLM calls."""
        if not self.text:
            return ""
        if len(self.text) > MAX_TEXT_CHARS:
            return self.text[:MAX_TEXT_CHARS] + "\n[... truncated ...]"
        return self.text


def parse_document(filename: str, content: bytes) -> ParsedDocument:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        return _parse_pdf(filename, ext, content)
    elif ext == "docx":
        return _parse_docx(filename, ext, content)
    elif ext == "txt":
        return _parse_txt(filename, ext, content)
    elif ext in {"csv", "xlsx", "xls"}:
        return _parse_tabular(filename, ext, content)
    else:
        return ParsedDocument(
            filename=filename, extension=ext,
            parse_error=f"Unsupported file type: .{ext}",
        )


def _parse_pdf(filename: str, ext: str, content: bytes) -> ParsedDocument:
    import pdfplumber
    try:
        text_parts: List[str] = []
        page_count = 0
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        text = "\n".join(text_parts)
        logger.info("pdf_parse filename=%s pages=%d chars=%d", filename, page_count, len(text))
        return ParsedDocument(filename=filename, extension=ext, text=text)
    except Exception as e:
        logger.error("pdf_parse_failed filename=%s error=%s", filename, e)
        return ParsedDocument(filename=filename, extension=ext, parse_error=str(e))


def _parse_docx(filename: str, ext: str, content: bytes) -> ParsedDocument:
    from docx import Document
    try:
        doc = Document(io.BytesIO(content))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        logger.info("docx_parse filename=%s chars=%d", filename, len(text))
        return ParsedDocument(filename=filename, extension=ext, text=text)
    except Exception as e:
        logger.error("docx_parse_failed filename=%s error=%s", filename, e)
        return ParsedDocument(filename=filename, extension=ext, parse_error=str(e))


def _parse_txt(filename: str, ext: str, content: bytes) -> ParsedDocument:
    try:
        text = content.decode("utf-8", errors="replace")
        logger.info("txt_parse filename=%s chars=%d", filename, len(text))
        return ParsedDocument(filename=filename, extension=ext, text=text)
    except Exception as e:
        return ParsedDocument(filename=filename, extension=ext, parse_error=str(e))


def _parse_tabular(filename: str, ext: str, content: bytes) -> ParsedDocument:
    import pandas as pd
    try:
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        rows = df.fillna("").to_dict(orient="records")
        text = df.to_string(index=False)
        logger.info(
            "tabular_parse filename=%s rows=%d cols=%d", filename, len(rows), len(df.columns)
        )
        return ParsedDocument(
            filename=filename, extension=ext,
            text=text, rows=rows, row_count=len(rows),
        )
    except Exception as e:
        logger.error("tabular_parse_failed filename=%s error=%s", filename, e)
        return ParsedDocument(filename=filename, extension=ext, parse_error=str(e))
