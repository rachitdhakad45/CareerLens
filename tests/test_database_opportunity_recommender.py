
from datetime import date

from src.database.opportunity_store import (
    create_database_engine,
    initialize_database,
    upsert_opportunity,
)
from src.recommendations.opportunity_recommender import (
    load_database_opportunities,
)


def test_load_database_opportunities_maps_fields(tmp_path):
    database_path = tmp_path / "opportunities.db"
    engine = create_database_engine(f"sqlite:///{database_path}")
    initialize_database(engine)

    try:
        upsert_opportunity(
            engine,
            source_id="GH-TEST",
            external_id="123",
            title="Python Intern",
            company="Example Company",
            opportunity_type="internship",
            url="https://example.com/jobs/123",
            skills="python;sql",
            career_families="Data & Analytics",
            location="Remote",
            work_mode="remote",
            experience_level="entry-level",
            eligibility="Students",
            compensation="",
            deadline="2026-12-31",
            description="Python and SQL internship.",
            status="open",
        )

        opportunities = load_database_opportunities(engine)

        assert len(opportunities) == 1

        opportunity = opportunities[0]
        assert opportunity["opportunity_id"] == "GH-TEST:123"
        assert opportunity["title"] == "Python Intern"
        assert opportunity["skills"] == "python;sql"
        assert opportunity["source"] == "GH-TEST"
        assert opportunity["last_verified"] == date.today().isoformat()

    finally:
        engine.dispose()


def test_closed_database_opportunities_are_not_loaded(tmp_path):
    database_path = tmp_path / "opportunities.db"
    engine = create_database_engine(f"sqlite:///{database_path}")
    initialize_database(engine)

    try:
        upsert_opportunity(
            engine,
            source_id="GH-TEST",
            external_id="456",
            title="Closed Python Intern",
            company="Example Company",
            opportunity_type="internship",
            url="https://example.com/jobs/456",
            skills="python",
            career_families="Data & Analytics",
            description="Closed listing.",
            status="closed",
        )

        assert load_database_opportunities(engine) == []

    finally:
        engine.dispose()


def test_database_recommendations_match_missing_skills(tmp_path):
    database_path = tmp_path / "recommendations.db"
    engine = create_database_engine(f"sqlite:///{database_path}")
    initialize_database(engine)

    try:
        upsert_opportunity(
            engine,
            source_id="GH-TEST",
            external_id="789",
            title="Python and SQL Intern",
            company="Example Analytics",
            opportunity_type="internship",
            url="https://example.com/jobs/789",
            skills="python;sql",
            career_families="Data & Analytics",
            location="Remote",
            work_mode="remote",
            experience_level="entry-level",
            description="Internship involving Python and SQL.",
            status="open",
        )

        from src.recommendations.opportunity_recommender import (
            recommend_opportunities,
        )

        results = recommend_opportunities(
            resume_text="Technical Skills\nPython",
            career_family="Data & Analytics",
            engine=engine,
            today=date.today(),
        )

        assert len(results) == 1
        assert results[0]["title"] == "Python and SQL Intern"
        assert "sql" in results[0]["matched_skills"]
        assert results[0]["source"] == "GH-TEST"

    finally:
        engine.dispose()
