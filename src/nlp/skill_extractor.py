import re
from .taxonomy import SKILL_TAXONOMY
from dataclasses import dataclass

@dataclass
class SkillMatch:
    """Represent a detected skill with explainable evidence."""

    skill: str
    category: str | None
    confidence: float
    evidence: str

SKILL_ALIASES = {
    "python": "python",
    "c++": "c++",
    "cpp": "c++",
    "javascript": "javascript",
    "js": "javascript",

    "machine learning": "machine learning",
    "ml": "machine learning",

    "deep learning": "deep learning",
    "dl": "deep learning",

    "scikit-learn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",

    "numpy": "numpy",
    "pandas": "pandas",

    "github": "github",
    "git hub": "github",
    "git": "git",

    "sql": "sql",
    "mysql": "mysql",

    "oops": "oops",
    "object oriented programming": "oops",

    "dsa": "dsa",
    "data structures": "data structures",
    "algorithms": "algorithms",
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill name to its canonical taxonomy form."""

    normalized = skill.strip().lower()

    return SKILL_ALIASES.get(normalized, normalized)


def get_skill_category(skill: str) -> str | None:
    """Return the category containing the given skill."""

    normalized = normalize_skill(skill)

    for category, skills in SKILL_TAXONOMY.items():
        if normalized in skills:
            return category

    return None


def extract_skills(text: str) -> list[str]:
    """Extract and normalize known skills from resume text."""

    text_lower = text.lower()

    found_skills = set()

    # Check canonical skills.
    all_skills = set()

    for skills in SKILL_TAXONOMY.values():
        all_skills.update(skills)

    for skill in all_skills:
        pattern = rf"(?<!\w){re.escape(skill)}(?!\w)"

        if re.search(pattern, text_lower):
            found_skills.add(normalize_skill(skill))

    # Check known aliases.
    for alias, canonical_skill in SKILL_ALIASES.items():
        pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"

        if re.search(pattern, text_lower):
            found_skills.add(canonical_skill)

    return sorted(found_skills)

def extract_skill_matches(text: str) -> list[SkillMatch]:
    """Extract skills with category, confidence, and evidence."""

    text_lower = text.lower()
    matches = {}

    # Check canonical skills and aliases.
    all_terms = set()

    for skills in SKILL_TAXONOMY.values():
        all_terms.update(skills)

    all_terms.update(SKILL_ALIASES.keys())

    for term in all_terms:
        pattern = rf"(?<!\w){re.escape(term)}(?!\w)"

        if not re.search(pattern, text_lower):
            continue

        canonical_skill = normalize_skill(term)
        category = get_skill_category(canonical_skill)

        # Determine evidence from the resume text.
        technical_skills_section = re.search(
            r"technical skills(.*?)(?=\n\s*projects\b|\n\s*certifications\b|$)",
            text_lower,
            re.DOTALL,
        )

        project_core_skills = re.findall(
            r"core skills:(.*?)(?=\n|$)",
            text_lower,
        )

        if technical_skills_section and re.search(
            pattern,
            technical_skills_section.group(1),
        ):
            confidence = 1.00
            evidence = "Technical Skills"

        elif any(
            re.search(pattern, section)
            for section in project_core_skills
        ):
            confidence = 0.90
            evidence = "Project Core Skills"

        else:
            confidence = 0.75
            evidence = "Resume Mention"

        new_match = SkillMatch(
            skill=canonical_skill,
            category=category,
            confidence=confidence,
            evidence=evidence,
        )

        existing_match = matches.get(canonical_skill)

        if (
            existing_match is None
            or new_match.confidence > existing_match.confidence
        ):
            matches[canonical_skill] = new_match

    return sorted(
        matches.values(),
        key=lambda match: match.skill
    )

def group_skill_matches_by_category(
    matches: list[SkillMatch],
) -> dict[str, list[SkillMatch]]:
    """Group detected skill matches by their category."""

    grouped = {}

    for match in matches:
        category = match.category or "other"

        if category not in grouped:
            grouped[category] = []

        grouped[category].append(match)

    return grouped



