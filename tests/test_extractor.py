from src.resume.extractor import (
    extract_email,
    extract_name,
    extract_phone,
    extract_skills,
)


def test_contact_extraction():

    resume_text = """
    RACHIT DHAKAD
    rachit.dhakad45@gmail.com
    (+91)909-868-9136

    CAREER OBJECTIVE
    Dedicated third-year student.
    """

    assert extract_name(resume_text) == "RACHIT DHAKAD"
    assert extract_email(resume_text) == "rachit.dhakad45@gmail.com"
    assert extract_phone(resume_text) == "9098689136"

from src.resume.extractor import detect_sections


def test_section_detection():

    resume_text = """
    RACHIT DHAKAD

    ACADEMIC RECORD
    B.Tech. in CSE
    AITR, Indore

    TECHNICAL SKILLS
    Python
    Machine Learning
    SQL

    PROJECTS
    Credit Card Default Prediction

    CERTIFICATIONS
    Oracle OCI Data Science
    """

    sections = detect_sections(resume_text)

    assert "B.Tech. in CSE" in sections["education"]
    assert "Python" in sections["skills"]
    assert "Credit Card Default Prediction" in sections["projects"]
    assert "Oracle OCI Data Science" in sections["certifications"]

from src.resume.extractor import extract_education

def test_education_extraction():

    sections = {
        "education": [
            "B.Tech. in CSE",
            "AITR, Indore",
            "CGPA: 6.18",
            "2023 – 2027",
        ]
    }

    education = extract_education(sections)

    assert "B.Tech. in CSE" in education
    assert "AITR, Indore" in education
    assert "CGPA: 6.18" in education

from src.resume.extractor import (
    extract_email,
    extract_name,
    extract_phone,
    detect_sections,
    extract_education,
    extract_projects,
    extract_certifications,
    extract_experience,
    extract_skills,
    extract_resume_data,
)

def test_projects_and_certifications_extraction():

    sections = {
        "projects": [
            "Autonomous AI Sales & Recovery System",
            "Carbon Footprint Tracker for Indian Coal Mines",
        ],
        "certifications": [
            "Oracle OCI Data Science",
        ],
    }

    projects = extract_projects(sections)
    certifications = extract_certifications(sections)

    assert "Autonomous AI Sales & Recovery System" in projects
    assert "Carbon Footprint Tracker for Indian Coal Mines" in projects
    assert "Oracle OCI Data Science" in certifications

def test_experience_and_skills_extraction():

    sections = {
        "experience": [
            "ML & Backend Developer",
            "EY Techathon 6.0",
        ],
        "skills": [
            "Python",
            "Machine Learning",
            "SQL",
            "Pandas",
        ],
    }

    experience = extract_experience(sections)
    skills = extract_skills(sections)

    assert "ML & Backend Developer" in experience
    assert "Python" in skills
    assert "Machine Learning" in skills

def test_complete_resume_extraction():

    resume_text = """
    RACHIT DHAKAD
    rachit.dhakad45@gmail.com
    (+91)909-868-9136

    ACADEMIC RECORD
    B.Tech. in CSE
    AITR, Indore
    CGPA: 6.18

    TECHNICAL SKILLS
    Python
    Machine Learning
    SQL

    PROJECTS
    Autonomous AI Sales & Recovery System

    CERTIFICATIONS
    Oracle OCI Data Science
    """

    resume = extract_resume_data(resume_text)

    assert resume.name == "RACHIT DHAKAD"
    assert resume.email == "rachit.dhakad45@gmail.com"
    assert resume.phone == "9098689136"
    assert "B.Tech. in CSE" in resume.education
    assert "Python" in resume.skills
    assert "Autonomous AI Sales & Recovery System" in resume.projects
    assert "Oracle OCI Data Science" in resume.certifications

