
"""Load and validate configured opportunity sources."""

import csv
from pathlib import Path


DEFAULT_SOURCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "opportunity_sources.csv"
)

REQUIRED_COLUMNS = {
    "source_id",
    "company",
    "platform",
    "board_identifier",
    "enabled",
    "last_synced_at",
}

SUPPORTED_PLATFORMS = {
    "greenhouse",
    "lever",
    "ashby",
    "smartrecruiters",
}


def load_opportunity_sources(source_path=None) -> list[dict]:
    """Load source configuration and normalize enabled flags.

    Returns all configured sources. Disabled sources are retained so
    they can be inspected, but callers must not sync them.
    """
    path = Path(source_path) if source_path is not None else DEFAULT_SOURCE_PATH

    if not path.is_file():
        raise FileNotFoundError(f"Opportunity source registry not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("Opportunity source registry has no header.")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"Source registry is missing columns: {sorted(missing)}"
            )

        sources = []
        seen_ids = set()

        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed source registry row: {row_number}")

            source_id = row["source_id"].strip()
            company = row["company"].strip()
            platform = row["platform"].strip().lower()
            board_identifier = row["board_identifier"].strip()
            enabled_text = row["enabled"].strip().lower()

            if not source_id:
                raise ValueError(f"Missing source_id on row {row_number}")
            if source_id in seen_ids:
                raise ValueError(f"Duplicate source_id on row {row_number}")
            if enabled_text not in {"true", "false"}:
                raise ValueError(
                    f"Invalid enabled value on row {row_number}; use true or false."
                )
            if platform not in SUPPORTED_PLATFORMS:
                raise ValueError(
                    f"Unsupported platform on row {row_number}: {platform}"
                )
            if enabled_text == "true":
                if not company:
                    raise ValueError(f"Missing company on row {row_number}")
                if not board_identifier:
                    raise ValueError(
                        f"Missing board_identifier on row {row_number}"
                    )

            seen_ids.add(source_id)
            sources.append({
                "source_id": source_id,
                "company": company,
                "platform": platform,
                "board_identifier": board_identifier,
                "enabled": enabled_text == "true",
                "last_synced_at": row["last_synced_at"].strip(),
            })

    return sources


def get_enabled_sources(source_path=None, platform=None) -> list[dict]:
    """Return only enabled sources, optionally filtered by platform."""
    sources = load_opportunity_sources(source_path)
    if platform is not None:
        platform = platform.strip().lower()
        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError(f"Unsupported platform: {platform}")
        sources = [source for source in sources if source["platform"] == platform]

    return [source for source in sources if source["enabled"]]
