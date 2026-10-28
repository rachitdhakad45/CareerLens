
"""Database operations for CareerLens opportunities."""

from datetime import datetime, timezone

from sqlalchemy import create_engine, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.database.opportunity_model import Base, Opportunity, SyncRun


def create_database_engine(database_url: str = "sqlite:///data/careerlens.db") -> Engine:
    """Create a SQLAlchemy engine for SQLite or PostgreSQL."""
    if not isinstance(database_url, str) or not database_url.strip():
        raise ValueError("database_url must be a non-empty string.")

    return create_engine(database_url, pool_pre_ping=True)


def initialize_database(engine: Engine) -> None:
    """Create tables defined by the registered SQLAlchemy models."""
    Base.metadata.create_all(engine)


def upsert_opportunity(
    engine: Engine,
    *,
    source_id: str,
    external_id: str,
    title: str,
    company: str,
    opportunity_type: str,
    url: str,
    skills: str = "",
    career_families: str = "",
    location: str = "",
    work_mode: str = "",
    experience_level: str = "",
    eligibility: str = "",
    compensation: str = "",
    deadline: str = "",
    description: str = "",
    status: str = "open",
    seen_at: datetime | None = None,
) -> Opportunity:
    """Insert a new listing or update an existing listing from the same source.

    A successful upsert refreshes last_seen_at and last_verified_at.
    This function does not close listings that disappear from a source.
    """
    required = {
        "source_id": source_id,
        "external_id": external_id,
        "title": title,
        "company": company,
        "opportunity_type": opportunity_type,
        "url": url,
    }
    for field, value in required.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string.")

    allowed_statuses = {"open", "closed", "expired", "unknown"}
    if status not in allowed_statuses:
        raise ValueError(f"status must be one of {sorted(allowed_statuses)}.")

    now = seen_at or datetime.now(timezone.utc)
    values = {
        "title": title.strip(),
        "company": company.strip(),
        "opportunity_type": opportunity_type.strip(),
        "url": url.strip(),
        "skills": skills.strip(),
        "career_families": career_families.strip(),
        "location": location.strip(),
        "work_mode": work_mode.strip(),
        "experience_level": experience_level.strip(),
        "eligibility": eligibility.strip(),
        "compensation": compensation.strip(),
        "deadline": deadline.strip(),
        "description": description.strip(),
        "status": status,
        "last_seen_at": now,
        "last_verified_at": now,
    }

    with Session(engine) as session:
        record = session.scalar(
            select(Opportunity).where(
                Opportunity.source_id == source_id.strip(),
                Opportunity.external_id == external_id.strip(),
            )
        )

        if record is None:
            record = Opportunity(
                source_id=source_id.strip(),
                external_id=external_id.strip(),
                first_seen_at=now,
                **values,
            )
            session.add(record)
        else:
            for field, value in values.items():
                setattr(record, field, value)

        session.commit()
        session.refresh(record)
        session.expunge(record)
        return record


def list_open_opportunities(engine: Engine) -> list[Opportunity]:
    """Return currently open opportunities, ordered by company and title."""
    with Session(engine) as session:
        records = session.scalars(
            select(Opportunity)
            .where(Opportunity.status == "open")
            .order_by(Opportunity.company, Opportunity.title)
        ).all()
        for record in records:
            session.expunge(record)
        return list(records)


def close_missing_opportunities(
    engine: Engine,
    *,
    source_id: str,
    seen_external_ids: set[str],
    stale_before: datetime | None,
) -> int:
    """Close previously open source listings absent from a complete snapshot.

    Callers must only use this after a successful, fully processed fetch and
    an immediately preceding successful run. Empty snapshots are rejected;
    the timestamp also requires each closing candidate to have been absent
    from both complete snapshots.
    """
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string.")
    if not isinstance(seen_external_ids, set) or not seen_external_ids:
        raise ValueError("A non-empty set of seen listing IDs is required.")
    if stale_before is None:
        return 0
    if stale_before.tzinfo is None:
        raise ValueError("stale_before must be timezone-aware.")

    with Session(engine) as session:
        query = update(Opportunity).where(
            Opportunity.source_id == source_id.strip(),
            Opportunity.status == "open",
            Opportunity.external_id.not_in(seen_external_ids),
            Opportunity.last_seen_at < stale_before,
        ).values(status="closed")
        result = session.execute(query)
        session.commit()
        return result.rowcount or 0


def previous_sync_was_successful(
    engine: Engine,
    *,
    source_id: str,
    before_run_id: int,
) -> datetime | None:
    """Return the immediately previous run start only if it succeeded."""
    with Session(engine) as session:
        previous = session.scalar(
            select(SyncRun)
            .where(
                SyncRun.source_id == source_id,
                SyncRun.id < before_run_id,
            )
            .order_by(SyncRun.id.desc())
            .limit(1)
        )
        if previous is None or previous.status != "succeeded":
            return None
        return previous.started_at


def start_sync_run(
    engine: Engine,
    *,
    source_id: str,
    company: str = "",
) -> int:
    """Create a running sync-history record and return its ID."""
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string.")

    with Session(engine) as session:
        record = SyncRun(
            source_id=source_id.strip(),
            company=company.strip(),
            status="running",
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.id


def finish_sync_run(
    engine: Engine,
    *,
    run_id: int,
    status: str,
    jobs_fetched: int = 0,
    jobs_saved: int = 0,
    jobs_rejected: int = 0,
    error_message: str = "",
) -> None:
    """Finish a sync-history record with its outcome and counts."""
    allowed_statuses = {
        "succeeded",
        "partially_succeeded",
        "failed",
    }
    if status not in allowed_statuses:
        raise ValueError(
            f"status must be one of {sorted(allowed_statuses)}."
        )

    counts = {
        "jobs_fetched": jobs_fetched,
        "jobs_saved": jobs_saved,
        "jobs_rejected": jobs_rejected,
    }
    for field, value in counts.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{field} must be a non-negative integer.")

    with Session(engine) as session:
        record = session.get(SyncRun, run_id)
        if record is None:
            raise ValueError(f"Sync run {run_id} does not exist.")

        if record.status != "running":
            raise ValueError(f"Sync run {run_id} has already finished.")

        from datetime import datetime, timezone

        record.status = status
        record.finished_at = datetime.now(timezone.utc)
        record.jobs_fetched = jobs_fetched
        record.jobs_saved = jobs_saved
        record.jobs_rejected = jobs_rejected
        record.error_message = error_message.strip()

        session.commit()
