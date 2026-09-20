import streamlit as st

from src.resume.parser import extract_text_from_pdf


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
        resume_text = extract_text_from_pdf(uploaded_file)

        st.success("Resume text extracted successfully!")

        st.subheader("Extracted Resume Text")

        st.text_area(
            "Resume content",
            resume_text,
            height=400
        )

        st.caption(
            f"Extracted {len(resume_text)} characters from your resume."
        )

    except ValueError as error:
        st.error(str(error))