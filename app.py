"""
app.py
------
AI Job Application Assistant - Streamlit UI.

Run with:
    streamlit run app.py

Flow:
  1. Upload your resume once (PDF or .txt).
  2. Add job postings (by URL or pasted text) - add as many as you want.
  3. See a ranked table of fit scores (fast, local TF-IDF).
  4. Pick a job -> get a deep LLM gap analysis + a tailored cover letter.
"""

import os
import streamlit as st
from anthropic import Anthropic

from resume_parser import parse_resume
from job_parser import parse_job
from matcher import tfidf_match_score, llm_gap_analysis
from cover_letter import generate_cover_letter

MODEL = "claude-sonnet-4-6"

st.set_page_config(page_title="AI Job Application Assistant", layout="wide")

# ---------------------------------------------------------------- session state
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "jobs" not in st.session_state:
    # each job: {"label": str, "text": str, "score": float}
    st.session_state.jobs = []

# ---------------------------------------------------------------- sidebar (API key)
st.sidebar.title("Setup")
api_key = st.sidebar.text_input(
    "Anthropic API key",
    type="password",
    value=os.environ.get("ANTHROPIC_API_KEY", ""),
    help="Get one at console.anthropic.com. Stored only for this session.",
)
client = Anthropic(api_key=api_key) if api_key else None
if not api_key:
    st.sidebar.warning("Add your Anthropic API key to enable gap analysis and cover letters.")

st.title("🎯 AI Job Application Assistant")
st.caption("Upload your resume once, add job postings, get ranked fit scores, gap analysis, and tailored cover letters.")

tab_resume, tab_jobs, tab_rank, tab_letter = st.tabs(
    ["1. Resume", "2. Add Job Postings", "3. Ranked Matches", "4. Gap Analysis & Cover Letter"]
)

# ---------------------------------------------------------------- Tab 1: Resume
with tab_resume:
    st.subheader("Upload your resume")
    uploaded = st.file_uploader("PDF or .txt", type=["pdf", "txt"])
    if uploaded is not None:
        st.session_state.resume_text = parse_resume(uploaded.read(), uploaded.name)
        st.success(f"Parsed {len(st.session_state.resume_text)} characters from {uploaded.name}")

    if st.session_state.resume_text:
        with st.expander("Preview parsed resume text"):
            st.text(st.session_state.resume_text[:3000])

# ---------------------------------------------------------------- Tab 2: Add jobs
with tab_jobs:
    st.subheader("Add a job posting")
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input("Label (e.g. 'BMW - Werkstudent SWE')")
        url = st.text_input("Job posting URL (optional)")
    with col2:
        pasted = st.text_area("Or paste the job description text", height=180)

    if st.button("Add job posting", type="primary"):
        if not st.session_state.resume_text:
            st.error("Upload your resume in Tab 1 first.")
        elif not label:
            st.error("Give this job a short label so you can find it later.")
        else:
            try:
                job_text = parse_job(url or None, pasted or None)
                score = tfidf_match_score(st.session_state.resume_text, job_text)
                st.session_state.jobs.append({"label": label, "text": job_text, "score": score})
                st.success(f"Added '{label}' - quick fit score: {score}/100")
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))

    if st.session_state.jobs:
        st.write(f"**{len(st.session_state.jobs)} job posting(s) saved.**")

# ---------------------------------------------------------------- Tab 3: Ranked matches
with tab_rank:
    st.subheader("Ranked job matches (fast local scoring)")
    if not st.session_state.jobs:
        st.info("Add job postings in Tab 2 first.")
    else:
        ranked = sorted(st.session_state.jobs, key=lambda j: j["score"], reverse=True)
        st.table(
            [{"Job": j["label"], "Quick Fit Score": f"{j['score']}/100"} for j in ranked]
        )
        st.caption(
            "This score is a fast local TF-IDF similarity between resume and job text. "
            "Use Tab 4 for a proper LLM-based gap analysis on a specific job."
        )

# ---------------------------------------------------------------- Tab 4: Gap analysis + cover letter
with tab_letter:
    st.subheader("Deep analysis & tailored cover letter")
    if not st.session_state.jobs:
        st.info("Add job postings in Tab 2 first.")
    elif client is None:
        st.info("Add your Anthropic API key in the sidebar first.")
    else:
        labels = [j["label"] for j in st.session_state.jobs]
        chosen_label = st.selectbox("Choose a job posting", labels)
        chosen_job = next(j for j in st.session_state.jobs if j["label"] == chosen_label)

        if st.button("Run gap analysis"):
            with st.spinner("Analyzing fit with Claude..."):
                analysis = llm_gap_analysis(st.session_state.resume_text, chosen_job["text"], client, MODEL)
                st.session_state["last_analysis"] = analysis

        analysis = st.session_state.get("last_analysis")
        if analysis:
            st.metric("LLM Match Score", f"{analysis.match_score}/100")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**✅ Matched skills**")
                for s in analysis.matched_skills:
                    st.write(f"- {s}")
            with col2:
                st.write("**⚠️ Missing / weak skills**")
                for s in analysis.missing_skills:
                    st.write(f"- {s}")
            st.write("**Summary**")
            st.write(analysis.summary)

            st.divider()
            tone = st.selectbox(
                "Cover letter tone",
                ["professional and confident, slightly informal", "formal and traditional", "enthusiastic and energetic"],
            )
            if st.button("Generate cover letter"):
                with st.spinner("Drafting cover letter..."):
                    letter = generate_cover_letter(
                        st.session_state.resume_text,
                        chosen_job["text"],
                        analysis.matched_skills,
                        analysis.missing_skills,
                        client,
                        MODEL,
                        tone=tone,
                    )
                    st.session_state["last_letter"] = letter

            letter = st.session_state.get("last_letter")
            if letter:
                st.text_area("Generated cover letter", letter, height=300)
                st.download_button("Download as .txt", letter, file_name=f"cover_letter_{chosen_label}.txt")
