from pathlib import Path
import csv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_PATH = PROJECT_ROOT / "data" / "career_taxonomy.csv"


def load_career_taxonomy() -> list[dict[str, str]]:
    """Load the CareerLens career taxonomy."""

    if not TAXONOMY_PATH.exists():
        raise FileNotFoundError(
            f"Career taxonomy file not found: {TAXONOMY_PATH}"
        )

    with TAXONOMY_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        taxonomy = list(reader)

    required_columns = {
        "domain",
        "career_family",
        "career",
    }

    if not required_columns.issubset(reader.fieldnames or []):
        missing_columns = required_columns - set(reader.fieldnames or [])

        raise ValueError(
            f"Career taxonomy is missing columns: "
            f"{sorted(missing_columns)}"
        )

    return taxonomy