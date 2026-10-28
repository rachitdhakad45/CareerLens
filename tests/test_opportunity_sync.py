
import csv

from src.recommendations.opportunity_sync import sync_enabled_sources
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.opportunity_model import Opportunity, SyncRun
from src.database.opportunity_store import (
    create_database_engine,
    initialize_database,
)

COLUMNS = [
    "source_id",
    "company",
    "platform",
    "board_identifier",
    "enabled",
    "last_synced_at",
]


def create_registry(path, rows):
    """Create a temporary opportunity source registry."""
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def make_source(source_id, board, enabled="true", platform="greenhouse"):
    """Create a test source configuration."""
    return {
        "source_id": source_id,
        "company": f"Company {source_id}",
        "platform": platform,
        "board_identifier": board,
        "enabled": enabled,
        "last_synced_at": "",
    }


def make_job(job_id, title, url=None):
    """Create a valid Greenhouse-like job record."""
    return {
        "id": job_id,
        "title": title,
        "absolute_url": url or f"https://example.com/jobs/{job_id}",
        "location": {"name": "Remote"},
        "content": "Example job description",
        "departments": [],
    }


def test_sync_fetches_jobs_from_enabled_sources(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [
            make_source("GH-001", "board-one"),
            make_source("GH-002", "board-two"),
            make_source("GH-003", "board-three", enabled="false"),
        ],
    )

    calls = []

    def fake_fetcher(board):
        calls.append(board)
        return [make_job(1, f"Job from {board}")]

    report = sync_enabled_sources(registry, fetcher=fake_fetcher)

    assert calls == ["board-one", "board-two"]
    assert report["sources_configured"] == 2
    assert report["sources_succeeded"] == 2
    assert report["sources_failed"] == 0
    assert report["jobs_fetched"] == 2
    assert report["jobs_saved"] == 0  # No database engine was supplied.
    assert report["results"][0]["job_count"] == 1
    assert report["results"][0]["fetched_at"]
    assert report["results"][0]["job_errors"] == []


def test_empty_registry_has_no_results_or_errors(tmp_path):
    registry = create_registry(tmp_path / "sources.csv", [])

    report = sync_enabled_sources(registry)

    assert report["sources_configured"] == 0
    assert report["sources_succeeded"] == 0
    assert report["sources_failed"] == 0
    assert report["jobs_fetched"] == 0
    assert report["jobs_saved"] == 0
    assert report["results"] == []
    assert report["errors"] == []


def test_one_source_failure_does_not_stop_other_sources(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [
            make_source("GH-001", "working-board"),
            make_source("GH-002", "broken-board"),
        ],
    )

    def fake_fetcher(board):
        if board == "broken-board":
            raise ValueError("simulated failure")
        return [make_job(10, "Working job")]

    report = sync_enabled_sources(registry, fetcher=fake_fetcher)

    assert report["sources_succeeded"] == 1
    assert report["sources_failed"] == 1
    assert report["jobs_fetched"] == 1
    assert report["jobs_saved"] == 0
    assert report["results"][0]["source_id"] == "GH-001"
    assert report["errors"][0]["source_id"] == "GH-002"
    assert "simulated failure" in report["errors"][0]["error"]


def test_unsupported_connector_is_reported(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [
            make_source(
                "LV-001",
                "example",
                platform="lever",
            )
        ],
    )

    report = sync_enabled_sources(registry)

    assert report["sources_configured"] == 1
    assert report["sources_succeeded"] == 0
    assert report["sources_failed"] == 1
    assert "No connector implemented" in report["errors"][0]["error"]


def test_sync_persists_jobs_to_database(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)

    def fake_fetcher(board):
        return [make_job(101, "Python Intern")]

    try:
        report = sync_enabled_sources(
            registry,
            fetcher=fake_fetcher,
            engine=engine,
        )

        assert report["sources_succeeded"] == 1
        assert report["jobs_fetched"] == 1
        assert report["jobs_saved"] == 1

        with Session(engine) as session:
            records = session.scalars(select(Opportunity)).all()

        assert len(records) == 1
        assert records[0].external_id == "101"
        assert records[0].title == "Python Intern"
        assert records[0].status == "open"
    finally:
        engine.dispose()


def test_repeated_sync_updates_existing_job_without_duplicate(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)

    title = {"value": "Python Intern"}

    def fake_fetcher(board):
        return [make_job(101, title["value"])]

    try:
        first_report = sync_enabled_sources(
            registry, fetcher=fake_fetcher, engine=engine
        )
        title["value"] = "Python Intern - Updated"
        second_report = sync_enabled_sources(
            registry, fetcher=fake_fetcher, engine=engine
        )

        assert first_report["jobs_saved"] == 1
        assert second_report["jobs_saved"] == 1

        with Session(engine) as session:
            records = session.scalars(select(Opportunity)).all()

        assert len(records) == 1
        assert records[0].title == "Python Intern - Updated"
    finally:
        engine.dispose()


def test_source_failure_preserves_existing_database_records(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)

    def working_fetcher(board):
        return [make_job(101, "Python Intern")]

    try:
        sync_enabled_sources(
            registry, fetcher=working_fetcher, engine=engine
        )

        def failing_fetcher(board):
            raise ValueError("simulated source outage")

        report = sync_enabled_sources(
            registry, fetcher=failing_fetcher, engine=engine
        )

        assert report["sources_failed"] == 1

        with Session(engine) as session:
            records = session.scalars(select(Opportunity)).all()

        assert len(records) == 1
        assert records[0].title == "Python Intern"
        assert records[0].status == "open"
    finally:
        engine.dispose()


def test_complete_nonempty_snapshot_closes_missing_source_listings(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)
    try:
        from src.database.opportunity_store import upsert_opportunity

        upsert_opportunity(
            engine,
            source_id="GH-001",
            external_id="stale",
            title="Old Job",
            company="Company GH-001",
            opportunity_type="job",
            url="https://example.com/jobs/stale",
        )
        sync_enabled_sources(
            registry,
            fetcher=lambda board: [make_job(401, "Current Job")],
            engine=engine,
        )
        report = sync_enabled_sources(
            registry,
            fetcher=lambda board: [make_job(401, "Current Job Updated")],
            engine=engine,
        )

        with Session(engine) as session:
            records = {
                row.external_id: row.status
                for row in session.scalars(select(Opportunity)).all()
            }

        assert records == {"401": "open", "stale": "closed"}
        assert report["results"][0]["closed_count"] == 1
    finally:
        engine.dispose()


def test_one_missing_snapshot_does_not_close_a_listing(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)
    try:
        sync_enabled_sources(
            registry,
            fetcher=lambda board: [
                make_job(701, "Still Current"),
                make_job(702, "May Be Stale"),
            ],
            engine=engine,
        )
        sync_enabled_sources(
            registry,
            fetcher=lambda board: [make_job(701, "Still Current")],
            engine=engine,
        )

        with Session(engine) as session:
            record = session.scalar(
                select(Opportunity).where(Opportunity.external_id == "702")
            )
        assert record.status == "open"

        sync_enabled_sources(
            registry,
            fetcher=lambda board: [make_job(701, "Still Current")],
            engine=engine,
        )

        with Session(engine) as session:
            record = session.scalar(
                select(Opportunity).where(Opportunity.external_id == "702")
            )
        assert record.status == "closed"
    finally:
        engine.dispose()


def test_empty_snapshot_preserves_existing_open_listings(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)
    try:
        sync_enabled_sources(
            registry,
            fetcher=lambda board: [make_job(501, "Keep This Job")],
            engine=engine,
        )
        report = sync_enabled_sources(
            registry, fetcher=lambda board: [], engine=engine
        )

        with Session(engine) as session:
            record = session.scalar(select(Opportunity))
            run = session.scalar(
                select(SyncRun).order_by(SyncRun.id.desc())
            )

        assert record.status == "open"
        assert report["sources_partially_succeeded"] == 1
        assert report["results"][0]["closed_count"] == 0
        assert run.status == "partially_succeeded"
        assert "empty snapshot" in run.error_message
    finally:
        engine.dispose()


def test_partial_snapshot_does_not_close_missing_listings(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)
    try:
        sync_enabled_sources(
            registry,
            fetcher=lambda board: [make_job(601, "Existing Job")],
            engine=engine,
        )
        report = sync_enabled_sources(
            registry,
            fetcher=lambda board: [
                make_job(602, "Valid Job"),
                {"id": 603, "title": "Invalid Job"},
            ],
            engine=engine,
        )

        with Session(engine) as session:
            records = {
                row.external_id: row.status
                for row in session.scalars(select(Opportunity)).all()
            }

        assert records == {"601": "open", "602": "open"}
        assert report["results"][0]["closed_count"] == 0
        assert report["sources_partially_succeeded"] == 1
    finally:
        engine.dispose()


def test_invalid_job_is_not_saved(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)

    def fake_fetcher(board):
        return [{"id": 102, "title": "Missing application URL"}]

    try:
        report = sync_enabled_sources(
            registry, fetcher=fake_fetcher, engine=engine
        )

        assert report["jobs_fetched"] == 1
        assert report["jobs_saved"] == 0
        assert len(report["errors"]) == 1

        with Session(engine) as session:
            records = session.scalars(select(Opportunity)).all()

        assert records == []
    finally:
        engine.dispose()


def test_successful_sync_records_history(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)

    try:
        report = sync_enabled_sources(
            registry,
            fetcher=lambda board: [
                make_job(201, "Python Intern"),
                make_job(202, "Data Analyst"),
            ],
            engine=engine,
        )

        with Session(engine) as session:
            runs = session.scalars(select(SyncRun)).all()

        assert len(runs) == 1
        assert runs[0].status == "succeeded"
        assert runs[0].jobs_fetched == 2
        assert runs[0].jobs_saved == 2
        assert runs[0].jobs_rejected == 0
        assert runs[0].finished_at is not None
        assert report["sources_succeeded"] == 1
    finally:
        engine.dispose()


def test_invalid_job_records_partial_success_in_history(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)

    try:
        report = sync_enabled_sources(
            registry,
            fetcher=lambda board: [
                make_job(203, "Valid Job"),
                {"id": 204, "title": "Missing URL"},
            ],
            engine=engine,
        )

        with Session(engine) as session:
            runs = session.scalars(select(SyncRun)).all()

        assert len(runs) == 1
        assert runs[0].status == "partially_succeeded"
        assert runs[0].jobs_fetched == 2
        assert runs[0].jobs_saved == 1
        assert runs[0].jobs_rejected == 1
        assert runs[0].error_message
        assert report["jobs_saved"] == 1
    finally:
        engine.dispose()


def test_api_failure_records_failed_history(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)

    def failing_fetcher(board):
        raise ValueError("simulated API outage")

    try:
        report = sync_enabled_sources(
            registry,
            fetcher=failing_fetcher,
            engine=engine,
        )

        with Session(engine) as session:
            runs = session.scalars(select(SyncRun)).all()

        assert len(runs) == 1
        assert runs[0].status == "failed"
        assert runs[0].finished_at is not None
        assert "simulated API outage" in runs[0].error_message
        assert report["sources_failed"] == 1
    finally:
        engine.dispose()


def test_multiple_invalid_jobs_count_as_one_partial_source(tmp_path):
    registry = create_registry(
        tmp_path / "sources.csv",
        [make_source("GH-001", "board-one")],
    )
    engine = create_database_engine(
        f"sqlite:///{tmp_path / 'careerlens.db'}"
    )
    initialize_database(engine)

    try:
        report = sync_enabled_sources(
            registry,
            fetcher=lambda board: [
                {"id": 301, "title": "Missing URL"},
                {"id": 302, "absolute_url": "https://example.com/302"},
                {"id": 303, "title": "Also missing URL"},
            ],
            engine=engine,
        )

        assert report["sources_configured"] == 1
        assert report["sources_succeeded"] == 0
        assert report["sources_partially_succeeded"] == 1
        assert report["sources_failed"] == 0
        assert report["jobs_fetched"] == 3
        assert report["jobs_saved"] == 0
        assert len(report["errors"]) == 1
        assert len(report["errors"][0]["details"]) == 3
    finally:
        engine.dispose()


from src.recommendations.opportunity_sync import normalize_greenhouse_job


def test_normalizer_extracts_known_skills_from_job_description():
    source = {
        "source_id": "GH-TEST",
        "company": "Example Company",
        "platform": "greenhouse",
        "board_identifier": "example",
        "enabled": True,
        "last_synced_at": "",
    }

    job = {
        "id": 123,
        "title": "Python Data Analyst",
        "absolute_url": "https://example.com/jobs/123",
        "location": {"name": "Remote"},
        "content": (
            "<p>Required skills: Python, SQL, Pandas and NumPy.</p>"
        ),
        "departments": [{"name": "Data"}],
    }

    normalized = normalize_greenhouse_job(job, source)

    assert {"python", "sql", "pandas", "numpy"} <= set(
        normalized["skills"].split(";")
    )


def test_normalizer_does_not_invent_unknown_job_metadata():
    source = {
        "source_id": "GH-TEST",
        "company": "Example Company",
        "platform": "greenhouse",
        "board_identifier": "example",
        "enabled": True,
        "last_synced_at": "",
    }

    job = {
        "id": 456,
        "title": "Software Engineer",
        "absolute_url": "https://example.com/jobs/456",
        "location": {"name": "New York"},
        "content": "<p>Build reliable software systems.</p>",
        "departments": [],
    }

    normalized = normalize_greenhouse_job(job, source)

    assert normalized["skills"] == ""
    assert normalized["career_families"] == ""
    assert normalized["eligibility"] == ""
    assert normalized["compensation"] == ""
    assert normalized["deadline"] == ""
    assert normalized["location"] == "New York"


def test_normalizer_rejects_non_https_application_urls():
    source = {
        "source_id": "GH-TEST",
        "company": "Example Company",
    }
    job = {
        "id": 999,
        "title": "Unsafe URL Listing",
        "absolute_url": "javascript:alert(1)",
    }

    import pytest

    with pytest.raises(ValueError, match="HTTPS"):
        normalize_greenhouse_job(job, source)
