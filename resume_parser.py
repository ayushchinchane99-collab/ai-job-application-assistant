"""
resume_parser.py
-----------------
Extracts clean text from an uploaded resume (PDF or plain text) so the
rest of the pipeline (matching, gap analysis, cover letters) has a
single normalized string to work with.
"""

from io import BytesIO
from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract raw text from a PDF given as bytes (e.g. from a Streamlit upload)."""
    reader = PdfReader(BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n".join(pages).strip()


def clean_resume_text(raw_text: str) -> str:
    """Light cleanup: collapse excess whitespace/blank lines."""
    lines = [line.strip() for line in raw_text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def parse_resume(file_bytes: bytes, filename: str) -> str:
    """
    Entry point used by the app. Supports .pdf and .txt uploads.
    Returns cleaned resume text.
    """
    if filename.lower().endswith(".pdf"):
        raw = extract_text_from_pdf(file_bytes)
    else:
        raw = file_bytes.decode("utf-8", errors="ignore")
    return clean_resume_text(raw)
