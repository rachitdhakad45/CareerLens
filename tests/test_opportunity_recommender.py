
import csv
from datetime import date

import pytest

from src.recommendations.opportunity_recommender import (
    load_opportunity_catalog,
    recommend_opportunities,
)


COLUMNS = [
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
]


def create_test_catalog(path):
    opportunities = [
        {
            "opportunity_id": "INT-001",
            "title": "Python Data Intern",
            "company": "Example Analytics",
            "opportunity_type": "internship",
            "url": "https://example.com/python-intern",
            "skills": "python;sql",
            "career_families": "Data & Analytics",
            "location": "Remote",
            "work_mode": "remote",
            "experience_level": "entry-level",
            "eligibility": "Students",
            "compensation": "Not specified",
            "deadline": "2026-12-31",
            "source": "Test fixture",
            "description": "Example data internship.",
            "status": "open",
            "last_verified": "2026-10-10",
        },
        {
            "opportunity_id": "INT-002",
            "title": "Data Visualization Intern",
            "company": "Example Insights",
            "opportunity_type": "internship",
            "url": "https://example.com/visualization-intern",
            "skills": "data visualization",
            "career_families": "Data & Analytics",
            "location": "Indore",
            "work_mode": "hybrid",
            "experience_level": "entry-level",
            "eligibility": "Students",
            "compensation": "Not specified",
            "deadline": "2026-12-31",
            "source": "Test fixture",
            "description": "Example visualization internship.",
            "status": "open",
            "last_verified": "2026-10-10",
        },
        {
            "opportunity_id": "INT-003",
            "title": "Expired Opportunity",
            "company": "Example Company",
            "opportunity_type": "internship",
            "url": "https://example.com/expired",
            "skills": "sql",
            "career_families": "Data & Analytics",
            "location": "Remote",
            "work_mode": "remote",
            "experience_level": "entry-level",
            "eligibility": "Students",
            "compensation": "Not specified",
            "deadline": "2026-09-01",
            "source": "Test fixture",
            "description": "Expired test listing.",
            "status": "open",
            "last_verified": "2026-10-10",
        },
        {
            "opportunity_id": "INT-004",
            "title": "Unverified Opportunity",
            "company": "Example Company",
            "opportunity_type": "internship",
            "url": "https://example.com/unverified",
            "skills": "sql",
            "career_families": "Data & Analytics",
            "location": "Remote",
            "work_mode": "remote",
            "experience_level": "entry-level",
            "eligibility": "Students",
            "compensation": "Not specified",
            "deadline": "",
            "source": "Test fixture",
            "description": "Unverified test listing.",
            "status": "unknown",
            "last_verified": "",
        },
        {
            "opportunity_id": "JOB-001",
            "title": "Software Engineer",
            "company": "Example Software",
            "opportunity_type": "full-time",
            "url": "https://example.com/software-job",
            "skills": "python;git",
            "career_families": "Software Engineering",
            "location": "Remote",
            "work_mode": "remote",
            "experience_level": "entry-level",
            "eligibility": "Graduates",
            "compensation": "Not specified",
            "deadline": "",
            "source": "Test fixture",
            "description": "Example software job.",
            "status": "open",
            "last_verified": "2026-10-10",
        },
    ]

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(opportunities)

    return path


def test_load_opportunity_catalog(tmp_path):
    catalog_path = create_test_catalog(
        tmp_path / "opportunities.csv"
    )

    opportunities = load_opportunity_catalog(catalog_path)

    assert len(opportunities) == 5
    assert opportunities[0]["title"] == "Python Data Intern"


def test_missing_catalog_file_is_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_opportunity_catalog(tmp_path / "missing.csv")


def test_recommends_relevant_open_opportunities(tmp_path):
    catalog_path = create_test_catalog(
        tmp_path / "opportunities.csv"
    )

    results = recommend_opportunities(
        resume_text="Technical Skills\nPython",
        career_family="Data & Analytics",
        catalog_path=catalog_path,
        today=date(2026, 10, 12),
    )

    ids = [item["opportunity_id"] for item in results]

    assert "INT-001" in ids
    assert "INT-002" in ids


def test_expired_deadlines_are_excluded(tmp_path):
    catalog_path = create_test_catalog(
        tmp_path / "opportunities.csv"
    )

    results = recommend_opportunities(
        resume_text="Technical Skills\nPython",
        career_family="Data & Analytics",
        catalog_path=catalog_path,
        today=date(2026, 10, 12),
    )

    ids = [item["opportunity_id"] for item in results]

    assert "INT-003" not in ids


def test_unverified_opportunities_are_excluded(tmp_path):
    catalog_path = create_test_catalog(
        tmp_path / "opportunities.csv"
    )

    results = recommend_opportunities(
        resume_text="Technical Skills\nPython",
        career_family="Data & Analytics",
        catalog_path=catalog_path,
        today=date(2026, 10, 12),
    )

    ids = [item["opportunity_id"] for item in results]

    assert "INT-004" not in ids


def test_wrong_career_family_is_excluded(tmp_path):
    catalog_path = create_test_catalog(
        tmp_path / "opportunities.csv"
    )

    results = recommend_opportunities(
        resume_text="Technical Skills\nPython",
        career_family="Data & Analytics",
        catalog_path=catalog_path,
        today=date(2026, 10, 12),
    )

    ids = [item["opportunity_id"] for item in results]

    assert "JOB-001" not in ids


def test_stale_verification_is_excluded(tmp_path):
    catalog_path = create_test_catalog(
        tmp_path / "opportunities.csv"
    )

    with catalog_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    rows[0]["last_verified"] = "2026-08-01"

    with catalog_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    results = recommend_opportunities(
        resume_text="Technical Skills\nPython",
        career_family="Data & Analytics",
        catalog_path=catalog_path,
        today=date(2026, 10, 12),
    )

    ids = [item["opportunity_id"] for item in results]

    assert "INT-001" not in ids


def test_invalid_top_n_is_rejected():
    with pytest.raises(ValueError, match="top_n"):
        recommend_opportunities(
            resume_text="Python",
            career_family="Data & Analytics",
            top_n=0,
        )
