
"""Fetch, normalize, and persist opportunities from configured sources."""

from datetime import datetime, timezone

from src.database.opportunity_store import (
    finish_sync_run,
    start_sync_run,
    upsert_opportunity,
)
from src.nlp.skill_extractor import extract_skills
from src.recommendations.source_connectors.greenhouse import (
    fetch_greenhouse_jobs,
)
from src.recommendations.source_registry import get_enabled_sources


SUPPORTED_CONNECTORS = {
    "greenhouse": fetch_greenhouse_jobs,
}


def normalize_greenhouse_job(job: dict, source: dict) -> dict:
    """Convert one Greenhouse job into CareerLens storage fields."""
    if not isinstance(job, dict):
        raise ValueError("Job record must be a dictionary.")

    if not isinstance(source, dict):
        raise ValueError("Source configuration must be a dictionary.")

    external_id = job.get("id")
    title = job.get("title")
    absolute_url = job.get("absolute_url")

    if external_id is None or not str(external_id).strip():
        raise ValueError("Greenhouse job is missing its ID.")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("Greenhouse job is missing its title.")

    if not isinstance(absolute_url, str) or not absolute_url.strip():
        raise ValueError("Greenhouse job is missing its application URL.")

    title = title.strip()
    absolute_url = absolute_url.strip()

    location_data = job.get("location") or {}
    location = (
        location_data.get("name", "")
        if isinstance(location_data, dict)
        else ""
    )
    if not isinstance(location, str):
        location = ""

    content = job.get("content") or ""
    if not isinstance(content, str):
        content = ""

    # Extract only skills recognized by CareerLens's existing taxonomy.
    searchable_text = f"{title}\n{content}"
    extracted_skills = extract_skills(searchable_text)

    departments = job.get("departments") or []
    department_names = [
        item["name"].strip()
        for item in departments
        if (
            isinstance(item, dict)
            and isinstance(item.get("name"), str)
            and item["name"].strip()
        )
    ]

    company = source.get("company", "")
    if not isinstance(company, str):
        company = ""

    source_id = source.get("source_id", "")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("Source configuration is missing its source ID.")

    return {
        "source_id": source_id.strip(),
        "external_id": str(external_id).strip(),
        "title": title,
        "company": company.strip(),
        "opportunity_type": "job",
        "url": absolute_url,
        "skills": ";".join(extracted_skills),
        "career_families": ";".join(department_names),
        "location": location.strip(),
        "work_mode": "",
        "experience_level": "",
        "eligibility": "",
        "compensation": "",
        "deadline": "",
        "description": content,
        "status": "open",
    }


def sync_enabled_sources(
    source_path=None,
    fetcher=None,
    engine=None,
) -> dict:
    """Fetch configured sources, persist jobs, and record sync history.

    If an engine is supplied, each source attempt is recorded in the
    sync-history table and valid jobs are upserted into the database.

    A source failure never closes or deletes existing opportunities.
    """
    sources = get_enabled_sources(source_path)

    results = []
    errors = []
    total_fetched = 0
    total_saved = 0

    for source in sources:
        source_id = source["source_id"]
        platform = source["platform"]
        run_id = None

        try:
            if engine is not None:
                run_id = start_sync_run(
                    engine,
                    source_id=source_id,
                    company=source["company"],
                )

            connector = (
                fetcher
                if fetcher is not None and platform == "greenhouse"
                else SUPPORTED_CONNECTORS.get(platform)
            )

            if connector is None:
                raise ValueError(
                    f"No connector implemented for platform: {platform}"
                )

            jobs = connector(source["board_identifier"])

            if not isinstance(jobs, list):
                raise ValueError("Connector must return a list of jobs.")

            total_fetched += len(jobs)
            saved_count = 0
            job_errors = []

            for job in jobs:
                try:
                    if platform != "greenhouse":
                        raise ValueError(
                            f"Normalization is not implemented for {platform}."
                        )

                    normalized = normalize_greenhouse_job(job, source)

                    if engine is not None:
                        upsert_opportunity(engine, **normalized)
                        saved_count += 1

                except ValueError as exc:
                    job_errors.append(str(exc))

            total_saved += saved_count

            result = {
                "source_id": source_id,
                "company": source["company"],
                "platform": platform,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "job_count": len(jobs),
                "saved_count": saved_count,
                "jobs": jobs,
                "job_errors": job_errors,
            }
            results.append(result)

            if job_errors:
                errors.append({
                    "source_id": source_id,
                    "company": source["company"],
                    "error": (
                        f"{len(job_errors)} job record(s) "
                        "could not be processed."
                    ),
                    "details": job_errors,
                })

            if engine is not None:
                status = (
                    "succeeded"
                    if not job_errors
                    else "partially_succeeded"
                )

                finish_sync_run(
                    engine,
                    run_id=run_id,
                    status=status,
                    jobs_fetched=len(jobs),
                    jobs_saved=saved_count,
                    jobs_rejected=len(job_errors),
                    error_message="; ".join(job_errors),
                )

        except Exception as exc:
            error_text = f"{type(exc).__name__}: {exc}"

            errors.append({
                "source_id": source_id,
                "company": source["company"],
                "error": error_text,
            })

            if engine is not None and run_id is not None:
                try:
                    finish_sync_run(
                        engine,
                        run_id=run_id,
                        status="failed",
                        error_message=error_text,
                    )
                except Exception as history_exc:
                    errors.append({
                        "source_id": source_id,
                        "company": source["company"],
                        "error": (
                            "Could not finalize sync history: "
                            f"{type(history_exc).__name__}: "
                            f"{history_exc}"
                        ),
                    })

    # Count distinct source IDs, not individual error messages.
    failed_source_ids = {
        error["source_id"]
        for error in errors
        if "details" not in error
    }

    partial_source_ids = {
        result["source_id"]
        for result in results
        if result["job_errors"]
    }

    successful_source_ids = {
        result["source_id"]
        for result in results
        if not result["job_errors"]
    }

    # Keep source outcome categories mutually exclusive.
    successful_source_ids -= partial_source_ids
    failed_source_ids -= partial_source_ids
    failed_source_ids -= successful_source_ids

    return {
        "sources_configured": len(sources),
        "sources_succeeded": len(successful_source_ids),
        "sources_partially_succeeded": len(partial_source_ids),
        "sources_failed": len(failed_source_ids),
        "jobs_fetched": total_fetched,
        "jobs_saved": total_saved,
        "results": results,
        "errors": errors,
    }
