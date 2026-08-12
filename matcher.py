"""
matcher.py
----------
Two layers of matching between a resume and a job posting:

1. A fast, free, local TF-IDF cosine-similarity score - useful for
   ranking many job postings against one resume without burning API
   calls on every single one.
2. A deeper LLM-based analysis (via the Anthropic API) that returns
   structured JSON: matched skills, missing skills, and a short
   explanation. This is what actually informs the cover letter.
"""

import json
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def tfidf_match_score(resume_text: str, job_text: str) -> float:
    """Return a 0-100 similarity score between resume and job text."""
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf = vectorizer.fit_transform([resume_text, job_text])
    except ValueError:
        # happens if one of the texts is empty / has no meaningful tokens
        return 0.0
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return round(float(score) * 100, 1)


@dataclass
class GapAnalysis:
    match_score: int = 0
    matched_skills: list = field(default_factory=list)
    missing_skills: list = field(default_factory=list)
    summary: str = ""


GAP_ANALYSIS_PROMPT = """You are an expert technical recruiter. Compare the RESUME
against the JOB POSTING and respond with ONLY a JSON object (no markdown fences,
no preamble) matching exactly this schema:

{{
  "match_score": <integer 0-100, your honest estimate of overall fit>,
  "matched_skills": [<short strings, skills/requirements the resume already covers>],
  "missing_skills": [<short strings, requirements the resume does NOT show evidence of>],
  "summary": "<2-3 sentence honest summary of fit, including the single biggest gap>"
}}

RESUME:
{resume_text}

JOB POSTING:
{job_text}
"""


def llm_gap_analysis(resume_text: str, job_text: str, client, model: str) -> GapAnalysis:
    """
    Calls the Anthropic API to produce a structured skill-gap analysis.
    `client` is an anthropic.Anthropic() instance.
    """
    prompt = GAP_ANALYSIS_PROMPT.format(
        resume_text=resume_text[:6000],  # keep prompts reasonably sized
        job_text=job_text[:6000],
    )
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(block.text for block in response.content if block.type == "text")
    raw = raw.strip().removeprefix("```json").removesuffix("```").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return GapAnalysis(summary="Could not parse model output. Try again.")

    return GapAnalysis(
        match_score=int(data.get("match_score", 0)),
        matched_skills=data.get("matched_skills", []),
        missing_skills=data.get("missing_skills", []),
        summary=data.get("summary", ""),
    )
