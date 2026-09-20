import re
from dataclasses import dataclass, field


@dataclass
class ResumeData:
    """Structured information extracted from a resume."""

    name: str = ""
    email: str = ""
    phone: str = ""

    education: list[str] = field(default_factory=list)
    experience: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)


def extract_email(text: str) -> str:
    """Extract the first email address from resume text."""

    pattern = r"[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Za-z]{2,}"

    match = re.search(pattern, text)

    if not match:
        return ""

    return re.sub(r"\s+", "", match.group(0))


def extract_phone(text: str) -> str:
    """Extract the first Indian-style phone number from resume text."""

    pattern = r"(?:\(\+91\)[\s-]*|\+91[\s-]*)?([6-9]\d{2})[\s-]?(\d{3})[\s-]?(\d{4})"

    match = re.search(pattern, text)

    if not match:
        return ""

    return "".join(match.groups())


def extract_name(text: str) -> str:
    """Extract a likely candidate name from the beginning of the resume."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        return ""

    # Most resumes place the candidate's name near the top.
    first_line = lines[0]

    # Avoid treating an email/phone as a name.
    if "@" in first_line or re.search(r"\d", first_line):
        return ""

    return first_line

SECTION_ALIASES = {
    "education": {
        "education",
        "academic record",
        "academic background",
        "qualifications",
        "educational qualifications",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
    },
    "skills": {
        "skills",
        "technical skills",
        "technical expertise",
        "core skills",
    },
    "projects": {
        "projects",
        "academic projects",
        "personal projects",
        "project experience",
    },
    "certifications": {
        "certifications",
        "certificates",
        "licenses & certifications",
    },
    "other": {
    "strengths and interest",
    "strengths and interests",
    "strengths",
    "interests",
    "areas of interest",
    },
}


def normalize_heading(line: str) -> str:
    """Normalize a possible resume section heading."""

    return " ".join(line.lower().strip().split())


def detect_sections(text: str) -> dict[str, list[str]]:
    """Split resume text into recognized sections."""

    sections = {
        "education": [],
        "experience": [],
        "skills": [],
        "projects": [],
        "certifications": [],
        "other": [],
    }

    current_section = None

    for line in text.splitlines():
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        normalized_line = normalize_heading(cleaned_line)

        detected_section = None

        for section_name, aliases in SECTION_ALIASES.items():
            if normalized_line in aliases:
                detected_section = section_name
                break

        if detected_section:
            current_section = detected_section
            continue

        if current_section:
            sections[current_section].append(cleaned_line)

    return sections

def extract_education(sections: dict[str, list[str]]) -> list[str]:
    """Return education entries from the detected education section."""

    education = sections.get("education", [])

    return education.copy()

def extract_projects(sections: dict[str, list[str]]) -> list[str]:
    """Return project entries from the detected projects section."""

    return sections.get("projects", []).copy()


def extract_certifications(sections: dict[str, list[str]]) -> list[str]:
    """Return certification entries from the detected certifications section."""

    return sections.get("certifications", []).copy()

def extract_experience(sections: dict[str, list[str]]) -> list[str]:
    """Return experience entries from the detected experience section."""

    return sections.get("experience", []).copy()

def extract_skills(sections: dict[str, list[str]]) -> list[str]:
    """Return raw skill entries from the detected skills section."""

    return sections.get("skills", []).copy()

def extract_resume_data(text: str) -> ResumeData:
    """Extract all supported information from resume text."""

    sections = detect_sections(text)

    return ResumeData(
        name=extract_name(text),
        email=extract_email(text),
        phone=extract_phone(text),
        education=extract_education(sections),
        experience=extract_experience(sections),
        projects=extract_projects(sections),
        certifications=extract_certifications(sections),
        skills=extract_skills(sections),
    )

