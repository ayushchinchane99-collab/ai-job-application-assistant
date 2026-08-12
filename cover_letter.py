"""
cover_letter.py
----------------
Generates a tailored cover letter from a resume + job posting, using
the gap analysis so the letter leans into genuine strengths rather
than generic filler.
"""

COVER_LETTER_PROMPT = """You are helping a candidate write a concise, honest,
non-generic cover letter. Do NOT invent experience the candidate doesn't have.
Use the matched skills to build the core argument. If there are missing
skills, address at most one briefly and positively (e.g. framed as eagerness
to learn), don't dwell on gaps.

Tone: {tone}
Length: 3-4 short paragraphs, no more than 300 words total.
Do not use generic phrases like "I am writing to express my interest" or
"I am a perfect fit". Be specific and concrete, referencing real details
from the resume and the job posting.

RESUME:
{resume_text}

JOB POSTING:
{job_text}

MATCHED SKILLS (lean into these): {matched_skills}
KNOWN GAP (address briefly, positively, at most once): {top_missing_skill}

Write the cover letter now. Output only the letter text, no headers, no
markdown, no explanation.
"""


def generate_cover_letter(
    resume_text: str,
    job_text: str,
    matched_skills: list,
    missing_skills: list,
    client,
    model: str,
    tone: str = "professional and confident, slightly informal",
) -> str:
    top_missing = missing_skills[0] if missing_skills else "none"
    prompt = COVER_LETTER_PROMPT.format(
        tone=tone,
        resume_text=resume_text[:6000],
        job_text=job_text[:6000],
        matched_skills=", ".join(matched_skills) if matched_skills else "general fit",
        top_missing_skill=top_missing,
    )
    response = client.messages.create(
        model=model,
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()
