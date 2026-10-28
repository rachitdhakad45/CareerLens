"""Streamlit application for the CareerLens resume-to-career workflow."""

import hashlib
from html import escape
import os
from pathlib import Path

import streamlit as st

from src.ats.analyzer import (
    calculate_overall_ats_score,
    generate_ats_suggestions,
)
from src.ml.career_predictor import predict_career
from src.recommendations.career_requirements import CAREER_REQUIREMENTS
from src.recommendations.course_recommender import recommend_courses
from src.recommendations.opportunity_recommender import (
    recommend_opportunities,
)
from src.recommendations.opportunity_scheduler import run_sync
from src.recommendations.skill_gap import analyze_skill_gap
from src.resume.extractor import extract_resume_data
from src.resume.parser import extract_text_from_pdf
from src.nlp.skill_display import (
    format_category_name,
    prepare_skill_display,
)
from src.nlp.skill_extractor import extract_skill_matches
from src.ui.theme import inject_theme


PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_ROOT / "data" / "careerlens.db"
MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024


def get_gemini_api_key() -> str:
    """Read the assistant key from the server environment or Streamlit secrets."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if key:
        return key.strip()

    try:
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return ""


@st.cache_resource
def get_opportunity_engine(database_url: str):
    from src.database.opportunity_store import create_database_engine

    return create_database_engine(database_url)


def get_latest_sync_for_source(engine, source_id: str):
    """Read the latest sync record when the existing database has the table."""
    from sqlalchemy import inspect, select
    from sqlalchemy.orm import Session

    from src.database.opportunity_model import SyncRun

    if not inspect(engine).has_table("sync_runs"):
        return None

    with Session(engine) as session:
        return session.scalar(
            select(SyncRun)
            .where(SyncRun.source_id == source_id)
            .order_by(SyncRun.id.desc())
            .limit(1)
        )


def merge_opportunity_results(*groups: list[dict]) -> list[dict]:
    """Combine live and curated listings without showing duplicate IDs."""
    merged = {}
    for group in groups:
        for item in group:
            opportunity_id = item.get("opportunity_id")
            if opportunity_id:
                merged.setdefault(opportunity_id, item)

    return sorted(
        merged.values(),
        key=lambda item: (
            -item.get("priority_score", 0),
            -len(item.get("matched_skills", [])),
            -len(item.get("role_skills_matched", [])),
            item.get("title", "").lower(),
        ),
    )


def render_resume_profile(resume, skill_display: dict) -> None:
    """Show the extracted profile in a reviewable, readable form."""
    st.subheader("Resume overview")
    first_row = st.columns(3)
    for column, label, value in zip(
        first_row,
        ("Name", "Email", "Phone"),
        (resume.name, resume.email, resume.phone),
    ):
        with column:
            st.metric(label, value or "Not detected")

    left, right = st.columns(2)
    with left:
        st.markdown("**Education**")
        if resume.education:
            for item in resume.education:
                st.write(f"- {item}")
        else:
            st.caption("No education details detected.")

        st.markdown("**Projects**")
        if resume.projects:
            for item in resume.projects:
                st.write(f"- {item}")
        else:
            st.caption("No projects detected.")

    with right:
        st.markdown("**Experience**")
        if resume.experience:
            for item in resume.experience:
                st.write(f"- {item}")
        else:
            st.caption("No experience details detected.")

        st.markdown("**Certifications**")
        if resume.certifications:
            for item in resume.certifications:
                st.write(f"- {item}")
        else:
            st.caption("No certifications detected.")

    st.subheader("Skills found in the resume")
    if not skill_display:
        st.info("No skills from CareerLens' current skill vocabulary were found.")
        return

    columns = st.columns(min(3, len(skill_display)))
    for index, (category, skills) in enumerate(skill_display.items()):
        with columns[index % len(columns)]:
            st.markdown(f"**{format_category_name(category)}**")
            for skill in skills:
                st.write(f"{skill['skill']} · {skill['confidence']:.0%}")
                st.caption(f"Evidence: {skill['evidence']}")


def render_ats_analysis(resume, skill_matches: list, result: dict | None = None) -> dict:
    grouped_skills = {
        category: [
            match
            for match in skill_matches
            if (match.category or "other") == category
        ]
        for category in {
            match.category or "other"
            for match in skill_matches
        }
    }
    if result is None:
        result = calculate_overall_ats_score(
            resume,
            skill_matches,
            grouped_skills,
        )

    st.metric("ATS-oriented score", f"{result['total_score']:.1f} / 100")
    st.progress(min(max(result["total_score"] / 100, 0.0), 1.0))
    st.caption(
        "This score summarizes resume completeness and visible evidence. "
        "It is not a prediction of screening or hiring outcomes."
    )

    breakdown = result["breakdown"]
    score_rows = [
        ("Resume completeness", "resume_completeness"),
        ("Skills and keywords", "skills_keywords"),
        ("Projects and experience", "projects_experience"),
        ("Education and certifications", "education_certifications"),
        ("Resume structure", "resume_structure"),
        ("Content quality", "content_quality"),
    ]
    columns = st.columns(3)
    for index, (label, key) in enumerate(score_rows):
        section = breakdown[key]
        columns[index % len(columns)].metric(
            label,
            f"{section['score']:.1f} / {section['max_score']} ",
        )

    suggestions = generate_ats_suggestions(result)
    st.markdown("**Ways to strengthen the resume**")
    if suggestions:
        for suggestion in suggestions:
            st.write(f"- {suggestion}")
    else:
        st.success("No major ATS-oriented improvements were detected.")
    return result


def render_career_plan(resume_text: str, career_family: str) -> dict:
    gap = analyze_skill_gap(resume_text, career_family)
    st.metric(
        "Skills visible for this career family",
        f"{gap['coverage_score']:.0f}%",
        help=(
            "Coverage means a skill appears in the resume. It does not "
            "measure real-world proficiency."
        ),
    )

    covered, mention_only, missing = st.columns(3)
    covered.metric("Supported evidence", gap["covered_count"])
    mention_only.metric("Mentioned, needs context", gap["mention_only_count"])
    missing.metric("Not found in this resume", gap["missing_count"])
    st.caption(
        "A skill missing from the resume may still be one you have. Add "
        "evidence before treating it as a genuine gap."
    )

    with st.expander("Review skill evidence"):
        if gap["covered_skills"]:
            st.markdown("**Evidence detected**")
            for item in gap["covered_skills"]:
                st.write(f"- **{item['skill'].title()}** — {item['evidence']}")
        if gap["mention_only_skills"]:
            st.markdown("**Skills mentioned without strong evidence**")
            for item in gap["mention_only_skills"]:
                st.write(f"- **{item['skill'].title()}** — {item['evidence']}")
        if gap["missing_skills"]:
            st.markdown("**Skills not found in this resume**")
            for item in gap["missing_skills"]:
                st.write(
                    f"- {item['skill'].title()} "
                    f"({item['priority']} priority)"
                )

    st.subheader("Learning recommendations")
    try:
        courses = recommend_courses(resume_text, career_family, top_n=5)
    except (FileNotFoundError, ValueError) as error:
        st.warning(f"Course recommendations are unavailable: {error}")
        courses = []

    if courses:
        for course in courses:
            with st.container(border=True):
                st.markdown(f"**[{course['title']}]({course['url']})**")
                st.caption(
                    f"{course['provider']} · {course['level']} · "
                    f"{course['price']} · {course['duration'] or 'Duration not listed'}"
                )
                st.write(course["reason"])
                if course["description"]:
                    st.caption(course["description"])
    elif gap["missing_skills"]:
        st.info("No course in the current catalog maps to these skills yet.")
    else:
        st.success("No uncovered target-role skills were detected in this resume.")

    return gap


def render_opportunities(resume_text: str, career_family: str) -> list[dict]:
    st.session_state["career_opportunities"] = []
    configured_url = os.getenv("CAREERLENS_DATABASE_URL", "").strip()
    database_url = configured_url or f"sqlite:///{DATABASE_PATH.as_posix()}"
    engine = None
    use_database = bool(configured_url) or DATABASE_PATH.is_file()

    if use_database:
        try:
            engine = get_opportunity_engine(database_url)
        except Exception:
            st.warning(
                "The opportunities database could not be opened. "
                "Check CAREERLENS_DATABASE_URL and the database service."
            )

    left, right = st.columns([1, 3])
    with left:
        refresh_clicked = st.button(
            "Refresh job listings",
            help="Fetch the enabled sources and update the local opportunities database.",
        )
    with right:
        st.caption(
            "Refresh runs only when you press the button. It contacts the "
            "configured job source and writes results to the configured database."
        )

    if refresh_clicked:
        try:
            with st.spinner("Refreshing configured job sources..."):
                outcome = run_sync(database_url=database_url)
            st.session_state["latest_sync_outcome"] = outcome
            if engine is None:
                engine = get_opportunity_engine(database_url)
        except Exception:
            st.error(
                "Could not refresh job listings. Check the worker logs and "
                "the configured source/database settings."
            )

    outcome = st.session_state.get("latest_sync_outcome")
    if outcome:
        st.info(
            f"Last refresh: {outcome['jobs_fetched']} fetched, "
            f"{outcome['jobs_saved']} saved, "
            f"{outcome['jobs_rejected']} rejected; "
            f"{outcome['sources_failed']} source(s) failed."
        )
        for item in outcome["errors"]:
            st.warning(f"{item.get('source_id', 'Source')}: {item['error']}")

    latest_run = None
    if engine is not None:
        try:
            latest_run = get_latest_sync_for_source(engine, "GH-STRIPE-001")
        except Exception:
            latest_run = None
        try:
            recommendations = recommend_opportunities(
                resume_text,
                career_family,
                top_n=12,
                engine=engine,
                include_related=True,
            )
            data_source = "the synced opportunity database"
        except Exception:
            st.warning(
                "The synced job database is unavailable; showing the "
                "local catalog instead. Check the worker logs if this persists."
            )
            recommendations = recommend_opportunities(
                resume_text,
                career_family,
                top_n=12,
                include_related=True,
            )
            data_source = "the local opportunity catalog"
    else:
        recommendations = recommend_opportunities(
            resume_text,
            career_family,
            top_n=12,
            include_related=True,
        )
        data_source = "the local opportunity catalog"

    try:
        curated_recommendations = recommend_opportunities(
            resume_text,
            career_family,
            top_n=12,
            include_related=True,
        )
    except (FileNotFoundError, ValueError):
        curated_recommendations = []
    recommendations = merge_opportunity_results(
        recommendations,
        curated_recommendations,
    )

    if latest_run is not None:
        finished = latest_run.finished_at or latest_run.started_at
        st.caption(
            f"Latest Stripe sync: {finished:%d %b %Y, %H:%M UTC} · "
            f"{latest_run.status}"
        )
    else:
        st.caption(f"Searching {data_source}; freshness is shown on each listing.")

    st.caption(
        "Ranked by missing-skill matches first, then by skills related to "
        "your selected career path. Always review the employer's full criteria."
    )
    if not recommendations:
        st.warning(
            "No recent listings matched this career path yet. Refresh the "
            "source or try a neighboring career family."
        )
        return []

    filter_left, filter_right = st.columns([1.35, 1])
    with filter_left:
        location_filter = st.text_input(
            "Location or work mode",
            placeholder="Remote, Bengaluru, hybrid",
        ).strip().casefold()
    with filter_right:
        types = sorted({item["opportunity_type"] for item in recommendations})
        selected_type = st.selectbox(
            "Opportunity type",
            ["All types", *types],
        )
    shown = [
        item
        for item in recommendations
        if (
            (not location_filter
             or location_filter in item["location"].casefold()
             or location_filter in item["work_mode"].casefold())
            and (selected_type == "All types"
                 or item["opportunity_type"] == selected_type)
        )
    ]

    if not shown:
        st.info("No listings match these filters. Try clearing one filter.")
        return []

    st.session_state["career_opportunities"] = [
        {"title": item["title"], "company": item["company"]}
        for item in shown[:12]
    ]

    st.markdown(
        f'<div class="cl-results-count"><strong>{len(shown)} roles</strong><span>selected for {career_family}</span></div>',
        unsafe_allow_html=True,
    )

    for item in shown:
        with st.container(border=True):
            title_col, action_col = st.columns([3, 1])
            with title_col:
                st.markdown(f"### {item['title']}")
                st.markdown(
                    f"**{item['company']}** · "
                    f"{item['location'] or 'Location not listed'}"
                )
            with action_col:
                st.link_button("View role ↗", item["url"], use_container_width=True)
            metadata = [
                value
                for value in (
                    item["work_mode"],
                    item["experience_level"],
                    item["compensation"],
                )
                if value
            ]
            if metadata:
                st.markdown(
                    '<div class="cl-job-tags">'
                    + "".join(
                        f"<span>{escape(value)}</span>" for value in metadata
                    )
                    + "</div>",
                    unsafe_allow_html=True,
                )
            st.write(item["reason"])
            if item["deadline"]:
                st.caption(f"Apply by: {item['deadline']}")
            st.caption(
                f"Source: {item['source']} · Verified: {item['last_verified']}"
            )

    return shown


def build_assistant_context(
    resume,
    skill_matches: list,
    career_family: str,
    gap: dict,
    ats_result: dict | None = None,
    opportunities: list[dict] | None = None,
) -> dict:
    """Build a small context without contact fields or the raw resume PDF."""

    def clipped(items: list, limit: int, item_length: int) -> list[str]:
        return [str(item)[:item_length] for item in items[:limit]]

    return {
        "target_career_family": career_family,
        "skills_found": [
            {
                "skill": match.skill,
                "evidence": match.evidence[:80],
                "confidence": round(match.confidence, 2),
            }
            for match in skill_matches[:10]
        ],
        "education": clipped(resume.education, 2, 150),
        "experience": clipped(resume.experience, 2, 250),
        "projects": clipped(resume.projects, 2, 200),
        "certifications": clipped(resume.certifications, 2, 150),
        "skills_not_found_in_resume": [
            {"skill": item["skill"], "priority": item["priority"]}
            for item in gap["missing_skills"][:10]
        ],
        "skills_mentioned_without_strong_evidence": [
            item["skill"] for item in gap["mention_only_skills"][:10]
        ],
        "ats_score": (
            round(ats_result["total_score"], 1)
            if ats_result is not None
            else None
        ),
        "ats_suggestions": (
            clipped(generate_ats_suggestions(ats_result), 3, 180)
            if ats_result is not None
            else []
        ),
        "opportunities": (opportunities or [])[:4],
    }


def render_assistant(context: dict, context_id: str) -> None:
    from src.assistant.local import answer_career_question

    if st.session_state.get("assistant_context_id") != context_id:
        st.session_state["assistant_context_id"] = context_id
        st.session_state["assistant_messages"] = []

    st.markdown(
        "Ask about the evidence in your resume, your skill gaps, or a next step."
    )
    api_key = get_gemini_api_key()
    st.caption(
        "CareerLens may send a limited career summary and your question to "
        "an external AI service to prepare an answer."
    )

    for message in st.session_state.get("assistant_messages", []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if "assistant_notice" in st.session_state:
        st.warning(st.session_state.pop("assistant_notice"))

    st.caption("Quick prompts")
    prompt_rows = st.columns(3)
    prompt_options = (
        ("Skills to build", "What skill should I focus on next?"),
        ("My strengths", "What strengths stand out in my resume?"),
        ("Resume tips", "How can I improve my resume?"),
    )
    question_key = f"assistant_question_{context_id[:12]}"
    for column, (label, prompt) in zip(prompt_rows, prompt_options):
        with column:
            if st.button(label, key=f"assistant_prompt_{context_id[:8]}_{label}"):
                st.session_state[question_key] = prompt
                st.rerun()

    with st.form(f"career_assistant_form_{context_id[:12]}", clear_on_submit=True):
        question = st.text_input(
            "Your question",
            placeholder="What should I focus on next?",
            max_chars=1_000,
            key=question_key,
        )
        submitted = st.form_submit_button("Ask CareerLens", type="primary")

    if not submitted:
        return
    if not question.strip():
        st.warning("Type a question first.")
        return

    messages = st.session_state.setdefault("assistant_messages", [])
    messages.append({"role": "user", "content": question.strip()})
    if api_key:
        from src.assistant.gemini import (
            CareerAssistantError,
            ask_career_assistant,
        )

        try:
            with st.spinner("Thinking through your question..."):
                answer = ask_career_assistant(
                    question,
                    context,
                    api_key=api_key,
                    history=messages[:-1][-2:],
                    model=os.getenv(
                        "CAREERLENS_GEMINI_MODEL", "gemini-3.5-flash-lite"
                    ),
                )
        except (CareerAssistantError, ValueError) as error:
            answer = answer_career_question(question, context)
            st.session_state["assistant_notice"] = (
                f"Assistant request issue: {error}. "
                "Here's a resume-grounded answer in the meantime."
            )
    else:
        answer = answer_career_question(question, context)

    messages.append({"role": "assistant", "content": answer})
    st.rerun()


def render_topbar() -> None:
    st.markdown(
        """
        <header class="cl-topbar">
          <div class="cl-brand"><span class="cl-mark">C</span><span>CareerLens</span></div>
          <div class="cl-topbar-note"><span class="cl-live-dot"></span> YOUR CAREER, IN FOCUS</div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_landing_page() -> None:
    st.markdown(
        """
        <section class="cl-hero">
          <div class="cl-hero-copy">
            <div class="cl-eyebrow"><span class="cl-eyebrow-line"></span> YOUR CAREER, IN FOCUS</div>
            <h1>Find your next move.<br><span>Make it count.</span></h1>
            <p>Your experience has a story. CareerLens helps you see what's already strong, what to build next, and where your skills can take you.</p>
            <div class="cl-hero-tags"><span>01 · SEE YOUR STRENGTHS</span><span>02 · BUILD YOUR PLAN</span><span>03 · FIND YOUR FIT</span></div>
          </div>
          <div class="cl-hero-art" aria-hidden="true">
            <div class="cl-orbit cl-orbit-one"></div><div class="cl-orbit cl-orbit-two"></div>
            <div class="cl-orbit-core">✦</div>
            <div class="cl-art-label"><span>CAREERLENS INSIGHT</span><strong>Clarity over guesswork.</strong></div>
            <div class="cl-art-spark cl-spark-one">✳</div><div class="cl-art-spark cl-spark-two">·</div>
          </div>
        </section>
        <div class="cl-landing-intro"><span class="cl-section-kicker">A BETTER WAY TO PLAN YOUR CAREER</span><h2>Less guessing. More forward motion.</h2><p>One clear view of your resume, your next skills, and opportunities worth exploring.</p></div>
        <div class="cl-feature-row cl-landing-features">
          <div class="cl-feature"><span>01 · UNDERSTAND</span><strong>See the signal in your resume</strong><p>Review experience, skill evidence, and an ATS-oriented breakdown.</p></div>
          <div class="cl-feature"><span>02 · GROW</span><strong>Turn gaps into a roadmap</strong><p>Choose a direction, focus on priority skills, and find useful courses.</p></div>
          <div class="cl-feature"><span>03 · DISCOVER</span><strong>Explore roles with context</strong><p>Browse opportunities connected to your career path and skill profile.</p></div>
        </div>
        <div class="cl-how" id="how-it-works">
          <div><span class="cl-section-kicker">HOW IT WORKS</span><h2>From resume to next step</h2></div>
          <div class="cl-how-steps"><div><span>01</span><strong>Upload</strong><small>Add a text-based PDF.</small></div><i>→</i><div><span>02</span><strong>Explore</strong><small>Review evidence and career options.</small></div><i>→</i><div><span>03</span><strong>Move forward</strong><small>Pick one practical next action.</small></div></div>
        </div>
        <div class="cl-landing-trust"><span>✦</span><p><strong>Your resume stays yours.</strong> It's processed by the app and isn't saved in its database. The career assistant may send a limited career summary and your question to an external AI service to prepare an answer.</p><small>Public demo · Please don't upload confidential resumes.</small></div>
        """,
        unsafe_allow_html=True,
    )

    cta_col, link_col = st.columns([1.5, 5])
    with cta_col:
        if st.button(
            "Build my career plan  →",
            type="primary",
            key="landing_start_workspace",
            use_container_width=True,
        ):
            st.session_state["career_workspace_started"] = True
            st.rerun()
    with link_col:
        st.markdown('<div class="cl-landing-link"><a href="#how-it-works">See how CareerLens works ↓</a></div>', unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(
        page_title="CareerLens",
        page_icon="✦",
        layout="wide",
    )
    inject_theme()
    render_topbar()

    if not st.session_state.get("career_workspace_started", False):
        render_landing_page()
        return

    home_col, title_col = st.columns([1.1, 5])
    with home_col:
        if st.button("← Overview", key="back_to_landing"):
            st.session_state["career_workspace_started"] = False
            st.rerun()
    with title_col:
        st.markdown(
            '<div class="cl-workspace-title"><span class="cl-section-kicker">YOUR CAREER WORKSPACE</span><h1>Bring your experience into focus</h1><p>Start with your resume. Leave with one clear next step.</p></div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div class="cl-workspace-privacy"><strong>Resume handling</strong><span>Your PDF is processed by this app and isn\'t saved to its database. The career assistant may send a limited career summary and your question to an external AI service.</span><small>Public demo · Please don\'t upload confidential resumes.</small></div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        upload_left, upload_right = st.columns([1.35, 1])
        with upload_left:
            st.markdown("#### Upload your resume")
            st.caption("We'll map the experience and skills already present, then build your next-step plan.")
            uploaded_file = st.file_uploader(
                "Choose a text-based PDF resume",
                type=["pdf"],
                help="Scanned image-only PDFs are not supported yet.",
            )
        with upload_right:
            st.markdown(
                """
                <div class="cl-upload-aside">
                  <span class="cl-privacy-icon">✦</span>
                  <div><strong>One upload, four useful views</strong><p>Profile & ATS · career plan · matched opportunities · career assistant</p></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if uploaded_file is None:
        st.caption(
            "Choose a text-based PDF to open your skill snapshot and career views."
        )
        st.stop()
    if uploaded_file.size > MAX_RESUME_SIZE_BYTES:
        st.error("The PDF is too large. Please upload a file under 10 MB.")
        st.stop()

    try:
        resume_text = extract_text_from_pdf(uploaded_file)
        resume = extract_resume_data(resume_text)
        skill_matches = extract_skill_matches(resume_text)
        skill_display = prepare_skill_display(skill_matches)
    except Exception as error:
        st.error(f"We could not analyze this PDF: {error}")
        st.stop()

    try:
        prediction = predict_career(resume_text, top_n=3)
    except Exception as error:
        prediction = None
        st.warning(f"Career-family suggestions are unavailable: {error}")

    career_families = list(CAREER_REQUIREMENTS)
    default_family = (
        prediction["career_family"]
        if prediction and prediction["career_family"] in career_families
        else career_families[0]
    )
    selected_family = st.selectbox(
        "Choose a target career family",
        career_families,
        index=career_families.index(default_family),
        help="You can change the suggested family at any time.",
    )

    if prediction:
        ranked = " · ".join(
            f"{item['career_family']} ({item['probability']:.0%})"
            for item in prediction["alternatives"]
        )
        st.markdown(
            f'<div class="cl-prediction"><span class="cl-prediction-label">MODEL SUGGESTIONS</span><span>{ranked}</span><small>Suggestions to explore, not a definitive career assignment.</small></div>',
            unsafe_allow_html=True,
        )

    gap = analyze_skill_gap(resume_text, selected_family)
    grouped_skills = {}
    for match in skill_matches:
        grouped_skills.setdefault(match.category or "other", []).append(match)
    ats_result = calculate_overall_ats_score(
        resume,
        skill_matches,
        grouped_skills,
    )
    first_name = resume.name.split()[0] if resume.name else "there"
    st.markdown('<div class="cl-snapshot-kicker">YOUR CAREER SNAPSHOT</div>', unsafe_allow_html=True)
    st.subheader(f"A strong starting point, {first_name}.")
    with st.container(border=True):
        snapshot_cols = st.columns(4)
        snapshot_cols[0].metric("ATS readiness", f"{ats_result['total_score']:.0f} / 100")
        snapshot_cols[1].metric("Skills detected", len(skill_matches))
        snapshot_cols[2].metric("Skills to build", gap["missing_count"])
        snapshot_cols[3].metric("Career direction", selected_family)
        st.caption(
            "A quick orientation from your resume—not a hiring prediction. "
            "Explore each view below to decide what feels right."
        )
    profile_tab, plan_tab, jobs_tab, assistant_tab = st.tabs(
        ["Resume and ATS", "Career plan", "Opportunities", "Career assistant"],
        key="career_workspace_tabs",
        on_change="rerun",
    )

    with profile_tab:
        if profile_tab.open:
            render_resume_profile(resume, skill_display)
            st.divider()
            st.subheader("ATS-oriented analysis")
            render_ats_analysis(resume, skill_matches, ats_result)
            with st.expander("View extracted resume text"):
                st.text_area("Extracted text", resume_text, height=300)

    with plan_tab:
        if plan_tab.open:
            st.subheader(f"Your roadmap · {selected_family}")
            render_career_plan(resume_text, selected_family)

    with jobs_tab:
        if jobs_tab.open:
            st.subheader("Opportunities for your next move")
            render_opportunities(resume_text, selected_family)

    with assistant_tab:
        if assistant_tab.open:
            context_id = hashlib.sha256(
                f"{resume_text}\n{selected_family}".encode("utf-8")
            ).hexdigest()
            assistant_context = build_assistant_context(
                resume,
                skill_matches,
                selected_family,
                gap,
                ats_result,
                st.session_state.get("career_opportunities", []),
            )
            with st.expander("Review the career context used by the assistant"):
                st.json(assistant_context)
            render_assistant(assistant_context, context_id)


if __name__ == "__main__":
    main()
