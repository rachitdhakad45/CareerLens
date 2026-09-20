import streamlit as st

from src.resume.parser import extract_text_from_pdf
from src.resume.extractor import extract_resume_data


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

        st.subheader("🛠️ Skills")

        if resume.skills:
            for item in resume.skills:
                st.write(f"• {item}")
        else:
            st.info("No skills detected.")

        with st.expander("🔍 View Raw Extracted Text"):
            st.text_area(
                "Resume text",
                resume_text,
                height=400
            )

    except ValueError as error:
        st.error(str(error))


