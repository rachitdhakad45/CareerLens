import streamlit as st

from src.resume.parser import extract_text_from_pdf
from src.resume.extractor import extract_resume_data
from src.nlp.skill_extractor import extract_skill_matches
from src.nlp.skill_display import prepare_skill_display
from src.nlp.skill_display import (
    prepare_skill_display,
    format_category_name,
)
from src.ats.analyzer import (
    calculate_overall_ats_score,
    generate_ats_suggestions,
)

st.set_page_config(
    page_title="CareerLens",
    page_icon="🎯",
    layout="wide"
)


st.title("🎯 CareerLens")
st.subheader("AI-Powered Career Intelligence Platform")

st.write(
    "Understand your resume, discover your career path, "
    "identify skill gaps, and find opportunities."
)

st.divider()

st.header("📄 Resume Analysis")

uploaded_file = st.file_uploader(
    "Upload your resume",
    type=["pdf"],
    help="Upload your resume in PDF format."
)

if uploaded_file is not None:

    st.success(f"Uploaded: {uploaded_file.name}")

    try:
        # Step 1: Extract raw text from PDF
        resume_text = extract_text_from_pdf(uploaded_file)

        # Step 2: Convert raw text into structured information
        resume = extract_resume_data(resume_text)

        st.success("Resume analyzed successfully!")

        st.divider()

        st.header("👤 Resume Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Name**")
            st.write(resume.name or "Not detected")

        with col2:
            st.markdown("**Email**")
            st.write(resume.email or "Not detected")

        with col3:
            st.markdown("**Phone**")
            st.write(resume.phone or "Not detected")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🎓 Education")

            if resume.education:
                for item in resume.education:
                    st.write(f"• {item}")
            else:
                st.info("No education information detected.")

        with col2:
            st.subheader("💼 Experience")

            if resume.experience:
                for item in resume.experience:
                    st.write(f"• {item}")
            else:
                st.info("No experience information detected.")

        st.subheader("🚀 Projects")

        if resume.projects:
            for item in resume.projects:
                st.write(f"• {item}")
        else:
            st.info("No projects detected.")

        st.subheader("🏆 Certifications")

        if resume.certifications:
            for item in resume.certifications:
                st.write(f"• {item}")
        else:
            st.info("No certifications detected.")

        st.subheader("🛠️ Skills Analysis")

        skill_matches = extract_skill_matches(resume_text)
        skill_display = prepare_skill_display(skill_matches)

        for match in skill_matches:
            if match.skill == "machine learning":
                st.write(
                    "DEBUG:",
                    match.skill,
                    match.confidence,
                    match.evidence
                )

        if skill_display:

            for category, skills in skill_display.items():

                st.markdown(
                    f"### {format_category_name(category)}"
                )

                for skill in skills:

                    confidence = skill["confidence"] * 100

                    st.write(
                        f"**{skill['skill']}** — "
                        f"{confidence:.0f}% confidence"
                    )

                    st.caption(
                        f"Evidence: {skill['evidence']}"
                 )

        else:
            st.info("No recognized skills detected.")

        st.divider()

        st.subheader("📊 ATS Analysis")

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

        ats_result = calculate_overall_ats_score(
            resume,
            skill_matches,
            grouped_skills,
        )

        ats_score = ats_result["total_score"]

        st.metric(
            label="ATS Score",
            value=f"{ats_score:.1f} / 100",
        )

        st.progress(min(ats_score / 100, 1.0))

        st.markdown("### 📋 Score Breakdown")

        breakdown = ats_result["breakdown"]

        score_columns = st.columns(3)

        categories = [
            ("Resume Completeness", "resume_completeness"),
            ("Skills & Keywords", "skills_keywords"),
            ("Projects & Experience", "projects_experience"),
            ("Education & Certifications", "education_certifications"),
            ("Resume Structure", "resume_structure"),
            ("Content Quality", "content_quality"),
        ]

        for index, (label, key) in enumerate(categories):

            section = breakdown[key]

            with score_columns[index % 3]:
                st.metric(
                    label,
                    f"{section['score']:.1f} / {section['max_score']}",
                )

        suggestions = generate_ats_suggestions(ats_result)
    
        st.markdown("### 💡 Improvement Suggestions")

        if suggestions:
            for suggestion in suggestions:
                st.write(f"• {suggestion}")
        else:
            st.success("No major ATS improvements detected.")
        
        with st.expander("🔍 View Raw Extracted Text"):
            st.text_area(
                "Resume text",
                resume_text,
                height=400
            )

    except ValueError as error:
        st.error(str(error))


