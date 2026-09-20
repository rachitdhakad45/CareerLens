from .skill_extractor import SkillMatch


def format_category_name(category: str) -> str:
    """Convert an internal category name into a user-friendly label."""

    display_names = {
        "programming": "Programming",
        "data_science": "Data Science",
        "databases": "Databases",
        "web_development": "Web Development",
        "cloud": "Cloud",
        "devops": "DevOps",
        "core_cs": "Core CS",
        "other": "Other",
    }

    return display_names.get(
        category,
        category.replace("_", " ").title(),
    )


def format_skill_name(skill: str) -> str:
    """Convert a normalized skill name into a user-friendly label."""

    display_names = {
        "python": "Python",
        "javascript": "JavaScript",
        "c++": "C++",
        "sql": "SQL",
        "dbms": "DBMS",
        "dsa": "DSA",
        "oops": "OOPs",
        "github": "GitHub",
        "git": "Git",
        "mysql": "MySQL",
        "numpy": "NumPy",
        "pandas": "Pandas",
        "scikit-learn": "Scikit-Learn",
        "eda": "EDA",
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "data science": "Data Science",
        "data analytics": "Data Analytics",
        "ai integration": "AI Integration",
        "flask": "Flask",
    }

    return display_names.get(skill, skill.title())


def prepare_skill_display(
    matches: list[SkillMatch],
) -> dict[str, list[dict]]:
    """Prepare skill matches for display in the UI."""

    grouped = {}

    for match in matches:
        category = match.category or "other"

        if category not in grouped:
            grouped[category] = []

        grouped[category].append(
            {
                "skill": format_skill_name(match.skill),
                "confidence": match.confidence,
                "evidence": match.evidence,
            }
        )

    return grouped

