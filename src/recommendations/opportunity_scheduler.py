
"""Schedule automatic synchronization of job opportunities."""

import logging
import os
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.database.opportunity_store import (
    create_database_engine,
    initialize_database,
)
from src.recommendations.opportunity_sync import sync_enabled_sources


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = (
    f"sqlite:///{(PROJECT_ROOT / 'data' / 'careerlens.db').as_posix()}"
)


def run_sync(database_url: str | None = None) -> dict:
    """Run one synchronization cycle and log its outcome."""
    url = database_url or os.getenv(
        "CAREERLENS_DATABASE_URL",
        DEFAULT_DATABASE_URL,
    )

    engine = create_database_engine(url)

    try:
        initialize_database(engine)
        logger.info("Starting opportunity synchronization.")

        result = sync_enabled_sources(engine=engine)

        logger.info(
            "Sync finished: %s sources configured, %s succeeded, "
            "%s partially succeeded, %s failed; %s jobs fetched, "
            "%s saved, %s rejected, %s closed.",
            result["sources_configured"],
            result["sources_succeeded"],
            result["sources_partially_succeeded"],
            result["sources_failed"],
            result["jobs_fetched"],
            result["jobs_saved"],
            result["jobs_rejected"],
            result["jobs_closed"],
        )

        for error in result["errors"]:
            logger.error(
                "Source sync issue for %s: %s",
                error.get("source_id", "unknown"),
                error["error"],
            )

        return result
    except Exception:
        logger.exception("Opportunity synchronization failed.")
        raise
    finally:
        engine.dispose()


def start_scheduler(interval_minutes: int = 30) -> None:
    """Run one sync immediately, then repeat at the configured interval."""
    if (
        not isinstance(interval_minutes, int)
        or isinstance(interval_minutes, bool)
        or interval_minutes < 1
    ):
        raise ValueError("interval_minutes must be a positive integer.")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    scheduler = BlockingScheduler(timezone="UTC")

    # Initial attempt: a failed sync is logged, and the scheduler still starts.
    try:
        run_sync()
    except Exception:
        logger.exception("Initial sync failed; scheduled retries will continue.")

    scheduler.add_job(
        run_sync,
        trigger=IntervalTrigger(minutes=interval_minutes, timezone="UTC"),
        id="opportunity_sync",
        name="Synchronize job opportunities",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    logger.info(
        "Scheduler started. Next automatic sync interval: %s minutes.",
        interval_minutes,
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Opportunity scheduler stopped.")
        scheduler.shutdown(wait=False)
