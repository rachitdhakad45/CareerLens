
"""Recommend opportunities using candidate skill gaps."""

import csv
import re
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy.engine import Engine

from src.database.opportunity_store import list_open_opportunities
from src.nlp.skill_extractor import normalize_skill
from src.recommendations.career_requirements import (
    CAREER_REQUIREMENTS,
    SKILL_PRIORITIES,
)
from src.recommendations.skill_gap import analyze_skill_gap


DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "opportunity_catalog.csv"
)

REQUIRED_COLUMNS = {
    "opportunity_id",
    "title",
    "company",
    "opportunity_type",
    "url",
    "skills",
    "career_families",
    "location",
    "work_mode",
    "experience_level",
    "eligibility",
    "compensation",
    "deadline",
    "source",
    "description",
    "status",
    "last_verified",
}

PRIORITY_POINTS = {
    "high": 3,
    "medium": 2,
    "low": 1,
}

MAX_VERIFICATION_AGE_DAYS = 30

CAREER_FAMILY_TERMS = {
    "Software Engineering": (
        "software", "developer", "platform", "infrastructure",
        "backend", "frontend", "mobile", "security engineering",
        "systems engineering", "technology",
    ),
    "Data & Analytics": (
        "analytics", "data science", "data analyst", "business intelligence",
        "insights", "quantitative research",
    ),
    "Finance & Accounting": (
        "finance", "accounting", "financial", "treasury", "audit", "tax",
    ),
    "Graphic & Creative Design": (
        "creative", "graphic design", "illustration", "brand design",
        "visual design", "art direction",
    ),
    "Human Resources": (
        "human resources", "people team", "recruiting", "recruitment",
        "talent acquisition", "employee relations",
    ),
    "Marketing & Growth": (
        "marketing", "growth", "communications", "content marketing",
        "digital marketing", "seo", "campaigns",
    ),
    "Project & Product Management": (
        "product management", "product manager", "project management",
        "program management", "product operations",
    ),
    "Sales & Business Development": (
        "sales", "account executive", "business development", "revenue",
        "customer success", "partnerships",
    ),
    "Core Engineering": (
        "mechanical", "electrical", "manufacturing", "hardware",
        "civil engineering", "quality engineering", "engineering design",
    ),
    "UI/UX & Product Design": (
        "user experience", "user research", "interaction design", "product design",
        "design systems", "ux", "ui",
    ),
}

COMMON_CROSS_ROLE_SKILLS = {
    "python", "sql", "excel", "communication", "data analysis",
    "statistics", "leadership", "problem solving", "figma", "visual design",
}


def _matches_career_family(
    opportunity: dict,
    career_family: str,
    career_families: set[str],
    role_skill_overlap: list[str],
) -> bool:
    """Bridge source-specific departments to CareerLens role categories."""
    if career_family in career_families:
        return True

    source_labels = " ".join((
        opportunity.get("title", ""),
        opportunity.get("career_families", ""),
    )).casefold()
    if any(
        re.search(r"\b" + re.escape(term) + r"\b", source_labels)
        for term in CAREER_FAMILY_TERMS.get(career_family, ())
    ):
        return True

    specific_overlap = set(role_skill_overlap) - COMMON_CROSS_ROLE_SKILLS
    return bool(specific_overlap)


def load_opportunity_catalog(catalog_path=None) -> list[dict]:
    """Load and validate the legacy CSV opportunity catalog."""
    path = (
        Path(catalog_path)
        if catalog_path is not None
        else DEFAULT_CATALOG_PATH
    )

    if not path.is_file():
        raise FileNotFoundError(f"Opportunity catalog not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("Opportunity catalog has no header.")

        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing_columns:
            raise ValueError(
                "Opportunity catalog is missing columns: "
                f"{sorted(missing_columns)}"
            )

        opportunities = []

        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV row: {row_number}")

            if not row["opportunity_id"].strip():
                raise ValueError(
                    f"Missing opportunity_id on row {row_number}"
                )

            if not row["title"].strip():
                raise ValueError(f"Missing title on row {row_number}")

            opportunities.append(row)

    return opportunities


def load_database_opportunities(engine: Engine) -> list[dict]:
    """Map open database records to the recommender's common schema."""
    records = list_open_opportunities(engine)
    opportunities = []

    for record in records:
        verified_at = record.last_verified_at

        # Database timestamps are expected to be timezone-aware UTC.
        # Treat naive values as unverified rather than guessing a timezone.
        if (
            verified_at is not None
            and verified_at.tzinfo is not None
            and verified_at.utcoffset() is not None
        ):
            verified_date = verified_at.astimezone(timezone.utc).date()
            verified_text = verified_date.isoformat()
        else:
            verified_text = ""

        opportunities.append({
            "opportunity_id": (
                f"{record.source_id}:{record.external_id}"
            ),
            "title": record.title,
            "company": record.company,
            "opportunity_type": record.opportunity_type,
            "url": record.url,
            "skills": record.skills or "",
            "career_families": record.career_families or "",
            "location": record.location or "",
            "work_mode": record.work_mode or "",
            "experience_level": record.experience_level or "",
            "eligibility": record.eligibility or "",
            "compensation": record.compensation or "",
            "deadline": record.deadline or "",
            "source": record.source_id,
            "description": record.description or "",
            "status": record.status,
            "last_verified": verified_text,
        })

    return opportunities


def recommend_opportunities(
    resume_text: str,
    career_family: str,
    top_n: int = 5,
    catalog_path=None,
    today: date | None = None,
    engine: Engine | None = None,
    include_related: bool = False,
) -> list[dict]:
    """
    Recommend open, recently verified opportunities.

    Pass engine to use the database. Otherwise, use the legacy CSV
    catalog. Scores represent skill relevance, not hiring probability.
    include_related also returns jobs whose source departments differ from
    CareerLens role names, when their extracted skills overlap that role.
    """
    if (
        not isinstance(top_n, int)
        or isinstance(top_n, bool)
        or top_n < 1
    ):
        raise ValueError("top_n must be a positive integer.")

    if engine is not None and catalog_path is not None:
        raise ValueError(
            "Pass either engine or catalog_path, not both."
        )

    current_date = today or date.today()
    gap = analyze_skill_gap(resume_text, career_family)

    missing_priorities = {
        normalize_skill(item["skill"]): item["priority"]
        for item in gap["missing_skills"]
    }

    if not missing_priorities and not include_related:
        return []

    role_skills = {
        normalize_skill(skill)
        for group in CAREER_REQUIREMENTS[career_family].values()
        for skill in group
    }

    if engine is not None:
        opportunities = load_database_opportunities(engine)
    else:
        opportunities = load_opportunity_catalog(catalog_path)

    recommendations = []

    for opportunity in opportunities:
        if opportunity["status"].strip().lower() != "open":
            continue

        try:
            verified_date = datetime.strptime(
                opportunity["last_verified"].strip(),
                "%Y-%m-%d",
            ).date()
        except (ValueError, AttributeError):
            continue

        age_days = (current_date - verified_date).days

        if age_days < 0 or age_days > MAX_VERIFICATION_AGE_DAYS:
            continue

        deadline_text = opportunity["deadline"].strip()

        if deadline_text:
            try:
                deadline = datetime.strptime(
                    deadline_text,
                    "%Y-%m-%d",
                ).date()
            except ValueError:
                continue

            if deadline < current_date:
                continue

        career_families = {
            family.strip()
            for family in opportunity["career_families"].split(";")
            if family.strip()
        }

        opportunity_skills = {
            normalize_skill(skill)
            for skill in opportunity["skills"].split(";")
            if skill.strip()
        }

        role_skill_overlap = sorted(opportunity_skills & role_skills)
        # Greenhouse departments use employer-specific labels (for example,
        # "Security Analytics") rather than CareerLens's normalized roles.
        # Use source labels or distinctive role skills as a transparent bridge.
        if not _matches_career_family(
            opportunity,
            career_family,
            career_families,
            role_skill_overlap,
        ):
            continue

        matched_skills = sorted(
            opportunity_skills & missing_priorities.keys()
        )

        if not matched_skills and not include_related:
            continue

        priority_score = sum(
            PRIORITY_POINTS.get(missing_priorities[skill], 2)
            for skill in matched_skills
        )

        if matched_skills:
            reason = "Matches missing skills: " + ", ".join(matched_skills)
        elif role_skill_overlap:
            reason = (
                f"Related to {career_family} through: "
                + ", ".join(role_skill_overlap[:4])
            )
        else:
            reason = f"Listed in the {career_family} career family."

        recommendations.append({
            "opportunity_id": opportunity["opportunity_id"].strip(),
            "title": opportunity["title"].strip(),
            "company": opportunity["company"].strip(),
            "opportunity_type": opportunity["opportunity_type"].strip(),
            "url": opportunity["url"].strip(),
            "matched_skills": matched_skills,
            "role_skills_matched": role_skill_overlap,
            "priority_score": priority_score,
            "location": opportunity["location"].strip(),
            "work_mode": opportunity["work_mode"].strip(),
            "experience_level": opportunity["experience_level"].strip(),
            "eligibility": opportunity["eligibility"].strip(),
            "compensation": opportunity["compensation"].strip(),
            "deadline": deadline_text,
            "source": opportunity["source"].strip(),
            "last_verified": opportunity["last_verified"].strip(),
            "reason": reason,
        })

    recommendations.sort(
        key=lambda item: (
            -item["priority_score"],
            -len(item["matched_skills"]),
            -len(item["role_skills_matched"]),
            item["title"].lower(),
        )
    )

    unique_recommendations = []
    seen_ids = set()

    for recommendation in recommendations:
        opportunity_id = recommendation["opportunity_id"]

        if opportunity_id not in seen_ids:
            unique_recommendations.append(recommendation)
            seen_ids.add(opportunity_id)

    return unique_recommendations[:top_n]
