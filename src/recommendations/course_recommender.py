
import csv
from pathlib import Path

from src.nlp.skill_extractor import normalize_skill
from src.recommendations.career_requirements import SKILL_PRIORITIES
from src.recommendations.skill_gap import analyze_skill_gap


DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "course_catalog.csv"
)

REQUIRED_COLUMNS = {
    "course_id",
    "title",
    "provider",
    "url",
    "skills",
    "career_families",
    "level",
    "price",
    "duration",
    "description",
}

PRIORITY_POINTS = {
    "high": 3,
    "medium": 2,
    "low": 1,
}


def load_course_catalog(catalog_path=None) -> list[dict]:
    """Load and validate the course catalog CSV."""

    path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH

    if not path.is_file():
        raise FileNotFoundError(
            f"Course catalog not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("Course catalog has no header.")

        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)

        if missing_columns:
            raise ValueError(
                f"Course catalog is missing columns: "
                f"{sorted(missing_columns)}"
            )

        courses = []

        for row_number, row in enumerate(reader, start=2):
            if not row.get("course_id", "").strip():
                raise ValueError(
                    f"Missing course_id on CSV row {row_number}."
                )

            if not row.get("title", "").strip():
                raise ValueError(
                    f"Missing course title on CSV row {row_number}."
                )

            courses.append(row)

    return courses


def recommend_courses(
    resume_text: str,
    career_family: str,
    top_n: int = 5,
    catalog_path=None,
) -> list[dict]:
    """
    Recommend courses that target missing career skills.

    Courses are ranked using missing-skill priorities:
    high = 3 points, medium = 2 points, low = 1 point.

    The score measures priority-weighted skill coverage,
    not course quality or a student's proficiency.
    """

    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
        raise ValueError("top_n must be a positive integer.")

    # Reuse Phase 7's skill-gap analysis.
    gap = analyze_skill_gap(resume_text, career_family)

    missing_priorities = {
        normalize_skill(item["skill"]): item["priority"]
        for item in gap["missing_skills"]
    }

    if not missing_priorities:
        return []

    courses = load_course_catalog(catalog_path)
    recommendations = []

    for course in courses:
        course_families = {
            family.strip()
            for family in course["career_families"].split(";")
            if family.strip()
        }

        # Only consider courses relevant to the target career.
        if career_family not in course_families:
            continue

        course_skills = {
            normalize_skill(skill)
            for skill in course["skills"].split(";")
            if skill.strip()
        }

        matched_skills = sorted(
            course_skills & missing_priorities.keys()
        )

        # Skip courses that do not cover a missing skill.
        if not matched_skills:
            continue

        priority_score = sum(
            PRIORITY_POINTS.get(
                missing_priorities[skill],
                2,
            )
            for skill in matched_skills
        )

        priorities_covered = sorted({
            missing_priorities[skill]
            for skill in matched_skills
        })

        recommendations.append({
            "course_id": course["course_id"].strip(),
            "title": course["title"].strip(),
            "provider": course["provider"].strip(),
            "url": course["url"].strip(),
            "matched_skills": matched_skills,
            "priority_score": priority_score,
            "priorities_covered": priorities_covered,
            "level": course["level"].strip(),
            "price": course["price"].strip(),
            "duration": course["duration"].strip(),
            "description": course["description"].strip(),
            "reason": (
                "Covers missing skills: "
                + ", ".join(matched_skills)
            ),
        })

    # Rank by score, then by number of skills covered,
    # then alphabetically for consistent results.
    recommendations.sort(
        key=lambda item: (
            -item["priority_score"],
            -len(item["matched_skills"]),
            item["title"].lower(),
        )
    )

    # Prevent duplicate course IDs from appearing.
    unique_recommendations = []
    seen_ids = set()

    for recommendation in recommendations:
        course_id = recommendation["course_id"]

        if course_id not in seen_ids:
            unique_recommendations.append(recommendation)
            seen_ids.add(course_id)

    return unique_recommendations[:top_n]
