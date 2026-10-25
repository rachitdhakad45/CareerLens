
"""SQLAlchemy models for CareerLens opportunity storage."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime, TypeDecorator


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Store timestamps in UTC and restore timezone information on retrieval."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        if value.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware.")

        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)


class Base(DeclarativeBase):
    """Base class for CareerLens database models."""


class Opportunity(Base):
    """A job or internship collected from an external source."""

    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    opportunity_type: Mapped[str] = mapped_column(String(100), nullable=False)

    url: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[str] = mapped_column(Text, default="", nullable=False)
    career_families: Mapped[str] = mapped_column(Text, default="", nullable=False)

    location: Mapped[str] = mapped_column(
        String(500), default="", nullable=False
    )
    work_mode: Mapped[str] = mapped_column(
        String(100), default="", nullable=False
    )
    experience_level: Mapped[str] = mapped_column(
        String(100), default="", nullable=False
    )
    eligibility: Mapped[str] = mapped_column(Text, default="", nullable=False)
    compensation: Mapped[str] = mapped_column(
        String(255), default="", nullable=False
    )

    deadline: Mapped[str] = mapped_column(
        String(50), default="", nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text, default="", nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50), default="open", nullable=False
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=utc_now, nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=utc_now, nullable=False
    )
    last_verified_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=utc_now, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "external_id",
            name="uq_opportunity_source_external",
        ),
        Index("ix_opportunity_status", "status"),
        Index("ix_opportunity_company", "company"),
    )


class SyncRun(Base):
    """Audit record for one opportunity synchronization attempt."""

    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    source_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    company: Mapped[str] = mapped_column(
        String(255), default="", nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30), nullable=False
    )

    started_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=utc_now, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime(), nullable=True
    )

    jobs_fetched: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    jobs_saved: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    jobs_rejected: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    error_message: Mapped[str] = mapped_column(
        Text, default="", nullable=False
    )
