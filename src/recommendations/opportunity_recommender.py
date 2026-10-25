
"""Recommend opportunities using candidate skill gaps."""

import csv
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy.engine import Engine

from src.database.opportunity_store import list_open_opportunities
from src.nlp.skill_extractor import normalize_skill
from src.recommendations.career_requirements import SKILL_PRIORITIES
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
) -> list[dict]:
    """
    Recommend open, recently verified opportunities.

    Pass engine to use the database. Otherwise, use the legacy CSV
    catalog. Scores represent skill relevance, not hiring probability.
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

    if not missing_priorities:
        return []

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

        if career_family not in career_families:
            continue

        opportunity_skills = {
            normalize_skill(skill)
            for skill in opportunity["skills"].split(";")
            if skill.strip()
        }

        matched_skills = sorted(
            opportunity_skills & missing_priorities.keys()
        )

        if not matched_skills:
            continue

        priority_score = sum(
            PRIORITY_POINTS.get(missing_priorities[skill], 2)
            for skill in matched_skills
        )

        recommendations.append({
            "opportunity_id": opportunity["opportunity_id"].strip(),
            "title": opportunity["title"].strip(),
            "company": opportunity["company"].strip(),
            "opportunity_type": opportunity["opportunity_type"].strip(),
            "url": opportunity["url"].strip(),
            "matched_skills": matched_skills,
            "priority_score": priority_score,
            "location": opportunity["location"].strip(),
            "work_mode": opportunity["work_mode"].strip(),
            "experience_level": opportunity["experience_level"].strip(),
            "eligibility": opportunity["eligibility"].strip(),
            "compensation": opportunity["compensation"].strip(),
            "deadline": deadline_text,
            "source": opportunity["source"].strip(),
            "last_verified": opportunity["last_verified"].strip(),
            "reason": "Matches missing skills: " + ", ".join(matched_skills),
        })

    recommendations.sort(
        key=lambda item: (
            -item["priority_score"],
            -len(item["matched_skills"]),
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
