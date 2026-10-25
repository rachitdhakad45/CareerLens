
"""Entry point for the CareerLens opportunity-sync worker."""

import argparse
import logging
import sys
from pathlib import Path


# Ensure the project root is importable when this file is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.recommendations.opportunity_scheduler import start_scheduler


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Automatically synchronize CareerLens job opportunities."
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Minutes between syncs (default: 30).",
    )
    args = parser.parse_args()

    if args.interval < 1:
        parser.error("--interval must be at least 1 minute.")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    start_scheduler(interval_minutes=args.interval)


if __name__ == "__main__":
    main()
