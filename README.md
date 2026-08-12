# AI Job Application Assistant

An end-to-end tool that helps you triage and apply to jobs faster:
upload your resume once, add job postings, get instant fit-ranking
across all of them, then run a deep skill-gap analysis and generate a
tailored cover letter for the ones worth pursuing.

Built to actually solve a real problem (tracking fit across dozens of
applications) rather than as a toy demo.

## Features

- **Resume parsing** - upload a PDF or plain-text resume once.
- **Job ingestion** - add postings by URL (auto-scraped) or paste the
  text directly when a site blocks scraping.
- **Fast ranking** - every job gets an instant local TF-IDF similarity
  score against your resume, no API calls needed, so you can add 20
  postings and immediately see which are worth your time.
- **Deep gap analysis** - for a specific job, calls Claude to return a
  structured match score, matched skills, missing skills, and an
  honest one-line summary of fit.
- **Tailored cover letters** - generated from the gap analysis, so the
  letter leans into real matched skills instead of generic filler, and
  never invents experience you don't have.

## Architecture

```
                    ┌──────────────────┐
   Resume (PDF) ──▶ │  resume_parser.py │
                    └──────────────────┘
                              │
                              ▼
┌───────────────┐   ┌──────────────────┐    ┌──────────────┐
│ Job URL / text│──▶│   job_parser.py   │───▶│  matcher.py  │
└───────────────┘   └──────────────────┘    │ TF-IDF score │
                                             │ + LLM gap    │
                                             │   analysis   │
                                             └──────┬───────┘
                                                    │
                                                    ▼
                                          ┌───────────────────┐
                                          │ cover_letter.py    │
                                          │ (Claude API)        │
                                          └───────────────────┘
                                                    │
                                                    ▼
                                          ┌───────────────────┐
                                          │     app.py          │
                                          │  Streamlit UI        │
                                          └───────────────────┘
```

**Design decision:** ranking uses a local, free TF-IDF score so you're
not burning API calls scoring every job you glance at. The LLM is only
called once you've picked a specific job worth a deep look - this
keeps the tool fast and cheap to run.

## Setup

1. Clone / unzip this project and `cd` into it.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Get an Anthropic API key from [console.anthropic.com](https://console.anthropic.com)
   (pay-as-you-go, a few cents per cover letter).
4. Run the app:
   ```bash
   streamlit run app.py
   ```
5. Paste your API key into the sidebar (or set `ANTHROPIC_API_KEY` as
   an environment variable beforehand - see `.env.example`).

## Usage

1. **Tab 1** - upload your resume (PDF or .txt).
2. **Tab 2** - add job postings one at a time, either by URL or pasted
   text.
3. **Tab 3** - see all added jobs ranked by fit score.
4. **Tab 4** - pick the top job(s), run gap analysis, then generate and
   download a tailored cover letter.

## Tech stack

Python, Streamlit, Anthropic API (Claude), scikit-learn (TF-IDF),
pypdf, BeautifulSoup4.

## Possible extensions

- Swap the TF-IDF ranking layer for a proper vector DB (Chroma) with
  embeddings, for semantic rather than keyword-based ranking.
- Add browser automation (Playwright) to auto-fill application forms.
- Persist jobs/resumes to SQLite so history survives across sessions.
- Batch mode: point it at a list of company career pages and auto-crawl
  open roles.

## Resume bullet points (for your CV)

- *Built an end-to-end AI job-application assistant (Python, Streamlit,
  Claude API) that parses resumes/job postings, ranks fit across
  postings via TF-IDF, and generates tailored cover letters through an
  LLM-driven skill-gap analysis pipeline.*
- *Designed a two-tier matching architecture separating a free local
  similarity layer from an LLM-based deep analysis layer to balance
  speed, cost, and accuracy.*
