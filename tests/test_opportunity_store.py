
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.opportunity_model import Opportunity
from src.database.opportunity_store import (
    create_database_engine,
    initialize_database,
    list_open_opportunities,
    upsert_opportunity,
)


@pytest.fixture
def engine(tmp_path):
    database_path = tmp_path / "test_careerlens.db"
    test_engine = create_database_engine(f"sqlite:///{database_path}")
    initialize_database(test_engine)
    yield test_engine
    test_engine.dispose()


def sample_opportunity(**overrides):
    values = {
        "source_id": "GH-001",
        "external_id": "123",
        "title": "Python Intern",
        "company": "Example Company",
        "opportunity_type": "internship",
        "url": "https://example.com/jobs/123",
        "skills": "python;sql",
        "career_families": "Data & Analytics",
        "location": "Remote",
        "work_mode": "remote",
        "experience_level": "entry-level",
        "eligibility": "Students",
        "compensation": "Not specified",
        "deadline": "",
        "description": "Example internship",
        "status": "open",
    }
    values.update(overrides)
    return values


def test_initialize_database_creates_opportunity_table(engine):
    with Session(engine) as session:
        assert session.scalar(select(Opportunity.id)) is None


def test_upsert_inserts_new_opportunity(engine):
    record = upsert_opportunity(engine, **sample_opportunity())

    assert record.id is not None
    assert record.title == "Python Intern"
    assert record.source_id == "GH-001"
    assert record.external_id == "123"


def test_upsert_updates_existing_record_without_duplicate(engine):
    first = upsert_opportunity(engine, **sample_opportunity())
    first_id = first.id

    second = upsert_opportunity(
        engine,
        **sample_opportunity(title="Updated Python Intern"),
    )

    assert second.id == first_id
    assert second.title == "Updated Python Intern"

    with Session(engine) as session:
        count = len(session.scalars(select(Opportunity)).all())

    assert count == 1


def test_different_sources_can_have_same_external_id(engine):
    upsert_opportunity(engine, **sample_opportunity(source_id="GH-001"))
    upsert_opportunity(engine, **sample_opportunity(source_id="GH-002"))

    with Session(engine) as session:
        count = len(session.scalars(select(Opportunity)).all())

    assert count == 2


def test_first_seen_timestamp_is_preserved_on_update(engine):
    first_time = datetime(2026, 10, 1, tzinfo=timezone.utc)
    later_time = first_time + timedelta(days=2)

    first = upsert_opportunity(
        engine,
        **sample_opportunity(),
        seen_at=first_time,
    )
    second = upsert_opportunity(
        engine,
        **sample_opportunity(title="Updated title"),
        seen_at=later_time,
    )

    assert second.first_seen_at == first.first_seen_at
    assert second.last_seen_at == later_time
    assert second.last_verified_at == later_time


def test_only_open_opportunities_are_listed(engine):
    upsert_opportunity(engine, **sample_opportunity())
    upsert_opportunity(
        engine,
        **sample_opportunity(
            source_id="GH-002",
            external_id="456",
            status="closed",
        ),
    )

    results = list_open_opportunities(engine)

    assert len(results) == 1
    assert results[0].status == "open"


def test_missing_required_field_is_rejected(engine):
    with pytest.raises(ValueError, match="title"):
        upsert_opportunity(engine, **sample_opportunity(title=" "))


def test_invalid_status_is_rejected(engine):
    with pytest.raises(ValueError, match="status"):
        upsert_opportunity(engine, **sample_opportunity(status="maybe"))


def test_updating_a_record_does_not_automatically_close_it(engine):
    upsert_opportunity(engine, **sample_opportunity())

    # A later successful update that still says open must keep it open.
    updated = upsert_opportunity(
        engine,
        **sample_opportunity(title="Python Intern - Updated", status="open"),
    )

    assert updated.status == "open"
    assert len(list_open_opportunities(engine)) == 1
