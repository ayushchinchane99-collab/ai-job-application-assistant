"""
job_parser.py
-------------
Turns a job posting - either a URL or pasted text - into clean text
suitable for matching and analysis. Falls back gracefully if a page
can't be fetched (many company career sites block scrapers), in which
case the user is expected to paste the text manually.
"""

import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def fetch_job_posting(url: str, timeout: int = 10) -> str:
    """
    Fetch a job posting page and strip it down to visible text.
    Raises a RuntimeError with a friendly message on failure so the UI
    can prompt the user to paste the text instead.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not fetch this URL directly ({exc}). "
            "Paste the job description text instead."
        ) from exc

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "svg", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    return clean_job_text(text)


def clean_job_text(raw_text: str) -> str:
    lines = [line.strip() for line in raw_text.splitlines()]
    lines = [line for line in lines if line]
    text = "\n".join(lines)
    # collapse runs of blank-ish whitespace left over from stripped tags
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_job(url_or_none: str | None, pasted_text: str | None) -> str:
    """
    Entry point used by the app. Prefers a URL fetch; falls back to
    pasted text if no URL is given or the fetch fails.
    """
    if url_or_none:
        try:
            return fetch_job_posting(url_or_none)
        except RuntimeError:
            if pasted_text:
                return clean_job_text(pasted_text)
            raise
    if pasted_text:
        return clean_job_text(pasted_text)
    raise ValueError("Provide either a job posting URL or pasted text.")
